"""Synced Facebook profiles and photo/video inventory."""

from alembic import op

revision = "20261028_0010"
down_revision = "20261028_0009"
branch_labels = None
depends_on = None


def upgrade():
    from app.social import FacebookMedia, FacebookProfile

    for model in (FacebookProfile, FacebookMedia):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    from app.social import FacebookMedia, FacebookProfile

    for model in (FacebookMedia, FacebookProfile):
        model.__table__.drop(op.get_bind(), checkfirst=True)
