"""Delegable group invite permission for workspace members."""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261029_0019"
down_revision = "20261029_0018"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("workspace_members")}
    if "can_invite" not in columns:
        op.add_column(
            "workspace_members",
            sa.Column("can_invite", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("workspace_members")}
    if "can_invite" in columns:
        op.drop_column("workspace_members", "can_invite")
