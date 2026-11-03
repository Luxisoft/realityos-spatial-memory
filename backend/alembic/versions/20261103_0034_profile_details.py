"""Store personal details for email accounts separately from Facebook imports."""

import sqlalchemy as sa

from alembic import op

revision = "20261103_0034"
down_revision = "20261103_0033"
branch_labels = None
depends_on = None


def upgrade():
    # Historical 0014 creates this table from ORM metadata on a fresh database.
    existing = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("user_profiles")}
    for column in (
        sa.Column("birthday", sa.Date(), nullable=True),
        sa.Column("gender", sa.String(32), nullable=True),
        sa.Column("hometown", sa.String(160), nullable=True),
        sa.Column("location", sa.String(160), nullable=True),
    ):
        if column.name not in existing:
            op.add_column("user_profiles", column)


def downgrade():
    for name in ("location", "hometown", "gender", "birthday"):
        op.drop_column("user_profiles", name)
