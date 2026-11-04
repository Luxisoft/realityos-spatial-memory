"""Persist local account selector eligibility independently of fixture files."""

import sqlalchemy as sa

from alembic import op

revision = "20261104_0041"
down_revision = "20261104_0040"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "local_access_accounts",
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
        ),
        sa.Column(
            "workspace_id",
            sa.Uuid(),
            sa.ForeignKey("workspaces.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
    )
    op.create_index(
        "ix_local_access_accounts_workspace_id", "local_access_accounts", ["workspace_id"]
    )


def downgrade():
    op.drop_index("ix_local_access_accounts_workspace_id", table_name="local_access_accounts")
    op.drop_table("local_access_accounts")
