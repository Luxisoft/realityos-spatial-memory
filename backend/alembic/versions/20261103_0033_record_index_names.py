"""Align face_record_enrollments index names with the ORM.

Revision 0032 created one redundant workspace index: Alembic honors
index=True in op.create_table (auto names), so the extra explicit
op.create_index duplicated it. Rename to the ORM-declared names.
"""

from alembic import op

revision = "20261103_0033"
down_revision = "20261103_0032"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_index("ix_face_record_enrollment_workspace", table_name="face_record_enrollments")
    op.drop_index("ix_face_record_enrollments_record_id", table_name="face_record_enrollments")
    op.drop_index("ix_face_record_enrollments_workspace_id", table_name="face_record_enrollments")
    op.create_index(
        "ix_face_record_enrollment_record", "face_record_enrollments", ["record_id"]
    )
    op.create_index(
        "ix_face_record_enrollment_workspace", "face_record_enrollments", ["workspace_id"]
    )


def downgrade():
    op.drop_index("ix_face_record_enrollment_workspace", table_name="face_record_enrollments")
    op.drop_index("ix_face_record_enrollment_record", table_name="face_record_enrollments")
    op.create_index(
        "ix_face_record_enrollments_record_id", "face_record_enrollments", ["record_id"]
    )
    op.create_index(
        "ix_face_record_enrollments_workspace_id", "face_record_enrollments", ["workspace_id"]
    )
    op.create_index(
        "ix_face_record_enrollment_workspace", "face_record_enrollments", ["workspace_id"]
    )
