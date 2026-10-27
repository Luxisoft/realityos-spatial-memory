"""Store large media as ordered PostgreSQL BYTEA chunks.

Revision ID: 20261027_0003
Revises: 20261027_0002
Create Date: 2026-10-27
"""

import sqlalchemy as sa

from alembic import op

revision = "20261027_0003"
down_revision = "20261027_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "media_asset_chunks",
        sa.Column("asset_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["asset_id"], ["media_assets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("asset_id", "chunk_index"),
    )


def downgrade() -> None:
    op.drop_table("media_asset_chunks")
