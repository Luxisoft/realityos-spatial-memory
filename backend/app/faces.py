"""Consent-gated biometric face search (isolated arm, protected: see AGENTS.md).

This module never imports the object Register/Query pipeline. It only shares
infrastructure with the rest of the API: authentication, workspace membership
and BYTEA-backed media storage.
"""

from __future__ import annotations

import hashlib
import io
import math
import shutil
import struct
import subprocess
import tempfile
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal

import numpy as np
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from PIL import Image, ImageDraw, ImageOps
from pydantic import BaseModel, Field
from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    LargeBinary,
    String,
    UniqueConstraint,
    Uuid,
    func,
    select,
)
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.config import Settings
from app.db import Base
from app.dependencies import get_current_user, get_db, workspace_member
from app.models import (
    CaptureSession,
    CaptureStatus,
    MediaAsset,
    MediaKind,
    Role,
    TimestampMixin,
    User,
    Workspace,
    WorkspaceMember,
)

router = APIRouter(tags=["faces"])

_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}
_VIDEO_MIMES = {"video/mp4", "video/quicktime", "video/webm"}
_FACE_VIDEO_PROBE_TIMEOUT_SECONDS = 60
MOCK_ENGINE_NAME = "mock-faces-1"
MOCK_EMBEDDING_DIM = 128
# Sequential search stages: mandatory face captures first, then Facebook
# photos, then videos. The first stage with matches above threshold wins.
_FACE_SEARCH_STAGES: tuple[tuple[str, ...], ...] = (
    ("profile", "capture"),
    ("facebook-photo",),
    ("facebook-video", "frame"),
)
_SELF_MATCH_SOURCE = "profile"


@dataclass
class DetectedFace:
    bounding_box: dict[str, float]
    embedding: bytes
    quality: float


class FaceEngineError(RuntimeError):
    """The configured face engine is unavailable or rejected the input."""


class FaceEngine(ABC):
    name: str = "face-engine"
    embedding_dim: int = 0
    simulated: bool = False

    @abstractmethod
    def detect_faces(self, image: bytes) -> list[DetectedFace]:
        """Return faces with L2-normalized float32 embeddings."""
        ...


def cosine_similarity(left: bytes, right: bytes) -> float:
    if not left or len(left) != len(right):
        return 0.0
    count = len(left) // 4
    first = struct.unpack(f"<{count}f", left)
    second = struct.unpack(f"<{count}f", right)
    dot = sum(x * y for x, y in zip(first, second))
    norm_a = math.sqrt(sum(x * x for x in first))
    norm_b = math.sqrt(sum(y * y for y in second))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return max(-1.0, min(1.0, dot / (norm_a * norm_b)))


def _mock_embedding(image: bytes, index: int) -> bytes:
    values: list[float] = []
    counter = 0
    while len(values) < MOCK_EMBEDDING_DIM:
        block = hashlib.sha256(
            b"realityos-mock-faces-v1" + image + bytes([index]) + counter.to_bytes(4, "big")
        ).digest()
        for offset in range(0, len(block), 4):
            word = int.from_bytes(block[offset : offset + 4], "big")
            values.append(word / 0xFFFFFFFF * 2.0 - 1.0)
            if len(values) >= MOCK_EMBEDDING_DIM:
                break
        counter += 1
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return struct.pack(f"<{MOCK_EMBEDDING_DIM}f", *(value / norm for value in values))


def _mock_box(digest: bytes, index: int, count: int) -> dict[str, float]:
    slot = 1.0 / count
    width = round(min(0.5, slot * 0.7), 4)
    jitter = (digest[1 + index] % 9) / 100.0
    left = max(0.0, min(1.0 - width, index * slot + (slot - width) / 2 + jitter))
    return {"x": round(left, 4), "y": 0.2, "width": width, "height": 0.5}


class MockFaceEngine(FaceEngine):
    """Deterministic fixture engine: identical bytes always yield identical faces."""

    name = MOCK_ENGINE_NAME
    embedding_dim = MOCK_EMBEDDING_DIM
    simulated = True

    def detect_faces(self, image: bytes) -> list[DetectedFace]:
        if not image:
            return []
        digest = hashlib.sha256(b"realityos-mock-faces-v1" + image).digest()
        count = 1 + (digest[0] % 2)
        return [
            DetectedFace(
                bounding_box=_mock_box(digest, index, count),
                embedding=_mock_embedding(image, index),
                quality=round(0.92 - index * 0.04, 4),
            )
            for index in range(count)
        ]


class InsightFaceEngine(FaceEngine):
    """Provisional local engine. Requires the `faces` extra; live use is unverified."""

    name = "insightface-buffalo_l"
    embedding_dim = 512
    simulated = False

    def __init__(self) -> None:
        try:
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise FaceEngineError(
                "Face engine 'insightface' needs the backend faces extra "
                "(pip install 'realityos-backend[faces]')."
            ) from exc
        self._app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        self._app.prepare(ctx_id=0)

    def detect_faces(self, image: bytes) -> list[DetectedFace]:
        import numpy as np

        try:
            with Image.open(io.BytesIO(image)) as picture:
                rgb = ImageOps.exif_transpose(picture).convert("RGB")
        except Exception as exc:
            raise FaceEngineError("Invalid image data.") from exc
        width, height = rgb.size
        if width == 0 or height == 0:
            return []
        bgr = np.array(rgb)[:, :, ::-1]
        detected: list[DetectedFace] = []
        for face in self._app.get(bgr):
            left, top, right, bottom = (float(value) for value in face.bbox)
            detected.append(
                DetectedFace(
                    bounding_box={
                        "x": max(0.0, left / width),
                        "y": max(0.0, top / height),
                        "width": min(1.0, (right - left) / width),
                        "height": min(1.0, (bottom - top) / height),
                    },
                    embedding=np.asarray(face.embedding, dtype=np.float32).tobytes(),
                    quality=float(face.det_score),
                )
            )
        return detected


_engine_cache: dict[str, FaceEngine] = {}


def build_face_engine(settings: Settings) -> FaceEngine:
    mode = (settings.face_engine or "mock").strip().lower()
    if mode == "mock":
        return MockFaceEngine()
    if mode == "insightface":
        if mode not in _engine_cache:
            _engine_cache[mode] = InsightFaceEngine()
        return _engine_cache[mode]
    raise FaceEngineError(f"Unknown FACE_ENGINE mode: {settings.face_engine!r}.")


@dataclass
class SpoofAssessment:
    risk: float
    reasons: list[str]


