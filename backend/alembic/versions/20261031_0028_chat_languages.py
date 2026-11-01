"""Account preference and durable bilingual assistant messages.

Revision ID: 20261031_0028
Revises: 20261030_0027
"""

import sqlalchemy as sa

from alembic import op

revision = "20261031_0028"
down_revision = "20261030_0027"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("preferred_language", sa.String(2), nullable=True))
    op.add_column("chat_messages", sa.Column("response_language", sa.String(16), nullable=True))
    op.add_column("chat_messages", sa.Column("template_data", sa.JSON(), nullable=True))
    op.create_table(
        "chat_message_translations",
        sa.Column(
            "message_id",
            sa.Integer(),
            sa.ForeignKey("chat_messages.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("language", sa.String(2), primary_key=True),
        sa.Column("source_hash", sa.String(64), primary_key=True),
        sa.Column("text", sa.Text(), nullable=False, server_default=""),
        sa.Column("quick_replies", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("simulated", sa.Boolean(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("chat_message_translations")
    op.drop_column("chat_messages", "template_data")
    op.drop_column("chat_messages", "response_language")
    op.drop_column("users", "preferred_language")
