"""Authored public translations install after profiles and preserve local changes."""

from copy import deepcopy
from pathlib import Path

import pytest
from app.db import Base, Database
from app.faces import BiometricConsent, FaceEnrollment
from app.local import bootstrap, social_bootstrap, sql_data
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, WorkspaceMember
from app.social_features.models import FacebookProfile, Publication, UserProfile
from sqlalchemy import delete, select
from test_local_access import local_settings
from test_local_social import FixtureEngine

RECEIPT, FILENAME = social_bootstrap.PUBLIC_DISPLAY_REVISION


@pytest.fixture(params=["sqlite", "postgresql"])
def public_profiles_database(request, tmp_path, monkeypatch):
    path = tmp_path / "profile-display.sqlite"
    url = (
        request.getfixturevalue("postgres_url")
        if request.param == "postgresql"
        else f"sqlite:///{path}"
    )
    settings = local_settings(tmp_path, database_url=url, local_evaluation_enabled=True)
    monkeypatch.setattr(bootstrap, "DATA_UPDATES", ())
    try:
        with Database(url) as database:
            Base.metadata.create_all(database.engine)
            with database.session() as db:
                bootstrap.seed_evaluation(db, settings)
                assert db.get(LocalEvaluationState, RECEIPT) is None
            yield database, settings, FixtureEngine(database)
    finally:
        path.unlink(missing_ok=True)


def profiles(db):
    return list(
        db.scalars(
            select(UserProfile)
            .join(FacebookProfile, FacebookProfile.user_id == UserProfile.user_id)
            .order_by(UserProfile.user_id)
        )
    )


def original_data(db):
    return {
        "media": list(
            db.execute(
                select(MediaAsset.id, MediaAsset.sha256, MediaAsset.byte_size).order_by(
                    MediaAsset.id
                )
            )
        ),
        "enrollments": list(
            db.execute(
                select(
                    FaceEnrollment.id,
                    FaceEnrollment.user_id,
                    FaceEnrollment.media_asset_id,
                    FaceEnrollment.embedding,
                ).order_by(FaceEnrollment.id)
            )
        ),
        "consent": list(
            db.execute(
                select(
                    BiometricConsent.user_id,
                    BiometricConsent.notice_version,
                    BiometricConsent.consented_at,
                    BiometricConsent.revoked_at,
                ).order_by(BiometricConsent.user_id)
            )
        ),
        "publications": list(
            db.execute(
                select(
                    Publication.id,
                    Publication.media_id,
                    Publication.caption,
                    Publication.note_text,
                ).order_by(Publication.id)
            )
        ),
        "facebook": list(
            db.execute(
                select(
                    FacebookProfile.user_id,
                    FacebookProfile.gender,
                    FacebookProfile.hometown,
                    FacebookProfile.location,
                ).order_by(FacebookProfile.user_id)
            )
        ),
    }


def test_fresh_initialization_translates_public_fields_after_all_profiles(
    public_profiles_database, monkeypatch
):
    database, settings, engine = public_profiles_database
    with database.session() as db:
        engine.transaction = db
        with monkeypatch.context() as partial:
            partial.setattr(
                social_bootstrap,
                "SOCIAL_REVISIONS",
                social_bootstrap.SOCIAL_REVISIONS[:1],
            )
            social_bootstrap.seed_local_social(db, settings, engine=engine)
        assert db.query(FacebookProfile).count() == 10
        assert db.get(LocalEvaluationState, RECEIPT) is None
        result = social_bootstrap.seed_local_social(db, settings, engine=engine)
        assert result["profiles"] == 13
        assert db.get(LocalEvaluationState, RECEIPT)
        expected_gender = {
            "Hombre": ("Male", "Masculino"),
            "Mujer": ("Female", "Femenino"),
            "No binario": ("Non-binary", "No binario"),
        }
        localized_places = []
        for profile in profiles(db):
            en, es = expected_gender[profile.gender]
            assert profile.display_text["gender"] == {
                "source": profile.gender,
                "en": en,
                "es": es,
            }
            assert profile.display_text["headline"]["source"] == profile.headline
            assert profile.display_text["biography"]["source"] == profile.biography
            if "location" in profile.display_text:
                localized_places.append(profile.display_text["location"]["en"])
                for field in ("location", "hometown"):
                    assert profile.display_text[field]["source"] == getattr(
                        profile, field
                    )
                    assert profile.display_text[field]["es"] == getattr(profile, field)
        assert sorted(localized_places) == sorted(
            [
                "São Paulo, Brazil",
                "Cusco, Peru",
                "Lima, Peru",
                "Monterrey, Mexico",
                "Valencia, Spain",
            ]
        )
        assert db.query(User).count() == 19
        assert db.query(Publication).count() == 13
        assert db.query(FaceEnrollment).count() == 39


