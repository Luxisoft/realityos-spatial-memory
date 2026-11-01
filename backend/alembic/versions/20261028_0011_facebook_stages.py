"""Split facebook enrollments into photo and video stages."""

from sqlalchemy.orm import Session

from alembic import op

revision = "20261028_0011"
down_revision = "20261028_0010"
branch_labels = None
depends_on = None


def upgrade():
    from app.faces import FaceEnrollment
    from app.models import MediaAsset, MediaKind

    session = Session(bind=op.get_bind())
    rows = (
        session.query(FaceEnrollment, MediaAsset.kind)
        .join(MediaAsset, MediaAsset.id == FaceEnrollment.media_asset_id)
        .filter(FaceEnrollment.source == "facebook")
        .all()
    )
    for enrollment, kind in rows:
        enrollment.source = "facebook-video" if kind == MediaKind.FRAME else "facebook-photo"
    session.commit()


def downgrade():
    from app.faces import FaceEnrollment

    session = Session(bind=op.get_bind())
    for enrollment in session.query(FaceEnrollment).filter(
        FaceEnrollment.source.in_(["facebook-photo", "facebook-video"])
    ):
        enrollment.source = "facebook"
    session.commit()
