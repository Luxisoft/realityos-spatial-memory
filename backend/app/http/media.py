from __future__ import annotations

import logging
import uuid

import jwt
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_device, get_current_user, get_db, workspace_member
from app.http.common import _render_highlight
from app.models import (
    Device,
    DeviceStatus,
    MediaAsset,
    MediaAssetChunk,
    ObjectObservation,
    User,
    VerificationStatus,
)
from app.security import (
    decode_display_evidence_token,
)
from app.services import (
    media_is_chunked,
)
from app.social_features.publication_visibility import require_ordinary_media

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/media/{media_id}")
def get_media(
    media_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    asset = db.get(MediaAsset, media_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    workspace_member(asset.workspace_id, user, db)
    require_ordinary_media(asset, user, db)
    headers = {"Content-Disposition": f'inline; filename="{asset.id}"'}
    if media_is_chunked(asset):

        def chunk_stream():
            for chunk in db.scalars(
                select(MediaAssetChunk.content)
                .where(MediaAssetChunk.asset_id == asset.id)
                .order_by(MediaAssetChunk.chunk_index)
            ):
                yield chunk

        return StreamingResponse(chunk_stream(), media_type=asset.mime_type, headers=headers)
    return Response(content=asset.original_bytes, media_type=asset.mime_type, headers=headers)


@router.get("/observations/{observation_id}/highlighted")
def highlighted_observation(
    observation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    observation = db.get(ObjectObservation, observation_id)
    if observation is None or observation.verification_status != VerificationStatus.VERIFIED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found.")
    workspace_member(observation.workspace_id, user, db)
    asset = db.get(MediaAsset, observation.media_asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    require_ordinary_media(asset, None, db)
    return _render_highlight(db, observation, asset)


@router.get("/device/observations/{observation_id}/highlighted")
def device_highlighted_observation(
    observation_id: uuid.UUID,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> Response:
    observation = db.get(ObjectObservation, observation_id)
    if (
        observation is None
        or observation.workspace_id != device.workspace_id
        or observation.verification_status != VerificationStatus.VERIFIED
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found.")
    asset = db.get(MediaAsset, observation.media_asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    require_ordinary_media(asset, None, db)
    return _render_highlight(db, observation, asset)


@router.get("/device/display/observations/{observation_id}/highlighted")
def display_highlighted_observation(
    observation_id: uuid.UUID,
    token: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    """Serve one short-lived highlighted image to the DAT Display renderer.

    DAT Display fetches image URLs itself, so it cannot send the encrypted
    device credential held by the Android host. The signed token is deliberately
    limited to this observation and the still-active enrolled device.
    """

    try:
        token_observation_id, token_device_id = decode_display_evidence_token(
            token, request.app.state.settings
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found.")
    if token_observation_id != observation_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found.")
    device = db.get(Device, token_device_id)
    observation = db.get(ObjectObservation, observation_id)
    if (
        device is None
        or device.status != DeviceStatus.ACTIVE
        or observation is None
        or observation.workspace_id != device.workspace_id
        or observation.verification_status != VerificationStatus.VERIFIED
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found.")
    asset = db.get(MediaAsset, observation.media_asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence not found.")
    require_ordinary_media(asset, None, db)
    response = _render_highlight(db, observation, asset)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@router.get("/media/{media_id}/highlighted")
def highlighted_media(
    media_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    """Compatibility endpoint; queries now use an observation-specific overlay."""

    asset = db.get(MediaAsset, media_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    workspace_member(asset.workspace_id, user, db)
    require_ordinary_media(asset, user, db)
    observation = db.scalar(
        select(ObjectObservation)
        .where(
            ObjectObservation.media_asset_id == media_id,
            ObjectObservation.verification_status == VerificationStatus.VERIFIED,
        )
        .order_by(desc(ObjectObservation.seen_at))
    )
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No verified highlight is available."
        )
    require_ordinary_media(asset, None, db)
    return _render_highlight(db, observation, asset)
