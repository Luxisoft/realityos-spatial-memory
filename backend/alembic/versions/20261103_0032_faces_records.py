"""Link workspace person records to the isolated face-search arm.

Adds explicit biometric authorization columns to workspace_records and a new
face_record_enrollments table owned by backend/app/faces.py. No automatic
enrollment: integration batches may authorize, explicit worker action enrolls.
"""

import sqlalchemy as sa

from alembic import op

revision = "20261103_0032"
down_revision = "20261102_0031"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "workspace_records",
        sa.Column("biometric_authorized", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("workspace_records", sa.Column("biometric_basis", sa.String(200)))
    op.add_column("workspace_records", sa.Column("biometric_authorized_by", sa.Uuid()))
    op.add_column(
        "workspace_records", sa.Column("biometric_authorized_at", sa.DateTime(timezone=True))
    )
    op.create_foreign_key(
        "fk_record_biometric_by",
        "workspace_records",
        "users",
        ["biometric_authorized_by"],
        ["id"],
    )
    op.create_table(
        "face_record_enrollments",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "record_id", sa.Uuid(), sa.ForeignKey("workspace_records.id"), nullable=False, index=True
        ),
        sa.Column(
            "workspace_id", sa.Uuid(), sa.ForeignKey("workspaces.id"), nullable=False, index=True
        ),
        sa.Column(
            "media_asset_id", sa.Uuid(), sa.ForeignKey("media_assets.id"), nullable=False
        ),
        sa.Column("record_media_id", sa.Uuid(), sa.ForeignKey("workspace_record_media.id")),
        sa.Column("face_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_model", sa.String(80), nullable=False),
        sa.Column("embedding", sa.LargeBinary(), nullable=False),
        sa.Column("bounding_box", sa.JSON(), nullable=False),
        sa.Column("quality", sa.Float(), nullable=False, server_default="0"),
        sa.Column("source", sa.String(32), nullable=False, server_default="record-portrait"),
        sa.Column(
            "authorized_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")
        ),
        sa.UniqueConstraint("record_id", "media_asset_id", "face_index", name="uq_face_record_enrollment"),
    )
    op.create_index("ix_face_record_enrollment_workspace", "face_record_enrollments", ["workspace_id"])


def downgrade():
    op.drop_index("ix_face_record_enrollment_workspace", table_name="face_record_enrollments")
    op.drop_table("face_record_enrollments")
    op.drop_constraint("fk_record_biometric_by", "workspace_records", type_="foreignkey")
    op.drop_column("workspace_records", "biometric_authorized_at")
    op.drop_column("workspace_records", "biometric_authorized_by")
    op.drop_column("workspace_records", "biometric_basis")
    op.drop_column("workspace_records", "biometric_authorized")
