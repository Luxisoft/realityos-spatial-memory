"""Execute reviewed SQL migrations and hydrate media inside the caller's transaction."""

import hashlib
import re
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import bindparam, text

from app.db import Base

FIXTURES = Path(__file__).resolve().parents[3] / "simulator"
INSERT_TABLE = re.compile(r'^INSERT INTO "([a-z_]+)"')


def fixture_file(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Fixture must remain inside simulator.")
    return path


def statements(path: Path):
    pending = ""
    for line in path.read_text(encoding="utf-8").splitlines(keepends=True):
        if not pending and (not line.strip() or line.lstrip().startswith("--")):
            continue
        pending += line
        if sqlite3.complete_statement(pending):
            yield pending.strip()
            pending = ""
    if pending.strip():
        raise ValueError(f"Incomplete SQL statement in {path.name}.")


def seed_digest(root: Path, filename: str) -> str:
    return hashlib.sha256((root / "database" / filename).read_bytes()).hexdigest()


def _hydrate(db, root: Path, table: str):
    rows = db.execute(text("SELECT media_id, path, sha256 FROM bootstrap_media")).all()
    for media_id, relative, expected in rows:
        original = fixture_file(root, relative).read_bytes()
        if hashlib.sha256(original).hexdigest() != expected:
            raise ValueError(f"Fixture integrity failed: {relative}.")
        # The UUID type processes parameters consistently on PostgreSQL and SQLite.
        identifier = Base.metadata.tables["media_assets"].c.id.type
        statement = text(
            f'UPDATE "{table}" SET original_bytes = :original WHERE id = :identifier'
        ).bindparams(bindparam("identifier", type_=identifier))
        result = db.execute(statement, {"original": original, "identifier": uuid.UUID(media_id)})
        if result.rowcount != 1:
            raise ValueError("Media import must match exactly one database row.")


@contextmanager
def seed_tables(db, settings, filename: str, root: Path = FIXTURES, *, staged=False):
    """Staging is transaction-local and only used to upgrade earlier installations.

    All rows originate from the single versioned SQL seed. Staging never becomes
    an application table, an alternative query source, or a persistent catalog.
    """
    # A savepoint also makes SQLite's temporary DDL transactional in tests.
    with db.begin_nested():
        with _seed_tables(db, settings, filename, root, staged=staged) as tables:
            yield tables


@contextmanager
def _seed_tables(db, settings, filename, root, *, staged):
    commands = list(statements(root / "database" / filename))
    tables = list(dict.fromkeys(match[1] for sql in commands if (match := INSERT_TABLE.match(sql))))
    if any(name not in Base.metadata.tables for name in tables):
        raise ValueError("SQL seed references an unknown application table.")
    db.execute(
        text(
            "CREATE TEMP TABLE bootstrap_media (media_id VARCHAR(32), path TEXT, sha256 VARCHAR(64))"
        )
    )
    temporary = []
    if staged:
        for name in tables:
            temp = "bootstrap_" + name
            db.execute(text(f'CREATE TEMP TABLE "{temp}" AS SELECT * FROM "{name}" WHERE 1=0'))
            temporary.append(temp)
    for sql in commands:
        if staged:
            sql = INSERT_TABLE.sub(lambda match: f'INSERT INTO "bootstrap_{match[1]}"', sql)
        db.execute(
            text(sql), {"empty_bytes": b"", "notice_version": settings.biometric_notice_version}
        )
    _hydrate(db, root, "bootstrap_media_assets" if staged else "media_assets")
    yield {name: "bootstrap_" + name if staged else name for name in tables}
    # Exceptions propagate to the enclosing savepoint, which rolls back both
    # data and temporary DDL. Successful imports remove their staging tables.
    for name in reversed(temporary):
        db.execute(text(f'DROP TABLE "{name}"'))
    db.execute(text("DROP TABLE bootstrap_media"))


def apply_seed(db, settings, filename: str, root: Path = FIXTURES):
    with seed_tables(db, settings, filename, root):
        pass