def assess_spoof_risk(image: bytes, bounding_box: dict[str, float]) -> SpoofAssessment:
    """Passive anti-spoof heuristics v1 (tiny face, blur, moire, glare).

    Real computed signals, but basic: a trained presentation-attack model is
    the upgrade path. Tuned lenient; the caller sets the reject threshold.
    """

    try:
        with Image.open(io.BytesIO(image)) as picture:
            rgb = ImageOps.exif_transpose(picture).convert("RGB")
    except Exception:
        return SpoofAssessment(risk=1.0, reasons=["unreadable"])
    width, height = rgb.size
    try:
        left = max(0, int(float(bounding_box.get("x", 0.0)) * width))
        top = max(0, int(float(bounding_box.get("y", 0.0)) * height))
        right = min(width, left + int(float(bounding_box.get("width", 1.0)) * width))
        bottom = min(height, top + int(float(bounding_box.get("height", 1.0)) * height))
    except (TypeError, ValueError):
        return SpoofAssessment(risk=1.0, reasons=["invalid_box"])
    if (
        (right - left) * (bottom - top) < 0.02 * width * height
        or (right - left) < 24
        or (bottom - top) < 24
    ):
        return SpoofAssessment(risk=1.0, reasons=["face_too_small"])
    crop = np.asarray(rgb.crop((left, top, right, bottom)), dtype=np.float64)
    gray = crop.mean(axis=2)
    reasons: list[str] = []
    risk = 0.0
    # Sharpness: Laplacian variance collapses on prints and defocused shots.
    inner = gray[1:-1, 1:-1]
    laplacian = gray[:-2, 1:-1] + gray[2:, 1:-1] + gray[1:-1, :-2] + gray[1:-1, 2:] - 4.0 * inner
    if float(laplacian.var()) < 20.0:
        risk += 0.5
        reasons.append("blurry")
    # Moire: screens and prints show sharp spectral peaks; natural noise is flat.
    spectrum = np.abs(np.fft.rfft2(gray - gray.mean())) ** 2
    edge = spectrum[:, int(spectrum.shape[1] * 0.5) :]
    peak = float(edge.max()) if edge.size else 0.0
    if peak > 0:
        median = float(np.median(edge))
        total = float(spectrum.sum())
        floor = max(median, total / edge.size * 1e-6)
        if floor > 0 and peak / floor > 40.0:
            risk += 0.4
            reasons.append("screen_moire")
    # Glare: flash on screens and glossy prints blows out highlights.
    bright = float(((crop > 245).all(axis=2)).mean())
    if bright > 0.02:
        risk += 0.3
        reasons.append("glare")
    return SpoofAssessment(risk=round(min(1.0, risk), 4), reasons=reasons)


def _valid_face_box(box: object) -> dict[str, float] | None:
    """Clamp a normalized face box to the frame, mirroring object evidence rules."""

    if not isinstance(box, dict):
        return None
    try:
        x, y, width, height = (float(box[key]) for key in ("x", "y", "width", "height"))
    except (KeyError, TypeError, ValueError):
        return None
    if not all(math.isfinite(value) for value in (x, y, width, height)):
        return None
    if width <= 0 or height <= 0:
        return None
    left, top = max(0.0, x), max(0.0, y)
    right, bottom = min(1.0, x + width), min(1.0, y + height)
    if right <= left or bottom <= top:
        return None
    return {"x": left, "y": top, "width": right - left, "height": bottom - top}


def _usable_probe_face(
    face: DetectedFace, *, min_quality: float, min_area: float
) -> DetectedFace | None:
    """Keep probe faces with usable geometry and detector confidence."""

    box = _valid_face_box(face.bounding_box)
    if box is None or box["width"] * box["height"] < min_area:
        return None
    if not math.isfinite(face.quality) or face.quality < min_quality:
        return None
    if not face.embedding:
        return None
    return DetectedFace(bounding_box=box, embedding=face.embedding, quality=face.quality)


def _usable_enrollment(enrollment: FaceEnrollment, *, min_quality: float, min_area: float) -> bool:
    """Enrollments need the same usable geometry and quality as probe faces."""

    box = _valid_face_box(enrollment.bounding_box)
    if box is None or box["width"] * box["height"] < min_area:
        return False
    quality = enrollment.quality or 0.0
    if not math.isfinite(quality) or quality < min_quality:
        return False
    return bool(enrollment.embedding)


def _usable_record_enrollment(
    enrollment: FaceRecordEnrollment, *, min_quality: float, min_area: float
) -> bool:
    box = _valid_face_box(enrollment.bounding_box)
    if box is None or box["width"] * box["height"] < min_area:
        return False
    quality = enrollment.quality or 0.0
    if not math.isfinite(quality) or quality < min_quality:
        return False
    return bool(enrollment.embedding)


def _probe_video_duration_seconds(source: Path) -> float | None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=nokey=1:noprint_wrappers=1",
                str(source),
            ],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    try:
        duration = float(result.stdout.decode(errors="replace").strip())
    except ValueError:
        return None
    return duration if duration > 0 else None


def _extract_video_probe_frames(raw: bytes, max_frames: int) -> list[bytes]:
    """Sample up to ``max_frames`` JPEGs evenly across an ephemeral probe video.

    Bytes are never persisted outside temporary files that are removed
    afterwards; the original upload stays out of BYTEA, like image probes.
    """

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise FaceEngineError("Video probes need ffmpeg and ffprobe on the API host.")
    frames: list[bytes] = []
    with tempfile.TemporaryDirectory(prefix="realityos-face-probe-") as directory:
        source = Path(directory) / "probe-video"
        source.write_bytes(raw)
        duration = _probe_video_duration_seconds(source)
        rate = max_frames / duration if duration else 1.0
        pattern = str(Path(directory) / "frame-%03d.jpg")
        try:
            result = subprocess.run(
                [
                    "ffmpeg",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(source),
                    "-vf",
                    f"fps={rate:.6f},scale='min(1280,iw)':-2",
                    "-frames:v",
                    str(max_frames),
                    "-q:v",
                    "3",
                    pattern,
                ],
                capture_output=True,
                check=False,
                timeout=_FACE_VIDEO_PROBE_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise FaceEngineError("Video probes need ffmpeg on the API host.") from exc
        except subprocess.TimeoutExpired as exc:
            raise FaceEngineError("Video probe sampling timed out.") from exc
        if result.returncode:
            raise FaceEngineError("Invalid or unsupported probe video.")
        for path in sorted(Path(directory).glob("frame-*.jpg")):
            frames.append(path.read_bytes())
    if not frames:
        raise FaceEngineError("The probe video has no decodable frames.")
    return frames


class FaceEnrollment(TimestampMixin, Base):
    __tablename__ = "face_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "media_asset_id", "face_index", name="uq_face_enrollment"),
        Index("ix_face_enrollment_user", "user_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    media_asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media_assets.id", ondelete="CASCADE"), nullable=False
    )
    face_index: Mapped[int] = mapped_column(nullable=False, default=0)
    embedding_model: Mapped[str] = mapped_column(String(80), nullable=False)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    bounding_box: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(16), default="capture", nullable=False)


