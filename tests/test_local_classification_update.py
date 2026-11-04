"""Classification upgrades preserve owners' work and use recorded facts only."""

import uuid
from collections import Counter

import pytest
from app.db import Base, Database
from app.local import bootstrap, sql_data
from app.local.upgrades import POLICE, SOCIAL
from app.local_models import LocalEvaluationState
from app.main import create_app
from app.models import MediaAsset, User, Workspace, WorkspaceMember
from app.security import create_access_token
from app.social_features.evidence_models import PublicationUpload
from app.social_features.models import (
    Publication,
    PublicationTag,
    PublicationTerm,
    UserProfile,
)
from app.workspaces.models import Record, RecordMedia
from app.workspaces.purge import purge
from conftest import APIClient
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError
from test_local_access import local_settings

RECEIPT = "shared-publication-classification-v1"


@pytest.fixture(params=["sqlite", "postgresql"])
def earlier_classification(request, tmp_path, monkeypatch):
    revisions = {"group-videos-v1", "police-records-v2", RECEIPT}
    monkeypatch.setattr(
        bootstrap,
        "DATA_UPDATES",
        tuple(item for item in bootstrap.DATA_UPDATES if item[0] in revisions),
    )
    path = tmp_path / "classification.sqlite"
    url = (
        request.getfixturevalue("postgres_url")
        if request.param == "postgresql"
        else f"sqlite:///{path}"
    )
    settings = local_settings(tmp_path, database_url=url, local_evaluation_enabled=True)
    try:
        with Database(url) as database:
            Base.metadata.create_all(database.engine)
            with monkeypatch.context() as previous:
                previous.setattr(bootstrap, "DATA_UPDATES", bootstrap.DATA_UPDATES[:2])
                with database.session() as db:
                    bootstrap.seed_evaluation(db, settings)
            yield database, settings
    finally:
        path.unlink(missing_ok=True)


def posts(db):
    return {post.source_ref: post for post in db.scalars(select(Publication))}


def classes(db):
    return {
        post.id: (
            post.category_id,
            frozenset(
                db.scalars(
                    select(PublicationTag.term_id).where(
                        PublicationTag.post_id == post.id
                    )
                )
            ),
        )
        for post in db.scalars(select(Publication))
    }


def term(db, workspace, kind, name, *, active=True):
    row = PublicationTerm(
        workspace_id=workspace,
        kind=kind,
        name=name,
        name_key=name.casefold(),
        active=active,
        display_text={},
    )
    db.add(row)
    db.flush()
    return row


def install(db, settings):
    assert bootstrap.install_data_updates(db, settings) == {
        RECEIPT: {"publications": 0}
    }
    db.expire_all()


@pytest.fixture
def classified_api(earlier_classification):
    database, settings = earlier_classification
    with database.session() as db:
        install(db, settings)
    app = create_app(settings)
    try:
        yield APIClient(app)
    finally:
        app.state.database.engine.dispose()


def test_existing_installation_is_classified_without_creating_content(
    earlier_classification,
):
    database, settings = earlier_classification
    with database.session() as db:
        originals = {
            p.id: (p.media_id, p.owner_id, p.caption, p.note_text, p.published_at)
            for p in db.scalars(select(Publication))
        }
        original_media = list(db.execute(select(MediaAsset.id, MediaAsset.sha256)))
        install(db, settings)
        assert db.query(PublicationTerm).count() == 36
        assert db.query(PublicationTerm).filter_by(active=True).count() == 26
        assert Counter(db.scalars(select(PublicationTerm.name).join(Publication))) == {
            "Active arrest warrants": 5,
            "Missing persons": 4,
            "No warrants or criminal history": 7,
            "Public space videos": 6,
            "Introductions": 3,
        }
        assert {
            p.id: (p.media_id, p.owner_id, p.caption, p.note_text, p.published_at)
            for p in db.scalars(select(Publication))
        } == originals
        assert (
            list(db.execute(select(MediaAsset.id, MediaAsset.sha256))) == original_media
        )
        assert db.query(User).count() == 6
        classified = classes(db)
        assert len(classified) == 25
        assert bootstrap.seed_evaluation(db, settings)["updates"] == {}
        assert classes(db) == classified


