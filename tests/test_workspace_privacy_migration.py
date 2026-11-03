"""Exercise the release migration and its visibility rollback on an existing schema."""

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect


def test_upgrade_downgrade_upgrade_preserves_existing_tables(client):
    path = (
        Path(__file__).resolve().parents[1]
        / "backend/alembic/versions/20261103_0036_workspace_privacy.py"
    )
    spec = importlib.util.spec_from_file_location("release_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    with client.app.state.database.engine.begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
            migration.downgrade()
            assert "storage_objects" not in inspect(connection).get_table_names()
            migration.upgrade()
        tables = inspect(connection).get_table_names()
        assert "storage_objects" in tables and "biometric_setups" in tables
        assert "face_enrollments" in tables and "workspace_records" in tables
