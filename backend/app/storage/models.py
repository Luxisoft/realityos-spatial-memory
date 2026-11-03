import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models import TimestampMixin


class StorageConnection(TimestampMixin, Base):
    __tablename__ = "storage_connections"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    provider: Mapped[str] = mapped_column(String(16))
    endpoint: Mapped[str] = mapped_column(String(2048))
    bucket: Mapped[str] = mapped_column(String(63))
    region: Mapped[str] = mapped_column(String(80), default="auto")
    prefix: Mapped[str] = mapped_column(String(1024), default="")
    secret: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(default=True)
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workspaces.id"))


class StorageImport(TimestampMixin, Base):
    __tablename__ = "storage_imports"
    __table_args__ = (UniqueConstraint("connection_id", "request_key"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("storage_connections.id"), index=True
    )
    request_key: Mapped[str] = mapped_column(String(128))
    payload_hash: Mapped[str] = mapped_column(String(64))
    revision: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    audience: Mapped[str] = mapped_column(String(16))
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workspaces.id"))
    items: Mapped[list] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class StorageSync(TimestampMixin, Base):
    __tablename__ = "storage_syncs"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("storage_connections.id"), index=True
    )
    prefix: Mapped[str] = mapped_column(String(1024), default="")
    audience: Mapped[str] = mapped_column(String(16))
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workspaces.id"))
    interval_minutes: Mapped[int] = mapped_column(default=60)
    enabled: Mapped[bool] = mapped_column(default=False)
    next_run: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    cursor: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(String(200))
    seen_keys: Mapped[list] = mapped_column(JSON, default=list)
