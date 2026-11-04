"""Store manually authored Spanish and English copy alongside existing content."""

import sqlalchemy as sa

from alembic import op

revision = "20261104_0040"
down_revision = "20261104_0039"
branch_labels = None
depends_on = None

TABLES = ("workspaces", "publication_terms", "publications", "user_profiles", "workspace_records")


def upgrade():
    for table in TABLES:
        # Empty local databases are created from current ORM metadata and then
        # stamped at the pinned baseline before applying subsequent revisions.
        if "display_text" in {
            column["name"] for column in sa.inspect(op.get_bind()).get_columns(table)
        }:
            continue
        op.add_column(
            table, sa.Column("display_text", sa.JSON(), nullable=False, server_default="{}")
        )


def downgrade():
    for table in reversed(TABLES):
        op.drop_column(table, "display_text")
