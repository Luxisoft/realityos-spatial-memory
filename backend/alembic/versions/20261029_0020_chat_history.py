"""Per-user AI chat history."""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261029_0020"
down_revision = "20261029_0019"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if "chat_messages" not in inspect(bind).get_table_names():
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("role", sa.String(length=8), nullable=False),
            sa.Column("kind", sa.String(length=8), nullable=False, server_default="text"),
            sa.Column("text", sa.Text(), nullable=False),
            sa.Column("evidence_url", sa.String(length=1024)),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade():
    bind = op.get_bind()
    if "chat_messages" in inspect(bind).get_table_names():
        op.drop_table("chat_messages")
