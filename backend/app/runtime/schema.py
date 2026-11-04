"""Initialize a fixed PostgreSQL baseline, then apply the Alembic history."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import inspect, text

from alembic import command
from app.db import Database

BASELINE = "20261104_0040"
BACKEND = Path(__file__).resolve().parents[2]
SCHEMA = BACKEND / "schema" / BASELINE


def initialize_schema(database: Database) -> bool:
    """Only an empty database may receive the immutable, schema-only baseline."""
    with database.engine.begin() as connection:
        if connection.dialect.name != "postgresql":
            raise ValueError("Schema initialization requires PostgreSQL.")
        connection.execute(text("SELECT pg_advisory_xact_lock(7265615)"))
        tables = inspect(connection).get_table_names()
        if tables:
            if "alembic_version" not in tables:
                raise ValueError("Nonempty database has no migration version; no data was changed.")
            return False
        for name in ("01-schema.sql", "02-schema.sql"):
            connection.exec_driver_sql((SCHEMA / name).read_text(encoding="utf-8"))
        connection.execute(
            text("CREATE TABLE alembic_version (version_num VARCHAR(32) PRIMARY KEY)")
        )
        connection.execute(
            text("INSERT INTO alembic_version VALUES (:revision)"), {"revision": BASELINE}
        )
    return True


def upgrade_schema(database: Database) -> bool:
    created = initialize_schema(database)
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    config.set_main_option(
        "sqlalchemy.url",
        database.engine.url.render_as_string(hide_password=False).replace("%", "%%"),
    )
    with database.engine.begin() as connection:
        connection.execute(text("SELECT pg_advisory_xact_lock(7265615)"))
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
    return created


def main() -> None:
    from app.config import get_settings
    from app.local_runtime import validate_local_settings

    settings = get_settings()
    validate_local_settings(settings)
    database = Database(settings.database_url)
    try:
        created = upgrade_schema(database)
        print("Schema initialized." if created else "Schema upgraded; data preserved.")
    finally:
        database.engine.dispose()


if __name__ == "__main__":
    main()
