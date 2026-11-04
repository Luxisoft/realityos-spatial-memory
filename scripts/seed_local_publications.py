"""Publish owner-requested local case portraits and access-account introductions once."""

import hashlib
import json
import uuid

from app.local_catalog import FIXTURES, local_id
from app.local_models import LocalEvaluationState
from app.local_runtime import validate_local_settings
from app.local_seed import read_json
from app.models import MediaAsset, Workspace, WorkspaceMember
from app.social_features.classification import add_term, set_classification
from app.social_features.models import Publication, PublicationTerm
from app.workspaces.models import RecordMedia
from sqlalchemy import select, text

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
    manifest = read_json(root / "local/group-publications.json")
    counts = {"publications": 0}
    for entry in manifest["publications"]:
        workspace_id = uuid.UUID(entry["workspace_id"])
        if db.get(Workspace, workspace_id) is None:
            continue  # Never recreate a deleted group.
        owner_id = uuid.UUID(entry["owner_id"])
        member = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == owner_id,
            )
        )
        asset = db.get(MediaAsset, uuid.UUID(entry["media_id"]))
        if member is None or asset is None:
            continue  # Preserve deletions made before this one-time addition.
        if asset.workspace_id != workspace_id or asset.sha256 != entry["sha256"]:
            raise ValueError("Publication media does not match the local fixture.")
        if asset.extra_metadata.get("origin") not in {
            "local-evaluation",
            "account-avatar",
        }:
            raise ValueError(
                "Only case portraits and separate account avatars may be published."
            )
        post = Publication(
            id=local_id("group-publication", entry["key"]),
            workspace_id=workspace_id,
            owner_id=owner_id,
            media_id=asset.id,
            caption=entry["caption"]["en"],
            note_text=entry["note_text"]["en"],
            note_source="text",
            source="local-evaluation",
            source_ref=entry["key"],
            display_text={
                field: {**entry[field], "source": entry[field]["en"]}
                for field in ("caption", "note_text")
            },
        )
        db.add(post)
        db.flush()
        terms = []
        for kind, label in (("category", entry["category"]), ("tag", entry["tag"])):
            term = db.scalar(
                select(PublicationTerm).where(
                    PublicationTerm.workspace_id == workspace_id,
                    PublicationTerm.kind == kind,
                    PublicationTerm.name_key == label["en"].casefold(),
                )
            )
            if term is None:
                term = add_term(db, workspace_id, kind, label["en"])
                term.display_text = {"name": {**label, "source": label["en"]}}
            terms.append(term.id)
        set_classification(db, post, terms[0], [terms[1]])
        if entry.get("record_id"):
            attachment = db.scalar(
                select(RecordMedia).where(
                    RecordMedia.record_id == uuid.UUID(entry["record_id"]),
                    RecordMedia.media_id == asset.id,
                )
            )
            if attachment is None:
                raise ValueError("Missing case portrait attachment.")
            attachment.publication_id = post.id
        counts["publications"] += 1
    db.add(
        LocalEvaluationState(
            name=RECEIPT,
            manifest_hash=hashlib.sha256(
                json.dumps(manifest, sort_keys=True).encode()
            ).hexdigest(),
            counts=counts,
        )
    )
    db.flush()
    return {"initialized": True, **counts}
