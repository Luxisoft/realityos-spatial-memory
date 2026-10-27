"""Create RealityOS initial PostgreSQL schema.

Revision ID: 20261026_0001
Revises:
Create Date: 2026-10-26
"""

from alembic import op
from app import models  # noqa: F401
from app.db import Base

revision = "20261026_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
