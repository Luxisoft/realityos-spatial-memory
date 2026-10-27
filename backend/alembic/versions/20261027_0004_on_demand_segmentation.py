"""Add durable, on-demand SAM segmentation jobs.

Revision ID: 20261027_0004
Revises: 20261027_0003
Create Date: 2026-10-27
"""

from alembic import op

revision = "20261027_0004"
down_revision = "20261027_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Preserve Muse boxes and attach a job to an observation when needed.

    ``IF NOT EXISTS`` also makes this safe with the historical initial migration,
    which builds its schema from SQLAlchemy metadata for a brand-new database.
    """

    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(
        """
        DO $$ BEGIN
          CREATE TYPE processing_operation AS ENUM ('analysis', 'segmentation');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        "ALTER TABLE object_observations "
        "ADD COLUMN IF NOT EXISTS muse_bounding_box JSON"
    )
    op.execute(
        "UPDATE object_observations "
        "SET muse_bounding_box = bounding_box "
        "WHERE muse_bounding_box IS NULL AND bounding_box IS NOT NULL"
    )
    op.execute(
        "ALTER TABLE processing_jobs "
        "ADD COLUMN IF NOT EXISTS observation_id UUID "
        "REFERENCES object_observations(id) ON DELETE CASCADE"
    )
    op.execute(
        "ALTER TABLE processing_jobs "
        "ADD COLUMN IF NOT EXISTS operation processing_operation "
        "NOT NULL DEFAULT 'analysis'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_processing_jobs_observation_id "
        "ON processing_jobs (observation_id)"
    )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute("DROP INDEX IF EXISTS ix_processing_jobs_observation_id")
    op.execute("ALTER TABLE processing_jobs DROP COLUMN IF EXISTS operation")
    op.execute("ALTER TABLE processing_jobs DROP COLUMN IF EXISTS observation_id")
    op.execute("ALTER TABLE object_observations DROP COLUMN IF EXISTS muse_bounding_box")
    op.execute("DROP TYPE IF EXISTS processing_operation")
