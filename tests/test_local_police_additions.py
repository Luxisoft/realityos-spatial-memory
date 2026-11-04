"""Additive fictional case records preserve permission scope and existing data."""

import hashlib
import uuid
from pathlib import Path

import pytest
from app.db import Base, Database
from app.local.bootstrap import install_data_updates, seed_evaluation
from app.local.upgrades import POLICE
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, Workspace, WorkspaceMember
from app.security import create_access_token
from app.social_features.models import (
    Publication,
    PublicationTag,
    PublicationTerm,
    UserProfile,
)
from app.workspaces.models import Record, RecordMedia, RecordRevision
from app.workspaces.purge import purge
from sqlalchemy import delete, select, text, update
from test_local_access import local_settings

RECEIPT = "police-records-v2"
EXTERNAL_IDS = [f"security-person-{number}" for number in range(11, 17)]
FIRST_OWNER = uuid.UUID("6b70a3aa-0e7b-5234-8245-a923d31bd2ec")
CATEGORY = uuid.UUID("820e166a-7d73-44f6-9e63-5b03e225f6c4")
TAG = uuid.UUID("ea0709e7-73f2-4d40-aa3b-c18bbc5dc26f")


def new_records(db):
    return list(
        db.scalars(
            select(Record)
            .where(Record.external_id.in_(EXTERNAL_IDS))
            .order_by(Record.external_id)
        )
    )


@pytest.fixture
def earlier_installation(request, tmp_path, monkeypatch):
    from app.local import bootstrap

    dialect = getattr(request, "param", "postgresql")
    url = (
        request.getfixturevalue("postgres_url")
        if dialect == "postgresql"
        else f"sqlite:///{tmp_path / 'previous.sqlite'}"
    )
    settings = local_settings(tmp_path, database_url=url, local_evaluation_enabled=True)
    with Database(url) as database:
        Base.metadata.create_all(database.engine)
        with monkeypatch.context() as baseline:
            baseline.setattr(
                bootstrap,
                "DATA_UPDATES",
                tuple(item for item in bootstrap.DATA_UPDATES if item[0] != RECEIPT),
            )
            with database.session() as db:
                seed_evaluation(db, settings)
        yield database, settings


