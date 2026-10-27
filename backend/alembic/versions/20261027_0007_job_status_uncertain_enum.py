"""Align the production job-status enum with SQLAlchemy's persisted names.

Revision ID: 20261027_0007
Revises: 20261027_0006
Create Date: 2026-10-27
"""

from alembic import op

revision = "20261027_0007"
down_revision = "20261027_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the enum label used by the existing SQLAlchemy JobStatus mapping."""

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Existing initial-schema values are upper-case enum member names.
        # Revision 0005 accidentally added lowercase `uncertain`; retain that
        # historical value but add the valid member name used by the ORM.
        op.execute("ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'UNCERTAIN'")


def downgrade() -> None:
    # PostgreSQL does not support removing one enum value safely. Keeping the
    # additive label is deliberate and mirrors the existing migrations.
    pass