def test_upgrade_preserves_edits_deletions_memberships_and_protected_data(
    public_profiles_database, monkeypatch
):
    database, settings, engine = public_profiles_database
    with database.session() as db:
        engine.transaction = db
        with monkeypatch.context() as previous:
            previous.setattr(
                social_bootstrap, "_install_public_display", lambda *args: None
            )
            social_bootstrap.seed_local_social(db, settings, engine=engine)
        rows = profiles(db)
        rows[0].gender = "Owner-maintained gender"
        rows[1].display_text = {
            **rows[1].display_text,
            "biography": {
                **rows[1].display_text["biography"],
                "es": "Biografía revisada por su autor",
            },
        }
        db.execute(
            delete(WorkspaceMember).where(WorkspaceMember.user_id == rows[2].user_id)
        )
        db.get(User, rows[3].user_id).is_active = False
        removed = rows[4].user_id
        db.delete(rows[4])
        db.get(FacebookProfile, rows[5].user_id).gender = "Updated synchronized value"
        rows[6].headline = "Owner-maintained headline"
        rows[7].display_text = {
            **rows[7].display_text,
            "headline": {
                **rows[7].display_text["headline"],
                "fr": "Texte du propriétaire",
            },
        }
        # JSON formatting/key order is not an edit to its meaning.
        rows[8].display_text = dict(reversed(list(rows[8].display_text.items())))
        db.flush()
        preserved = {
            row.user_id: deepcopy(row.display_text)
            for row in rows[:8]
            if row.user_id != removed
        }
        unchanged = original_data(db)
        updated = rows[8].user_id
    with database.session() as db:
        result = social_bootstrap.seed_local_social(db, settings, engine=engine)
        assert not result["initialized"]
        assert db.get(LocalEvaluationState, RECEIPT)
        assert original_data(db) == unchanged
        assert db.get(UserProfile, removed) is None
        for identifier, display in preserved.items():
            assert db.get(UserProfile, identifier).display_text == display
        assert "gender" in db.get(UserProfile, updated).display_text
        assert (
            db.scalar(
                select(WorkspaceMember.id).where(
                    WorkspaceMember.user_id == rows[2].user_id
                )
            )
            is None
        )
        assert not db.get(User, rows[3].user_id).is_active
        after = db.get(UserProfile, updated)
        after.display_text = {
            **after.display_text,
            "gender": {
                "source": after.gender,
                "es": "Texto propio",
                "en": "Owner wording",
            },
        }
        deleted_after = profiles(db)[-1].user_id
        db.delete(db.get(UserProfile, deleted_after))
    with database.session() as db:
        social_bootstrap.seed_local_social(
            db, settings, root=Path("/fixtures-must-not-be-read"), engine=engine
        )
        assert db.get(UserProfile, removed) is None
        assert db.get(UserProfile, deleted_after) is None
        assert (
            db.get(UserProfile, updated).display_text["gender"]["en"] == "Owner wording"
        )


def test_failed_public_copy_rolls_back_pending_profile_revisions(
    public_profiles_database, monkeypatch
):
    database, settings, engine = public_profiles_database
    commands = sql_data.statements

    def broken(path):
        yield from commands(path)
        if path.name == FILENAME:
            yield "SELECT * FROM missing_profile_copy_relation;"

    with database.session() as db:
        engine.transaction = db
        with monkeypatch.context() as failure:
            failure.setattr(sql_data, "statements", broken)
            with pytest.raises(Exception, match="missing_profile_copy_relation"):
                social_bootstrap.seed_local_social(db, settings, engine=engine)
        assert db.query(User).count() == 6
        assert db.query(FacebookProfile).count() == 0
        assert db.query(FaceEnrollment).count() == 0
        assert db.query(BiometricConsent).count() == 0
        for name in (*social_bootstrap.PUBLIC_DISPLAY_REQUIRES, RECEIPT):
            assert db.get(LocalEvaluationState, name) is None
        social_bootstrap.seed_local_social(db, settings, engine=engine)
        assert len(profiles(db)) == 13
        assert all("gender" in row.display_text for row in profiles(db))