def test_six_portraits_create_correct_scoped_records_and_publications(evaluation):
    settings = evaluation.app.state.settings
    accounts = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
    assert len(accounts) == 6
    member = next(row for row in accounts if row["workspace_id"] == str(POLICE))
    outsider = next(row for row in accounts if row["workspace_id"] != str(POLICE))

    def auth(account):
        return {
            "Authorization": "Bearer "
            + create_access_token(uuid.UUID(account["id"]), settings)
        }

    with evaluation.app.state.database.session_factory() as db:
        assert db.query(Publication).count() == 25
        assert db.query(MediaAsset).count() == 28
        assert db.query(Record).count() == 16
        assert db.query(RecordMedia).count() == 16
        assert db.query(PublicationTerm).count() == 10
        assert db.query(User).count() == 6
        assert db.query(WorkspaceMember).count() == 6
        assert db.query(Publication).filter_by(workspace_id=POLICE).count() == 19
        police = list(db.scalars(select(Record).where(Record.workspace_id == POLICE)))
        assert len(police) == 16
        assert sum(record.data["has_active_warrant"] for record in police) == 5
        assert sum(record.data["has_active_proceedings"] for record in police) == 2
        assert sum(record.data.get("is_missing", False) for record in police) == 4
        assert (
            sum(record.data.get("has_active_search_order", False) for record in police)
            == 4
        )
        rows = new_records(db)
        assert [row.title for row in rows] == [
            "Bruno Escobar",
            "Daniel Serrano",
            "Samuel Ortega",
            "Elena Duarte",
            "Isabel Mora",
            "Natalia Campos",
        ]
        gallery = evaluation.get(
            "/v1/gallery/page",
            params={"workspace_id": str(POLICE), "limit": 30},
            headers=auth(member),
        )
        assert gallery.status_code == 200
        publications = {row["id"]: row for row in gallery.json()["items"]}
        for number, record in zip(range(11, 17), rows, strict=True):
            assert record.data["identifier"] == f"PRP-{number:04d}"
            assert record.simulated and not record.biometric_authorized
            assert record.biometric_basis is None
            assert not record.data["has_active_proceedings"]
            assert record.data["case_number"] is None
            assert record.data["criminal_history"] == (
                "Sin condenas ni antecedentes penales registrados"
            )
            assert record.data["has_active_warrant"] == (number < 13)
            assert record.data["is_missing"] == (number >= 13)
            assert record.data["has_active_search_order"] == (number >= 13)
            assert record.display_text["data"]["source"] == record.data
            assert record.display_text["data"]["es"]["Persona desaparecida"] == (
                "Sí" if number >= 13 else "No"
            )
            revision = db.scalar(
                select(RecordRevision).where(RecordRevision.record_id == record.id)
            )
            assert revision.snapshot["data"] == record.data
            assert revision.snapshot["display_text"] == record.display_text
            attachment = db.scalar(
                select(RecordMedia).where(RecordMedia.record_id == record.id)
            )
            asset = db.get(MediaAsset, attachment.media_id)
            post = db.get(Publication, attachment.publication_id)
            assert post.media_id == attachment.media_id
            assert asset.mime_type == "image/png"
            assert asset.width == asset.height == 1254
            assert hashlib.sha256(asset.original_bytes).hexdigest() == asset.sha256
            original = (
                Path(__file__).resolve().parents[1]
                / f"simulator/media/police/portraits/person-{number}.png"
            )
            assert asset.sha256 == hashlib.sha256(original.read_bytes()).hexdigest()
            assert publications[str(post.id)]["display_text"]["note_text"]["es"]
            detail_path = f"/v1/workspaces/{POLICE}/records/{record.id}"
            detail = evaluation.get(detail_path, headers=auth(member))
            assert detail.status_code == 200
            assert (
                detail.json()["display_text"]["data"]["es"]
                == (record.display_text["data"]["es"])
            )
            media_path = f"/v1/workspaces/{POLICE}/record-media/{attachment.id}"
            assert evaluation.get(media_path, headers=auth(member)).content == (
                asset.original_bytes
            )
            assert evaluation.get(media_path, headers=auth(outsider)).status_code in {
                403,
                404,
            }
            assert evaluation.get(detail_path, headers=auth(outsider)).status_code in {
                403,
                404,
            }
        for number, missing in zip(range(13, 17), rows[2:], strict=True):
            assert missing.data["warrant_reference"] is None
            assert missing.data["search_order_reference"] == f"PR-OB-2026-{number:03d}"
            assert (
                missing.data["missing_report_reference"] == f"PR-DES-2026-{number:03d}"
            )
            assert missing.data["last_seen_at"] and missing.data["last_seen_location"]
            assert "no es una orden de captura" in missing.data["notes"]
        assert db.scalar(text("SELECT count(*) FROM face_enrollments")) == 0
        assert db.scalar(text("SELECT count(*) FROM face_record_enrollments")) == 0


