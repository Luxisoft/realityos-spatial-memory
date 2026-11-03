"""Owner-selected avatar upload. Does not enroll or alter biometric data."""

import hashlib
import io

from fastapi import Depends, File, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy.orm import Session

from app.accounts.routes import router
from app.dependencies import get_current_user, get_db
from app.models import MediaAsset, MediaKind, User
from app.social_features.profiles import _user_profile
from app.social_features.upload_service import home_space


@router.post("/me/profile/avatar")
async def upload_avatar(
    file: UploadFile = File(), user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    raw = await file.read(5 * 1024 * 1024 + 1)
    if not raw or len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "Avatar must be at most 5 MiB.")
    try:
        with Image.open(io.BytesIO(raw)) as picture:
            if picture.width * picture.height > 16_000_000 or picture.format not in {
                "PNG",
                "JPEG",
                "WEBP",
            }:
                raise HTTPException(422, "Use a JPEG, PNG or WebP portrait under 16 megapixels.")
            mime = Image.MIME[picture.format]
            picture.verify()
    except (OSError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise HTTPException(422, "Invalid image.") from exc
    asset = MediaAsset(
        workspace_id=home_space(db, user.id),
        kind=MediaKind.IMAGE,
        mime_type=mime,
        original_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        extra_metadata={"origin": "account-avatar"},
    )
    db.add(asset)
    db.flush()
    _user_profile(db, user.id).avatar_media_id = asset.id
    return {"picture_url": f"/v1/profiles/{user.id}/avatar"}
