"""Replace only the local police group's content with the ten fictional people."""

import uuid

from app.local_catalog import FIXTURES
from app.local_models import LocalEvaluationState
from app.local_runtime import validate_local_settings
from app.local_seed import preflight, read_json, seed_records
from app.models import Device, MediaAsset, Workspace, WorkspaceMember
from app.social_features.models import UserProfile
from app.workspaces.models import Record
from purge_workspaces import purge
from sqlalchemy import select, text

RECEIPT = "police-people-v1"
WORKSPACE = uuid.UUID("09f6bc06-8d36-5e69-a050-6f690fe1168b")


def refresh_local_police(db, settings, root=FIXTURES):
    validate_local_settings(settings)
    if not (
        settings.environment == "local"
        and settings.local_login_enabled
        and settings.local_evaluation_enabled
    ):
        raise ValueError("Police replacement is restricted to local evaluation.")
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(7265616)"))
    if db.get(LocalEvaluationState, RECEIPT) or not db.get(
        LocalEvaluationState, "evaluation-v1"
    ):
        return
    workspace = db.get(Workspace, WORKSPACE)
    if workspace is None:
        return  # Never resurrect an owner-deleted group.
    if workspace.name != "Pacific Ridge Police Department":
        raise ValueError("Unexpected workspace; police replacement aborted.")
    data, _, _, _ = preflight(root)
    group = next(g for g in data["groups"] if g["id"] == str(WORKSPACE))
    if group.get("content_revision") != RECEIPT:
        raise ValueError("Missing police content revision.")
    members = list(
        db.scalars(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == WORKSPACE)
        )
    )
    if {m.user_id for m in members} != {uuid.UUID(u["id"]) for u in group["users"]}:
        raise ValueError("Unexpected membership; police replacement aborted.")
    avatars = set()
    for member in members:
        profile = db.get(UserProfile, member.user_id)
        if profile and profile.avatar_media_id:
            media = db.get(MediaAsset, profile.avatar_media_id)
            if media and media.workspace_id == WORKSPACE:
                avatars.add((media.id,))
    devices = {
        (d,)
        for d in db.scalars(select(Device.id).where(Device.workspace_id == WORKSPACE))
    }
    report = purge(
        db,
        [WORKSPACE],
        apply=True,
        commit=False,
        strict_scope=True,
        preserve_workspace=True,
        preserve_rows={
            "workspace_members": {(m.id,) for m in members},
            "media_assets": avatars,
            "devices": devices,
        },
    )
    counts = {"records": 0, "attachments": 0}
    seed_records(db, root, group, WORKSPACE, workspace.created_by_id, counts)
    display = next(
        g
        for g in read_json(root / "local/display-text.json")["groups"]
        if g["id"] == str(WORKSPACE)
    )
    for entry in display["records"]:
        db.get(Record, uuid.UUID(entry["id"])).display_text = entry["fields"]
    description = display["fields"]["description"]
    workspace.description = description["en"]
    workspace.display_text = {
        **display["fields"],
        "description": {**description, "source": description["en"]},
    }
    db.flush()
    return {"removed": report["rows"], "created": counts}
