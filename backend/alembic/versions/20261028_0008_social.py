"""Facebook identity and social publications."""

from alembic import op

revision = "20261028_0008"
down_revision = "20261027_0007"
branch_labels = None
depends_on = None


def upgrade():
    from app.social import Comment, FacebookIdentity, GroupInvite, Publication, Reaction, Report

    for model in (FacebookIdentity, Publication, Reaction, Comment, Report, GroupInvite):
        model.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    from app.social import Comment, FacebookIdentity, GroupInvite, Publication, Reaction, Report

    for model in (GroupInvite, Report, Comment, Reaction, Publication, FacebookIdentity):
        model.__table__.drop(op.get_bind(), checkfirst=True)
