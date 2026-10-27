"""Persist detailed SAM video trajectories without duplicating source pixels.

Revision ID: 20261027_0006
Revises: 20261027_0005
Create Date: 2026-10-27
"""

from alembic import op


revision = "20261027_0006"
down_revision = "20261027_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql":
        return
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS object_tracks (
          id UUID PRIMARY KEY,
          workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
          object_id UUID NOT NULL REFERENCES tracked_objects(id) ON DELETE CASCADE,
          source_media_asset_id UUID NOT NULL REFERENCES media_assets(id) ON DELETE CASCADE,
          processing_job_id UUID REFERENCES processing_jobs(id),
          model_name VARCHAR(120) NOT NULL,
          status VARCHAR(32) NOT NULL DEFAULT 'queued',
          last_seen_at TIMESTAMPTZ,
          last_seen_pts_seconds DOUBLE PRECISION,
          metadata JSON NOT NULL DEFAULT '{}'::json,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT uq_video_track_object UNIQUE (source_media_asset_id, object_id)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_object_track_workspace_status "
        "ON object_tracks (workspace_id, status)"
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS object_track_segments (
          id UUID PRIMARY KEY,
          track_id UUID NOT NULL REFERENCES object_tracks(id) ON DELETE CASCADE,
          segment_index INTEGER NOT NULL,
          start_pts_seconds DOUBLE PRECISION NOT NULL,
          end_pts_seconds DOUBLE PRECISION NOT NULL,
          provider_file_id VARCHAR(160),
          request_state VARCHAR(32) NOT NULL DEFAULT 'queued',
          error_message TEXT,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT uq_track_segment_index UNIQUE (track_id, segment_index)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS object_track_frames (
          id UUID PRIMARY KEY,
          track_id UUID NOT NULL REFERENCES object_tracks(id) ON DELETE CASCADE,
          track_segment_id UUID REFERENCES object_track_segments(id) ON DELETE CASCADE,
          source_frame_index INTEGER NOT NULL,
          pts_seconds DOUBLE PRECISION NOT NULL,
          visible BOOLEAN NOT NULL,
          bounding_box JSON,
          mask_rle BYTEA,
          mask_width INTEGER,
          mask_height INTEGER,
          confidence DOUBLE PRECISION,
          simulated BOOLEAN NOT NULL DEFAULT false,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          CONSTRAINT uq_track_source_frame UNIQUE (track_id, source_frame_index)
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_track_frame_track_pts "
        "ON object_track_frames (track_id, pts_seconds)"
    )


def downgrade() -> None:
    pass
