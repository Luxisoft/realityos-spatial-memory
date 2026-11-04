"""Apply the shared publication catalog once to previously initialized local groups."""

import hashlib
import json
import uuid

from app.local_catalog import FIXTURES, catalog
from app.local_models import LocalEvaluationState
from app.local_runtime import validate_local_settings
from app.local_seed import seed_publications
from app.models import Workspace
from sqlalchemy import text

RECEIPT = "local-group-publications-v1"


def seed_local_publications(db, settings, root=FIXTURES):
    validate_local_settings(settings)
    if not (
        settings.environment == "local"
        and settings.local_login_enabled
        and settings.local_evaluation_enabled
    ):
        raise ValueError(
            "Publication initialization is restricted to local evaluation."
        )
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(7265616)"))
    previous = db.get(LocalEvaluationState, RECEIPT)
    if previous:
        return {"initialized": False, **previous.counts}
    groups = [
        g for g in catalog(root)["groups"] if g["slug"] in {"security", "meta-social"}
    ]
    counts = {
        "publications": sum(
            seed_publications(db, root, group, preserve_missing=True)
            for group in groups
            if db.get(Workspace, uuid.UUID(group["id"])) is not None
        )
    }
    db.add(
        LocalEvaluationState(
            name=RECEIPT,
            manifest_hash=hashlib.sha256(
                json.dumps(groups, sort_keys=True).encode()
            ).hexdigest(),
            counts=counts,
        )
    )
    db.flush()
    return {"initialized": True, **counts}
