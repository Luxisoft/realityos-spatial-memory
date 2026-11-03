"""Resource-specific, short-lived HTTPS images for the DAT Display renderer."""

import io
import json
import threading
import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

import jwt
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from PIL import Image, ImageOps
from pydantic import BaseModel, Field, ValidationError, field_validator
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.social_features.display_annotations import render_face_group
from app.social_features.evidence import evidence_image
from app.social_features.gallery import thumbnail
from app.social_features.uploads import publication_upload_preview

router = APIRouter()


class DisplayMediaRequest(BaseModel):
    kind: Literal["evidence", "upload", "publication", "face_enrollment", "face_record_enrollment"]
    resource_id: uuid.UUID
    labels: list[str] = Field(default_factory=list, max_length=30)


def render(payload, user, db):
    if payload.kind == "evidence":
        response = evidence_image(payload.resource_id, ",".join(payload.labels), True, user, db)
    elif payload.kind == "upload":
        response = publication_upload_preview(payload.resource_id, user, db)
    elif payload.kind == "face_enrollment":
        from app.faces import enrollment_thumbnail

        response = enrollment_thumbnail(payload.resource_id, True, user, db)
    elif payload.kind == "face_record_enrollment":
        from app.faces import record_enrollment_thumbnail

        response = record_enrollment_thumbnail(payload.resource_id, True, user, db)
    else:
        response = thumbnail(payload.resource_id, user, db)
    # Reserve space for date, confidence and controls on a 600px Display.
    # Contain the entire annotation; originals and regular gallery URLs are untouched.
    from fastapi.responses import Response

    with Image.open(io.BytesIO(response.body)) as source:
        picture = ImageOps.contain(source.convert("RGB"), (600, 280))
        canvas = Image.new("RGB", (600, 280), "black")
        canvas.paste(picture, ((600 - picture.width) // 2, (280 - picture.height) // 2))
        output = io.BytesIO()
        canvas.save(output, "JPEG", quality=92)
    return Response(output.getvalue(), media_type="image/jpeg")


@router.post("/display/media-links")
def media_link(
    payload: DisplayMediaRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate access and stored annotations before issuing a capability URL.
    render(payload, user, db)
    settings = request.app.state.settings
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.display_evidence_token_minutes)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "typ": "display_media",
            "iat": now,
            "exp": expires,
            "resource": payload.model_dump(mode="json"),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return {
        "url": f"{settings.api_prefix}/display/media?token={token}",
        "expires_at": expires.isoformat(),
    }


@router.get("/display/media")
def display_media(token: str, request: Request, db: Session = Depends(get_db)):
    settings = request.app.state.settings
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if claims.get("typ") != "display_media":
            raise ValueError("Wrong token type")
        user = db.get(User, uuid.UUID(claims["sub"]))
        payload = DisplayMediaRequest.model_validate(claims["resource"])
        if user is None or not user.is_active:
            raise ValueError("User unavailable")
    except (jwt.PyJWTError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(404, "Display media unavailable.") from error
    response = render(payload, user, db)
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


class FaceGroupMark(BaseModel):
    box: dict[str, float]
    color: str = Field(min_length=7, max_length=7)
    number: int = Field(ge=1, le=99)

    @field_validator("box")
    @classmethod
    def _valid_box(cls, box: dict[str, float]) -> dict[str, float]:
        if set(box) != {"x", "y", "width", "height"}:
            raise ValueError("Box needs x, y, width and height.")
        if not all(
            isinstance(value, (int, float)) and 0.0 <= value <= 1.0 for value in box.values()
        ):
            raise ValueError("Box coordinates must be normalized 0..1.")
        if box["width"] <= 0.0 or box["height"] <= 0.0:
            raise ValueError("Box needs a positive size.")
        return {key: float(value) for key, value in box.items()}

    @field_validator("color")
    @classmethod
    def _valid_color(cls, color: str) -> str:
        if not color.startswith("#") or len(color) != 7:
            raise ValueError("Color must be #RRGGBB.")
        try:
            int(color[1:], 16)
        except ValueError as error:
            raise ValueError("Color must be #RRGGBB.") from error
        return color


# Ephemeral probe bytes stay out of the database: rendered group cards live in
# this bounded memory cache until their token expires. Single-replica only.
_GROUP_CACHE: dict[str, tuple[bytes, datetime]] = {}
_GROUP_CACHE_LOCK = threading.Lock()
_GROUP_CACHE_MAX = 64
_FACE_GROUP_MARKS_MAX = 20


def _group_cache_store(payload: bytes, expires: datetime) -> str:
    key = uuid.uuid4().hex
    now = datetime.now(UTC)
    with _GROUP_CACHE_LOCK:
        stale = [known for known, (_, deadline) in _GROUP_CACHE.items() if deadline <= now]
        for known in stale:
            del _GROUP_CACHE[known]
        while len(_GROUP_CACHE) >= _GROUP_CACHE_MAX:
            _GROUP_CACHE.pop(next(iter(_GROUP_CACHE)))
        _GROUP_CACHE[key] = (payload, expires)
    return key


def _group_cache_fetch(key: str) -> bytes | None:
    with _GROUP_CACHE_LOCK:
        found = _GROUP_CACHE.get(key)
        if found is None:
            return None
        payload, expires = found
        if expires <= datetime.now(UTC):
            del _GROUP_CACHE[key]
            return None
        return payload


@router.post("/display/face-group-links")
async def face_group_link(
    request: Request,
    marks: str = Form(...),
    probe: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Draw numbered color boxes over an uploaded probe for the Display.

    The probe is never stored as media: only the rendered card is cached in
    memory until its short-lived token expires.
    """

    del db
    try:
        parsed = [FaceGroupMark.model_validate(item) for item in json.loads(marks)]
    except (ValueError, ValidationError, TypeError) as error:
        raise HTTPException(status_code=422, detail="Invalid marks.") from error
    if not parsed or len(parsed) > _FACE_GROUP_MARKS_MAX:
        raise HTTPException(status_code=422, detail="Invalid marks.")
    if probe.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG or WebP images are accepted.")
    raw = await probe.read()
    if not raw or len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Invalid image size.")
    try:
        with Image.open(io.BytesIO(raw)) as decoded:
            frame = ImageOps.exif_transpose(decoded).convert("RGB")
    except Exception as error:
        raise HTTPException(status_code=422, detail="The image cannot be decoded.") from error
    canvas = render_face_group(frame, parsed)
    output = io.BytesIO()
    canvas.save(output, "JPEG", quality=92)
    settings = request.app.state.settings
    now = datetime.now(UTC)
    expires = now + timedelta(minutes=settings.display_evidence_token_minutes)
    key = _group_cache_store(output.getvalue(), expires)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "typ": "display_face_group",
            "jti": key,
            "iat": now,
            "exp": expires,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    return {
        "url": f"{settings.api_prefix}/display/face-group?token={token}",
        "expires_at": expires.isoformat(),
    }


@router.get("/display/face-group")
def face_group_media(token: str, request: Request, db: Session = Depends(get_db)):
    settings = request.app.state.settings
    try:
        claims = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if claims.get("typ") != "display_face_group":
            raise ValueError("Wrong token type")
        user = db.get(User, uuid.UUID(claims["sub"]))
        if user is None or not user.is_active:
            raise ValueError("User unavailable")
        payload = _group_cache_fetch(str(claims["jti"]))
        if payload is None:
            raise ValueError("Card expired")
    except (jwt.PyJWTError, ValueError, KeyError, TypeError) as error:
        raise HTTPException(404, "Display media unavailable.") from error
    from fastapi.responses import Response

    response = Response(payload, media_type="image/jpeg")
    response.headers["Cache-Control"] = "private, no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response