def test_manual_classification_content_and_deletions_survive(earlier_classification):
    database, settings = earlier_classification
    with database.session() as db:
        by_ref = posts(db)
        cases = [
            by_ref[f"security:police-case:security-person-{n:02}"] for n in range(1, 11)
        ]
        category = term(db, POLICE, "category", "Owner review")
        tag = term(db, POLICE, "tag", "Owner note")
        cases[0].category_id = category.id
        db.add(PublicationTag(post_id=cases[1].id, term_id=tag.id))
        db.execute(delete(PublicationTag).where(PublicationTag.post_id == cases[2].id))
        cases[3].hidden = True
        cases[4].caption = "Owner-edited publication"
        cases[5].note_text = "Owner-edited case note"
        custom = Publication(
            workspace_id=POLICE,
            owner_id=cases[6].owner_id,
            media_id=cases[6].media_id,
            category_id=cases[6].category_id,
            caption="An ordinary owner publication",
        )
        db.add(custom)
        db.flush()
        old_tag = db.scalar(
            select(PublicationTag.term_id).where(PublicationTag.post_id == cases[6].id)
        )
        db.add(PublicationTag(post_id=custom.id, term_id=old_tag))
        deleted = cases[9].id
        db.execute(
            update(RecordMedia)
            .where(RecordMedia.publication_id == deleted)
            .values(publication_id=None)
        )
        db.execute(delete(PublicationTag).where(PublicationTag.post_id == deleted))
        db.delete(cases[9])
        db.flush()
        preserved_ids = {p.id for p in [*cases[:6], custom]}
        before = classes(db)
        install(db, settings)
        after = classes(db)
        assert {key: after[key] for key in preserved_ids} == {
            key: before[key] for key in preserved_ids
        }
        assert db.get(Publication, deleted) is None
        assert db.get(PublicationTerm, old_tag).active
        assert db.query(Publication).count() == 25  # One deleted and one owner-created.
        changed = db.get(Publication, cases[6].id)
        changed.category_id = category.id
        changed.hidden = True
        db.flush()
        edited = classes(db)
        assert bootstrap.seed_evaluation(db, settings)["updates"] == {}
        assert classes(db) == edited
        assert changed.hidden


@pytest.mark.parametrize("change", ["removed_member", "inactive_owner"])
def test_unavailable_owners_keep_their_classification(earlier_classification, change):
    database, settings = earlier_classification
    with database.session() as db:
        owner = db.scalar(
            select(Publication.owner_id).where(Publication.workspace_id == POLICE)
        )
        identifiers = set(
            db.scalars(select(Publication.id).where(Publication.owner_id == owner))
        )
        if change == "removed_member":
            db.execute(
                delete(WorkspaceMember).where(
                    WorkspaceMember.user_id == owner,
                    WorkspaceMember.workspace_id == POLICE,
                )
            )
        else:
            db.get(User, owner).is_active = False
        db.flush()
        before = classes(db)
        install(db, settings)
        after = classes(db)
        assert {key: after[key] for key in identifiers} == {
            key: before[key] for key in identifiers
        }
        assert any(after[key] != before[key] for key in before.keys() - identifiers)
        if change == "removed_member":
            assert (
                db.scalar(
                    select(WorkspaceMember.id).where(
                        WorkspaceMember.user_id == owner,
                        WorkspaceMember.workspace_id == POLICE,
                    )
                )
                is None
            )
        else:
            assert not db.get(User, owner).is_active


def test_unknown_or_edited_case_facts_are_never_assumed_false(earlier_classification):
    database, settings = earlier_classification
    with database.session() as db:
        records = {r.external_id: r for r in db.scalars(select(Record))}
        affected = []
        for number, key, value in [
            (4, "has_active_warrant", None),
            (5, "has_active_proceedings", "delete"),
            (6, "has_active_warrant", "false"),
            (11, "is_missing", "delete"),
        ]:
            record = records[f"security-person-{number:02}"]
            data = dict(record.data)
            if value == "delete":
                del data[key]
            else:
                data[key] = value
            record.data = data
            affected.append(
                db.scalar(
                    select(RecordMedia.publication_id).where(
                        RecordMedia.record_id == record.id
                    )
                )
            )
        db.flush()
        before = classes(db)
        install(db, settings)
        after = classes(db)
        assert {key: after[key] for key in affected} == {
            key: before[key] for key in affected
        }


def test_removed_group_is_never_recreated(earlier_classification):
    database, settings = earlier_classification
    with database.session() as db:
        db.execute(
            update(UserProfile)
            .where(
                UserProfile.avatar_media_id.in_(
                    select(MediaAsset.id).where(MediaAsset.workspace_id == SOCIAL)
                )
            )
            .values(avatar_media_id=None)
        )
        purge(db, [SOCIAL], apply=True, commit=False, strict_scope=True)
        install(db, settings)
        assert db.get(Workspace, SOCIAL) is None
        assert db.query(Publication).filter_by(workspace_id=SOCIAL).count() == 0
        assert db.query(PublicationTerm).filter_by(workspace_id=SOCIAL).count() == 0
        assert db.query(Publication).filter_by(workspace_id=POLICE).count() == 19
        assert bootstrap.seed_evaluation(db, settings)["updates"] == {}
        assert db.get(Workspace, SOCIAL) is None


@pytest.mark.parametrize("kind", ["category", "tag"])
def test_renamed_original_vocabulary_is_not_replaced(earlier_classification, kind):
    database, settings = earlier_classification
    with database.session() as db:
        name = "Person records" if kind == "category" else "Case information"
        original = db.scalar(
            select(PublicationTerm).where(
                PublicationTerm.workspace_id == POLICE, PublicationTerm.name == name
            )
        )
        original.name = "Owner investigation"
        original.name_key = "owner investigation"
        db.flush()
        identifiers = {
            p.id
            for p in db.scalars(
                select(Publication).where(
                    Publication.source_ref.like("security:police-case:%")
                )
            )
        }
        before = classes(db)
        install(db, settings)
        after = classes(db)
        assert {key: after[key] for key in identifiers} == {
            key: before[key] for key in identifiers
        }
        assert original.name == "Owner investigation"
        assert original.active


