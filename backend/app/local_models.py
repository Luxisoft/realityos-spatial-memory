"""One installation receipt, deliberately independent of deletable scenario data."""

import uuid

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models import TimestampMixin


class LocalEvaluationState(TimestampMixin, Base):
    __tablename__ = "local_evaluation_state"
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    manifest_hash: Mapped[str] = mapped_column(String(64))
    counts: Mapped[dict] = mapped_column(JSON)


class LocalAccessAccount(Base):
    """Explicit local selector eligibility; account/profile data stay in their tables."""

    __tablename__ = "local_access_accounts"
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