class BiometricConsent(Base):
    __tablename__ = "biometric_consents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    notice_version: Mapped[str] = mapped_column(String(80), nullable=False)
    consented_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FaceVerification(TimestampMixin, Base):
    """Internal identity-verification attempts. Never exposed beyond their owner."""

    __tablename__ = "face_verifications"
    __table_args__ = (Index("ix_face_verification_user", "user_id"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    result: Mapped[str] = mapped_column(String(16), nullable=False)
    score: Mapped[float | None] = mapped_column(Float)
    threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    engine: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    simulated: Mapped[bool] = mapped_column(default=False, nullable=False)
    verified_for_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FaceRecordEnrollment(TimestampMixin, Base):
    """Face embedding linked to a workspace person record, not to a login user.

    Owned by the faces arm. Record must stay active + biometric-authorized to
    be searchable; enrollment rows are never created automatically.
    """

    __tablename__ = "face_record_enrollments"
    __table_args__ = (
        UniqueConstraint(
            "record_id", "media_asset_id", "face_index", name="uq_face_record_enrollment"
        ),
        Index("ix_face_record_enrollment_record", "record_id"),
        Index("ix_face_record_enrollment_workspace", "workspace_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace_records.id", ondelete="CASCADE"), nullable=False
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False
    )
    media_asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media_assets.id", ondelete="CASCADE"), nullable=False
    )
    record_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspace_record_media.id", ondelete="SET NULL")
    )
    face_index: Mapped[int] = mapped_column(nullable=False, default=0)
    embedding_model: Mapped[str] = mapped_column(String(80), nullable=False)
    embedding: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    bounding_box: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    quality: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    source: Mapped[str] = mapped_column(String(32), default="record-portrait", nullable=False)
    authorized_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


def has_biometric_consent(db: Session, user_id: uuid.UUID) -> bool:
    row = db.get(BiometricConsent, user_id)
    return row is not None and row.revoked_at is None


def require_biometric_consent(db: Session, user: User) -> BiometricConsent:
    row = db.get(BiometricConsent, user.id)
    if row is None or row.revoked_at is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Biometric consent is required for face search.",
        )
    return row


class ConsentRequest(BaseModel):
    confirm: bool


class ConsentResponse(BaseModel):
    consented: bool
    notice_version: str | None = None
    consented_at: datetime | None = None
    revoked_at: datetime | None = None
    face_capture_done: bool = False
    identity_verified: bool = False


class FaceVerifyResponse(BaseModel):
    verified: bool
    status: Literal["verified", "pending", "failed", "locked"]
    simulated: bool = False
    attempts_remaining: int | None = None
    retry_after_seconds: int | None = None


def delete_selfie_enrollments(db: Session, user_id: uuid.UUID) -> None:
    """Drop the current selfie plus its private capture asset, if any."""

    for enrollment in db.scalars(
        select(FaceEnrollment).where(
            FaceEnrollment.user_id == user_id,
            FaceEnrollment.source == _SELF_MATCH_SOURCE,
        )
    ):
        asset = db.get(MediaAsset, enrollment.media_asset_id)
        db.delete(enrollment)
        if asset is not None and (asset.extra_metadata or {}).get("face_profile"):
            db.delete(asset)


def has_face_capture(db: Session, user_id: uuid.UUID) -> bool:
    """Whether the user completed the mandatory first-time face capture."""

    return (
        db.scalar(
            select(FaceEnrollment.id)
            .where(
                FaceEnrollment.user_id == user_id,
                FaceEnrollment.source == _SELF_MATCH_SOURCE,
            )
            .limit(1)
        )
        is not None
    )


def has_fresh_verification(db: Session, user_id: uuid.UUID) -> bool:
    """Whether the user verified after their latest Facebook sync (login)."""

    from app.social import FacebookProfile

    profile = db.get(FacebookProfile, user_id)
    if profile is None or profile.synced_at is None:
        return False
    return (
        db.scalar(
            select(FaceVerification.id)
            .where(
                FaceVerification.user_id == user_id,
                FaceVerification.result == "verified",
                FaceVerification.verified_for_synced_at == profile.synced_at,
            )
            .limit(1)
        )
        is not None
    )


def _best_identity_score(captures: list[bytes], references: list[bytes]) -> float:
    """Best cosine similarity between capture and reference embeddings."""

    best = -1.0
    for capture in captures:
        for reference in references:
            score = cosine_similarity(capture, reference)
            if score > best:
                best = score
    return best


class RevokeResponse(BaseModel):
    revoked: bool
    enrollments_deleted: int


class EnrollRequest(BaseModel):
    media_id: uuid.UUID


class EnrollResponse(BaseModel):
    media_id: uuid.UUID
    faces_enrolled: int
    enrollment_ids: list[uuid.UUID]
    simulated: bool


class OwnEnrollmentResponse(BaseModel):
    id: uuid.UUID
    media_id: uuid.UUID
    source: str
    quality: float
    thumbnail_url: str


class FaceMatchEvidence(BaseModel):
    enrollment_id: uuid.UUID
    media_id: uuid.UUID
    thumbnail_url: str
    source: str


class FaceMatch(BaseModel):
    user_id: uuid.UUID
    display_name: str
    similarity: float
    match_type: Literal["direct", "possible_acquaintance"] = "direct"
    picture_url: str | None = None
    profile_link: str | None = None
    evidence: FaceMatchEvidence
    probe_face_index: int
    probe_box: dict[str, float]


class RecordFaceMatchEvidence(BaseModel):
    enrollment_id: uuid.UUID
    media_id: uuid.UUID
    thumbnail_url: str
    source: str


class RecordFaceMatch(BaseModel):
    record_id: uuid.UUID
    workspace_id: uuid.UUID
    external_id: str
    title: str
    similarity: float
    record_url: str
    simulated: bool = False
    evidence: RecordFaceMatchEvidence
    probe_face_index: int
    probe_box: dict[str, float]


class FaceSearchResponse(BaseModel):
    found: bool
    probe_faces: int
    probe_frames: int = 0
    probe_faces_skipped: int = 0
    enrollments_skipped: int = 0
    matches: list[FaceMatch] = Field(default_factory=list)
    matches_records: list[RecordFaceMatch] = Field(default_factory=list)
    record_enrollments_skipped: int = 0
    threshold: float
    simulated: bool
    stage: int | None = None
    stages_searched: list[int] = Field(default_factory=list)


class RecordEnrollRequest(BaseModel):
    record_id: uuid.UUID
    media_id: uuid.UUID | None = None
    record_media_id: uuid.UUID | None = None
    biometric_basis: str | None = Field(default=None, max_length=200)


class RecordEnrollResponse(BaseModel):
    record_id: uuid.UUID
    media_id: uuid.UUID
    faces_enrolled: int
    enrollment_ids: list[uuid.UUID]
    simulated: bool


class OwnRecordEnrollmentResponse(BaseModel):
    id: uuid.UUID
    record_id: uuid.UUID
    workspace_id: uuid.UUID
    media_id: uuid.UUID
    source: str
    quality: float
    thumbnail_url: str


def _face_engine_or_503(settings: Settings) -> FaceEngine:
    try:
        return build_face_engine(settings)
    except FaceEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc


def _ensure_home_workspace(db: Session, user: User) -> Workspace:
    name = f"home:{user.id}"
    workspace = db.scalar(select(Workspace).where(Workspace.name == name))
    if workspace is None:
        workspace = Workspace(name=name, created_by_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN))
        db.flush()
    return workspace


