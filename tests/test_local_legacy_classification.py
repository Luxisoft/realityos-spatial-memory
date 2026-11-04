"""Repair delivered legacy UUIDs/references without replacing local user work."""

from copy import deepcopy
from datetime import UTC, datetime

import pytest
from app.db import Base, Database
from app.local import bootstrap, sql_data
from app.local.upgrades import POLICE, SOCIAL
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, WorkspaceMember
from app.social_features.classification_service import add_term
from app.social_features.evidence_models import PublicationRevision, PublicationUpload
from app.social_features.models import (
    Publication,
    PublicationTag,
    PublicationTerm,
    UserProfile,
)
from app.workspaces.models import Record, RecordMedia
from sqlalchemy import delete, inspect, select, update
from sqlalchemy.exc import DBAPIError
from test_local_access import local_settings
from test_local_operational_classification import (
    assert_taxonomy,
    classifications,
    original_content,
    owner_term,
)

RECEIPT = "legacy-publication-classification-repair-v1"
FILENAME = "011-legacy-classification-repair.sql"


def reuse_original_media(db, posts):
    media = {}
    for post in posts:
        original = db.get(MediaAsset, post.media_id)
        actual = MediaAsset(
            **{
                attribute.key: deepcopy(getattr(original, attribute.key))
                for attribute in inspect(MediaAsset).column_attrs
                if attribute.key != "id"
            }
        )
        db.add(actual)
        db.flush()
        media[original.id] = actual.id
        for model, field in (
            (Publication, Publication.media_id),
            (RecordMedia, RecordMedia.media_id),
            (UserProfile, UserProfile.avatar_media_id),
        ):
            db.execute(
                update(model).where(field == original.id).values({field: actual.id})
            )
        db.delete(original)
        db.flush()
    return media


def seed_legacy_history(
    db, settings, monkeypatch, *, legacy_source_refs=False, alternate_media=False
):
    """Model 8f17813/6112b1d's add_term UUIDs and SHA-based media reuse, then run 008/010."""
    with monkeypatch.context() as initial:
        initial.setattr(bootstrap, "DATA_UPDATES", ())
        bootstrap.seed_evaluation(db, settings)
    terms = {}
    for previous in list(db.scalars(select(PublicationTerm))):
        key = previous.name_key
        previous.name_key = "temporary-remap:" + previous.id.hex
        db.flush()
        actual = add_term(db, previous.workspace_id, previous.kind, previous.name)
        actual.display_text = deepcopy(previous.display_text)
        assert actual.name_key == key
        terms[previous.id] = actual.id
        db.execute(
            update(Publication)
            .where(Publication.category_id == previous.id)
            .values(category_id=actual.id)
        )
        db.execute(
            update(PublicationTag)
            .where(PublicationTag.term_id == previous.id)
            .values(term_id=actual.id)
        )
        db.delete(previous)
        db.flush()
    posts = list(db.scalars(select(Publication)))
    if legacy_source_refs:
        for post in posts:
            post.source_ref = post.source_ref.split(":", 1)[1]
    media = reuse_original_media(db, posts) if alternate_media else {}
    with monkeypatch.context() as previous_release:
        previous_release.setattr(
            bootstrap,
            "DATA_UPDATES",
            tuple(item for item in bootstrap.DATA_UPDATES if item[0] != RECEIPT),
        )
        bootstrap.seed_evaluation(db, settings)
    db.expire_all()
    assert db.get(LocalEvaluationState, "shared-publication-classification-v1")
    assert db.get(LocalEvaluationState, "use-case-publication-classification-v1")
    assert db.get(LocalEvaluationState, RECEIPT) is None
    return {"terms": terms, "media": media}


