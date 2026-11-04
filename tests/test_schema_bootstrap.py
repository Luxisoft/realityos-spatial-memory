"""Exercise immutable DDL and incremental upgrades against real PostgreSQL."""

import pytest
from alembic.runtime.migration import MigrationContext
from app.db import Base, Database
from app.models import User
from app.runtime.schema import BASELINE, initialize_schema, upgrade_schema
from sqlalchemy import Column, Integer, MetaData, Table, UniqueConstraint, inspect, text


def test_fixed_baseline_ignores_model_changes(postgres_url, monkeypatch):
    database = Database(postgres_url)
    monkeypatch.setattr(
        Base.metadata, "create_all", lambda *a, **k: pytest.fail("Mutable ORM DDL")
    )
    try:
        assert initialize_schema(database)
        with database.engine.connect() as connection:
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == BASELINE
            )
            tables = inspect(connection).get_table_names()
            assert "publications" in tables
            assert "biometric_publication_quarantine" in tables
        assert not initialize_schema(database)
    finally:
        database.engine.dispose()


def test_existing_unversioned_data_is_never_stamped(postgres_url):
    database = Database(postgres_url)
    try:
        metadata = MetaData()
        Table("existing_data", metadata, Column("id", Integer, primary_key=True))
        metadata.create_all(database.engine)
        with database.engine.begin() as connection:
            connection.execute(text("INSERT INTO existing_data VALUES (7)"))
        with pytest.raises(ValueError, match="Nonempty database"):
            initialize_schema(database)
        with database.engine.connect() as connection:
            assert connection.scalar(text("SELECT id FROM existing_data")) == 7
            assert "alembic_version" not in inspect(connection).get_table_names()
    finally:
        database.engine.dispose()


def test_new_and_updated_schema_match_current_model_columns(postgres_url):
    database = Database(postgres_url)
    try:
        assert upgrade_schema(database)
        assert not upgrade_schema(database)
        inspector = inspect(database.engine)
        with database.engine.connect() as connection:
            comparison = MigrationContext.configure(connection).impl
        for table in Base.metadata.sorted_tables:
            columns = {
                column["name"]: column for column in inspector.get_columns(table.name)
            }
            assert columns.keys() == {column.name for column in table.columns}, (
                table.name
            )
            for column in table.columns:
                assert columns[column.name]["nullable"] == column.nullable, (
                    table.name,
                    column.name,
                )
                assert not comparison.compare_type(
                    Column(column.name, columns[column.name]["type"]), column
                ), (table.name, column.name)
            assert set(
                inspector.get_pk_constraint(table.name)["constrained_columns"]
            ) == {column.name for column in table.primary_key.columns}
            expected_indexes = {index.name for index in table.indexes}
            actual_indexes = {
                index["name"] for index in inspector.get_indexes(table.name)
            }
            assert expected_indexes <= actual_indexes, table.name
            expected_unique = {
                tuple(column.name for column in constraint.columns)
                for constraint in table.constraints
                if isinstance(constraint, UniqueConstraint)
            }
            assert {
                tuple(constraint["column_names"])
                for constraint in inspector.get_unique_constraints(table.name)
            } == expected_unique, table.name
            expected_foreign_keys = {
                (
                    tuple(element.parent.name for element in constraint.elements),
                    constraint.referred_table.name,
                    tuple(element.column.name for element in constraint.elements),
                    constraint.ondelete,
                )
                for constraint in table.foreign_key_constraints
            }
            assert {
                (
                    tuple(constraint["constrained_columns"]),
                    constraint["referred_table"],
                    tuple(constraint["referred_columns"]),
                    constraint["options"].get("ondelete"),
                )
                for constraint in inspector.get_foreign_keys(table.name)
            } == expected_foreign_keys, table.name
    finally:
        database.engine.dispose()


def test_incremental_upgrade_preserves_existing_rows(postgres_url):
    database = Database(postgres_url)
    try:
        initialize_schema(database)
        with database.session() as db:
            user = User(
                email="existing@example.test",
                display_name="Edited account",
                password_hash="unused",
            )
            db.add(user)
            db.flush()
            identifier = user.id
        assert not upgrade_schema(database)
        with database.session() as db:
            assert db.get(User, identifier).display_name == "Edited account"
    finally:
        database.engine.dispose()