def _owned_root_session(db: Session, asset: MediaAsset, user: User) -> CaptureSession:
    node: MediaAsset | None = asset
    for _ in range(8):
        if node is None or node.parent_asset_id is None:
            break
        node = db.get(MediaAsset, node.parent_asset_id)
    session = (
        db.get(CaptureSession, node.capture_session_id)
        if node is not None and node.capture_session_id is not None
        else None
    )
    if session is None or session.created_by_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the capture owner can enroll this media.",
        )
    return session


def _face_source_images(db: Session, asset: MediaAsset) -> tuple[list[MediaAsset], str]:
    if asset.kind in {MediaKind.IMAGE, MediaKind.FRAME}:
        source = "frame" if asset.parent_asset_id else "capture"
        return [asset], source
    if asset.kind == MediaKind.VIDEO:
        frames = list(
            db.scalars(
                select(MediaAsset)
                .where(MediaAsset.parent_asset_id == asset.id)
                .order_by(MediaAsset.created_at)
                .limit(16)
            )
        )
        if not frames:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Process this video before face search so frames exist.",
            )
        return frames, "frame"
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Face search needs an image or video.",
    )


def _enroll_images(
    db: Session,
    user: User,
    images: list[MediaAsset],
    source: str,
    engine: FaceEngine,
    spoof_max_risk: float | None = None,
) -> list[FaceEnrollment]:
    created: list[FaceEnrollment] = []
    for image in images:
        try:
            faces = engine.detect_faces(image.original_bytes)
        except FaceEngineError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        if len(faces) != 1:
            # Identity cannot be attributed in a group photo: every extra face
            # would be stored under the importing user and later match as them.
            continue
        if spoof_max_risk is not None:
            for face in faces:
                assessment = assess_spoof_risk(image.original_bytes, face.bounding_box)
                if assessment.risk > spoof_max_risk:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            "No live face could be verified in this image. "
                            "Take the photo directly with the camera in good light."
                        ),
                    )
        for index, face in enumerate(faces):
            existing = db.scalar(
                select(FaceEnrollment).where(
                    FaceEnrollment.user_id == user.id,
                    FaceEnrollment.media_asset_id == image.id,
                    FaceEnrollment.face_index == index,
                )
            )
            if existing is not None:
                if existing.embedding_model == engine.name:
                    created.append(existing)
                    continue
                db.delete(existing)
                db.flush()
            enrollment = FaceEnrollment(
                user_id=user.id,
                media_asset_id=image.id,
                face_index=index,
                embedding_model=engine.name,
                embedding=face.embedding,
                bounding_box=face.bounding_box,
                quality=face.quality,
                source=source,
            )
            db.add(enrollment)
            db.flush()
            created.append(enrollment)
    return created


def ingest_media_assets(
    db: Session,
    user: User,
    images: list[MediaAsset],
    source: str,
    engine: FaceEngine,
    spoof_max_risk: float | None = None,
) -> list[FaceEnrollment]:
    """Enrollment write API owned by the faces arm; used by the Facebook importer."""

    return _enroll_images(db, user, images, source, engine, spoof_max_risk)


def _enroll_record_images(
    db: Session,
    *,
    record_id: uuid.UUID,
    workspace_id: uuid.UUID,
    record_media_id: uuid.UUID | None,
    authorized_by: uuid.UUID,
    images: list[MediaAsset],
    source: str,
    engine: FaceEngine,
    spoof_max_risk: float | None = None,
) -> list[FaceRecordEnrollment]:
    created: list[FaceRecordEnrollment] = []
    for image in images:
        try:
            faces = engine.detect_faces(image.original_bytes)
        except FaceEngineError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
        if len(faces) != 1:
            continue
        if spoof_max_risk is not None:
            for face in faces:
                assessment = assess_spoof_risk(image.original_bytes, face.bounding_box)
                if assessment.risk > spoof_max_risk:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=(
                            "No live face could be verified in this image. "
                            "Take the photo directly with the camera in good light."
                        ),
                    )
        for index, face in enumerate(faces):
            existing = db.scalar(
                select(FaceRecordEnrollment).where(
                    FaceRecordEnrollment.record_id == record_id,
                    FaceRecordEnrollment.media_asset_id == image.id,
                    FaceRecordEnrollment.face_index == index,
                )
            )
            if existing is not None:
                if existing.embedding_model == engine.name:
                    created.append(existing)
                    continue
                db.delete(existing)
                db.flush()
            enrollment = FaceRecordEnrollment(
                record_id=record_id,
                workspace_id=workspace_id,
                media_asset_id=image.id,
                record_media_id=record_media_id,
                face_index=index,
                embedding_model=engine.name,
                embedding=face.embedding,
                bounding_box=face.bounding_box,
                quality=face.quality,
                source=source,
                authorized_by=authorized_by,
            )
            db.add(enrollment)
            db.flush()
            created.append(enrollment)
    return created


async def _read_probe_image(probe: UploadFile, settings: Settings) -> bytes:
    if (probe.content_type or "") not in _IMAGE_MIMES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Probe must be a JPEG, PNG or WebP image.",
        )
    raw = await probe.read()
    if len(raw) == 0 or (settings.max_image_bytes and len(raw) > settings.max_image_bytes):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Invalid probe size.",
        )
    try:
        with Image.open(io.BytesIO(raw)) as picture:
            picture.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image data."
        )
    return raw


async def _read_probe_upload(probe: UploadFile, settings: Settings) -> tuple[bytes, str]:
    """Read an ephemeral search probe: a photo or a short video, never persisted."""

    mime = probe.content_type or ""
    if mime in _IMAGE_MIMES:
        return await _read_probe_image(probe, settings), "image"
    if mime not in _VIDEO_MIMES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Probe must be a JPEG, PNG or WebP image, or an MP4, MOV or WebM video.",
        )
    raw = await probe.read()
    if not raw or (settings.max_video_bytes and len(raw) > settings.max_video_bytes):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Invalid probe size.",
        )
    return raw, "video"


@router.post("/faces/consent", response_model=ConsentResponse)
def grant_consent(
    payload: ConsentRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.confirm:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Explicit confirmation is required.",
        )
    settings = request.app.state.settings
    row = db.get(BiometricConsent, user.id)
    now = datetime.now(UTC)
    if row is None:
        row = BiometricConsent(
            user_id=user.id, notice_version=settings.biometric_notice_version, consented_at=now
        )
        db.add(row)
    else:
        row.notice_version = settings.biometric_notice_version
        row.consented_at = now
        row.revoked_at = None
    db.flush()
    return ConsentResponse(
        consented=True,
        notice_version=row.notice_version,
        consented_at=row.consented_at,
        face_capture_done=has_face_capture(db, user.id),
        identity_verified=has_fresh_verification(db, user.id),
    )


