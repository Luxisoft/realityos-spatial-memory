"""The approved local taxonomy migrates intact seed rows without replacing owner work."""

from collections import Counter
from copy import deepcopy

import pytest
from app.db import Base, Database
from app.local import bootstrap, sql_data
from app.local.upgrades import POLICE, SOCIAL
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, Workspace, WorkspaceMember
from app.social_features.evidence_models import PublicationUpload
from app.social_features.models import (
    Publication,
    PublicationTag,
    PublicationTerm,
    UserProfile,
)
from app.workspaces.models import Record, RecordMedia
from app.workspaces.purge import purge
from sqlalchemy import delete, select, update
from sqlalchemy.exc import DBAPIError
from test_local_access import local_settings

RECEIPT = "use-case-publication-classification-v1"
FILENAME = "010-use-case-classification.sql"
EARLIER = tuple(item for item in bootstrap.DATA_UPDATES if item[0] != RECEIPT)


@pytest.fixture(params=["sqlite", "postgresql"])
def operational_database(request, tmp_path):
    path = tmp_path / "operational-classification.sqlite"
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


def seed_previous(db, settings, monkeypatch):
    with monkeypatch.context() as previous:
        previous.setattr(bootstrap, "DATA_UPDATES", EARLIER)
        bootstrap.seed_evaluation(db, settings)
    assert db.query(PublicationTerm).count() == 36
    assert db.query(PublicationTerm).filter_by(active=True).count() == 26
    assert db.get(LocalEvaluationState, RECEIPT) is None


def install(db, settings):
    assert bootstrap.install_data_updates(db, settings) == {
        RECEIPT: {"publications": 0}
    }
    db.expire_all()


def classifications(db):
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


def by_reference(db):
    return {post.source_ref: post for post in db.scalars(select(Publication))}


def owner_term(db, workspace, kind, name, *, active=True):
    term = PublicationTerm(
        workspace_id=workspace,
        kind=kind,
        name=name,
        name_key=name.casefold(),
        active=active,
        display_text={},
    )
    db.add(term)
    db.flush()
    return term


def original_content(db):
    return {
        "publications": list(
            db.execute(
                select(
                    Publication.id,
                    Publication.owner_id,
                    Publication.workspace_id,
                    Publication.media_id,
                    Publication.caption,
                    Publication.note_text,
                    Publication.display_text,
                    Publication.published_at,
                ).order_by(Publication.id)
            )
        ),
        "media": list(
            db.execute(
                select(MediaAsset.id, MediaAsset.sha256, MediaAsset.byte_size).order_by(
                    MediaAsset.id
                )
            )
        ),
        "records": list(
            db.execute(
                select(
                    Record.id, Record.version, Record.data, Record.display_text
                ).order_by(Record.id)
            )
        ),
        "memberships": list(
            db.execute(
                select(
                    WorkspaceMember.id,
                    WorkspaceMember.user_id,
                    WorkspaceMember.workspace_id,
                    WorkspaceMember.role,
                ).order_by(WorkspaceMember.id)
            )
        ),
    }


def assert_taxonomy(db):
    assert db.query(PublicationTerm).count() == 44
    assert db.query(PublicationTerm).filter_by(active=True).count() == 17
    assert db.query(PublicationTerm).filter_by(active=False).count() == 27
    expected = {
        POLICE: {
            "category": {
                "Órdenes de captura vigentes": 5,
                "Personas desaparecidas": 4,
                "Sin órdenes ni antecedentes": 7,
                "Material audiovisual": 3,
            },
            "tag": {
                "Orden de captura vigente": 5,
                "Sin antecedentes registrados": 16,
                "Proceso judicial activo": 2,
                "Sin procesos activos": 14,
                "Orden de búsqueda vigente": 4,
                "Sin órdenes de captura": 11,
                "Video de observación": 3,
            },
        },
        SOCIAL: {
            "category": {"Presentaciones": 3, "Contenido social": 3},
            "tag": {
                "Presentación personal": 3,
                "Comunidad": 3,
                "Video": 3,
                "Vida cotidiana": 3,
            },
        },
    }
    for workspace, kinds in expected.items():
        for kind, counts in kinds.items():
            terms = list(
                db.scalars(
                    select(PublicationTerm).where(
                        PublicationTerm.workspace_id == workspace,
                        PublicationTerm.kind == kind,
                        PublicationTerm.active.is_(True),
                    )
                )
            )
            actual = {}
            for term in terms:
                display = term.display_text["name"]
                assert display["source"] == display["en"] == term.name
                statement = select(Publication.id).where(
                    Publication.workspace_id == workspace
                )
                statement = (
                    statement.where(Publication.category_id == term.id)
                    if kind == "category"
                    else statement.join(PublicationTag).where(
                        PublicationTag.term_id == term.id
                    )
                )
                actual[display["es"]] = len(list(db.scalars(statement)))
            assert actual == counts
    videos = list(
        db.scalars(select(Publication).where(Publication.source_ref.like("%:pexels-%")))
    )
    assert len(videos) == 6
    for post in videos:
        tags = set(
            db.scalars(
                select(PublicationTerm.name)
                .join(PublicationTag)
                .where(PublicationTag.post_id == post.id)
            )
        )
        assert tags == (
            {"Observation video"}
            if post.workspace_id == POLICE
            else {"Video", "Everyday life"}
        )
    retired = {
        "Spring",
        "Winter",
        "Park",
        "Overcast day",
        "City sidewalk",
        "Cycling",
        "Walking",
        "Portrait",
        "Photography",
        "Projects",
        "Experiences",
        "Stories",
    }
    assert (
        not set(
            db.scalars(
                select(PublicationTerm.name).where(PublicationTerm.active.is_(True))
            )
        )
        & retired
    )
    assert Counter(db.scalars(select(Publication.workspace_id))) == {
        POLICE: 19,
        SOCIAL: 6,
    }
    assert db.query(MediaAsset).count() == 28
    assert db.query(Record).count() == db.query(RecordMedia).count() == 16
    assert db.query(User).count() == db.query(WorkspaceMember).count() == 6