@pytest.fixture(params=["sqlite", "postgresql"])
def legacy_database(request, tmp_path):
    path = tmp_path / "legacy-classification.sqlite"
    url = (
        request.getfixturevalue("postgres_url")
        if request.param == "postgresql"
        else f"sqlite:///{path}"
    )
    settings = local_settings(tmp_path, database_url=url, local_evaluation_enabled=True)
    try:
        with Database(url) as database:
            Base.metadata.create_all(database.engine)
            yield database, settings
    finally:
        path.unlink(missing_ok=True)


def install(db, settings):
    assert bootstrap.seed_evaluation(db, settings)["updates"] == {
        RECEIPT: {"publications": 0}
    }
    db.expire_all()


def active_terms(db):
    return {
        (t.workspace_id, t.kind, t.name): t
        for t in db.scalars(
            select(PublicationTerm).where(PublicationTerm.active.is_(True))
        )
    }


def assert_approved(db):
    expected = {
        POLICE: {
            "category": {
                "Active arrest warrants": 5,
                "Missing persons": 4,
                "No warrants or criminal history": 7,
                "Audiovisual material": 3,
            },
            "tag": {
                "Active arrest warrant": 5,
                "No recorded criminal history": 16,
                "Active judicial proceedings": 2,
                "No active proceedings": 14,
                "Active search order": 4,
                "No active arrest warrants": 11,
                "Observation video": 3,
            },
        },
        SOCIAL: {
            "category": {"Introductions": 3, "Social content": 3},
            "tag": {
                "Personal introduction": 3,
                "Community": 3,
                "Video": 3,
                "Everyday life": 3,
            },
        },
    }
    actual = active_terms(db)
    assert len(actual) == 17
    for workspace, kinds in expected.items():
        for kind, names in kinds.items():
            assert {
                name
                for group, term_kind, name in actual
                if (group, term_kind) == (workspace, kind)
            } == set(names)
            for name, count in names.items():
                term = actual[workspace, kind, name]
                query = select(Publication.id).where(
                    Publication.workspace_id == workspace
                )
                query = (
                    query.where(Publication.category_id == term.id)
                    if kind == "category"
                    else query.join(PublicationTag).where(
                        PublicationTag.term_id == term.id
                    )
                )
                assert len(list(db.scalars(query))) == count
                assert (
                    term.display_text["name"]["source"]
                    == term.display_text["name"]["en"]
                    == name
                )
                assert term.display_text["name"]["es"]


@pytest.mark.parametrize("old_references", [False, True])
def test_repairs_the_reported_two_tags_after_previous_receipts(
    legacy_database, monkeypatch, old_references, tmp_path
):
    database, settings = legacy_database
    with database.session() as db:
        identities = seed_legacy_history(
            db,
            settings,
            monkeypatch,
            legacy_source_refs=old_references,
            alternate_media=old_references,
        )
        names = set(
            db.scalars(
                select(PublicationTerm.name)
                .join(PublicationTag)
                .join(Publication)
                .where(Publication.workspace_id == POLICE)
            )
        )
        assert names == {"Case information", "Observation video"}
        assert db.query(Record).count() == 16
        case = db.scalar(
            select(Publication).where(Publication.caption == "Adrián Salcedo")
        )
        case.indexed_at = datetime.now(UTC)
        case.ai_caption = "Indexed source portrait"
        asset = db.get(MediaAsset, case.media_id)
        asset.extra_metadata = {
            **asset.extra_metadata,
            "gallery_index_version": "existing-index",
        }
        db.flush()
        original = original_content(db)
        previous_terms = set(db.scalars(select(PublicationTerm.id)))
        old_receipts = {
            key: db.get(LocalEvaluationState, key).manifest_hash
            for key in (
                "shared-publication-classification-v1",
                "use-case-publication-classification-v1",
            )
        }
        install(db, settings)
        assert_approved(db)
        assert original_content(db) == original
        assert previous_terms <= set(db.scalars(select(PublicationTerm.id)))
        assert set(identities["terms"].values()) <= set(
            db.scalars(select(PublicationTerm.id))
        )
        assert db.get(Publication, case.id).ai_caption == "Indexed source portrait"
        for key, digest in old_receipts.items():
            assert db.get(LocalEvaluationState, key).manifest_hash == digest
        repaired = classifications(db)
    with database.session() as db:
        assert (
            bootstrap.seed_evaluation(db, settings, tmp_path / "missing-fixtures")[
                "updates"
            ]
            == {}
        )
        assert classifications(db) == repaired


