"""Guest users and device binding for Meta and guest logins."""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261029_0017"
down_revision = "20261029_0016"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    user_columns = {column["name"] for column in inspect(bind).get_columns("users")}
    if "is_guest" not in user_columns:
        op.add_column(
            "users",
            sa.Column("is_guest", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
    if "device_id" not in user_columns:
        op.add_column("users", sa.Column("device_id", sa.String(length=128)))
    indexes = {index["name"] for index in inspect(bind).get_indexes("users")}
    if "ix_users_device_id" not in indexes:
        op.create_index("ix_users_device_id", "users", ["device_id"])


def downgrade():
    bind = op.get_bind()
    indexes = {index["name"] for index in inspect(bind).get_indexes("users")}
    if "ix_users_device_id" in indexes:
        op.drop_index("ix_users_device_id", table_name="users")
    columns = {column["name"] for column in inspect(bind).get_columns("users")}
    for column in ("device_id", "is_guest"):
        if column in columns:
            op.drop_column("users", column)