def test_owner_vocabulary_and_pending_uploads_are_preserved(earlier_classification):
    database, settings = earlier_classification
    with database.session() as db:
        category = term(db, POLICE, "category", "Active arrest warrants")
        archived = term(db, SOCIAL, "tag", "Park", active=False)
        intro = posts(db)["meta-social:social-introduction:elena-marquez"]
        old_category = intro.category_id
        old_tag = db.scalar(
            select(PublicationTag.term_id).where(PublicationTag.post_id == intro.id)
        )
        upload = PublicationUpload(
            owner_id=intro.owner_id,
            request_key="pending-owner-upload",
            workspace_id=SOCIAL,
            category_id=old_category,
            tag_ids=[str(old_tag)],
            original_bytes=b"pending",
            mime_type="image/png",
            status="awaiting_classification",
        )
        db.add(upload)
        db.flush()
        before = classes(db)
        park_posts = {
            p.id
            for p in db.scalars(
                select(Publication).where(
                    Publication.source_ref.in_(
                        ["meta-social:pexels-12557513", "meta-social:pexels-3699519"]
                    )
                )
            )
        }
        install(db, settings)
        assert db.query(Publication).filter_by(category_id=category.id).count() == 5
        assert category.display_text == {}
        assert not db.get(PublicationTerm, archived.id).active
        after = classes(db)
        assert {key: after[key] for key in park_posts} == {
            key: before[key] for key in park_posts
        }
        assert db.get(PublicationTerm, old_category).active
        assert db.get(PublicationTerm, old_tag).active
        assert db.get(PublicationUpload, upload.id).tag_ids == [str(old_tag)]


def test_sql_failure_rolls_back_classification_without_caller_rollback(
    earlier_classification, monkeypatch
):
    database, settings = earlier_classification
    original_statements = sql_data.statements

    def broken(path):
        yield from original_statements(path)
        if path.name == "008-shared-publication-classification.sql":
            yield "SELECT * FROM missing_classification_relation;"

    with database.session() as db:
        before = classes(db)
        with monkeypatch.context() as failure:
            failure.setattr(sql_data, "statements", broken)
            with pytest.raises(DBAPIError, match="missing_classification_relation"):
                bootstrap.install_data_updates(db, settings)
        assert classes(db) == before
        assert db.query(PublicationTerm).count() == 10
        assert db.get(LocalEvaluationState, RECEIPT) is None
        install(db, settings)


def test_status_and_content_filters_are_scoped_to_the_group(classified_api):
    evaluation = classified_api
    accounts = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
    expected = {
        POLICE: {
            "Active arrest warrants": 5,
            "Missing persons": 4,
            "No warrants or criminal history": 7,
            "Public space videos": 3,
            "Active judicial proceedings": 2,
            "Active search order": 4,
            "No active arrest warrants": 11,
            "No active proceedings": 14,
        },
        SOCIAL: {
            "Introductions": 3,
            "Public space videos": 3,
            "Photography": 2,
            "Projects": 1,
            "Experiences": 1,
            "Stories": 1,
            "Cycling": 1,
            "City sidewalk": 1,
            "Winter": 1,
        },
    }
    for workspace, counts in expected.items():
        account = next(row for row in accounts if row["workspace_id"] == str(workspace))
        auth = {
            "Authorization": "Bearer "
            + create_access_token(
                uuid.UUID(account["id"]), evaluation.app.state.settings
            )
        }
        with evaluation.app.state.database.session_factory() as db:
            vocabulary = list(
                db.scalars(
                    select(PublicationTerm).where(
                        PublicationTerm.workspace_id == workspace,
                        PublicationTerm.active.is_(True),
                    )
                )
            )
        options = evaluation.get(
            "/v1/gallery/filter-options",
            headers=auth,
            params={"workspace_id": str(workspace)},
        )
        assert options.status_code == 200
        for kind, field in (("category", "categories"), ("tag", "tags")):
            assert {row["id"] for row in options.json()[field]} == {
                str(value.id) for value in vocabulary if value.kind == kind
            }
        for name, count in counts.items():
            selected = next(t for t in vocabulary if t.name == name)
            query = "category_ids" if selected.kind == "category" else "tag_ids"
            response = evaluation.get(
                "/v1/gallery/page",
                headers=auth,
                params={
                    "workspace_id": str(workspace),
                    query: str(selected.id),
                    "limit": 30,
                },
            )
            assert response.status_code == 200, response.text
            assert len(response.json()["items"]) == count
            assert all(
                item["workspace_id"] == str(workspace)
                for item in response.json()["items"]
            )
            assert selected.display_text["name"]["en"] == name
            assert selected.display_text["name"]["es"]
        foreign = SOCIAL if workspace == POLICE else POLICE
        assert (
            evaluation.get(
                "/v1/gallery/page", headers=auth, params={"workspace_id": str(foreign)}
            ).status_code
            == 403
        )