@pytest.mark.parametrize(
    "earlier_installation", ["sqlite", "postgresql"], indirect=True
)
def test_additions_rollback_and_never_restore_edits_or_deletions(
    earlier_installation, tmp_path, monkeypatch
):
    from app.local import sql_data

    database, settings = earlier_installation
    with database.session() as db:
        existing_posts = {
            row.id: (row.caption, row.media_id, row.hidden)
            for row in db.scalars(select(Publication))
        }
        before_terms = db.query(PublicationTerm).count()
        original_path = sql_data.fixture_file
        invalid = tmp_path / "bad.png"
        invalid.write_bytes(b"invalid portrait")
        with monkeypatch.context() as corrupt:
            corrupt.setattr(
                sql_data,
                "fixture_file",
                lambda root, relative: (
                    invalid
                    if relative.endswith("person-16.png")
                    else original_path(root, relative)
                ),
            )
            with pytest.raises(ValueError, match="integrity"):
                install_data_updates(db, settings)
        assert new_records(db) == []
        assert db.query(Publication).count() == 19
        assert db.query(MediaAsset).count() == 22
        assert db.get(LocalEvaluationState, RECEIPT) is None
        assert install_data_updates(db, settings) == {RECEIPT: {"publications": 6}}
        assert db.query(PublicationTerm).count() == before_terms
        assert {
            row.id: (row.caption, row.media_id, row.hidden)
            for row in db.scalars(
                select(Publication).where(Publication.id.in_(existing_posts))
            )
        } == existing_posts
    with database.session() as db:
        edited, removed = new_records(db)[:2]
        edited.title = "Owner-maintained record"
        edited.data = {**edited.data, "notes": "Owner-maintained notes"}
        edited_id, removed_id = edited.id, removed.id
        attachment = db.scalar(
            select(RecordMedia).where(RecordMedia.record_id == removed.id)
        )
        media_id, publication_id = attachment.media_id, attachment.publication_id
        db.execute(delete(RecordMedia).where(RecordMedia.record_id == removed.id))
        db.execute(delete(RecordRevision).where(RecordRevision.record_id == removed.id))
        db.execute(delete(Record).where(Record.id == removed.id))
        db.execute(
            delete(PublicationTag).where(PublicationTag.post_id == publication_id)
        )
        db.execute(delete(Publication).where(Publication.id == publication_id))
        db.execute(delete(MediaAsset).where(MediaAsset.id == media_id))
    with database.session() as db:
        assert install_data_updates(db, settings, root=Path("/no-fixtures")) == {}
        assert db.get(Record, edited_id).title == "Owner-maintained record"
        assert db.get(Record, edited_id).data["notes"] == "Owner-maintained notes"
        assert db.get(Record, removed_id) is None
        assert db.get(Publication, publication_id) is None
        assert db.get(MediaAsset, media_id) is None


@pytest.mark.parametrize(
    "change",
    [
        "removed_member",
        "inactive_owner",
        "removed_group",
        "removed_category",
        "renamed_terms",
    ],
)
def test_additions_respect_current_group_membership_and_vocabulary(
    earlier_installation, change
):
    database, settings = earlier_installation
    with database.session() as db:
        category, tag = db.get(PublicationTerm, CATEGORY), db.get(PublicationTerm, TAG)
        expected = 6
        if change == "removed_member":
            db.execute(
                delete(WorkspaceMember).where(
                    WorkspaceMember.user_id == FIRST_OWNER,
                    WorkspaceMember.workspace_id == POLICE,
                )
            )
            expected = 4
        elif change == "inactive_owner":
            db.get(User, FIRST_OWNER).is_active = False
            expected = 4
        elif change == "removed_group":
            db.execute(
                update(UserProfile)
                .where(
                    UserProfile.avatar_media_id.in_(
                        select(MediaAsset.id).where(MediaAsset.workspace_id == POLICE)
                    )
                )
                .values(avatar_media_id=None)
            )
            purge(db, [POLICE], apply=True, commit=False, strict_scope=True)
            expected = 0
        elif change == "removed_category":
            db.delete(category)
            expected = 0
        else:
            category.name = category.name_key = "Edited category"
            tag.name = tag.name_key = "Edited tag"
        db.flush()
        before_terms = db.query(PublicationTerm).count()
        before_media = db.query(MediaAsset).count()
        assert install_data_updates(db, settings) == {
            RECEIPT: {"publications": expected}
        }
        assert len(new_records(db)) == expected
        assert db.query(MediaAsset).count() == before_media + expected
        assert db.query(PublicationTerm).count() == before_terms
        if change == "removed_group":
            assert db.get(Workspace, POLICE) is None
        if change == "renamed_terms":
            assert category.name == "Edited category"
            assert tag.name == "Edited tag"
        if change in {"removed_member", "inactive_owner"}:
            assert all(
                row.external_id not in {"security-person-11", "security-person-14"}
                for row in new_records(db)
            )
    with database.session() as db:
        assert install_data_updates(db, settings, root=Path("/no-fixtures")) == {}
