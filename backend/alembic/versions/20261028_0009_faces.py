"""Biometric face enrollments and consent records."""

from alembic import op

revision = "20261028_0009"
down_revision = "20261028_0008"
branch_labels = None
depends_on = None


def upgrade():
    from app.faces import BiometricConsent, FaceEnrollment

    for model in (BiometricConsent, FaceEnrollment):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    from app.faces import BiometricConsent, FaceEnrollment

    for model in (FaceEnrollment, BiometricConsent):
        model.__table__.drop(op.get_bind(), checkfirst=True)
