from __future__ import annotations

import uuid
from datetime import UTC, datetime

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Database
from app.models import Device, DeviceStatus, Role, User, WorkspaceMember
from app.security import decode_token, verify_device_credential

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db(request: Request):
    database: Database = request.app.state.database
    db = database.session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required."
        )
    try:
        payload = decode_token(credentials.credentials, request.app.state.settings, "access")
        user_id = uuid.UUID(str(payload["sub"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token."
        )
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user."
        )
    return user


async def get_current_device(
    request: Request,
    db: Session = Depends(get_db),
) -> Device:
    """Authenticate a physical ingestion device, not a human user account."""

    identifier = request.headers.get("X-RealityOS-Device-ID", "").strip()
    credential = request.headers.get("X-RealityOS-Device-Key", "").strip()
    if not identifier or not credential:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device credentials are required.",
        )
    device = db.scalar(select(Device).where(Device.device_identifier == identifier))
    if (
        device is None
        or device.status != DeviceStatus.ACTIVE
        or not verify_device_credential(credential, device.credential_hash, request.app.state.settings)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked device credentials.",
        )
    device.last_seen_at = datetime.now(UTC)
    return device


def workspace_member(
    workspace_id: uuid.UUID,
    user: User,
    db: Session,
    allowed_roles: set[Role] | None = None,
) -> WorkspaceMember:
    member = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user.id,
        )
    )
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied."
        )
    if allowed_roles and member.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient workspace role."
        )
    return member
