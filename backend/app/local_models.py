"""One installation receipt, deliberately independent of deletable scenario data."""

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models import TimestampMixin


class LocalEvaluationState(TimestampMixin, Base):
    __tablename__ = "local_evaluation_state"
    name: Mapped[str] = mapped_column(String(80), primary_key=True)
    manifest_hash: Mapped[str] = mapped_column(String(64))
    counts: Mapped[dict] = mapped_column(JSON)
