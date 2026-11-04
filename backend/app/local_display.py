"""Install the reviewed ES/EN fixture copy once, only in the local realm."""

import hashlib
import json
import uuid

from sqlalchemy import select

from app.local_catalog import FIXTURES
from app.local_models import LocalEvaluationState
from app.models import Workspace
from app.social_features.models import Publication, PublicationTerm, UserProfile
from app.workspaces.models import Record

RECEIPT = "bilingual-copy-v1"


def install_display_text(db, settings, root=FIXTURES):
    if settings.environment != "local" or not settings.local_evaluation_enabled:
        raise ValueError("Authored fixture copy is restricted to local evaluation.")
    if db.get(LocalEvaluationState, RECEIPT):
        return
    raw = (root / "local/display-text.json").read_bytes()
    counts = {"fields": 0}

    def apply(row, fields):
        if row is None:
            return
        values = dict(row.display_text or {})
        for field, pair in fields.items():
            if getattr(row, field) == pair["source"]:
                values[field] = pair
                counts["fields"] += 1
        row.display_text = values

    for group in json.loads(raw)["groups"]:
        workspace_id = uuid.UUID(group["id"])
        workspace = db.get(Workspace, workspace_id)
        if workspace is None:
            continue
        apply(workspace, group["fields"])
        # Retire the old visible fixture label without changing an owner's edit.
        description = group["fields"]["description"]
        if workspace.description == description["source"]:
            workspace.description = description["en"]
            workspace.display_text = {
                **workspace.display_text,
                "description": {**description, "source": description["en"]},
            }
        for entry in group["terms"]:
            term = db.scalar(
                select(PublicationTerm).where(
                    PublicationTerm.workspace_id == workspace_id,
                    PublicationTerm.kind == entry["kind"],
                    PublicationTerm.name == entry["name"],
                )
            )
            apply(term, entry["fields"])
        for key, model in (("records", Record), ("publications", Publication)):
            for entry in group[key]:
                row = db.get(model, uuid.UUID(entry["id"]))
                if row is not None and row.workspace_id == workspace_id:
                    apply(row, entry["fields"])
        for entry in group["profiles"]:
            apply(db.get(UserProfile, uuid.UUID(entry["id"])), entry["fields"])
    db.add(
        LocalEvaluationState(
            name=RECEIPT, manifest_hash=hashlib.sha256(raw).hexdigest(), counts=counts
        )
    )
    db.flush()
