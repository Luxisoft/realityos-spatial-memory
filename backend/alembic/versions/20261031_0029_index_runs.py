"""Stage resumable gallery analysis before atomic activation.

Revision ID: 20261031_0029
Revises: 20261031_0028
"""

import sqlalchemy as sa

from alembic import op

revision = "20261031_0029"
down_revision = "20261031_0028"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "gallery_index_runs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "post_id",
            sa.Uuid(),
            sa.ForeignKey("publications.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("media_id", sa.Uuid(), sa.ForeignKey("media_assets.id"), nullable=False),
        sa.Column("source_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("stage", sa.String(32), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("lease", sa.String(36), nullable=False),
        sa.Column("lease_until", sa.DateTime(timezone=True)),
        sa.Column("progress", sa.JSON(), nullable=False),
        sa.Column("error", sa.JSON()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_gallery_index_runs_post_id", "gallery_index_runs", ["post_id"])
    op.add_column(
        "gallery_evidence",
        sa.Column("index_run_id", sa.Uuid(), sa.ForeignKey("gallery_index_runs.id")),
    )
    op.create_index("ix_gallery_evidence_index_run_id", "gallery_evidence", ["index_run_id"])
    op.add_column("publications", sa.Column("active_index_run_id", sa.Uuid()))
    op.create_foreign_key(
        "fk_publication_active_index_run",
        "publications",
        "gallery_index_runs",
        ["active_index_run_id"],
        ["id"],
    )


def downgrade():
    op.drop_constraint("fk_publication_active_index_run", "publications", type_="foreignkey")
    op.drop_column("publications", "active_index_run_id")
    op.drop_index("ix_gallery_evidence_index_run_id", table_name="gallery_evidence")
    op.drop_column("gallery_evidence", "index_run_id")
    op.drop_table("gallery_index_runs")
