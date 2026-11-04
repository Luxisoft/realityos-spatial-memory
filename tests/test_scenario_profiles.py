"""SQL preparation never overwrites an account owner's private profile changes."""

from app.local.bootstrap import seed_evaluation
from app.local_models import LocalAccessAccount
from app.models import MediaAsset, User
from app.social_features.models import UserProfile
from sqlalchemy import select


def test_prepared_profiles_are_complete_and_restart_preserves_private_data(evaluation):
    with evaluation.app.state.database.session_factory() as db:
        profiles = list(
            db.scalars(
                select(UserProfile).join(
                    LocalAccessAccount,
                    LocalAccessAccount.user_id == UserProfile.user_id,
                )
            )
        )
        assert len(profiles) == 6
        for profile in profiles:
            assert profile.headline and profile.biography and profile.birthday
            assert db.get(MediaAsset, profile.avatar_media_id).original_bytes
        owner = profiles[0]
        old_avatar = owner.avatar_media_id
        old_password = db.get(User, owner.user_id).password_hash
        owner.biography = "Biography edited by owner"
        owner.cv_bytes = b"private CV"
        owner.cv_context = "Private analysis"
        owner.cv_status = "ready"
        db.commit()
        assert (
            seed_evaluation(db, evaluation.app.state.settings)["initialized"] is False
        )
        assert owner.biography == "Biography edited by owner"
        assert (
            owner.cv_bytes == b"private CV" and owner.cv_context == "Private analysis"
        )
        assert owner.avatar_media_id == old_avatar
        assert db.get(User, owner.user_id).password_hash == old_password