def test_new_installation_uses_the_approved_operational_taxonomy(operational_database):
    database, settings = operational_database
    with database.session() as db:
        result = bootstrap.seed_evaluation(db, settings)
        assert result["updates"][RECEIPT] == {"publications": 0}
        assert db.get(
            LocalEvaluationState, RECEIPT
        ).manifest_hash == sql_data.seed_digest(sql_data.FIXTURES, FILENAME)
        assert_taxonomy(db)


def test_previous_installation_changes_only_classification_and_runs_once(
    operational_database, monkeypatch, tmp_path
):
    database, settings = operational_database
    with database.session() as db:
        seed_previous(db, settings, monkeypatch)
        original = original_content(db)
        install(db, settings)
        assert original_content(db) == original
        assert_taxonomy(db)
        post = by_reference(db)["meta-social:pexels-3699519"]
        custom = owner_term(db, SOCIAL, "tag", "My reviewed tag")
        db.add(PublicationTag(post_id=post.id, term_id=custom.id))
        post.hidden = True
        deleted = by_reference(db)["meta-social:pexels-33802407"].id
        db.execute(delete(PublicationTag).where(PublicationTag.post_id == deleted))
        db.execute(delete(Publication).where(Publication.id == deleted))
        db.flush()
        after = classifications(db)
    with database.session() as db:
        assert (
            bootstrap.seed_evaluation(db, settings, tmp_path / "missing-fixtures")[
                "updates"
            ]
            == {}
        )
        assert classifications(db) == after
        assert db.get(Publication, deleted) is None
        assert db.get(Publication, post.id).hidden


def test_manual_edits_hidden_rows_and_deletions_are_preserved(
    operational_database, monkeypatch
):
    database, settings = operational_database
    with database.session() as db:
        seed_previous(db, settings, monkeypatch)
        posts = by_reference(db)
        cases = [
            posts[f"security:police-case:security-person-{n:02}"] for n in range(1, 17)
        ]
        category = owner_term(db, POLICE, "category", "Owner review")
        tag = owner_term(db, POLICE, "tag", "Owner tag")
        cases[0].category_id = category.id
        db.add(PublicationTag(post_id=cases[1].id, term_id=tag.id))
        db.execute(delete(PublicationTag).where(PublicationTag.post_id == cases[2].id))
        cases[3].hidden = True
        cases[4].caption = "Owner caption"
        cases[5].note_text = "Owner case note"
        cases[6].display_text = {
            **cases[6].display_text,
            "caption": {
                "source": cases[6].caption,
                "es": "Título actualizado",
                "en": "Updated title",
            },
        }
        records = {r.external_id: r for r in db.scalars(select(Record))}
        records["security-person-08"].data = {
            **records["security-person-08"].data,
            "occupation": "Owner update",
        }
        records["security-person-09"].data = None
        cases[9].display_text = {"caption": "Owner plain text"}
        records["security-person-11"].data = {
            **records["security-person-11"].data,
            "has_active_warrant": "true",
        }
        custom = Publication(
            workspace_id=POLICE,
            owner_id=cases[11].owner_id,
            media_id=cases[11].media_id,
            category_id=cases[11].category_id,
            caption="Owner publication",
        )
        db.add(custom)
        db.flush()
        original_tag = db.scalar(
            select(PublicationTag.term_id).where(PublicationTag.post_id == cases[11].id)
        )
        db.add(PublicationTag(post_id=custom.id, term_id=original_tag))
        deleted = cases[15].id
        db.execute(
            update(RecordMedia)
            .where(RecordMedia.publication_id == deleted)
            .values(publication_id=None)
        )
        db.execute(delete(PublicationTag).where(PublicationTag.post_id == deleted))
        db.execute(delete(Publication).where(Publication.id == deleted))
        # Equivalent JSON ordering does not suppress the update.
        cases[12].display_text = dict(reversed(list(cases[12].display_text.items())))
        db.flush()
        original = original_content(db)
        before = classifications(db)
        untouched = {p.id for p in cases[:11]} | {custom.id}
        install(db, settings)
        after = classifications(db)
        assert {key: after[key] for key in untouched} == {
            key: before[key] for key in untouched
        }
        assert after[cases[12].id] != before[cases[12].id]
        assert original_content(db) == original
        assert db.get(Publication, deleted) is None
        assert db.get(PublicationTerm, original_tag).active


