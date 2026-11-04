"""Password entry exclusively for an explicitly enabled local installation."""

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.device_profiles import issue_capture_profile
from app.http.identity import login
from app.local_catalog import accounts
from app.models import RefreshToken, User, Workspace, WorkspaceMember
from app.schemas import LoginRequest, TokenResponse
from app.security import create_access_token, create_refresh_token

router = APIRouter()


@router.get("/auth/local-session")
async def local_session(request: Request, user: User = Depends(get_current_user)):
    settings = request.app.state.settings
    if settings.environment != "local" or not settings.local_login_enabled:
        raise HTTPException(404, "Not found.")
    return {"local_access": True}


class LocalLoginResponse(TokenResponse):
    local_access: Literal[True] = True
    capture_profile: dict[str, str]


def require_evaluation(request):
    settings = request.app.state.settings
    if not (
        settings.environment == "local"
        and settings.local_login_enabled
        and settings.local_evaluation_enabled
    ):
        raise HTTPException(404, "Not found.")
    return settings


@router.get("/auth/local-accounts")
def local_accounts(request: Request, response: Response, db: Session = Depends(get_db)):
    require_evaluation(request)
    response.headers["Cache-Control"] = "no-store"
    result = []
    for entry in accounts():
        user = db.get(User, UUID(entry["id"]))
        workspace = db.get(Workspace, UUID(entry["workspace_id"]))
        member = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == UUID(entry["workspace_id"]),
                WorkspaceMember.user_id == UUID(entry["id"]),
            )
        )
        if user and user.is_active and workspace and member:
            result.append(
                {
                    "id": str(user.id),
                    "display_name": user.display_name,
                    "username": entry["username"],
                    "workspace_id": str(workspace.id),
                    "workspace_name": workspace.name,
                }
            )
    return {"local_access": True, "accounts": result}


class LocalSelection(BaseModel):
    user_id: UUID


@router.post("/auth/local-select", response_model=LocalLoginResponse)
def local_select(
    payload: LocalSelection, request: Request, response: Response, db: Session = Depends(get_db)
):
    settings = require_evaluation(request)
    entry = next((entry for entry in accounts() if entry["id"] == str(payload.user_id)), None)
    user = db.get(User, payload.user_id) if entry else None
    workspace = db.get(Workspace, UUID(entry["workspace_id"])) if entry else None
    if user is None or not user.is_active or workspace is None:
        raise HTTPException(404, "Local account unavailable.")
    profile = issue_capture_profile(db, settings, user, local=True, local_workspace=workspace)
    token, jti, expires = create_refresh_token(user.id, settings)
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires))
    response.headers["Cache-Control"] = "no-store"
    return LocalLoginResponse(
        access_token=create_access_token(user.id, settings),
        refresh_token=token,
        local_access=True,
        capture_profile=profile,
    )


@router.post("/auth/local-login", response_model=LocalLoginResponse)
async def local_login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    settings = request.app.state.settings
    # Defense in depth: a later settings change must not activate this on a server.
    if settings.environment != "local" or not settings.local_login_enabled:
        raise HTTPException(404, "Not found.")
    tokens = await login(payload, request, db)
    user = db.scalar(select(User).where(User.email == payload.email.casefold()))
    response.headers["Cache-Control"] = "no-store"
    return LocalLoginResponse(
        **tokens.model_dump(),
        local_access=True,
        capture_profile=issue_capture_profile(db, settings, user, local=True),
    )
