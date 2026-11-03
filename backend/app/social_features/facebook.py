from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import (
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import (
    RefreshToken,
    User,
)
from app.security import create_access_token, create_refresh_token
from app.social_features.models import (
    FacebookIdentity,
    FacebookPost,
    FacebookProfile,
)
from app.social_features.schemas import FacebookLogin, GuestLogin

"""Facebook identities and explicitly shared audiovisual publications."""


router = APIRouter()


@router.post("/auth/logout")
def logout(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for token in db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
        )
    ):
        token.revoked_at = datetime.now(UTC)
    return {"ok": True}


@router.post("/auth/facebook")
async def facebook_login(payload: FacebookLogin, request: Request, db: Session = Depends(get_db)):
    from app.social_features.facebook_import import import_facebook_media, sync_facebook_profile

    settings = request.app.state.settings
    if not settings.facebook_app_id or not settings.facebook_app_secret:
        raise HTTPException(503, "Facebook Login is not configured.")
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.get(
                "https://graph.facebook.com/debug_token",
                params={
                    "input_token": payload.access_token,
                    "access_token": f"{settings.facebook_app_id}|{settings.facebook_app_secret}",
                },
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            if (
                not data.get("is_valid")
                or data.get("app_id") != settings.facebook_app_id
                or not data.get("user_id")
                or data.get("expires_at", 0) <= datetime.now(UTC).timestamp()
            ):
                raise HTTPException(401, "Invalid Facebook identity.")
            profile_response = await client.get(
                "https://graph.facebook.com/me",
                params={
                    "fields": "id,name",
                    "access_token": payload.access_token,
                },
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
            if profile.get("id") != data["user_id"]:
                raise HTTPException(401, "Invalid Facebook identity.")
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise HTTPException(503, "Facebook verification unavailable.") from exc
    # Facebook IDs are scoped to a Meta app, not globally interchangeable.
    subject = f"{settings.facebook_app_id}:{data['user_id']}"
    identity = db.get(FacebookIdentity, subject)
    if identity is None:
        user = User(
            email=f"{uuid.uuid4()}@facebook.invalid",
            display_name=profile.get("name", "Facebook"),
            password_hash=secrets.token_hex(64),
        )
        db.add(user)
        db.flush()
        db.add(FacebookIdentity(subject=subject, user_id=user.id))
    else:
        user = db.get(User, identity.user_id)
    if user is None or not user.is_active:
        raise HTTPException(401, "Inactive identity.")
    # The basic identity read is repeated on every login, including returning users.
    if isinstance(profile.get("name"), str) and profile["name"].strip():
        user.display_name = profile["name"].strip()[:160]
    if payload.device_id:
        user.device_id = payload.device_id.strip()[:128]
    refresh, jti, expires = create_refresh_token(user.id, settings)
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires))
    granted_scopes = data.get("scopes", [])
    if not isinstance(granted_scopes, list):
        granted_scopes = []
    profile_synced = False
    import_status = "pending"
    try:
        async with httpx.AsyncClient(timeout=15) as sync_client:
            profile_row = await sync_facebook_profile(
                db, settings, user, sync_client, payload.access_token, granted_scopes
            )
        profile_synced = profile_row.sync_diagnostics.get("profile") == "ready"
        import_status = profile_row.import_status
        if settings.enqueue_processing:
            from app.tasks import import_facebook_media_task

            try:
                import_facebook_media_task.delay(str(user.id))
            except Exception:
                pass
        else:
            result = import_facebook_media(db, settings, user.id)
            import_status = result["import_status"]
    except Exception:
        # Profile sync is best-effort: identity login never fails because of it.
        pass
    return {
        "access_token": create_access_token(user.id, settings),
        "refresh_token": refresh,
        "token_type": "bearer",
        "granted_scopes": granted_scopes,
        "profile_synced": profile_synced,
        "import_status": import_status,
    }


@router.post("/auth/guest")
def guest_login(payload: GuestLogin, request: Request, db: Session = Depends(get_db)):
    """Create or resume the guest user bound to one device identifier."""

    settings = request.app.state.settings
    device_id = payload.device_id.strip()
    if not device_id:
        raise HTTPException(422, "Device identifier required.")
    guest = db.scalar(select(User).where(User.is_guest.is_(True), User.device_id == device_id))
    if guest is None:
        slug = (
            "".join(
                character for character in device_id if character.isalnum() or character in "-_"
            )[:64]
            or hashlib.sha256(device_id.encode()).hexdigest()[:16]
        )
        tag = hashlib.sha256(device_id.encode()).hexdigest()[:6].upper()
        guest = User(
            email=f"guest-{slug}@guest.invalid",
            display_name=f"Invitado-{tag}",
            password_hash=secrets.token_hex(64),
            is_guest=True,
            device_id=device_id,
        )
        db.add(guest)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            guest = db.scalar(
                select(User).where(User.is_guest.is_(True), User.device_id == device_id)
            )
            if guest is None:
                raise HTTPException(503, "Guest login unavailable.") from None
    if not guest.is_active:
        raise HTTPException(401, "Inactive identity.")
    refresh, jti, expires = create_refresh_token(guest.id, settings)
    db.add(RefreshToken(user_id=guest.id, jti=jti, expires_at=expires))
    return {
        "access_token": create_access_token(guest.id, settings),
        "refresh_token": refresh,
        "token_type": "bearer",
        "is_guest": True,
    }


@router.get("/me/facebook-profile")
def own_facebook_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):

    profile = db.get(FacebookProfile, user.id)
    if profile is None:
        raise HTTPException(404, "No Facebook profile synced yet.")
    posts = list(db.scalars(select(FacebookPost).where(FacebookPost.user_id == user.id).limit(50)))
    return {
        "email": profile.email,
        "birthday": profile.birthday,
        "age_min": profile.age_min,
        "age_max": profile.age_max,
        "gender": profile.gender,
        "hometown": profile.hometown,
        "location": profile.location,
        "profile_link": profile.profile_link,
        "picture_url": profile.picture_url,
        "friends_count": profile.friends_count,
        "likes_count": profile.likes_count,
        "photos_count": profile.photos_count,
        "videos_count": profile.videos_count,
        "granted_scopes": profile.granted_scopes,
        "import_status": profile.import_status,
        "imported_photos": profile.imported_photos,
        "imported_videos": profile.imported_videos,
        "skipped_media": profile.skipped_media,
        "sync_diagnostics": profile.sync_diagnostics,
        "synced_at": profile.synced_at.isoformat() if profile.synced_at else None,
        "picture_imported": profile.picture_imported,
        "posts": [
            {
                "fb_id": item.fb_id,
                "message": item.message,
                "fb_created_time": item.fb_created_time,
                "permalink": item.permalink,
            }
            for item in posts
        ],
        "media": [],
        "references_private": True,
    }
