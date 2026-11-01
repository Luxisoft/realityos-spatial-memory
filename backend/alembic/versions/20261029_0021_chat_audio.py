"""Voice note audio attached to chat turns."""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261029_0021"
down_revision = "20261029_0020"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("chat_messages")}
    if "audio_duration_ms" not in columns:
        op.add_column(
            "chat_messages",
            sa.Column(
                "audio_duration_ms", sa.Integer(), nullable=False, server_default="0"
            ),
        )
    if "chat_audio" not in inspect(bind).get_table_names():
        op.create_table(
            "chat_audio",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column(
                "message_id",
                sa.Integer(),
                sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "user_id",
                sa.Uuid(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("audio", sa.LargeBinary(), nullable=False),
            sa.Column("mime_type", sa.String(length=32), nullable=False),
            sa.Column("duration_ms", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade():
    bind = op.get_bind()
    if "chat_audio" in inspect(bind).get_table_names():
        op.drop_table("chat_audio")
    columns = {column["name"] for column in inspect(bind).get_columns("chat_messages")}
    if "audio_duration_ms" in columns:
        op.drop_column("chat_messages", "audio_duration_ms")
