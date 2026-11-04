"""Create the current local schema on an EMPTY database, then apply later migrations.

The historical 0001 revision imports evolving ORM metadata and cannot bootstrap
an empty database reliably. Existing installations always use Alembic upgrades.
This baseline is pinned: raising it requires a new reviewed schema baseline.
"""

import os
import subprocess

from app.db import Base
from app.local_runtime import validate_local_settings
from app.main import (
    app,
)  # Registers the complete current schema, including isolated features.
from sqlalchemy import inspect, text

BASELINE = "20261104_0039"


def prepare(database, settings):
    if settings.environment != "local" or not settings.local_evaluation_enabled:
        raise ValueError("Schema initialization is restricted to local evaluation.")
    validate_local_settings(settings)
    with database.engine.begin() as connection:
        if connection.dialect.name != "postgresql":
            raise ValueError("Local installations require PostgreSQL.")
        connection.execute(text("SELECT pg_advisory_xact_lock(7265615)"))
        tables = inspect(connection).get_table_names()
        if tables:
            if "alembic_version" not in tables:
                raise ValueError(
                    "Nonempty database has no migration version; no data was changed."
                )
            return False
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        Base.metadata.create_all(connection)
        for table, column, prefix in (
            ("tracked_objects", "canonical_name", "tracked_objects_name"),
            ("object_aliases", "alias", "object_aliases_alias"),
            ("publications", "search_text", "publications_search_text"),
        ):
            connection.execute(
                text(
                    f"CREATE INDEX ix_{prefix}_trgm ON {table} USING gin ({column} gin_trgm_ops)"
                )
            )
            if table != "publications":
                connection.execute(
                    text(
                        f"CREATE INDEX ix_{prefix}_fts ON {table} USING gin (to_tsvector('simple', {column}))"
                    )
                )
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        )
        connection.execute(
            text("INSERT INTO alembic_version VALUES (:revision)"),
            {"revision": BASELINE},
        )
    return True


if __name__ == "__main__":
    settings = app.state.settings
    created = prepare(app.state.database, settings)
    subprocess.run(
        ["alembic", "upgrade", "head"],
        check=True,
        env={**os.environ, "DATABASE_URL": settings.database_url},
    )
    print(
        "Local schema initialized."
        if created
        else "Local schema upgraded; data preserved."
    )
