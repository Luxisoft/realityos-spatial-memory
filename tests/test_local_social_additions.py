"""New private profiles are additive, atomic and preserve existing local edits."""

from datetime import UTC, datetime

import pytest
from app.db import Base, Database
from app.faces import BiometricConsent, FaceEnrollment
from app.local import bootstrap, social_bootstrap
from app.local_models import LocalAccessAccount, LocalEvaluationState
from app.models import MediaAsset, User, Workspace
from app.social_features.models import FacebookMedia, FacebookProfile, Publication
from sqlalchemy import select
from test_local_access import local_settings
from test_local_social import FixtureEngine


@pytest.fixture(params=["sqlite", "postgresql"])
def previous_social(request, tmp_path, monkeypatch):
    url = (
        request.getfixturevalue("postgres_url")
        if request.param == "postgresql"
        else f"sqlite:///{tmp_path / 'social.sqlite'}"
    )
    settings = local_settings(tmp_path, database_url=url, local_evaluation_enabled=True)
    with Database(url) as database:
        Base.metadata.create_all(database.engine)
        engine = FixtureEngine(database)
        with monkeypatch.context() as initial:
            initial.setattr(bootstrap, "DATA_UPDATES", ())
            initial.setattr(
                social_bootstrap,
                "SOCIAL_REVISIONS",
                social_bootstrap.SOCIAL_REVISIONS[:1],
            )
            with database.session() as db:
                engine.transaction = db
                bootstrap.seed_evaluation(db, settings)
                social_bootstrap.seed_local_social(db, settings, engine=engine)
        yield database, settings, engine


def test_additions_preserve_renaming_revocation_and_deletions(previous_social):
    database, settings, engine = previous_social
    with database.session() as db:
        original_id = db.scalar(select(FacebookProfile.user_id))
        db.get(User, original_id).display_name = "Edited profile"
        db.get(BiometricConsent, original_id).revoked_at = datetime.now(UTC)
        db.get(Workspace, social_bootstrap.WORKSPACE).name = "Renamed group"
        removed = db.scalar(select(FaceEnrollment))
        removed_id = removed.id
        db.delete(removed)
    with database.session() as db:
        engine.transaction = db
        original_publications = db.query(Publication).count()
        result = social_bootstrap.seed_local_social(db, settings, engine=engine)
        assert result["initialized"] and result["profiles"] == 13
        assert db.get(User, original_id).display_name == "Edited profile"
        assert db.get(BiometricConsent, original_id).revoked_at is not None
        assert db.get(FaceEnrollment, removed_id) is None
        assert db.query(FaceEnrollment).count() == 38
        assert db.query(FacebookMedia).count() == 39
        assert db.query(LocalAccessAccount).count() == 6
        assert db.query(Publication).count() == original_publications
        new_users = list(
            db.scalars(
                select(User)
                .join(FacebookProfile)
                .where(
                    FacebookProfile.sync_diagnostics["revision"].as_string()
                    == "meta-social-profiles-v2"
                )
            )
        )
        assert {user.display_name for user in new_users} == {
            "Gabriel Herrera",
            "Adrián Navarro",
            "Paula Méndez",
        }
        second_id = new_users[0].id
        db.get(BiometricConsent, second_id).revoked_at = datetime.now(UTC)
    with database.session() as db:
        result = social_bootstrap.seed_local_social(db, settings, engine=engine)
        assert not result["initialized"]
        assert db.get(BiometricConsent, second_id).revoked_at is not None


def test_failed_addition_rolls_back_without_losing_installed_profiles(previous_social):
    database, settings, engine = previous_social
    with database.session() as db:
        original_media = db.query(MediaAsset).count()
        engine.detect_faces = lambda data: []
        with pytest.raises(ValueError, match="Three usable"):
            social_bootstrap.seed_local_social(db, settings, engine=engine)
        # The caller may commit unrelated work after the rejected revision.
        assert db.query(User).count() == 16
        assert db.query(FaceEnrollment).count() == 30
        assert db.query(MediaAsset).count() == original_media
        assert db.get(LocalEvaluationState, "meta-social-profiles-v1") is not None
        assert db.get(LocalEvaluationState, "meta-social-profiles-v2") is None


def test_removed_social_group_is_not_recreated(previous_social):
    database, settings, engine = previous_social
    with database.session() as db:
        group = db.get(Workspace, social_bootstrap.WORKSPACE)
        # Model a missing group lookup without deleting protected dependencies.
        original_get = db.get
        db.get = lambda model, key, **kwargs: (
            None
            if model is Workspace and key == group.id
            else original_get(model, key, **kwargs)
        )
        assert social_bootstrap.seed_local_social(db, settings, engine=engine) == {
            "initialized": False,
            "reason": "workspace-removed",
        }
        assert db.query(FacebookProfile).count() == 10
