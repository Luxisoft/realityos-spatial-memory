"""Account-owned capture credentials shared by authenticated entry points."""

import uuid

from sqlalchemy import select

from app.models import Device, Role, Workspace, WorkspaceMember, Zone
from app.security import create_device_credential, hash_device_credential


def issue_capture_profile(db, settings, user, *, local=False):
    workspace = db.scalar(select(Workspace).where(Workspace.name == f"home:{user.id}"))
    if workspace is not None and workspace.created_by_id != user.id:
        from fastapi import HTTPException

        raise HTTPException(
            409, "The account workspace name is already reserved; contact an administrator."
        )
    if workspace is None:
        workspace = Workspace(name=f"home:{user.id}", created_by_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN))
        db.add(Zone(workspace_id=workspace.id, name="Casa", kind="zone"))
    secret = create_device_credential()
    kind = "local" if local else "facebook"
    device = Device(
        workspace_id=workspace.id,
        device_identifier=f"{kind}-display-{uuid.uuid4().hex}",
        label="Local account capture" if local else "Facebook owner capture",
        created_by_id=user.id,
        credential_hash=hash_device_credential(secret, settings),
        metadata_json={f"{kind}_owner": str(user.id)},
    )
    db.add(device)
    db.flush()
    return {
        "workspace_id": str(workspace.id),
        "workspace_name": "Casa",
        "device_id": device.device_identifier,
        "device_key": secret,
    }