@pytest.mark.parametrize(
    "change", ["removed_membership", "inactive_owner", "foreign_group"]
)
def test_owner_and_workspace_scope_is_preserved(
    operational_database, monkeypatch, change
):
    database, settings = operational_database
    with database.session() as db:
        seed_previous(db, settings, monkeypatch)
        post = by_reference(db)["security:pexels-29401365"]
        owner = post.owner_id
        if change == "removed_membership":
            db.execute(
                delete(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == POLICE,
                    WorkspaceMember.user_id == owner,
                )
            )
        elif change == "inactive_owner":
            db.get(User, owner).is_active = False
        else:
            post.workspace_id = SOCIAL
        db.flush()
        protected = (
            {
                p.id
                for p in db.scalars(
                    select(Publication).where(Publication.owner_id == owner)
                )
            }
            if change != "foreign_group"
            else {post.id}
        )
        before = classifications(db)
        install(db, settings)
        after = classifications(db)
        assert {key: after[key] for key in protected} == {
            key: before[key] for key in protected
        }
        assert any(after[key] != before[key] for key in before.keys() - protected)


def test_deleted_group_is_not_recreated(operational_database, monkeypatch):
    database, settings = operational_database
    with database.session() as db:
        seed_previous(db, settings, monkeypatch)
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
        assert db.query(PublicationTerm).filter_by(workspace_id=SOCIAL).count() == 0
        assert db.query(Publication).filter_by(workspace_id=POLICE).count() == 19


def test_owner_terms_and_pending_uploads_keep_their_existing_references(
    operational_database, monkeypatch
):
    database, settings = operational_database
    with database.session() as db:
        seed_previous(db, settings, monkeypatch)
        posts = by_reference(db)
        police_video = posts["security:pexels-25757454"]
        old_category = police_video.category_id
        cycling = db.scalar(
            select(PublicationTerm).where(
                PublicationTerm.workspace_id == POLICE,
                PublicationTerm.name == "Cycling",
            )
        )
        cycling.display_text = {
            "name": {
                "source": cycling.name,
                "en": "Owner classification",
                "es": "Clasificación propia",
            }
        }
        owner_display = deepcopy(cycling.display_text)
        archived = owner_term(db, SOCIAL, "tag", "Video", active=False)
        owner_category = owner_term(db, POLICE, "category", "Audiovisual material")
        spring = db.scalar(
            select(PublicationTerm).where(
                PublicationTerm.workspace_id == POLICE, PublicationTerm.name == "Spring"
            )
        )
        upload = PublicationUpload(
            owner_id=police_video.owner_id,
            request_key="owner-pending-taxonomy",
            workspace_id=POLICE,
            category_id=old_category,
            tag_ids=[str(spring.id)],
            original_bytes=b"pending",
            mime_type="image/png",
            status="awaiting_classification",
        )
        db.add(upload)
        db.flush()
        before = classifications(db)
        install(db, settings)
        after = classifications(db)
        assert after[police_video.id] == before[police_video.id]
        assert db.get(PublicationTerm, cycling.id).display_text == owner_display
        for post in posts.values():
            if post.workspace_id == SOCIAL and ":pexels-" in post.source_ref:
                assert after[post.id] == before[post.id]
        assert not db.get(PublicationTerm, archived.id).active
        assert (
            db.query(Publication).filter_by(category_id=owner_category.id).count() == 2
        )
        assert db.get(PublicationTerm, owner_category.id).display_text == {}
        assert db.get(PublicationTerm, spring.id).active
        assert db.get(PublicationTerm, old_category).active
        assert db.get(PublicationUpload, upload.id).tag_ids == [str(spring.id)]


def test_sql_failure_rolls_back_terms_links_and_receipt(
    operational_database, monkeypatch
):
    database, settings = operational_database
    original_statements = sql_data.statements

    def broken(path):
        yield from original_statements(path)
        if path.name == FILENAME:
            yield "SELECT * FROM missing_operational_classification_relation;"

    with database.session() as db:
        seed_previous(db, settings, monkeypatch)
        before = classifications(db)
        old_terms = [
            (t.id, t.active, deepcopy(t.display_text))
            for t in db.scalars(select(PublicationTerm).order_by(PublicationTerm.id))
        ]
        with monkeypatch.context() as failure:
            failure.setattr(sql_data, "statements", broken)
            with pytest.raises(
                DBAPIError, match="missing_operational_classification_relation"
            ):
                bootstrap.install_data_updates(db, settings)
        db.expire_all()
        assert classifications(db) == before
        assert [
            (t.id, t.active, t.display_text)
            for t in db.scalars(select(PublicationTerm).order_by(PublicationTerm.id))
        ] == old_terms
        assert db.get(LocalEvaluationState, RECEIPT) is None
        install(db, settings)
        assert_taxonomy(db)
