from __future__ import annotations

import io
import uuid
from datetime import datetime

from fastapi import (
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from PIL import Image, ImageDraw
from sqlalchemy.orm import Session

from app.models import (
    CaptureSession,
    MediaAsset,
    ObjectObservation,
)
from app.processing.captures import store_capture
from app.processing.presentation import _capture_response
from app.schemas import (
    CaptureResponse,
)


def _store_capture(
    request: Request,
    session: CaptureSession,
    captured_at: datetime | None,
    file: UploadFile,
    *,
    db: Session,
    actor_id: uuid.UUID | None,
    device_id: uuid.UUID | None = None,
) -> CaptureResponse:
    asset = store_capture(
        db,
        request.app.state.settings,
        session,
        file.file.read(),
        file.content_type,
        file.filename,
        captured_at,
        actor_id=actor_id,
        device_id=device_id,
    )
    return _capture_response(asset)


def _render_highlight(db: Session, observation: ObjectObservation, asset: MediaAsset) -> Response:
    """Render an ephemeral overlay; original evidence and binary mask stay immutable."""

    if observation.workspace_id != asset.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    try:
        with Image.open(io.BytesIO(asset.original_bytes)).convert("RGBA") as image:
            if observation.mask_asset_id:
                mask_asset = db.get(MediaAsset, observation.mask_asset_id)
                if mask_asset is None or mask_asset.workspace_id != observation.workspace_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="SAM mask is no longer available.",
                    )
                with Image.open(io.BytesIO(mask_asset.original_bytes)).convert("L") as mask:
                    resized_mask = mask.resize(image.size, Image.Resampling.NEAREST)
                alpha = resized_mask.point(lambda value: 128 if value else 0)
                overlay = Image.new("RGBA", image.size, (255, 199, 0, 0))
                overlay.putalpha(alpha)
                image.alpha_composite(overlay)
                box = observation.bounding_box
                if box:
                    _draw_box(image, box, color=(255, 235, 90, 255))
            else:
                box = observation.muse_bounding_box or observation.bounding_box
                if not box:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No highlight geometry is available.",
                    )
                _draw_box(image, box, color=(255, 199, 0, 255))
            output = io.BytesIO()
            image.save(output, format="PNG")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Media cannot be highlighted."
        )
    return Response(content=output.getvalue(), media_type="image/png")


def _draw_box(image: Image.Image, box: dict, color: tuple[int, int, int, int]) -> None:
    x = int(float(box["x"]) * image.width)
    y = int(float(box["y"]) * image.height)
    right = int((float(box["x"]) + float(box["width"])) * image.width)
    bottom = int((float(box["y"]) + float(box["height"])) * image.height)
    ImageDraw.Draw(image).rectangle(
        (x, y, right, bottom), outline=color, width=max(3, image.width // 120)
    )
