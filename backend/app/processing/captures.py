from __future__ import annotations

import io
import uuid
from datetime import datetime

from fastapi import (
    HTTPException,
    status,
)
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit import _audit
from app.config import Settings
from app.models import (
    CaptureSession,
    CaptureStatus,
    MediaAsset,
    MediaKind,
)
from app.processing.storage import (
    add_postgres_bytea_chunks,
    media_sha256,
)
from app.video import VideoProcessingError, probe_video


def store_capture(
    db: Session,
    settings: Settings,
    session: CaptureSession,
    raw: bytes,
    mime_type: str,
    filename: str | None,
    captured_at: datetime | None,
    *,
    actor_id: uuid.UUID | None,
    device_id: uuid.UUID | None = None,
) -> MediaAsset:
    """Validate and persist an explicit capture; a query never calls this service."""
    if session.status != CaptureStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Capture session is closed."
        )
    image_types = {"image/jpeg", "image/png", "image/webp"}
    video_types = {"video/mp4", "video/quicktime", "video/webm"}
    if mime_type not in image_types | video_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image or video type.",
        )
    is_video = mime_type in video_types
    limit = settings.max_video_bytes if is_video else settings.max_image_bytes
    if len(raw) == 0 or (limit and len(raw) > limit):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Invalid media size.",
        )
    duration_seconds: float | None = None
    if is_video:
        try:
            video_info = probe_video(raw)
        except VideoProcessingError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
        if settings.max_video_seconds and video_info.duration_seconds > settings.max_video_seconds:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Video exceeds the {settings.max_video_seconds}-second limit.",
            )
        width, height = video_info.width, video_info.height
        duration_seconds = video_info.duration_seconds
    else:
        try:
            with Image.open(io.BytesIO(raw)) as image:
                width, height = image.size
                image.verify()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image data."
            )
    digest = media_sha256(raw)
    existing = db.scalar(
        select(MediaAsset).where(
            MediaAsset.capture_session_id == session.id,
            MediaAsset.sha256 == digest,
        )
    )
    if existing:
        return existing
    chunked_video = is_video and len(raw) > settings.video_inline_bytes
    asset = MediaAsset(
        workspace_id=session.workspace_id,
        capture_session_id=session.id,
        kind=MediaKind.VIDEO if is_video else MediaKind.IMAGE,
        mime_type=mime_type,
        original_bytes=b"" if chunked_video else raw,
        sha256=digest,
        byte_size=len(raw),
        width=width,
        height=height,
        captured_at=captured_at,
        extra_metadata={
            "filename": filename or "capture",
            **({"duration_seconds": duration_seconds} if duration_seconds is not None else {}),
        },
    )
    db.add(asset)
    db.flush()
    if chunked_video:
        add_postgres_bytea_chunks(db, asset, raw, settings.video_bytea_chunk_bytes)
    if session.created_by_id is not None:
        from app.models import Workspace
        from app.social_features.models import Publication

        workspace = db.get(Workspace, session.workspace_id)
        if workspace and not workspace.name.startswith("home:"):
            db.add(
                Publication(
                    owner_id=session.created_by_id,
                    media_id=asset.id,
                    workspace_id=session.workspace_id,
                )
            )
    _audit(
        db,
        "capture.created",
        "media_asset",
        actor_id,
        asset.id,
        session.workspace_id,
        device_id,
    )
    return asset
