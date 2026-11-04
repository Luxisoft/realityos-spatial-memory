"""Account-owned capture credentials shared by authenticated entry points."""

import uuid

from sqlalchemy import select

from app.models import Device, Role, Workspace, WorkspaceMember, Zone
from app.security import create_device_credential, hash_device_credential


def issue_capture_profile(db, settings, user, *, local=False, account=False, local_workspace=None):
    if local_workspace is not None:
        from fastapi import HTTPException

        member = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == local_workspace.id,
                WorkspaceMember.user_id == user.id,
            )
        )
        if (
            not local
            or settings.environment != "local"
            or member is None
            or member.role == Role.QUERY
        ):
            raise HTTPException(403, "Local capture requires a writable group membership.")
    workspace = local_workspace or db.scalar(
        select(Workspace).where(Workspace.name == f"home:{user.id}")
    )
    if local_workspace is None and workspace is not None and workspace.created_by_id != user.id:
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
    kind = "local" if local else "account" if account else "facebook"
    device = Device(
        workspace_id=workspace.id,
        device_identifier=f"{kind}-display-{uuid.uuid4().hex}",
        label="Account capture"
        if account
        else "Local account capture"
        if local
        else "Facebook owner capture",
        created_by_id=user.id,
        credential_hash=hash_device_credential(secret, settings),
        metadata_json={f"{kind}_owner": str(user.id)},
    )
    db.add(device)
    db.flush()
    return {
        "workspace_id": str(workspace.id),
        "workspace_name": workspace.name if local_workspace is not None else "Casa",
        "device_id": device.device_identifier,
        "device_key": secret,
    }
