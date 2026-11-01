"""Unique 9-digit join PIN per work group."""

import secrets

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261029_0018"
down_revision = "20261029_0017"
branch_labels = None
depends_on = None


def _random_pin(taken: set[str]) -> str:
    for _ in range(200):
        pin = "".join(secrets.choice("0123456789") for _ in range(9))
        if pin not in taken:
            taken.add(pin)
            return pin
    raise RuntimeError("Could not allocate unique group PINs.")


def upgrade():
    bind = op.get_bind()
    workspace_columns = {column["name"] for column in inspect(bind).get_columns("workspaces")}
    if "join_pin" not in workspace_columns:
        op.add_column("workspaces", sa.Column("join_pin", sa.String(length=9)))
    rows = bind.execute(sa.text("SELECT id, join_pin FROM workspaces")).fetchall()
    taken = {row[1] for row in rows if row[1]}
    for workspace_id, pin in rows:
        if not pin:
            bind.execute(
                sa.text("UPDATE workspaces SET join_pin = :pin WHERE id = :id"),
                {"pin": _random_pin(taken), "id": str(workspace_id)},
            )
    indexes = {index["name"] for index in inspect(bind).get_indexes("workspaces")}
    if "ix_workspaces_join_pin" not in indexes:
        op.create_index("ix_workspaces_join_pin", "workspaces", ["join_pin"], unique=True)


def downgrade():
    bind = op.get_bind()
    indexes = {index["name"] for index in inspect(bind).get_indexes("workspaces")}
    if "ix_workspaces_join_pin" in indexes:
        op.drop_index("ix_workspaces_join_pin", table_name="workspaces")
    columns = {column["name"] for column in inspect(bind).get_columns("workspaces")}
    if "join_pin" in columns:
        op.drop_column("workspaces", "join_pin")
