import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models import TimestampMixin


class Connection(TimestampMixin, Base):
    __tablename__ = "workspace_connections"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), index=True)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    name: Mapped[str] = mapped_column(String(160))
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    active: Mapped[bool] = mapped_column(default=True)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    secret_encrypted: Mapped[str | None] = mapped_column(Text)


class ImportRun(TimestampMixin, Base):
    __tablename__ = "workspace_import_runs"
    __table_args__ = (UniqueConstraint("connection_id", "request_key"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace_connections.id"), index=True
    )
    request_key: Mapped[str] = mapped_column(String(128))
    payload_hash: Mapped[str] = mapped_column(String(64))
    result: Mapped[dict] = mapped_column(JSON, default=dict)


class Record(TimestampMixin, Base):
    __tablename__ = "workspace_records"
    __table_args__ = (UniqueConstraint("connection_id", "external_id"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), index=True)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspace_connections.id"), index=True
    )
    external_id: Mapped[str] = mapped_column(String(160))
    kind: Mapped[str] = mapped_column(String(32), index=True)
    title: Mapped[str] = mapped_column(String(200))
    data: Mapped[dict] = mapped_column(JSON, default=dict)
    related_ids: Mapped[list] = mapped_column(JSON, default=list)
    version: Mapped[int] = mapped_column(default=1)
    status: Mapped[str] = mapped_column(String(16), default="draft")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    simulated: Mapped[bool] = mapped_column(default=False)


class RecordRevision(TimestampMixin, Base):
    __tablename__ = "workspace_record_revisions"
    __table_args__ = (UniqueConstraint("record_id", "version"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspace_records.id"), index=True)
    version: Mapped[int]
    snapshot: Mapped[dict] = mapped_column(JSON)


class RecordNote(TimestampMixin, Base):
    __tablename__ = "workspace_record_notes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspace_records.id"), index=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    text: Mapped[str] = mapped_column(Text)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RecordMedia(TimestampMixin, Base):
    __tablename__ = "workspace_record_media"
    __table_args__ = (UniqueConstraint("record_id", "external_id"),)
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    record_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspace_records.id"), index=True)
    external_id: Mapped[str] = mapped_column(String(160))
    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_assets.id"))
    publication_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("publications.id"))
