"""Ownership of bucket copies, introduced after publication uploads exist."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models import TimestampMixin


class StorageObject(TimestampMixin, Base):
    __tablename__ = "storage_objects"
    __table_args__ = (
        UniqueConstraint("connection_id", "revision", "key", "workspace_id", "upload_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    connection_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("storage_connections.id"), index=True
    )
    revision: Mapped[int] = mapped_column(Integer)
    key: Mapped[str] = mapped_column(String(1024))
    sha256: Mapped[str] = mapped_column(String(64))
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("workspaces.id"))
    upload_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("publication_uploads.id"))
    retired: Mapped[bool] = mapped_column(default=False)
