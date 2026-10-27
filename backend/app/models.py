from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Role(str, enum.Enum):
    ADMIN = "admin"
    REGISTER = "register"
    QUERY = "query"


class CaptureStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"


class MediaKind(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    FRAME = "frame"
    MASK = "mask"
    CROP = "crop"


class VerificationStatus(str, enum.Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


class ProcessingOperation(str, enum.Enum):
    """The durable operation represented by a processing job."""

    ANALYSIS = "analysis"
    SEGMENTATION = "segmentation"
    VIDEO_TRACKING = "video_tracking"


class DeviceStatus(str, enum.Enum):
    ACTIVE = "active"
    REVOKED = "revoked"


class FactProvenance(str, enum.Enum):
    VISIBLE_TEXT = "visible_text"
    VISUAL = "visual"
    TEMPORAL = "temporal"
    MANUAL = "manual"
    LEGACY = "legacy"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Workspace(TimestampMixin, Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class WorkspaceMember(TimestampMixin, Base):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id", name="uq_workspace_member"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    role: Mapped[Role] = mapped_column(Enum(Role, name="workspace_role"), nullable=False)


class Device(TimestampMixin, Base):
    """A revocable, workspace-bound ingestion identity, never a human account."""

    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("device_identifier", name="uq_device_identifier"),
        Index("ix_device_workspace_status", "workspace_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    device_identifier: Mapped[str] = mapped_column(String(96), nullable=False)
    label: Mapped[str] = mapped_column(String(160), nullable=False)
    credential_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, name="device_status"), default=DeviceStatus.ACTIVE, nullable=False
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class DeviceAssignment(TimestampMixin, Base):
    """Administrator-declared owner label, retained as historical metadata."""

    __tablename__ = "device_assignments"
    __table_args__ = (Index("ix_device_assignment_active", "device_id", "effective_to"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True, nullable=False
    )
    operator_label: Mapped[str] = mapped_column(String(160), nullable=False)
    external_reference: Mapped[str | None] = mapped_column(String(160))
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attested_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    notice_version: Mapped[str] = mapped_column(String(80), nullable=False)
    attested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Zone(TimestampMixin, Base):
    __tablename__ = "zones"
    __table_args__ = (UniqueConstraint("workspace_id", "parent_id", "name", name="uq_zone_path"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("zones.id"))
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), default="zone", nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class CaptureSession(TimestampMixin, Base):
    __tablename__ = "capture_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("zones.id"))
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    device_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("devices.id"), index=True)
    device_assignment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("device_assignments.id")
    )
    origin: Mapped[str] = mapped_column(String(16), default="admin", nullable=False)
    status: Mapped[CaptureStatus] = mapped_column(
        Enum(CaptureStatus, name="capture_status"), default=CaptureStatus.OPEN, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consent_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class MediaAsset(TimestampMixin, Base):
    __tablename__ = "media_assets"
    __table_args__ = (
        UniqueConstraint("capture_session_id", "sha256", name="uq_media_session_hash"),
        Index("ix_media_workspace_sha256", "workspace_id", "sha256"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    capture_session_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("capture_sessions.id", ondelete="SET NULL"), index=True
    )
    parent_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("media_assets.id"))
    kind: Mapped[MediaKind] = mapped_column(Enum(MediaKind, name="media_kind"), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(127), nullable=False)
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    extra_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class MediaAssetChunk(Base):
    """Ordered PostgreSQL BYTEA pieces for media larger than one practical value."""

    __tablename__ = "media_asset_chunks"

    asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media_assets.id", ondelete="CASCADE"), primary_key=True
    )
    chunk_index: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)


class TrackedObject(TimestampMixin, Base):
    __tablename__ = "tracked_objects"
    __table_args__ = (
        UniqueConstraint("workspace_id", "canonical_name", name="uq_object_workspace_name"),
        Index("ix_object_workspace_name", "workspace_id", "canonical_name"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    canonical_name: Mapped[str] = mapped_column(String(240), nullable=False)
    category: Mapped[str | None] = mapped_column(String(120))
    attributes: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class ObjectAlias(TimestampMixin, Base):
    __tablename__ = "object_aliases"
    __table_args__ = (UniqueConstraint("object_id", "alias", name="uq_object_alias"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_objects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    alias: Mapped[str] = mapped_column(String(240), index=True, nullable=False)


class ObjectObservation(TimestampMixin, Base):
    __tablename__ = "object_observations"
    __table_args__ = (
        Index("ix_observation_object_verified_seen", "object_id", "verification_status", "seen_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_objects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("zones.id"))
    media_asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_assets.id"), nullable=False)
    mask_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("media_assets.id"))
    capture_session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("capture_sessions.id"))
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    # Muse Spark's detection box is retained even after SAM refines the visible
    # geometry, so a failed/refused refinement never removes usable evidence.
    muse_bounding_box: Mapped[dict[str, float] | None] = mapped_column(JSON)
    bounding_box: Mapped[dict[str, float] | None] = mapped_column(JSON)
    spatial_description: Mapped[str | None] = mapped_column(Text)
    relationships: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    visual_confidence: Mapped[float] = mapped_column(Float, nullable=False)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ObjectFact(TimestampMixin, Base):
    """One evidenced claim about an object; summaries are derived from these rows."""

    __tablename__ = "object_facts"
    __table_args__ = (
        Index("ix_object_fact_workspace_type_status", "workspace_id", "fact_type", "verification_status"),
        Index("ix_object_fact_object_type", "object_id", "fact_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_objects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    observation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("object_observations.id", ondelete="CASCADE"), index=True
    )
    fact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    value_text: Mapped[str | None] = mapped_column(String(500))
    normalized_value: Mapped[str | None] = mapped_column(String(500), index=True)
    numeric_value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(40))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    provenance: Mapped[FactProvenance] = mapped_column(
        Enum(FactProvenance, name="fact_provenance"), nullable=False
    )
    evidence_geometry: Mapped[dict[str, float] | None] = mapped_column(JSON)
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.PENDING,
        nullable=False,
    )
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ObjectActivityEvent(TimestampMixin, Base):
    """A bounded, evidence-backed temporal event, never biometric attribution."""

    __tablename__ = "object_activity_events"
    __table_args__ = (Index("ix_activity_workspace_started", "workspace_id", "started_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_objects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    observation_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("object_observations.id"))
    capture_session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("capture_sessions.id"))
    device_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("devices.id"), index=True)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    start_pts_seconds: Mapped[float | None] = mapped_column(Float)
    end_pts_seconds: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    provenance: Mapped[FactProvenance] = mapped_column(
        Enum(FactProvenance, name="fact_provenance"), nullable=False
    )
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus, name="verification_status"),
        default=VerificationStatus.PENDING,
        nullable=False,
    )


class ObjectTrack(TimestampMixin, Base):
    """One priority object followed through a source video in detailed mode."""

    __tablename__ = "object_tracks"
    __table_args__ = (
        UniqueConstraint("source_media_asset_id", "object_id", name="uq_video_track_object"),
        Index("ix_object_track_workspace_status", "workspace_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    object_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_objects.id", ondelete="CASCADE"), index=True, nullable=False
    )
    source_media_asset_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media_assets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    processing_job_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("processing_jobs.id"))
    model_name: Mapped[str] = mapped_column(String(120), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_pts_seconds: Mapped[float | None] = mapped_column(Float)
    metadata_json: Mapped[dict[str, Any]] = mapped_column("metadata", JSON, default=dict)


class ObjectTrackSegment(TimestampMixin, Base):
    """External-request state for one bounded source-video interval."""

    __tablename__ = "object_track_segments"
    __table_args__ = (UniqueConstraint("track_id", "segment_index", name="uq_track_segment_index"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("object_tracks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_pts_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_pts_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    provider_file_id: Mapped[str | None] = mapped_column(String(160))
    request_state: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)


class ObjectTrackFrame(TimestampMixin, Base):
    """Per-frame SAM geometry. Original pixels remain in the PostgreSQL video asset."""

    __tablename__ = "object_track_frames"
    __table_args__ = (
        UniqueConstraint("track_id", "source_frame_index", name="uq_track_source_frame"),
        Index("ix_track_frame_track_pts", "track_id", "pts_seconds"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("object_tracks.id", ondelete="CASCADE"), index=True, nullable=False
    )
    track_segment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("object_track_segments.id", ondelete="CASCADE"), index=True
    )
    source_frame_index: Mapped[int] = mapped_column(Integer, nullable=False)
    pts_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    bounding_box: Mapped[dict[str, float] | None] = mapped_column(JSON)
    mask_rle: Mapped[bytes | None] = mapped_column(LargeBinary)
    mask_width: Mapped[int | None] = mapped_column(Integer)
    mask_height: Mapped[int | None] = mapped_column(Integer)
    confidence: Mapped[float | None] = mapped_column(Float)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ProcessingJob(TimestampMixin, Base):
    __tablename__ = "processing_jobs"
    __table_args__ = (
        UniqueConstraint("workspace_id", "idempotency_key", name="uq_job_workspace_idempotency"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True, nullable=False
    )
    media_asset_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_assets.id"), nullable=False)
    capture_session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("capture_sessions.id"))
    observation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("object_observations.id", ondelete="CASCADE"), index=True
    )
    operation: Mapped[ProcessingOperation] = mapped_column(
        Enum(
            ProcessingOperation,
            name="processing_operation",
            values_callable=lambda enum_class: [member.value for member in enum_class],
        ),
        default=ProcessingOperation.ANALYSIS,
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.QUEUED, nullable=False
    )
    idempotency_key: Mapped[str] = mapped_column(String(160), nullable=False)
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class RefreshToken(TimestampMixin, Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class QueryHistory(TimestampMixin, Base):
    __tablename__ = "query_history"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    result_observation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("object_observations.id")
    )


class AuditEvent(TimestampMixin, Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workspaces.id"), index=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    device_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("devices.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