def test_current_installation_remains_unchanged(legacy_database):
    database, settings = legacy_database
    with database.session() as db:
        bootstrap.seed_evaluation(db, settings)
        assert_taxonomy(db)
        before = classifications(db)
        assert bootstrap.seed_evaluation(db, settings)["updates"] == {}
        assert classifications(db) == before


def test_partially_repaired_008_row_accepts_010_authored_term_copy(
    legacy_database, monkeypatch
):
    database, settings = legacy_database
    with database.session() as db:
        with monkeypatch.context() as initial:
            initial.setattr(bootstrap, "DATA_UPDATES", ())
            bootstrap.seed_evaluation(db, settings)
        post = db.scalar(
            select(Publication).where(Publication.caption == "Adrián Salcedo")
        )
        reuse_original_media(db, [post])
        with monkeypatch.context() as previous:
            previous.setattr(
                bootstrap,
                "DATA_UPDATES",
                tuple(item for item in bootstrap.DATA_UPDATES if item[0] != RECEIPT),
            )
            bootstrap.seed_evaluation(db, settings)
        db.expire_all()
        tags = set(
            db.scalars(
                select(PublicationTerm.name)
                .join(PublicationTag)
                .where(PublicationTag.post_id == post.id)
            )
        )
        assert tags == {"Portrait", "Active judicial proceedings"}
        proceedings = db.scalar(
            select(PublicationTerm).where(
                PublicationTerm.workspace_id == POLICE,
                PublicationTerm.name == "Active judicial proceedings",
            )
        )
        assert proceedings.display_text["name"]["es"] == "Proceso judicial activo"
        before = original_content(db)
        install(db, settings)
        assert_taxonomy(db)
        assert original_content(db) == before


def test_manual_history_content_memberships_and_deleted_rows_are_preserved(
    legacy_database, monkeypatch
):
    database, settings = legacy_database
    with database.session() as db:
        seed_legacy_history(db, settings, monkeypatch)
        cases = [
            db.scalar(
                select(Publication)
                .join(RecordMedia)
                .join(Record)
                .where(Record.external_id == f"security-person-{number:02}")
            )
            for number in range(1, 17)
        ]
        # Explicitly resaving original classification is still a human decision.
        db.add(
            PublicationRevision(
                post_id=cases[0].id,
                previous={"classification": {"category": "Person records"}},
            )
        )
        cases[1].caption = "Owner caption"
        cases[2].note_text += "\nMerged duplicate note"
        cases[3].hidden = True
        own = owner_term(db, POLICE, "tag", "Owner follow-up")
        db.add(PublicationTag(post_id=cases[4].id, term_id=own.id))
        db.execute(delete(PublicationTag).where(PublicationTag.post_id == cases[5].id))
        record = db.scalar(
            select(Record).where(Record.external_id == "security-person-07")
        )
        record.data = {**record.data, "criminal_history": "Owner updated facts"}
        asset = db.get(MediaAsset, cases[7].media_id)
        asset.sha256 = "0" * 64
        asset = db.get(MediaAsset, cases[8].media_id)
        asset.original_bytes = b"Changed bytes"
        db.get(MediaAsset, cases[9].media_id).extra_metadata = {"origin": "user-upload"}
        removed = cases[10].id
        db.execute(
            update(RecordMedia)
            .where(RecordMedia.publication_id == removed)
            .values(publication_id=None)
        )
        db.execute(delete(PublicationTag).where(PublicationTag.post_id == removed))
        db.execute(delete(Publication).where(Publication.id == removed))
        meta = list(
            db.scalars(
                select(Publication).where(
                    Publication.workspace_id == SOCIAL,
                    Publication.source_ref.like("%social-introduction:%"),
                )
            )
        )
        db.execute(
            delete(WorkspaceMember).where(
                WorkspaceMember.workspace_id == SOCIAL,
                WorkspaceMember.user_id == meta[0].owner_id,
            )
        )
        db.get(User, meta[1].owner_id).is_active = False
        meta[2].workspace_id = POLICE
        db.flush()
        before = classifications(db)
        retained = {case.id for case in cases[:10]} | {p.id for p in meta}
        install(db, settings)
        after = classifications(db)
        assert {key: after[key] for key in retained} == {
            key: before[key] for key in retained
        }
        assert db.get(Publication, removed) is None
        assert any(before[key] != after[key] for key in before.keys() - retained)


