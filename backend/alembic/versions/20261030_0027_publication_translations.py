"""Persist prepared English/Spanish publication information; additive."""

import sqlalchemy as sa

from alembic import op

revision = "20261030_0027"
down_revision = "20261030_0026"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "publication_translations",
        sa.Column(
            "post_id",
            sa.Uuid(),
            sa.ForeignKey("publications.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("language", sa.String(2), primary_key=True),
        sa.Column("text_hash", sa.String(64), primary_key=True),
        sa.Column("translated_text", sa.Text(), nullable=False),
        sa.Column("simulated", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("publication_translations")
