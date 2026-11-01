"""Store gallery AI detection boxes for overlay rendering.

Revision ID: 20261030_0025
Revises: 20261030_0024
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261030_0025"
down_revision = "20261030_0024"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("publications")}
    if "ai_detections" not in columns:
        op.add_column(
            "publications",
            sa.Column("ai_detections", sa.JSON(), nullable=False, server_default="[]"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    columns = {item["name"] for item in inspect(bind).get_columns("publications")}
    if "ai_detections" in columns:
        op.drop_column("publications", "ai_detections")