def test_owner_vocabulary_and_pending_uploads_are_not_replaced(
    legacy_database, monkeypatch
):
    database, settings = legacy_database
    with database.session() as db:
        seed_legacy_history(db, settings, monkeypatch)
        archived = owner_term(
            db, POLICE, "tag", "No recorded criminal history", active=False
        )
        community = db.scalar(
            select(PublicationTerm).where(
                PublicationTerm.workspace_id == SOCIAL,
                PublicationTerm.kind == "category",
                PublicationTerm.name == "Community",
            )
        )
        community.name = "Owner community"
        community.name_key = "owner community"
        db.flush()
        before = classifications(db)
        install(db, settings)
        assert classifications(db) == before
        assert not db.get(PublicationTerm, archived.id).active
        assert db.get(PublicationTerm, community.id).name == "Owner community"


def test_legacy_term_referenced_by_upload_is_retained(legacy_database, monkeypatch):
    database, settings = legacy_database
    with database.session() as db:
        seed_legacy_history(db, settings, monkeypatch)
        post = db.scalar(
            select(Publication).where(Publication.caption == "Adrián Salcedo")
        )
        category = post.category_id
        tag = db.scalar(
            select(PublicationTag.term_id).where(PublicationTag.post_id == post.id)
        )
        upload = PublicationUpload(
            owner_id=post.owner_id,
            workspace_id=POLICE,
            request_key="legacy-pending-upload",
            category_id=category,
            tag_ids=[str(tag)],
            original_bytes=b"pending",
            mime_type="image/png",
            status="awaiting_classification",
        )
        db.add(upload)
        db.flush()
        install(db, settings)
        assert db.get(PublicationTerm, category).active
        assert db.get(PublicationTerm, tag).active
        assert db.get(PublicationUpload, upload.id).tag_ids == [str(tag)]
        assert db.get(Publication, post.id).category_id != category


def test_failure_rolls_back_repair_without_replaying_prior_revisions(
    legacy_database, monkeypatch
):
    database, settings = legacy_database
    original = sql_data.statements

    def broken(path):
        yield from original(path)
        if path.name == FILENAME:
            yield "SELECT * FROM missing_legacy_repair_relation;"

    with database.session() as db:
        seed_legacy_history(db, settings, monkeypatch)
        before = classifications(db)
        terms = [
            (t.id, t.active, deepcopy(t.display_text))
            for t in db.scalars(select(PublicationTerm).order_by(PublicationTerm.id))
        ]
        with monkeypatch.context() as failure:
            failure.setattr(sql_data, "statements", broken)
            with pytest.raises(DBAPIError, match="missing_legacy_repair_relation"):
                bootstrap.seed_evaluation(db, settings)
        db.expire_all()
        assert classifications(db) == before
        assert [
            (t.id, t.active, t.display_text)
            for t in db.scalars(select(PublicationTerm).order_by(PublicationTerm.id))
        ] == terms
        assert db.get(LocalEvaluationState, RECEIPT) is None
        install(db, settings)
        assert_approved(db)
