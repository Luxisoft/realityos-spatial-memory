"""One-time owner-requested replacement, restricted to the isolated local realm."""

import uuid

from app.local_catalog import catalog
from app.local_models import LocalEvaluationState
from app.local_runtime import validate_local_settings
from app.models import MediaAsset, Workspace, WorkspaceMember
from app.social_features.models import UserProfile
from purge_workspaces import purge
from sqlalchemy import select, text

OLD_ID = uuid.UUID("749f3aad-1543-55d1-9633-03f0cf443a1a")
RECEIPT = "replace-hospital-meta-social-v1"


def replace_local_hospital(db, settings):
    validate_local_settings(settings)
    if not (
        settings.environment == "local"
        and settings.local_login_enabled
        and settings.local_evaluation_enabled
    ):
        raise ValueError("Replacement is restricted to local evaluation.")
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(7265616)"))
    if db.get(LocalEvaluationState, RECEIPT):
        return
    old = db.get(Workspace, OLD_ID)
    if old is None:
        return
    if not db.get(LocalEvaluationState, "evaluation-v1"):
        raise ValueError("Only the initialized public local dataset can be replaced.")
    if old.name != "California Valley Medical Center":
        raise ValueError("Unexpected old workspace; replacement aborted.")
    group = next(g for g in catalog()["groups"] if g["slug"] == "meta-social")
    destination = uuid.UUID(group["id"])
    members = list(
        db.scalars(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == OLD_ID)
        )
    )
    if {m.user_id for m in members} != {uuid.UUID(u["id"]) for u in group["users"]}:
        raise ValueError("Unexpected membership; replacement aborted.")
    db.add(
        Workspace(
            id=destination,
            name=group["name"],
            created_by_id=old.created_by_id,
            description="",
            display_text={},
        )
    )
    db.flush()
    for member in members:
        member.workspace_id = destination
        profile = db.get(UserProfile, member.user_id)
        if profile and profile.avatar_media_id:
            avatar = db.get(MediaAsset, profile.avatar_media_id)
            if avatar and avatar.workspace_id == OLD_ID:
                avatar.workspace_id = destination
    db.flush()
    # All changes, including identities' reassignment, commit together in bootstrap.
    # The purge aborts if any protected identity/biometric or other group's row
    # would be removed. Original account profiles and avatar bytes are retained.
    report = purge(db, [OLD_ID], apply=True, commit=False, strict_scope=True)
    db.add(
        LocalEvaluationState(
            name=RECEIPT,
            manifest_hash="owner-request-2026-11-04",
            counts=report["rows"],
        )
    )
    db.flush()
    return report
