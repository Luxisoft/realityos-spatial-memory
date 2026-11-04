"""Record initialization of a local dataset without recreating deleted resources."""

import sqlalchemy as sa

from alembic import op

revision = "20261104_0039"
down_revision = "20261103_0038"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "local_evaluation_state",
        sa.Column("name", sa.String(80), primary_key=True),
        sa.Column("manifest_hash", sa.String(64), nullable=False),
        sa.Column("counts", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )


def downgrade():
    op.drop_table("local_evaluation_state")
