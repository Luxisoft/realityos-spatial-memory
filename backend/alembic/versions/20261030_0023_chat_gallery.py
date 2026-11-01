"""Persist gallery matches and simulated flag on chat turns.

Revision ID: 20261030_0023
Revises: 20261030_0022
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261030_0023"
down_revision = "20261030_0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("chat_messages")}
    if "gallery" not in columns:
        op.add_column(
            "chat_messages",
            sa.Column("gallery", sa.JSON(), nullable=False, server_default="[]"),
        )
    if "simulated" not in columns:
        op.add_column(
            "chat_messages",
            sa.Column("simulated", sa.Boolean(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    for column in ("simulated", "gallery"):
        columns = {item["name"] for item in inspect(bind).get_columns("chat_messages")}
        if column in columns:
            op.drop_column("chat_messages", column)
