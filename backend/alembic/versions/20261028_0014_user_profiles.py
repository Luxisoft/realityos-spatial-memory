"""Public user profiles, replaceable private CVs and app-visible Facebook friends."""

from alembic import op

revision = "20261028_0014"
down_revision = "20261028_0013"
branch_labels = None
depends_on = None


def upgrade():
    from app.social import FacebookFriend, UserProfile

    for model in (UserProfile, FacebookFriend):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    from app.social import FacebookFriend, UserProfile

    for model in (FacebookFriend, UserProfile):
        model.__table__.drop(op.get_bind(), checkfirst=True)
