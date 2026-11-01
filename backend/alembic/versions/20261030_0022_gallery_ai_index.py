"""AI index columns for gallery publications.

Revision ID: 20261030_0022
Revises: 20261029_0021
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261030_0022"
down_revision = "20261029_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("publications")}
    if "ai_labels" not in columns:
        op.add_column(
            "publications",
            sa.Column("ai_labels", sa.JSON(), nullable=False, server_default="[]"),
        )
    if "ai_caption" not in columns:
        op.add_column(
            "publications",
            sa.Column("ai_caption", sa.Text(), nullable=False, server_default=""),
        )
    if "face_count" not in columns:
        op.add_column(
            "publications",
            sa.Column("face_count", sa.Integer(), nullable=False, server_default="0"),
        )
    if "indexed_at" not in columns:
        op.add_column("publications", sa.Column("indexed_at", sa.DateTime(timezone=True)))
    if "index_error" not in columns:
        op.add_column("publications", sa.Column("index_error", sa.Text()))
    if bind.dialect.name == "postgresql":
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_publications_search_text_trgm "
            "ON publications USING gin (search_text gin_trgm_ops)"
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("DROP INDEX IF EXISTS ix_publications_search_text_trgm")
    for column in ("index_error", "indexed_at", "face_count", "ai_caption", "ai_labels"):
        columns = {item["name"] for item in inspect(bind).get_columns("publications")}
        if column in columns:
            op.drop_column("publications", column)
