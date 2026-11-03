"""Explicit administrator provisioning for the owner's synthetic jury dataset."""

import secrets
import uuid

from fastapi import Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import PasswordAccount
from app.dependencies import get_current_user, get_db, workspace_member
from app.http.common import _audit
from app.models import Role, User, WorkspaceMember
from app.security import hash_password
from app.workspaces.routes import router


class TestWorker(BaseModel):
    username: str = Field(pattern=r"^[a-z][a-z0-9_.-]{2,63}$")
    display_name: str = Field(min_length=2, max_length=160)
    role: Role = Role.REGISTER


@router.post("/workspaces/{workspace_id}/test-workers", status_code=201)
async def provision(
    workspace_id: uuid.UUID,
    payload: TestWorker,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not request.app.state.settings.test_worker_provisioning_enabled:
        raise HTTPException(404)
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    if db.scalar(select(PasswordAccount).where(PasswordAccount.username == payload.username)):
        raise HTTPException(409, "Username already exists.")
    password = secrets.token_urlsafe(24)
    worker = User(
        email=f"{payload.username}@jury.example.test",
        display_name=payload.display_name,
        password_hash=hash_password(password),
        is_active=True,
    )
    db.add(worker)
    db.flush()
    db.add(PasswordAccount(user_id=worker.id, username=payload.username, provisioned_by=user.id))
    db.add(WorkspaceMember(workspace_id=workspace_id, user_id=worker.id, role=payload.role))
    _audit(db, "account.test_provisioned", "user", user.id, worker.id, workspace_id)
    return {
        "user_id": str(worker.id),
        "username": payload.username,
        "password": password,
        "email_verified": False,
        "simulated_account": True,
    }
