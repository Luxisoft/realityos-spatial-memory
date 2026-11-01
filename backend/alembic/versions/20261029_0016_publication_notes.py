"""Mobile publication notes (voice transcription or direct text)."""

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op

revision = "20261029_0016"
down_revision = "20261028_0015"
branch_labels = None
depends_on = None


def _columns(bind, table: str) -> set[str]:
    return {column["name"] for column in inspect(bind).get_columns(table)}


def upgrade():
    bind = op.get_bind()
    publication_columns = _columns(bind, "publications")
    if "note_text" not in publication_columns:
        op.add_column(
            "publications",
            sa.Column("note_text", sa.Text(), nullable=False, server_default=""),
        )
    if "note_source" not in publication_columns:
        op.add_column(
            "publications",
            sa.Column("note_source", sa.String(length=16), nullable=False, server_default=""),
        )


def downgrade():
    bind = op.get_bind()
    for column in ("note_source", "note_text"):
        if column in _columns(bind, "publications"):
            op.drop_column("publications", column)
