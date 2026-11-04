"""Authorized previews shared by gallery HTTP and the native display adapter."""

import subprocess

from fastapi import HTTPException
from sqlalchemy import select

from app.models import MediaAsset, MediaKind
from app.processing.previews import image_thumbnail, video_thumbnail
from app.social_features.publication_access import get_post


def publication_thumbnail(post_id, user, db) -> bytes:
    post = get_post(post_id, user, db)
    asset = db.get(MediaAsset, post.media_id)
    if asset.mime_type.startswith("image/"):
        raw = asset.original_bytes
    else:
        frame = db.scalar(
            select(MediaAsset).where(
                MediaAsset.parent_asset_id == asset.id, MediaAsset.kind == MediaKind.FRAME
            )
        )
        if frame is not None:
            raw = frame.original_bytes
        else:
            try:
                raw = video_thumbnail(db, asset)
            except (subprocess.SubprocessError, OSError, ValueError) as error:
                raise HTTPException(422, "Video thumbnail unavailable.") from error
    try:
        return image_thumbnail(raw, (360, 480))
    except (ValueError, OSError) as error:
        raise HTTPException(422, "Thumbnail unavailable.") from error