@router.get("/faces/consent", response_model=ConsentResponse)
def read_consent(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(BiometricConsent, user.id)
    if row is None:
        return ConsentResponse(consented=False)
    return ConsentResponse(
        consented=row.revoked_at is None,
        notice_version=row.notice_version,
        consented_at=row.consented_at,
        revoked_at=row.revoked_at,
        face_capture_done=has_face_capture(db, user.id),
        identity_verified=has_fresh_verification(db, user.id),
    )


@router.post("/faces/verify-identity", response_model=FaceVerifyResponse)
def verify_identity(
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check the selfie against the account's Facebook faces.

    Failures stay in place for direct retry with a new photo; after
    ``face_max_attempts`` failures the account locks for
    ``face_lockout_minutes``. A success resets the failure chain.
    """

    from app.social import FacebookProfile

    require_biometric_consent(db, user)
    settings = request.app.state.settings
    engine = _face_engine_or_503(settings)
    window = timedelta(minutes=settings.face_lockout_minutes)

    def recent_failures() -> list[FaceVerification]:
        # Window filter in SQL (a coarse boundary is harmless here); the
        # success reset below runs in Python so timestamp precision and time
        # zones compare exactly on every database.
        cutoff = datetime.now(UTC) - window
        last_success = db.scalar(
            select(func.max(FaceVerification.created_at)).where(
                FaceVerification.user_id == user.id,
                FaceVerification.result == "verified",
            )
        )
        if last_success is not None and last_success.tzinfo is None:
            last_success = last_success.replace(tzinfo=UTC)
        rows = list(
            db.scalars(
                select(FaceVerification)
                .where(
                    FaceVerification.user_id == user.id,
                    FaceVerification.result == "failed",
                    FaceVerification.created_at >= cutoff,
                )
                .order_by(FaceVerification.created_at.desc())
                .limit(settings.face_max_attempts)
            )
        )
        if last_success is None:
            return rows
        fresh = []
        for row in rows:
            stamp = row.created_at
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=UTC)
            # Inclusive: coarse timestamp precision can stamp a retry in the
            # same instant as the success that reset the chain.
            if stamp >= last_success:
                fresh.append(row)
        return fresh

    def locked_response(failures: list[FaceVerification]) -> FaceVerifyResponse:
        newest = failures[0].created_at
        if newest.tzinfo is None:
            newest = newest.replace(tzinfo=UTC)
        retry_after = newest + window - datetime.now(UTC)
        return FaceVerifyResponse(
            verified=False,
            status="locked",
            simulated=engine.simulated,
            attempts_remaining=0,
            retry_after_seconds=max(1, int(retry_after.total_seconds())),
        )

    def record_failure(score: float | None) -> FaceVerifyResponse:
        db.add(
            FaceVerification(
                user_id=user.id,
                result="failed",
                score=score,
                threshold=settings.face_identity_threshold,
                engine=engine.name,
                simulated=engine.simulated,
            )
        )
        if score is not None:
            # A scored mismatch proves the enrolled selfie is not this account:
            # drop it so the retry captures a fresh photo instead of
            # re-checking the same stale embedding.
            delete_selfie_enrollments(db, user.id)
        db.flush()
        failures = recent_failures()
        if len(failures) >= settings.face_max_attempts:
            return locked_response(failures)
        return FaceVerifyResponse(
            verified=False,
            status="failed",
            simulated=engine.simulated,
            attempts_remaining=settings.face_max_attempts - len(failures),
        )

    failures = recent_failures()
    if len(failures) >= settings.face_max_attempts:
        return locked_response(failures)

    captures = list(
        db.scalars(
            select(FaceEnrollment.embedding).where(
                FaceEnrollment.user_id == user.id,
                FaceEnrollment.source == _SELF_MATCH_SOURCE,
                FaceEnrollment.embedding_model == engine.name,
            )
        )
    )
    if not captures:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A face capture is required before verification.",
        )
    profile = db.get(FacebookProfile, user.id)
    if profile is None:
        # Password accounts without Facebook have no reference faces. They use
        # capture + biometric consent; verification stays pending, never failed.
        return FaceVerifyResponse(verified=False, status="pending", simulated=engine.simulated)
    assert profile is not None
    if profile.import_status not in ("done", "partial"):
        # Self-healing: resumed sessions may never have triggered the import.
        if profile.import_status == "pending":
            if settings.enqueue_processing:
                from app.tasks import import_facebook_media_task

                try:
                    import_facebook_media_task.delay(str(user.id))
                except Exception:
                    pass
                return FaceVerifyResponse(
                    verified=False, status="pending", simulated=engine.simulated
                )
            from app.social import import_facebook_media

            try:
                import_facebook_media(db, settings, user.id)
                db.refresh(profile)
            except Exception:
                pass
            if profile.import_status not in ("done", "partial"):
                return FaceVerifyResponse(
                    verified=False, status="pending", simulated=engine.simulated
                )
        else:
            return FaceVerifyResponse(verified=False, status="pending", simulated=engine.simulated)
    references = list(
        db.scalars(
            select(FaceEnrollment.embedding).where(
                FaceEnrollment.user_id == user.id,
                FaceEnrollment.source.in_(["facebook-photo", "facebook-video"]),
                FaceEnrollment.embedding_model == engine.name,
            )
        )
    )
    if engine.simulated:
        # Mock embeddings carry no identity signal; the check cannot run here.
        db.add(
            FaceVerification(
                user_id=user.id,
                result="verified",
                score=None,
                threshold=settings.face_identity_threshold,
                engine=engine.name,
                simulated=True,
                verified_for_synced_at=profile.synced_at,
            )
        )
        db.flush()
        return FaceVerifyResponse(verified=True, status="verified", simulated=True)
    if not references:
        return record_failure(None)
    best = _best_identity_score(captures, references)
    if best < settings.face_identity_threshold:
        return record_failure(round(best, 4))
    db.add(
        FaceVerification(
            user_id=user.id,
            result="verified",
            score=round(best, 4),
            threshold=settings.face_identity_threshold,
            engine=engine.name,
            simulated=False,
            verified_for_synced_at=profile.synced_at,
        )
    )
    db.flush()
    return FaceVerifyResponse(verified=True, status="verified", simulated=False)


@router.delete("/faces/consent", response_model=RevokeResponse)
def revoke_consent(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    row = db.get(BiometricConsent, user.id)
    if row is None or row.revoked_at is not None:
        return RevokeResponse(revoked=False, enrollments_deleted=0)
    row.revoked_at = datetime.now(UTC)
    enrollments = list(db.scalars(select(FaceEnrollment).where(FaceEnrollment.user_id == user.id)))
    for enrollment in enrollments:
        db.delete(enrollment)
    db.flush()
    return RevokeResponse(revoked=True, enrollments_deleted=len(enrollments))


@router.post("/faces/profile-photo", response_model=EnrollResponse, status_code=201)
async def upload_profile_photo(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_biometric_consent(db, user)
    if user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Guest users cannot use face search."
        )
    settings = request.app.state.settings
    engine = _face_engine_or_503(settings)
    raw = await _read_probe_image(file, settings)
    with Image.open(io.BytesIO(raw)) as picture:
        width, height = picture.size
    try:
        pre_faces = engine.detect_faces(raw)
    except FaceEngineError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    if len(pre_faces) > 1:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Profile photos must show exactly one face.",
        )
    # A new selfie replaces the previous one: a single current capture per user.
    delete_selfie_enrollments(db, user.id)
    db.flush()
    workspace = _ensure_home_workspace(db, user)
    session = CaptureSession(
        workspace_id=workspace.id,
        created_by_id=user.id,
        status=CaptureStatus.OPEN,
        consent_confirmed=True,
    )
    db.add(session)
    db.flush()
    asset = MediaAsset(
        workspace_id=workspace.id,
        capture_session_id=session.id,
        kind=MediaKind.IMAGE,
        mime_type=file.content_type or "image/jpeg",
        original_bytes=raw,
        sha256=hashlib.sha256(raw).hexdigest(),
        byte_size=len(raw),
        width=width,
        height=height,
        captured_at=datetime.now(UTC),
        extra_metadata={"filename": file.filename or "profile-photo", "face_profile": True},
    )
    db.add(asset)
    session.status = CaptureStatus.CLOSED
    session.closed_at = datetime.now(UTC)
    db.flush()
    spoof_max_risk = None if engine.simulated else settings.face_spoof_max_risk
    created = _enroll_images(db, user, [asset], "profile", engine, spoof_max_risk)
    db.flush()
    return EnrollResponse(
        media_id=asset.id,
        faces_enrolled=len(created),
        enrollment_ids=[item.id for item in created],
        simulated=engine.simulated,
    )


@router.post("/faces/enroll", response_model=EnrollResponse, status_code=201)
def enroll_media(
    payload: EnrollRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_biometric_consent(db, user)
    if user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Guest users cannot use face search."
        )
    settings = request.app.state.settings
    engine = _face_engine_or_503(settings)
    asset = db.get(MediaAsset, payload.media_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    _owned_root_session(db, asset, user)
    images, source = _face_source_images(db, asset)
    spoof_max_risk = None if engine.simulated else settings.face_spoof_max_risk
    created = _enroll_images(db, user, images, source, engine, spoof_max_risk)
    db.flush()
    return EnrollResponse(
        media_id=asset.id,
        faces_enrolled=len(created),
        enrollment_ids=[item.id for item in created],
        simulated=engine.simulated,
    )


@router.get("/faces/enrollments", response_model=list[OwnEnrollmentResponse])
def list_own_enrollments(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = list(
        db.scalars(
            select(FaceEnrollment)
            .where(FaceEnrollment.user_id == user.id)
            .order_by(FaceEnrollment.created_at)
        )
    )
    return [
        OwnEnrollmentResponse(
            id=item.id,
            media_id=item.media_asset_id,
            source=item.source,
            quality=item.quality,
            thumbnail_url=f"/v1/faces/enrollments/{item.id}/thumbnail",
        )
        for item in rows
    ]


@router.post("/faces/record-enroll", response_model=RecordEnrollResponse, status_code=201)
def enroll_record_media(
    payload: RecordEnrollRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.workspaces.models import Record as WorkspaceRecord
    from app.workspaces.models import RecordMedia as WorkspaceRecordMedia

    require_biometric_consent(db, user)
    if user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Guest users cannot use face search."
        )
    record = db.get(WorkspaceRecord, payload.record_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found.")
    workspace_member(record.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    if record.kind != "person" or record.status != "active":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only active person records may be enrolled.",
        )
    if not bool(getattr(record, "biometric_authorized", False)):
        basis = (payload.biometric_basis or "").strip()
        if not basis:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Record requires explicit biometric authorization with a traceable basis.",
            )
        record.biometric_authorized = True
        record.biometric_basis = basis
        record.biometric_authorized_by = user.id
        record.biometric_authorized_at = datetime.now(UTC)
        db.flush()
    if (payload.media_id is None) == (payload.record_media_id is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either media_id or record_media_id.",
        )
    settings = request.app.state.settings
    engine = _face_engine_or_503(settings)
    link: WorkspaceRecordMedia | None = None
    if payload.record_media_id is not None:
        link = db.get(WorkspaceRecordMedia, payload.record_media_id)
        if link is None or link.record_id != record.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Record media not found."
            )
        asset = db.get(MediaAsset, link.media_id)
    else:
        assert payload.media_id is not None
        asset = db.get(MediaAsset, payload.media_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    if asset.workspace_id != record.workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Media belongs to another workspace."
        )
    images, image_source = _face_source_images(db, asset)
    source = "record-frame" if image_source == "frame" else "record-portrait"
    spoof_max_risk = None if engine.simulated else settings.face_spoof_max_risk
    created = _enroll_record_images(
        db,
        record_id=record.id,
        workspace_id=record.workspace_id,
        record_media_id=link.id if link else None,
        authorized_by=user.id,
        images=images,
        source=source,
        engine=engine,
        spoof_max_risk=spoof_max_risk,
    )
    db.flush()
    return RecordEnrollResponse(
        record_id=record.id,
        media_id=asset.id,
        faces_enrolled=len(created),
        enrollment_ids=[item.id for item in created],
        simulated=engine.simulated,
    )


@router.get("/faces/record-enrollments", response_model=list[OwnRecordEnrollmentResponse])
def list_record_enrollments(
    workspace_id: uuid.UUID = Query(...),
    record_id: uuid.UUID | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_biometric_consent(db, user)
    workspace_member(workspace_id, user, db)
    query = select(FaceRecordEnrollment).where(FaceRecordEnrollment.workspace_id == workspace_id)
    if record_id is not None:
        query = query.where(FaceRecordEnrollment.record_id == record_id)
    rows = list(db.scalars(query.order_by(FaceRecordEnrollment.created_at)))
    return [
        OwnRecordEnrollmentResponse(
            id=item.id,
            record_id=item.record_id,
            workspace_id=item.workspace_id,
            media_id=item.media_asset_id,
            source=item.source,
            quality=item.quality,
            thumbnail_url=f"/v1/faces/record-enrollments/{item.id}/thumbnail",
        )
        for item in rows
    ]


@router.delete("/faces/record-enrollments/{enrollment_id}")
def delete_record_enrollment(
    enrollment_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_biometric_consent(db, user)
    if user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Guest users cannot use face search."
        )
    enrollment = db.get(FaceRecordEnrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found.")
    workspace_member(enrollment.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    record_id = enrollment.record_id
    db.delete(enrollment)
    db.flush()
    return {"deleted": True, "record_id": str(record_id)}


def _rank_stage(
    probe_faces: list[DetectedFace],
    enrollments: list[FaceEnrollment],
    threshold: float,
    limit: int,
) -> list[tuple[uuid.UUID, float, FaceEnrollment, int]]:
    """Best match per user within one stage pool, sorted by similarity."""

    best: dict[uuid.UUID, tuple[float, FaceEnrollment, int]] = {}
    for probe_index, probe_face in enumerate(probe_faces):
        for enrollment in enrollments:
            score = cosine_similarity(probe_face.embedding, enrollment.embedding)
            current = best.get(enrollment.user_id)
            if current is None or score > current[0]:
                best[enrollment.user_id] = (score, enrollment, probe_index)
    return sorted(
        (
            (user_id, score, enrollment, probe_index)
            for user_id, (score, enrollment, probe_index) in best.items()
            if score >= threshold
        ),
        key=lambda item: (-item[1], str(item[0])),
    )[:limit]


def _rank_record_stage(
    probe_faces: list[DetectedFace],
    enrollments: list[FaceRecordEnrollment],
    threshold: float,
    limit: int,
) -> list[tuple[uuid.UUID, float, FaceRecordEnrollment, int]]:
    best: dict[uuid.UUID, tuple[float, FaceRecordEnrollment, int]] = {}
    for probe_index, probe_face in enumerate(probe_faces):
        for enrollment in enrollments:
            score = cosine_similarity(probe_face.embedding, enrollment.embedding)
            current = best.get(enrollment.record_id)
            if current is None or score > current[0]:
                best[enrollment.record_id] = (score, enrollment, probe_index)
    return sorted(
        (
            (record_id, score, enrollment, probe_index)
            for record_id, (score, enrollment, probe_index) in best.items()
            if score >= threshold
        ),
        key=lambda item: (-item[1], str(item[0])),
    )[:limit]


@router.post("/faces/search", response_model=FaceSearchResponse)
async def search_faces(
    request: Request,
    workspace_id: str = Form(...),
    media_id: str | None = Form(default=None),
    probe: UploadFile | None = File(default=None),
    include_records: bool = Form(default=True),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_biometric_consent(db, user)
    if user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Guest users cannot use face search."
        )
    settings = request.app.state.settings
    engine = _face_engine_or_503(settings)
    try:
        workspace_uuid = uuid.UUID(workspace_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid workspace id."
        )
    workspace_member(workspace_uuid, user, db)
    if (probe is None) == (media_id is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either an ephemeral probe image or a stored media id.",
        )
    probe_faces: list[DetectedFace] = []
    probe_frames = 0
    if probe is not None:
        raw, kind = await _read_probe_upload(probe, settings)
        try:
            if kind == "video":
                frames = _extract_video_probe_frames(raw, settings.face_video_probe_frames)
                probe_frames = len(frames)
                for frame_bytes in frames:
                    probe_faces.extend(engine.detect_faces(frame_bytes))
            else:
                probe_frames = 1
                probe_faces = engine.detect_faces(raw)
        except FaceEngineError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
    else:
        assert media_id is not None
        try:
            media_uuid = uuid.UUID(media_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid media id."
            )
        asset = db.get(MediaAsset, media_uuid)
        if asset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
        workspace_member(asset.workspace_id, user, db)
        images, _ = _face_source_images(db, asset)
        probe_frames = len(images)
        try:
            for image in images:
                probe_faces.extend(engine.detect_faces(image.original_bytes))
        except FaceEngineError as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
            ) from exc
    usable_faces = [
        kept
        for face in probe_faces
        if (
            kept := _usable_probe_face(
                face,
                min_quality=settings.face_min_quality,
                min_area=settings.face_min_box_area,
            )
        )
        is not None
    ]
    usable_faces.sort(key=lambda face: face.quality, reverse=True)
    probe_faces_skipped = len(probe_faces) - len(usable_faces)
    if len(usable_faces) > settings.face_probe_max_faces:
        probe_faces_skipped += len(usable_faces) - settings.face_probe_max_faces
        usable_faces = usable_faces[: settings.face_probe_max_faces]
    probe_faces = usable_faces
    if not probe_faces:
        return FaceSearchResponse(
            found=False,
            probe_faces=0,
            probe_frames=probe_frames,
            probe_faces_skipped=probe_faces_skipped,
            threshold=settings.face_match_threshold,
            simulated=engine.simulated,
        )
    member_ids = list(
        db.scalars(
            select(WorkspaceMember.user_id).where(WorkspaceMember.workspace_id == workspace_uuid)
        )
    )
    consented_ids: set[uuid.UUID] = set()
    if member_ids:
        consented_ids = set(
            db.scalars(
                select(BiometricConsent.user_id).where(
                    BiometricConsent.user_id.in_(member_ids),
                    BiometricConsent.revoked_at.is_(None),
                )
            )
        )
    candidates = (
        list(db.scalars(select(FaceEnrollment).where(FaceEnrollment.user_id.in_(consented_ids))))
        if consented_ids
        else []
    )
    enrollments: list[FaceEnrollment] = []
    enrollments_skipped = 0
    for candidate in candidates:
        if candidate.embedding_model != engine.name:
            enrollments_skipped += 1
            continue
        if not _usable_enrollment(
            candidate,
            min_quality=settings.face_min_quality,
            min_area=settings.face_min_box_area,
        ):
            enrollments_skipped += 1
            continue
        enrollments.append(candidate)
    by_source: dict[str, list[FaceEnrollment]] = {}
    for enrollment in enrollments:
        by_source.setdefault(enrollment.source, []).append(enrollment)
    ranked: list[tuple[uuid.UUID, float, FaceEnrollment, int]] = []
    stage: int | None = None
    stages_searched: list[int] = []
    for index, sources in enumerate(_FACE_SEARCH_STAGES, start=1):
        stages_searched.append(index)
        pool = [item for source in sources for item in by_source.get(source, [])]
        ranked = _rank_stage(
            probe_faces, pool, settings.face_match_threshold, settings.face_search_limit
        )
        if ranked:
            stage = index
            break
    # Display-only enrichment: read-only lookup of synced Facebook profile
    # fields. The faces arm still owns every enrollment write and route; the
    # import is lazy so the arms never couple at module load.
    from app.social import FacebookProfile

    profiles = {}
    if ranked:
        profiles = {
            row.user_id: row
            for row in db.scalars(
                select(FacebookProfile).where(
                    FacebookProfile.user_id.in_([user_id for user_id, _, _, _ in ranked])
                )
            )
        }
    matches: list[FaceMatch] = []
    for user_id, score, enrollment, probe_index in ranked:
        candidate = db.get(User, user_id)
        if candidate is None or not candidate.is_active:
            continue
        profile = profiles.get(user_id)
        matches.append(
            FaceMatch(
                user_id=user_id,
                display_name=candidate.display_name,
                similarity=round(score, 4),
                match_type=(
                    "direct" if enrollment.source == _SELF_MATCH_SOURCE else "possible_acquaintance"
                ),
                picture_url=profile.picture_url if profile else None,
                profile_link=profile.profile_link if profile else None,
                evidence=FaceMatchEvidence(
                    enrollment_id=enrollment.id,
                    media_id=enrollment.media_asset_id,
                    thumbnail_url=f"/v1/faces/enrollments/{enrollment.id}/thumbnail",
                    source=enrollment.source,
                ),
                probe_face_index=probe_index,
                probe_box=dict(probe_faces[probe_index].bounding_box),
            )
        )
    record_matches: list[RecordFaceMatch] = []
    record_skipped = 0
    if include_records:
        from app.workspaces.models import Record as WorkspaceRecord

        record_candidates = list(
            db.scalars(
                select(FaceRecordEnrollment).where(
                    FaceRecordEnrollment.workspace_id == workspace_uuid
                )
            )
        )
        usable_records: list[FaceRecordEnrollment] = []
        wanted_records: set[uuid.UUID] = set()
        for item in record_candidates:
            if item.embedding_model != engine.name:
                record_skipped += 1
                continue
            if not _usable_record_enrollment(
                item,
                min_quality=settings.face_min_quality,
                min_area=settings.face_min_box_area,
            ):
                record_skipped += 1
                continue
            wanted_records.add(item.record_id)
            usable_records.append(item)
        authorized: dict[uuid.UUID, WorkspaceRecord] = {}
        if wanted_records:
            for row in db.scalars(
                select(WorkspaceRecord).where(WorkspaceRecord.id.in_(wanted_records))
            ):
                if (
                    row.workspace_id != workspace_uuid
                    or row.status != "active"
                    or row.kind != "person"
                    or not bool(getattr(row, "biometric_authorized", False))
                ):
                    continue
                authorized[row.id] = row
        searchable = [item for item in usable_records if item.record_id in authorized]
        record_skipped += len(usable_records) - len(searchable)
        ranked_records = _rank_record_stage(
            probe_faces, searchable, settings.face_match_threshold, settings.face_search_limit
        )
        for record_id, score, enrollment, probe_index in ranked_records:
            row = authorized.get(record_id)
            if row is None:
                continue
            record_matches.append(
                RecordFaceMatch(
                    record_id=record_id,
                    workspace_id=workspace_uuid,
                    external_id=row.external_id,
                    title=row.title,
                    similarity=round(score, 4),
                    record_url=f"/v1/workspaces/{workspace_uuid}/records/{record_id}",
                    simulated=bool(row.simulated),
                    evidence=RecordFaceMatchEvidence(
                        enrollment_id=enrollment.id,
                        media_id=enrollment.media_asset_id,
                        thumbnail_url=f"/v1/faces/record-enrollments/{enrollment.id}/thumbnail",
                        source=enrollment.source,
                    ),
                    probe_face_index=probe_index,
                    probe_box=dict(probe_faces[probe_index].bounding_box),
                )
            )
    return FaceSearchResponse(
        found=bool(matches or record_matches),
        probe_faces=len(probe_faces),
        probe_frames=probe_frames,
        probe_faces_skipped=probe_faces_skipped,
        enrollments_skipped=enrollments_skipped,
        matches=matches,
        matches_records=record_matches,
        record_enrollments_skipped=record_skipped,
        threshold=settings.face_match_threshold,
        simulated=engine.simulated,
        stage=stage,
        stages_searched=stages_searched,
    )


@router.get("/faces/enrollments/{enrollment_id}/thumbnail")
def enrollment_thumbnail(
    enrollment_id: uuid.UUID,
    full_size: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    require_biometric_consent(db, user)
    enrollment = db.get(FaceEnrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found.")
    asset = db.get(MediaAsset, enrollment.media_asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence media not found."
        )
    # Enrollment evidence may live in the candidate's home workspace, so access
    # follows the same rule as search results: a shared workspace plus consent.
    shared = db.scalar(
        select(WorkspaceMember.id)
        .where(WorkspaceMember.user_id == user.id)
        .where(
            WorkspaceMember.workspace_id.in_(
                select(WorkspaceMember.workspace_id).where(
                    WorkspaceMember.user_id == enrollment.user_id
                )
            )
        )
        .limit(1)
    )
    if shared is None or not has_biometric_consent(db, enrollment.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied."
        )
    try:
        with Image.open(io.BytesIO(asset.original_bytes)) as picture:
            frame = ImageOps.exif_transpose(picture).convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image data."
        )
    width, height = frame.size
    box = enrollment.bounding_box or {}
    try:
        left = float(box.get("x", 0.0)) * width
        top = float(box.get("y", 0.0)) * height
        right = left + float(box.get("width", 1.0)) * width
        bottom = top + float(box.get("height", 1.0)) * height
    except (TypeError, ValueError):
        left, top, right, bottom = 0.0, 0.0, float(width), float(height)
    # A photo-wide stroke can fill a small face. Keep the outline outside
    # the detected region and size it relative to that face instead.
    face_size = max(1.0, min(right - left, bottom - top))
    outline = max(1, min(max(2, width // 200), int(face_size / 24)))
    ImageDraw.Draw(frame).rectangle(
        [
            max(0, left - outline),
            max(0, top - outline),
            min(width - 1, right + outline),
            min(height - 1, bottom + outline),
        ],
        outline=(240, 191, 36),
        width=outline,
    )
    if not full_size:
        frame.thumbnail((360, 480))
    output = io.BytesIO()
    frame.save(output, format="JPEG", quality=95 if full_size else 85)
    return Response(
        output.getvalue(),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store"},
    )


@router.get("/faces/record-enrollments/{enrollment_id}/thumbnail")
def record_enrollment_thumbnail(
    enrollment_id: uuid.UUID,
    full_size: bool = True,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.workspaces.models import Record as WorkspaceRecord

    require_biometric_consent(db, user)
    enrollment = db.get(FaceRecordEnrollment, enrollment_id)
    if enrollment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found.")
    workspace_member(enrollment.workspace_id, user, db)
    record = db.get(WorkspaceRecord, enrollment.record_id)
    if (
        record is None
        or record.workspace_id != enrollment.workspace_id
        or record.status != "active"
        or not bool(getattr(record, "biometric_authorized", False))
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Record biometric access denied."
        )
    asset = db.get(MediaAsset, enrollment.media_asset_id)
    if asset is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evidence media not found."
        )
    try:
        with Image.open(io.BytesIO(asset.original_bytes)) as picture:
            frame = ImageOps.exif_transpose(picture).convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image data."
        )
    width, height = frame.size
    box = enrollment.bounding_box or {}
    try:
        left = float(box.get("x", 0.0)) * width
        top = float(box.get("y", 0.0)) * height
        right = left + float(box.get("width", 1.0)) * width
        bottom = top + float(box.get("height", 1.0)) * height
    except (TypeError, ValueError):
        left, top, right, bottom = 0.0, 0.0, float(width), float(height)
    face_size = max(1.0, min(right - left, bottom - top))
    outline = max(1, min(max(2, width // 200), int(face_size / 24)))
    ImageDraw.Draw(frame).rectangle(
        [
            max(0, left - outline),
            max(0, top - outline),
            min(width - 1, right + outline),
            min(height - 1, bottom + outline),
        ],
        outline=(240, 191, 36),
        width=outline,
    )
    if not full_size:
        frame.thumbnail((360, 480))
    output = io.BytesIO()
    frame.save(output, format="JPEG", quality=95 if full_size else 85)
    return Response(
        output.getvalue(),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store"},
    )
