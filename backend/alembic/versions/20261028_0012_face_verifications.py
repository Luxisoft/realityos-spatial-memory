"""Internal identity-verification attempts."""

from alembic import op

revision = "20261028_0012"
down_revision = "20261028_0011"
branch_labels = None
depends_on = None


def upgrade():
    from app.faces import FaceVerification

    FaceVerification.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    from app.faces import FaceVerification

    FaceVerification.__table__.drop(op.get_bind(), checkfirst=True)
