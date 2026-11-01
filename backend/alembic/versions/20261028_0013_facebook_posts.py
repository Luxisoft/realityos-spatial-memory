"""Facebook posts inventory and profile picture import flag."""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261028_0013"
down_revision = "20261028_0012"
branch_labels = None
depends_on = None


def upgrade():
    from app.social import FacebookPost

    FacebookPost.__table__.create(op.get_bind(), checkfirst=True)
    bind = op.get_bind()
    columns = [column["name"] for column in inspect(bind).get_columns("facebook_profiles")]
    if "picture_imported" not in columns:
        op.add_column(
            "facebook_profiles",
            sa.Column("picture_imported", sa.Boolean(), nullable=False, server_default=sa.false()),
        )


def downgrade():
    from app.social import FacebookPost

    FacebookPost.__table__.drop(op.get_bind(), checkfirst=True)
    bind = op.get_bind()
    columns = [column["name"] for column in inspect(bind).get_columns("facebook_profiles")]
    if "picture_imported" in columns:
        op.drop_column("facebook_profiles", "picture_imported")
