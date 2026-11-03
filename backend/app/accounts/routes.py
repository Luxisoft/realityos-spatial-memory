import re
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.accounts.models import AccountChallenge, PasswordAccount
from app.accounts.service import challenge, consume, throttle
from app.dependencies import get_current_user, get_db
from app.device_profiles import issue_capture_profile
from app.models import RefreshToken, User
from app.security import hash_password

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


class ChallengeRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)


class ResetRequest(ChallengeRequest):
    password: str = Field(min_length=12, max_length=512)


@router.post("/auth/register", status_code=202)
async def register(payload: Registration, request: Request, db: Session = Depends(get_db)):
    throttle(db, request, payload.email, "register")
    username = payload.username.casefold()
    if db.scalar(select(User).where(User.email == payload.email)) or db.scalar(
        select(PasswordAccount).where(PasswordAccount.username == username)
    ):
        raise HTTPException(409, "This email or username cannot be registered.")
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
        raise HTTPException(409, "This email or username cannot be registered.")
    await challenge(db, request.app.state.settings, user, "verify")
    return {"status": "confirmation_sent"}


@router.post("/auth/resend-confirmation", status_code=202)
async def resend(payload: EmailRequest, request: Request, db: Session = Depends(get_db)):
    throttle(db, request, payload.email, "mail")
    user = db.scalar(select(User).where(User.email == payload.email.strip().casefold()))
    account = db.get(PasswordAccount, user.id) if user else None
    if account and not account.verified_at:
        await challenge(db, request.app.state.settings, user, "verify")
    return {"status": "If eligible, a confirmation email has been sent."}


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
    user = db.scalar(select(User).where(User.email == payload.email.strip().casefold()))
    account = db.get(PasswordAccount, user.id) if user else None
    if account and account.verified_at and user.is_active:
        await challenge(db, request.app.state.settings, user, "reset")
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


async def action_page(action: str):
    if action not in {"verify", "reset"}:
        raise HTTPException(404)
    reset = action == "reset"
    title = "Restablecer contraseña" if reset else "Confirmar correo"
    endpoint = "reset-password" if reset else "confirm-email"
    password = (
        '<label>Nueva contraseña<input id="password" type="password" minlength="12" maxlength="512" autocomplete="new-password" required></label>'
        if reset
        else ""
    )
    nonce = __import__("secrets").token_urlsafe(20)
    return HTMLResponse(
        f'''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>RealityOS — {title}</title><body><main><h1>RealityOS</h1><h2>{title}</h2>
<form>{password}<button>Continuar</button></form><p role="status" id="status"></p></main>
<script nonce="{nonce}">const token=new URLSearchParams(location.hash.slice(1)).get('token');history.replaceState(null,'',location.pathname);
document.querySelector('form').onsubmit=async e=>{{e.preventDefault();let body={{token}};let password=document.querySelector('#password');if(password)body.password=password.value;
try{{let r=await fetch('/v1/auth/{endpoint}',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(body)}});document.querySelector('#status').textContent=r.ok?'Listo. Vuelve a la aplicación para iniciar sesión.':'Enlace inválido o vencido. Solicita uno nuevo.';if(r.ok)document.querySelector('form').remove();}}catch{{document.querySelector('#status').textContent='No se pudo conectar. Intenta de nuevo.';}}}};</script></body></html>''',
        headers={
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": f"default-src 'none'; script-src 'nonce-{nonce}'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'",
        },
    )


@router.get("/auth/verify", response_class=HTMLResponse, include_in_schema=False)
async def verify_page():
    return await action_page("verify")


@router.get("/auth/reset", response_class=HTMLResponse, include_in_schema=False)
async def reset_page():
    return await action_page("reset")
