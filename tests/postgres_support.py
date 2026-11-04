"""Disposable PostgreSQL for database integration tests; never connects to runtime data."""

import getpass
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from sqlalchemy.engine import URL

ROOT = Path(__file__).resolve().parents[1]


def postgres_binary(name):
    installed = shutil.which(name)
    if installed:
        return installed
    candidates = sorted(Path("/usr/lib/postgresql").glob(f"*/bin/{name}"), reverse=True)
    if not candidates:
        pytest.skip(
            "Local PostgreSQL binaries are required for database integration tests"
        )
    return str(candidates[0])


@pytest.fixture(scope="session")
def postgres_cluster():
    """Each test process owns one cluster, using Unix sockets and no TCP listener."""
    initdb, pg_ctl = postgres_binary("initdb"), postgres_binary("pg_ctl")
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.skip("Run PostgreSQL integration tests as an unprivileged user")
    runtime = ROOT / ".runtime"
    runtime.mkdir(exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="postgres-tests-", dir=runtime))
    data = directory / "data"
    # Unix socket addresses are limited to 107 bytes on Linux. GitHub's long
    # checkout path cannot contain the socket; only the bulky data stays there.
    sockets = Path(tempfile.mkdtemp(prefix="ros-pg-", dir="/tmp"))
    user = getpass.getuser()
    started = False
    try:
        subprocess.run(
            [initdb, "-D", str(data), "-A", "trust", "--no-locale", "--encoding=UTF8"],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        result = subprocess.run(
            [
                pg_ctl,
                "-D",
                str(data),
                "-l",
                str(directory / "server.log"),
                "-o",
                f"-k {sockets} -h '' -p 55439 -F",
                "-w",
                "start",
            ],
            check=False,
            stdout=subprocess.DEVNULL,
        )
        if result.returncode:
            raise RuntimeError((directory / "server.log").read_text())
        started = True
        url = URL.create(
            "postgresql+psycopg",
            username=user,
            database="postgres",
            query={"host": str(sockets), "port": "55439"},
        )
        connection = {
            "host": str(sockets),
            "port": 55439,
            "dbname": "postgres",
            "user": user,
        }
        with psycopg.connect(**connection, autocommit=True) as db:
            db.execute("CREATE EXTENSION pg_trgm")
        yield url, connection
    finally:
        try:
            if started:
                subprocess.run(
                    [pg_ctl, "-D", str(data), "-m", "immediate", "-w", "stop"],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
        finally:
            shutil.rmtree(directory)
            shutil.rmtree(sockets)


@pytest.fixture
def postgres_url(postgres_cluster):
    """An empty schema per test; data and BYTEA originals are removed at teardown."""
    url, connection = postgres_cluster
    schema = "test_" + uuid.uuid4().hex
    with psycopg.connect(**connection, autocommit=True) as db:
        db.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
    try:
        yield url.update_query_dict(
            {"options": f"-csearch_path={schema},public"}
        ).render_as_string(hide_password=False)
    finally:
        with psycopg.connect(**connection, autocommit=True) as db:
            db.execute(sql.SQL("DROP SCHEMA {} CASCADE").format(sql.Identifier(schema)))
