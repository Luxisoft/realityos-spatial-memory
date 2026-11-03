"""Resumable account enrollment, owned by the isolated biometric arm."""

import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy import DateTime, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.dependencies import get_current_user, get_db
from app.faces import (
    FaceEngineError,
    FaceEnrollment,
    _enroll_images,
    _ensure_home_workspace,
    _face_engine_or_503,
    _read_probe_image,
    _usable_enrollment,
    cosine_similarity,
    require_biometric_consent,
)
from app.models import MediaAsset, MediaKind

router = APIRouter(prefix="/faces", tags=["faces"])
REFERENCE_SOURCE = "account-photo"
MINIMUM = 3
MAXIMUM = 25


class BiometricSetup(Base):
    __tablename__ = "biometric_setups"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


def references(db, user):
    return list(
        db.scalars(
            select(FaceEnrollment).where(
                FaceEnrollment.user_id == user.id, FaceEnrollment.source == REFERENCE_SOURCE
            )
        )
    )


def setup_state(db, user):
    from app.accounts.models import PasswordAccount
    from app.faces import has_biometric_consent, has_face_capture
    from app.social_features.models import UserProfile

    row = db.get(BiometricSetup, user.id)
    profile = db.get(UserProfile, user.id)
    saved_references = references(db, user)
    count = len({r.media_asset_id for r in saved_references})
    consent = has_biometric_consent(db, user.id)
    primary = has_face_capture(db, user.id)
    avatar = bool(profile and profile.avatar_media_id)
    complete = bool(
        row and row.completed_at and consent and primary and avatar and count >= MINIMUM
    )
    return dict(
        required=db.get(PasswordAccount, user.id) is not None,
        consented=consent,
        profile_photo_ready=primary,
        avatar_ready=avatar,
        accepted_photos=count,
        reference_ids=[str(r.id) for r in saved_references],
        minimum_photos=MINIMUM,
        maximum_photos=MAXIMUM,
        complete=complete,
    )


@router.get("/setup")
def status(user=Depends(get_current_user), db=Depends(get_db)):
    return setup_state(db, user)


@router.post("/reference-photos", status_code=201)
async def add_reference(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    require_biometric_consent(db, user)
    if user.is_guest:
        raise HTTPException(403, "Sign in to enroll reference photos.")
    db.refresh(user, with_for_update=True)
    settings = request.app.state.settings
    engine = _face_engine_or_503(settings)
    raw = await _read_probe_image(file, settings)
    digest = hashlib.sha256(raw).hexdigest()
    current = references(db, user)
    for enrollment in current:
        if db.get(MediaAsset, enrollment.media_asset_id).sha256 == digest:
            return dict(id=str(enrollment.id), duplicate=True, **setup_state(db, user))
    if len(current) >= MAXIMUM:
        raise HTTPException(422, "At most 25 reference photos are allowed.")
    primary = db.scalar(
        select(FaceEnrollment).where(
            FaceEnrollment.user_id == user.id, FaceEnrollment.source == "profile"
        )
    )
    if primary is None:
        raise HTTPException(409, "Upload the profile photo first.")
    if db.get(MediaAsset, primary.media_asset_id).sha256 == digest:
        raise HTTPException(
            422, "Choose another photo; the profile photo does not count as a reference."
        )
    try:
        detected = engine.detect_faces(raw)
    except FaceEngineError as exc:
        raise HTTPException(422, str(exc)) from exc
    if len(detected) != 1:
        raise HTTPException(422, "Each reference photo must show exactly one face.")
    face = detected[0]
    if not engine.simulated and (
        primary.embedding_model != engine.name
        or cosine_similarity(primary.embedding, face.embedding) < settings.face_identity_threshold
    ):
        raise HTTPException(422, "This photo does not match the registered face.")
    asset = MediaAsset(
        workspace_id=_ensure_home_workspace(db, user).id,
        kind=MediaKind.IMAGE,
        mime_type=file.content_type or "image/jpeg",
        original_bytes=raw,
        sha256=digest,
        byte_size=len(raw),
        extra_metadata={"purpose": "biometric-reference", "owner_id": str(user.id)},
    )
    db.add(asset)
    db.flush()
    created = _enroll_images(
        db,
        user,
        [asset],
        REFERENCE_SOURCE,
        engine,
        None if engine.simulated else settings.face_spoof_max_risk,
    )
    if not created or (
        not engine.simulated
        and not _usable_enrollment(
            created[0], min_quality=settings.face_min_quality, min_area=settings.face_min_box_area
        )
    ):
        raise HTTPException(422, "The face is too small or unclear. Choose a sharper photo.")
    return dict(id=str(created[0].id), duplicate=False, **setup_state(db, user))


@router.delete("/reference-photos/{enrollment_id}")
def remove_reference(enrollment_id: uuid.UUID, user=Depends(get_current_user), db=Depends(get_db)):
    db.refresh(user, with_for_update=True)
    row = db.get(FaceEnrollment, enrollment_id)
    if not row or row.user_id != user.id or row.source != REFERENCE_SOURCE:
        raise HTTPException(404, "Reference unavailable.")
    asset = db.get(MediaAsset, row.media_asset_id)
    setup = db.get(BiometricSetup, user.id)
    if setup:
        setup.completed_at = None
    db.delete(row)
    db.flush()
    db.delete(asset)
    db.flush()
    return setup_state(db, user)


@router.post("/setup/complete")
def complete(request: Request, user=Depends(get_current_user), db=Depends(get_db)):
    require_biometric_consent(db, user)
    db.refresh(user, with_for_update=True)
    state = setup_state(db, user)
    if (
        not state["profile_photo_ready"]
        or not state["avatar_ready"]
        or state["accepted_photos"] < MINIMUM
    ):
        raise HTTPException(
            409, "A profile photo and at least three accepted reference photos are required."
        )
    settings = request.app.state.settings
    engine = _face_engine_or_503(settings)
    primary = db.scalar(
        select(FaceEnrollment).where(
            FaceEnrollment.user_id == user.id, FaceEnrollment.source == "profile"
        )
    )
    if not engine.simulated:
        valid = [
            r
            for r in references(db, user)
            if r.embedding_model == primary.embedding_model == engine.name
            and _usable_enrollment(
                r, min_quality=settings.face_min_quality, min_area=settings.face_min_box_area
            )
            and cosine_similarity(primary.embedding, r.embedding)
            >= settings.face_identity_threshold
        ]
        if len(valid) < MINIMUM:
            raise HTTPException(
                409, "Upload at least three clear references matching the current profile photo."
            )
    row = db.get(BiometricSetup, user.id)
    if row is None:
        row = BiometricSetup(user_id=user.id)
        db.add(row)
    row.completed_at = datetime.now(UTC)
    db.flush()
    return setup_state(db, user)
