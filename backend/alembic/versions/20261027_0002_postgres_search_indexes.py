"""Add PostgreSQL text and trigram indexes for object retrieval.

Revision ID: 20261027_0002
Revises: 20261026_0001
Create Date: 2026-10-27
"""

from alembic import op

revision = "20261027_0002"
down_revision = "20261026_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tracked_objects_name_trgm "
        "ON tracked_objects USING gin (canonical_name gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_object_aliases_alias_trgm "
        "ON object_aliases USING gin (alias gin_trgm_ops)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_tracked_objects_name_fts "
        "ON tracked_objects USING gin (to_tsvector('simple', canonical_name))"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_object_aliases_alias_fts "
        "ON object_aliases USING gin (to_tsvector('simple', alias))"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_object_aliases_alias_fts")
    op.execute("DROP INDEX IF EXISTS ix_tracked_objects_name_fts")
    op.execute("DROP INDEX IF EXISTS ix_object_aliases_alias_trgm")
    op.execute("DROP INDEX IF EXISTS ix_tracked_objects_name_trgm")
