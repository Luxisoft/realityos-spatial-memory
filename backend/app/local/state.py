"""Local installation guard and durable receipts shared by data migrations."""

from sqlalchemy import text

from app.local_models import LocalEvaluationState
from app.local_runtime import validate_local_settings


def require_local(db, settings):
    validate_local_settings(settings)
    if not (
        settings.environment == "local"
        and settings.local_login_enabled
        and settings.local_evaluation_enabled
    ):
        raise ValueError("Data initialization is restricted to local evaluation.")
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(7265616)"))
    elif db.bind.dialect.name == "sqlite":
        # SQLite's legacy mode does not begin a transaction for reads or DDL.
        # Start only this import transaction explicitly so releasing a savepoint
        # cannot commit data before its durable initialization receipt.
        connection = db.connection()
        if not connection.connection.driver_connection.in_transaction:
            connection.exec_driver_sql("BEGIN")


def receipt(db, name, digest, counts):
    db.add(LocalEvaluationState(name=name, manifest_hash=digest, counts=counts))
    db.flush()
