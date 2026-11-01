"""Password entry exclusively for an explicitly enabled local installation."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.device_profiles import issue_capture_profile
from app.http.identity import login
from app.models import User
from app.schemas import LoginRequest, TokenResponse

router = APIRouter()


@router.get("/auth/local-session")
async def local_session(request: Request, user: User = Depends(get_current_user)):
    settings = request.app.state.settings
    if settings.environment != "local" or not settings.local_login_enabled:
        raise HTTPException(404, "Not found.")
    return {"local_access": True}


class LocalLoginResponse(TokenResponse):
    local_access: bool
    capture_profile: dict[str, str]


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
