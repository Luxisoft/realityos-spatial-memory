"""Versioned visual evidence and private, unpublished upload candidates."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models import TimestampMixin


class GalleryEvidence(TimestampMixin, Base):
    __tablename__ = "gallery_evidence"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.id"), index=True)
    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_assets.id"), index=True)
    image_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    content_hash: Mapped[str] = mapped_column(String(64), index=True)
    frame_timestamp_ms: Mapped[int | None] = mapped_column(Integer)
    detections: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(Integer, default=2)
    index_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("gallery_index_runs.id"), index=True
    )


class PublicationUpload(TimestampMixin, Base):
    __tablename__ = "publication_uploads"
    __table_args__ = (UniqueConstraint("owner_id", "request_key", name="uq_upload_request"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    request_key: Mapped[str] = mapped_column(String(64))
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workspaces.id"))
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("publication_terms.id", ondelete="SET NULL")
    )
    tag_ids: Mapped[list] = mapped_column(JSON, default=list, nullable=False, server_default="[]")
    original_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    mime_type: Mapped[str] = mapped_column(String(64))
    caption: Mapped[str] = mapped_column(Text, default="")
    note_text: Mapped[str] = mapped_column(Text, default="")
    note_source: Mapped[str] = mapped_column(String(16), default="")
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    duplicate_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("publications.id"))
    expected_media_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("media_assets.id"))
    result_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("publications.id"))
    analysis: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)


class PublicationRevision(TimestampMixin, Base):
    __tablename__ = "publication_revisions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.id"), index=True)
    previous: Mapped[dict] = mapped_column(JSON)


class PublicationDuplicate(TimestampMixin, Base):
    __tablename__ = "publication_duplicates"
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.id"), primary_key=True)
    canonical_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.id"), index=True)
    previous: Mapped[dict] = mapped_column(JSON, default=dict)


class PublicationTranslation(TimestampMixin, Base):
    """Prepared text by publication, language and immutable source-text digest."""

    __tablename__ = "publication_translations"
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True
    )
    language: Mapped[str] = mapped_column(String(2), primary_key=True)
    text_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    translated_text: Mapped[str] = mapped_column(Text)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)


class GalleryIndexRun(TimestampMixin, Base):
    __tablename__ = "gallery_index_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), index=True
    )
    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_assets.id"))
    source_hash: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(24), default="running")
    stage: Mapped[str] = mapped_column(String(32), default="detection")
    attempt: Mapped[int] = mapped_column(Integer, default=1)
    lease: Mapped[str] = mapped_column(String(36))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    lease_until: Mapped[object | None] = mapped_column(DateTime(timezone=True))
    progress: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[dict | None] = mapped_column(JSON)
