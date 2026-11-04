"""Prepare the isolated local schema through the shared migration entry point."""

from app.config import get_settings
from app.db import Database
from app.local_runtime import validate_local_settings
from app.runtime.schema import initialize_schema, upgrade_schema


def prepare(database, settings):
    if settings.environment != "local" or not settings.local_evaluation_enabled:
        raise ValueError("Schema initialization is restricted to local evaluation.")
    validate_local_settings(settings)
    return initialize_schema(database)


if __name__ == "__main__":
    settings = get_settings()
    database = Database(settings.database_url)
    try:
        prepare(database, settings)
        upgrade_schema(database)
        print("Local schema ready; existing data preserved.")
    finally:
        database.engine.dispose()
