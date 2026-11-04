"""Password entry exclusively for an explicitly enabled local installation."""

import io
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.device_profiles import issue_capture_profile
from app.http.identity import login
from app.local.access import list_accounts, selected_account
from app.models import MediaAsset, RefreshToken, User, WorkspaceMember
from app.schemas import LoginRequest, TokenResponse
from app.security import create_access_token, create_refresh_token
from app.social_features.models import UserProfile

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
    return {"local_access": True, "accounts": list_accounts(db)}


@router.get("/auth/local-accounts/{user_id}/avatar", response_class=Response)
def local_account_avatar(user_id: UUID, request: Request, db: Session = Depends(get_db)):
    """Only the selected profile avatar of an eligible local database account."""
    require_evaluation(request)
    selected_account(db, user_id, require_membership=True)
    profile = db.get(UserProfile, user_id)
    asset = (
        db.get(MediaAsset, profile.avatar_media_id) if profile and profile.avatar_media_id else None
    )
    if (
        asset is None
        or asset.mime_type not in {"image/jpeg", "image/png", "image/webp"}
        or db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == asset.workspace_id,
                WorkspaceMember.user_id == user_id,
            )
        )
        is None
    ):
        raise HTTPException(404, "Profile picture unavailable.")
    # Never fall back to captured images, reference photos or biometric enrollments.
    try:
        with Image.open(io.BytesIO(asset.original_bytes)) as original:
            if original.width * original.height > 16_000_000:
                raise HTTPException(404, "Profile picture unavailable.")
            portrait = ImageOps.exif_transpose(original).convert("RGB")
            portrait.thumbnail((192, 192))
            output = io.BytesIO()
            portrait.save(output, "JPEG", quality=85)
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise HTTPException(404, "Profile picture unavailable.") from exc
    return Response(
        output.getvalue(), media_type="image/jpeg", headers={"Cache-Control": "no-store"}
    )


class LocalSelection(BaseModel):
    user_id: UUID


@router.post("/auth/local-select", response_model=LocalLoginResponse)
def local_select(
    payload: LocalSelection, request: Request, response: Response, db: Session = Depends(get_db)
):
    settings = require_evaluation(request)
    user, workspace = selected_account(db, payload.user_id)
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
