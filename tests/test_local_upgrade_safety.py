"""Local installation preserves existing edits and rolls back invalid additions."""

import pytest
from app.db import Base, Database
from app.local.bootstrap import seed_evaluation
from app.local.social_bootstrap import RECEIPT, seed_local_social
from app.local.upgrades import POLICE, SOCIAL, upgrade_local_data
from app.local_models import LocalAccessAccount, LocalEvaluationState
from app.models import MediaAsset, User
from app.social_features.models import FacebookMedia, Publication, PublicationTerm
from app.workspaces.models import Record, RecordMedia
from sqlalchemy import delete, select
from test_local_access import local_settings
from test_local_social import FixtureEngine


@pytest.fixture
def installed_local(postgres_url, tmp_path, monkeypatch):
    from app.local import bootstrap

    settings = local_settings(
        tmp_path, database_url=postgres_url, local_evaluation_enabled=True
    )
    with Database(postgres_url) as database:
        Base.metadata.create_all(database.engine)
        with monkeypatch.context() as configuration:
            configuration.setattr(bootstrap, "DATA_UPDATES", ())
            with database.session() as db:
                seed_evaluation(db, settings)
        yield database, settings


@pytest.mark.parametrize("kind", ["category", "tag"])
def test_publication_upgrade_preserves_renamed_vocabulary(installed_local, kind):
    database, settings = installed_local
    with database.session() as db:
        police_count = db.query(Publication).filter_by(workspace_id=POLICE).count()
        term = db.scalar(
            select(PublicationTerm).where(
                PublicationTerm.workspace_id == SOCIAL, PublicationTerm.kind == kind
            )
        )
        identifier = term.id
        term.name = "Edited by the group owner"
        term.name_key = term.name.casefold()
        db.delete(db.get(LocalEvaluationState, "local-group-publications-v1"))
        # Simulate the release before the three introductions were installed.
        db.execute(delete(Publication).where(Publication.workspace_id == SOCIAL))
    with database.session() as db:
        result = upgrade_local_data(db, settings)
        assert result["local-group-publications-v1"] == {"publications": 3}
        term = db.get(PublicationTerm, identifier)
        assert term.name == "Edited by the group owner"
        assert term.name_key == "edited by the group owner"
        assert (
            db.query(Publication).filter_by(workspace_id=POLICE).count() == police_count
        )
    with database.session() as db:
        assert upgrade_local_data(db, settings) == {}


def test_selector_restart_does_not_restore_deleted_eligibility(installed_local):
    database, settings = installed_local
    with database.session() as db:
        account = db.scalar(select(LocalAccessAccount))
        identifier = account.user_id
        db.delete(account)
    with database.session() as db:
        assert seed_evaluation(db, settings)["initialized"] is False
        assert db.get(LocalAccessAccount, identifier) is None
        assert db.get(User, identifier) is not None


def test_duplicate_references_in_one_profile_rollback_without_caller_rollback(
    installed_local, monkeypatch
):
    from app.local import social_bootstrap

    database, settings = installed_local
    original_apply = social_bootstrap.apply_seed

    def duplicate_one_reference(db, *args, **kwargs):
        original_apply(db, *args, **kwargs)
        owner = db.scalar(select(FacebookMedia.user_id))
        assets = list(
            db.scalars(
                select(MediaAsset)
                .join(FacebookMedia, FacebookMedia.imported_media_id == MediaAsset.id)
                .where(FacebookMedia.user_id == owner)
            )
        )
        assets[1].sha256 = assets[0].sha256
        assets[1].original_bytes = assets[0].original_bytes
        db.flush()

    monkeypatch.setattr(social_bootstrap, "apply_seed", duplicate_one_reference)
    with database.session() as db:
        media_count = db.query(MediaAsset).count()
        engine = FixtureEngine(database)
        engine.transaction = db
        with pytest.raises(ValueError, match="distinct private references"):
            seed_local_social(db, settings, engine=engine)
        # The caller can keep using its transaction: the failed addition rolls back.
        assert db.query(User).count() == 6
        assert db.query(MediaAsset).count() == media_count
        assert db.query(FacebookMedia).count() == 0
        assert db.get(LocalEvaluationState, RECEIPT) is None


def test_police_replacement_creates_publications_after_record_media(installed_local):
    database, settings = installed_local
    with database.session() as db:
        original_posts = {
            post.id: post.media_id
            for post in db.scalars(
                select(Publication).where(Publication.workspace_id == POLICE)
            )
        }
        db.delete(db.get(LocalEvaluationState, "police-people-v1"))
        # Exercise the intermediate release where publication receipts already
        # exist: replacement must recreate links after their targets, even then.
    with database.session() as db:
        assert "police-people-v1" in upgrade_local_data(db, settings)
        restored = {
            post.id: post.media_id
            for post in db.scalars(
                select(Publication).where(Publication.workspace_id == POLICE)
            )
        }
        assert restored == original_posts
        records = list(
            db.scalars(
                select(RecordMedia).join(Record).where(Record.workspace_id == POLICE)
            )
        )
        assert len(records) == 10
        for attachment in records:
            assert restored[attachment.publication_id] == attachment.media_id
    with database.session() as db:
        assert upgrade_local_data(db, settings) == {}
