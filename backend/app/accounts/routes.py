import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.accounts.models import AccountChallenge, PasswordAccount
from app.accounts.presentation import action_page, language
from app.accounts.service import challenge, consume, throttle
from app.dependencies import get_current_user, get_db
from app.device_profiles import issue_capture_profile
from app.models import RefreshToken, User
from app.security import hash_password, verify_password

router = APIRouter(tags=["accounts"])


class Registration(BaseModel):
    username: str = Field(pattern=r"^[a-zA-Z][a-zA-Z0-9_.-]{2,63}$")
    email: str = Field(min_length=5, max_length=320)
    display_name: str = Field(min_length=1, max_length=160)
    password: str = Field(min_length=12, max_length=512)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        value = value.strip().casefold()
        if not re.fullmatch(r"[^\s@<>]+@[^\s@<>]+\.[^\s@<>]+", value):
            raise ValueError("Invalid email")
        return value


class EmailRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class PendingEmailChange(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=320,
        description="Existing registration username or current email address.",
    )
    email: str = Field(min_length=5, max_length=320)
    password: str = Field(min_length=1, max_length=512)

    @field_validator("email")
    @classmethod
    def valid_email(cls, value):
        return Registration.valid_email(value)


class ChallengeRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class ResetRequest(ChallengeRequest):
    password: str = Field(min_length=12, max_length=512)


def registration_conflicts(db, email, username):
    fields = []
    if db.scalar(select(User.id).where(User.email == email)):
        fields.append("email")
    if db.scalar(select(PasswordAccount.user_id).where(PasswordAccount.username == username)):
        fields.append("username")
    return fields


@router.post("/auth/register", status_code=202)
async def register(payload: Registration, request: Request, db: Session = Depends(get_db)):
    throttle(db, request, payload.email, "register")
    username = payload.username.casefold()
    conflicts = registration_conflicts(db, payload.email, username)
    if conflicts:
        raise HTTPException(409, {"code": "registration_conflict", "fields": conflicts})
    user = User(
        email=payload.email,
        display_name=payload.display_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=False,
    )
    try:
        db.add(user)
        db.flush()
        db.add(PasswordAccount(user_id=user.id, username=username))
        db.commit()  # Retain pending account if SMTP is temporarily unavailable.
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            409,
            {
                "code": "registration_conflict",
                "fields": registration_conflicts(db, payload.email, username)
                or ["email", "username"],
            },
        )
    await challenge(
        db, request.app.state.settings, user, "verify", request.headers.get("accept-language")
    )
    return {"status": "confirmation_sent"}


@router.post("/auth/resend-confirmation", status_code=202)
async def resend(payload: EmailRequest, request: Request, db: Session = Depends(get_db)):
    throttle(db, request, payload.email, "mail")
    user = db.scalar(
        select(User).where(User.email == payload.email.strip().casefold()).with_for_update()
    )
    account = db.get(PasswordAccount, user.id) if user else None
    if account and not account.verified_at:
        await challenge(
            db, request.app.state.settings, user, "verify", request.headers.get("accept-language")
        )
    return {"status": "If eligible, a confirmation email has been sent."}


@router.post("/auth/change-pending-email", status_code=202)
async def change_pending_email(
    payload: PendingEmailChange, request: Request, db: Session = Depends(get_db)
):
    username = payload.username.strip().casefold()
    throttle(db, request, username, "change-email")
    user = db.scalar(
        select(User)
        .join(PasswordAccount, PasswordAccount.user_id == User.id)
        .where(or_(PasswordAccount.username == username, User.email == username))
        .with_for_update(of=User)
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid account credentials.")
    account = db.get(PasswordAccount, user.id)
    if account.verified_at or account.provisioned_by or user.is_active:
        raise HTTPException(409, "Only an unconfirmed registration can change its email here.")
    if db.scalar(select(User.id).where(User.email == payload.email, User.id != user.id)):
        raise HTTPException(409, {"code": "registration_conflict", "fields": ["email"]})
    try:
        user.email = payload.email
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, {"code": "registration_conflict", "fields": ["email"]})
    # One transaction: SMTP failure preserves both the old address and its link.
    # Successful delivery invalidates the old links and keeps the same account.
    await challenge(
        db, request.app.state.settings, user, "verify", request.headers.get("accept-language")
    )
    return {"status": "confirmation_sent"}


@router.post("/auth/confirm-email")
async def confirm(payload: ChallengeRequest, db: Session = Depends(get_db)):
    user_id = consume(db, payload.token, "verify")
    account = db.get(PasswordAccount, user_id)
    account.verified_at = datetime.now(UTC)
    db.get(User, user_id).is_active = True
    return {"status": "confirmed"}


@router.post("/auth/forgot-password", status_code=202)
async def forgot(payload: EmailRequest, request: Request, db: Session = Depends(get_db)):
    throttle(db, request, payload.email, "mail")
    user = db.scalar(
        select(User).where(User.email == payload.email.strip().casefold()).with_for_update()
    )
    account = db.get(PasswordAccount, user.id) if user else None
    if account and account.verified_at and user.is_active:
        await challenge(
            db, request.app.state.settings, user, "reset", request.headers.get("accept-language")
        )
    return {"status": "If eligible, a recovery email has been sent."}


@router.post("/auth/reset-password")
async def reset(payload: ResetRequest, db: Session = Depends(get_db)):
    user_id = consume(db, payload.token, "reset")
    now = datetime.now(UTC)
    db.get(User, user_id).password_hash = hash_password(payload.password)
    db.get(PasswordAccount, user_id).revoked_before = now
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user_id).values(revoked_at=now))
    db.execute(
        update(AccountChallenge).where(AccountChallenge.user_id == user_id).values(consumed_at=now)
    )
    return {"status": "password_changed"}


@router.get("/auth/account-session")
async def account_session(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.get(PasswordAccount, user.id)
    return {
        "password_account": bool(account and (account.verified_at or account.provisioned_by)),
        "user_id": str(user.id),
    }


@router.post("/auth/account-capture-profile")
async def capture_profile(
    request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    account = db.get(PasswordAccount, user.id)
    if not account or not (account.verified_at or account.provisioned_by):
        raise HTTPException(403, "Confirmed password account required.")
    return issue_capture_profile(db, request.app.state.settings, user, account=True)


@router.get("/auth/verify", response_class=HTMLResponse, include_in_schema=False)
async def verify_page(request: Request):
    return action_page(
        "verify",
        language(
            request.query_params.get("lang"), language(request.headers.get("accept-language"))
        ),
    )


@router.get("/auth/reset", response_class=HTMLResponse, include_in_schema=False)
async def reset_page(request: Request):
    return action_page(
        "reset",
        language(
            request.query_params.get("lang"), language(request.headers.get("accept-language"))
        ),
    )
