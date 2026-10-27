"""Add device-originated capture and evidence-backed inventory facts.

Revision ID: 20261027_0005
Revises: 20261027_0004
Create Date: 2026-10-27
"""

from alembic import op


revision = "20261027_0005"
down_revision = "20261027_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply only additive PostgreSQL changes; historic observations remain intact."""

    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(
        """
        DO $$ BEGIN
          CREATE TYPE device_status AS ENUM ('active', 'revoked');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute(
        """
        DO $$ BEGIN
          CREATE TYPE fact_provenance AS ENUM ('visible_text', 'visual', 'temporal', 'manual', 'legacy');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
        """
    )
    op.execute("ALTER TYPE processing_operation ADD VALUE IF NOT EXISTS 'video_tracking'")
    op.execute("ALTER TYPE job_status ADD VALUE IF NOT EXISTS 'uncertain'")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS devices (
          id UUID PRIMARY KEY,
          workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
          device_identifier VARCHAR(96) NOT NULL,
          label VARCHAR(160) NOT NULL,
          credential_hash VARCHAR(128) NOT NULL,
          status device_status NOT NULL DEFAULT 'active',
          created_by_id UUID NOT NULL REFERENCES users(id),
          last_seen_at TIMESTAMPTZ,
          revoked_at TIMESTAMPTZ,
          metadata JSON NOT NULL DEFAULT '{}'::json,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT uq_device_identifier UNIQUE (device_identifier)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_device_workspace_status ON devices (workspace_id, status)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS device_assignments (
          id UUID PRIMARY KEY,
          device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
          operator_label VARCHAR(160) NOT NULL,
          external_reference VARCHAR(160),
          effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
          effective_to TIMESTAMPTZ,
          attested_by_id UUID NOT NULL REFERENCES users(id),
          notice_version VARCHAR(80) NOT NULL,
          attested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_device_assignment_active "
        "ON device_assignments (device_id, effective_to)"
    )
    op.execute("ALTER TABLE capture_sessions ALTER COLUMN created_by_id DROP NOT NULL")
    op.execute(
        "ALTER TABLE capture_sessions ADD COLUMN IF NOT EXISTS device_id UUID REFERENCES devices(id)"
    )
    op.execute(
        "ALTER TABLE capture_sessions ADD COLUMN IF NOT EXISTS device_assignment_id UUID "
        "REFERENCES device_assignments(id)"
    )
    op.execute(
        "ALTER TABLE capture_sessions ADD COLUMN IF NOT EXISTS origin VARCHAR(16) "
        "NOT NULL DEFAULT 'admin'"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_capture_sessions_device_id ON capture_sessions (device_id)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS object_facts (
          id UUID PRIMARY KEY,
          workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
          object_id UUID NOT NULL REFERENCES tracked_objects(id) ON DELETE CASCADE,
          observation_id UUID REFERENCES object_observations(id) ON DELETE CASCADE,
          fact_type VARCHAR(64) NOT NULL,
          value_text VARCHAR(500),
          normalized_value VARCHAR(500),
          numeric_value DOUBLE PRECISION,
          unit VARCHAR(40),
          confidence DOUBLE PRECISION NOT NULL,
          provenance fact_provenance NOT NULL,
          evidence_geometry JSON,
          model_name VARCHAR(120) NOT NULL,
          verification_status verification_status NOT NULL DEFAULT 'pending',
          verified_by_id UUID REFERENCES users(id),
          verified_at TIMESTAMPTZ,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_object_fact_workspace_type_status "
        "ON object_facts (workspace_id, fact_type, verification_status)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_object_fact_object_type ON object_facts (object_id, fact_type)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_object_facts_normalized_value ON object_facts (normalized_value)")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS object_activity_events (
          id UUID PRIMARY KEY,
          workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
          object_id UUID NOT NULL REFERENCES tracked_objects(id) ON DELETE CASCADE,
          observation_id UUID REFERENCES object_observations(id),
          capture_session_id UUID REFERENCES capture_sessions(id),
          device_id UUID REFERENCES devices(id),
          activity_type VARCHAR(64) NOT NULL,
          started_at TIMESTAMPTZ NOT NULL,
          ended_at TIMESTAMPTZ,
          start_pts_seconds DOUBLE PRECISION,
          end_pts_seconds DOUBLE PRECISION,
          confidence DOUBLE PRECISION NOT NULL,
          provenance fact_provenance NOT NULL,
          verification_status verification_status NOT NULL DEFAULT 'pending',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_activity_workspace_started "
        "ON object_activity_events (workspace_id, started_at)"
    )
    op.execute("ALTER TABLE audit_events ADD COLUMN IF NOT EXISTS device_id UUID REFERENCES devices(id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_events_device_id ON audit_events (device_id)")


def downgrade() -> None:
    # Historic evidence is intentionally retained; destructive rollback is not supported.
    pass
