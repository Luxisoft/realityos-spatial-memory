"""Drop face enrollments that cannot be attributed to one person.

Revision ID: 20261101_0030
Revises: 20261031_0029
"""

from alembic import op

revision = "20261101_0030"
down_revision = "20261031_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Identity cannot be attributed in a group photo: every companion face was
    # stored under the importing user and later matched as them. Keep only the
    # enrollments from single-face media. The pre-migration table snapshot in
    # .runtime/ is the reversal path for these rows.
    op.execute(
        """
        DELETE FROM face_enrollments
        WHERE media_asset_id IN (
            SELECT media_asset_id FROM face_enrollments
            GROUP BY media_asset_id HAVING COUNT(*) > 1
        )
        """
    )


def downgrade() -> None:
    # Removed rows cannot be reconstructed by SQL; restore them from the
    # pre-migration snapshot if this revision must be reversed.
    pass
