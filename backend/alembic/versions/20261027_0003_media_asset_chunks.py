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
    if op.get_bind().dialect.name == "postgresql":
        op.execute(
            """
            CREATE TABLE IF NOT EXISTS media_asset_chunks (
              asset_id UUID NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
              chunk_index INTEGER NOT NULL,
              content BYTEA NOT NULL,
              byte_size INTEGER NOT NULL,
              PRIMARY KEY (asset_id, chunk_index)
            )
            """
        )
        return
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
