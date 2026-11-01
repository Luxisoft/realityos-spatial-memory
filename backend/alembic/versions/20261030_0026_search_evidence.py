"""Immutable gallery evidence and private upload review; additive migration."""

import sqlalchemy as sa

from alembic import op

revision = "20261030_0026"
down_revision = "20261030_0025"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "publications",
        sa.Column("evidence_version", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_table(
        "gallery_evidence",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("post_id", sa.Uuid(), sa.ForeignKey("publications.id"), nullable=False),
        sa.Column("media_id", sa.Uuid(), sa.ForeignKey("media_assets.id"), nullable=False),
        sa.Column("image_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("frame_timestamp_ms", sa.Integer(), nullable=True),
        sa.Column("detections", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_gallery_evidence_post_id", "gallery_evidence", ["post_id"])
    op.create_index("ix_gallery_evidence_media_id", "gallery_evidence", ["media_id"])
    op.create_index("ix_gallery_evidence_content_hash", "gallery_evidence", ["content_hash"])
    op.create_table(
        "publication_uploads",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("owner_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("request_key", sa.String(64), nullable=False),
        sa.Column("audience", sa.String(16), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=True),
        sa.Column("original_bytes", sa.LargeBinary(), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("caption", sa.Text(), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=False),
        sa.Column("note_source", sa.String(16), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("duplicate_id", sa.Uuid(), sa.ForeignKey("publications.id"), nullable=True),
        sa.Column("expected_media_id", sa.Uuid(), sa.ForeignKey("media_assets.id"), nullable=True),
        sa.Column("result_id", sa.Uuid(), sa.ForeignKey("publications.id"), nullable=True),
        sa.Column("analysis", sa.JSON(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("owner_id", "request_key", name="uq_upload_request"),
    )
    op.create_index("ix_publication_uploads_status", "publication_uploads", ["status"])
    op.create_index("ix_publication_uploads_owner_id", "publication_uploads", ["owner_id"])
    op.create_table(
        "publication_revisions",
        sa.Column("id", sa.Uuid(), nullable=False, primary_key=True),
        sa.Column("post_id", sa.Uuid(), sa.ForeignKey("publications.id"), nullable=False),
        sa.Column("previous", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index("ix_publication_revisions_post_id", "publication_revisions", ["post_id"])
    op.create_table(
        "publication_duplicates",
        sa.Column(
            "post_id", sa.Uuid(), sa.ForeignKey("publications.id"), nullable=False, primary_key=True
        ),
        sa.Column("canonical_id", sa.Uuid(), sa.ForeignKey("publications.id"), nullable=False),
        sa.Column("previous", sa.JSON(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
    )
    op.create_index(
        "ix_publication_duplicates_canonical_id", "publication_duplicates", ["canonical_id"]
    )


def downgrade():
    op.drop_column("publications", "evidence_version")
    op.drop_table("publication_duplicates")
    op.drop_table("publication_revisions")
    op.drop_table("publication_uploads")
    op.drop_table("gallery_evidence")
