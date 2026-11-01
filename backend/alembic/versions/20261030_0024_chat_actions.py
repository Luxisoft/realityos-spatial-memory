"""Persist quick replies and face action on chat turns.

Revision ID: 20261030_0024
Revises: 20261030_0023
Create Date: 2026-10-30
"""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261030_0024"
down_revision = "20261030_0023"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("chat_messages")}
    if "quick_replies" not in columns:
        op.add_column(
            "chat_messages",
            sa.Column("quick_replies", sa.JSON(), nullable=False, server_default="[]"),
        )
    if "face_action" not in columns:
        op.add_column(
            "chat_messages",
            sa.Column("face_action", sa.Boolean(), nullable=False, server_default="0"),
        )


def downgrade() -> None:
    bind = op.get_bind()
    for column in ("face_action", "quick_replies"):
        columns = {item["name"] for item in inspect(bind).get_columns("chat_messages")}
        if column in columns:
            op.drop_column("chat_messages", column)
