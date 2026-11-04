"""Retirement removes local access without following shared or protected data."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from app.accounts.models import PasswordAccount
from app.db import Base, Database
from app.faces import BiometricConsent, FaceEnrollment, FaceRecordEnrollment
from app.local import bootstrap, retirement
from app.local.bootstrap import seed_evaluation
from app.local.retirement import RECEIPT, USERS, WORKSPACE, retire_memory
from app.local_models import LocalAccessAccount, LocalEvaluationState
from app.models import (
    CaptureSession,
    Device,
    DeviceStatus,
    MediaAsset,
    MediaKind,
    RefreshToken,
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from app.social_features.models import Publication, UserProfile
from app.workspaces.models import Connection, Record, RecordMedia, RecordRevision
from sqlalchemy import delete, select
from test_local_access import local_settings


@pytest.fixture(params=["sqlite", "postgresql"])
def previous_installation(request, tmp_path, monkeypatch):
    url = (
        request.getfixturevalue("postgres_url")
        if request.param == "postgresql"
        else f"sqlite:///{tmp_path / 'retirement.sqlite'}"
    )
    settings = local_settings(tmp_path, database_url=url, local_evaluation_enabled=True)
    monkeypatch.setattr(bootstrap, "DATA_UPDATES", ())
    with Database(url) as database:
        Base.metadata.create_all(database.engine)
        with database.session() as db:
            seed_evaluation(db, settings)
            db.execute(
                delete(LocalEvaluationState).where(LocalEvaluationState.name == RECEIPT)
            )
            owner = min(USERS)
            for index, identifier in enumerate(sorted(USERS)):
                db.add(
                    User(
                        id=identifier,
                        email=f"retired-{index}@local.test",
                        display_name=f"Historical account {index}",
                        password_hash="disabled-test-secret",
                    )
                )
            db.flush()
            db.add(
                Workspace(
                    id=WORKSPACE,
                    name="Retired local scenario",
                    created_by_id=owner,
                    join_pin="123456789",
                )
            )
            db.flush()
            for index, identifier in enumerate(sorted(USERS)):
                db.add_all(
                    [
                        WorkspaceMember(
                            workspace_id=WORKSPACE, user_id=identifier, role=Role.ADMIN
                        ),
                        LocalAccessAccount(
                            workspace_id=WORKSPACE,
                            user_id=identifier,
                            position=6 + index,
                        ),
                        PasswordAccount(
                            user_id=identifier, username=f"retired-{index}"
                        ),
                        RefreshToken(
                            user_id=identifier,
                            jti=f"retired-{index}",
                            expires_at=datetime.now(UTC) + timedelta(days=1),
                        ),
                    ]
                )
            device = Device(
                workspace_id=WORKSPACE,
                device_identifier="retired-device",
                label="Old local capture device",
                credential_hash="0" * 64,
                created_by_id=owner,
            )
            connection = Connection(
                workspace_id=WORKSPACE,
                created_by_id=owner,
                name="Retired source",
                token_hash="0" * 64,
            )
            db.add_all([device, connection])
            db.flush()
            capture = CaptureSession(
                workspace_id=WORKSPACE, created_by_id=owner, device_id=device.id
            )
            db.add(capture)
            db.flush()
            content = b"isolated historical media bytes"
            media = MediaAsset(
                workspace_id=WORKSPACE,
                capture_session_id=capture.id,
                kind=MediaKind.IMAGE,
                mime_type="image/png",
                original_bytes=content,
                sha256=hashlib.sha256(content).hexdigest(),
                byte_size=len(content),
            )
            record = Record(
                workspace_id=WORKSPACE,
                connection_id=connection.id,
                external_id="retired-case",
                kind="person",
                title="Historical local record",
                data={"owner_edit": True},
                occurred_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
            db.add_all([media, record])
            db.flush()
            post = Publication(
                workspace_id=WORKSPACE,
                owner_id=owner,
                media_id=media.id,
                caption="Historical local publication",
                source="local-evaluation",
            )
            db.add(post)
            db.flush()
            db.add_all(
                [
                    RecordMedia(
                        record_id=record.id,
                        external_id="portrait",
                        media_id=media.id,
                        publication_id=post.id,
                    ),
                    RecordRevision(
                        record_id=record.id, version=1, snapshot={"title": record.title}
                    ),
                    UserProfile(
                        user_id=owner,
                        avatar_media_id=media.id,
                        cv_bytes=b"private document",
                    ),
                ]
            )
            identifiers = {
                "owner": owner,
                "media": media.id,
                "post": post.id,
                "record": record.id,
                "device": device.id,
                "capture": capture.id,
                "connection": connection.id,
            }
        yield database, settings, identifiers


def test_retirement_removes_exclusive_data_and_keeps_other_group_edits(
    previous_installation,
):
    database, settings, ids = previous_installation
    with database.session() as db:
        other = db.scalar(
            select(Publication).where(Publication.workspace_id != WORKSPACE)
        )
        other.caption = "Owner-maintained text"
        other_id = other.id
    with database.session() as db:
        result = seed_evaluation(db, settings)
        assert result["initialized"] is False
        assert (
            result["groups"],
            result["users"],
            result["records"],
            result["publications"],
        ) == (2, 6, 10, 13)
        assert db.get(Workspace, WORKSPACE) is None
        for user in USERS:
            assert db.get(User, user) is None
            assert db.get(PasswordAccount, user) is None
            assert db.get(UserProfile, user) is None
        for model, key in (
            (MediaAsset, "media"),
            (Publication, "post"),
            (Record, "record"),
            (Device, "device"),
            (CaptureSession, "capture"),
            (Connection, "connection"),
        ):
            assert db.get(model, ids[key]) is None
        assert db.query(RefreshToken).count() == 0
        assert db.query(LocalAccessAccount).count() == 6
        assert db.query(MediaAsset).count() == 16
        assert db.query(RecordMedia).count() == 10
        assert db.query(RecordRevision).count() == 10
        assert db.get(Publication, other_id).caption == "Owner-maintained text"
        assert db.get(LocalEvaluationState, RECEIPT).counts["removed"]["users"] == 3
    with database.session() as db:
        assert (
            seed_evaluation(db, settings, root=Path("/fixtures-must-not-be-read"))[
                "initialized"
            ]
            is False
        )
        assert db.get(Workspace, WORKSPACE) is None
        assert db.get(Publication, other_id).caption == "Owner-maintained text"


def test_shared_publication_and_another_account_avatar_keep_original_bytes(
    previous_installation,
):
    database, settings, ids = previous_installation
    with database.session() as db:
        other = db.scalar(select(Workspace).where(Workspace.id != WORKSPACE))
        profile = db.get(UserProfile, other.created_by_id)
        other_avatar = profile.avatar_media_id
        retired_profile = next(user for user in USERS if user != ids["owner"])
        db.add(UserProfile(user_id=retired_profile, avatar_media_id=other_avatar))
        profile.avatar_media_id = ids["media"]
        copy = Publication(
            owner_id=other.created_by_id,
            workspace_id=other.id,
            media_id=ids["media"],
            shared_from_id=ids["post"],
            caption="Retained group copy",
        )
        db.add(copy)
        db.flush()
        copy_id, profile_id = copy.id, profile.user_id
    with database.session() as db:
        report = retire_memory(db, settings)
        assert report["retained_dependencies"]["media_assets"] == 1
        assert db.get(Publication, copy_id).caption == "Retained group copy"
        assert db.get(Publication, copy_id).shared_from_id == ids["post"]
        assert db.get(Publication, ids["post"]).hidden is True
        assert db.get(UserProfile, profile_id).avatar_media_id == ids["media"]
        assert (
            db.get(MediaAsset, ids["media"]).original_bytes
            == b"isolated historical media bytes"
        )
        assert db.get(MediaAsset, ids["media"]).workspace_id == WORKSPACE
        assert db.get(Device, ids["device"]).status == DeviceStatus.REVOKED
        assert db.get(User, ids["owner"]).is_active is False
        assert db.query(WorkspaceMember).filter_by(workspace_id=WORKSPACE).count() == 0
        assert db.query(LocalAccessAccount).count() == 6
        assert db.query(RefreshToken).count() == 0
        assert db.get(UserProfile, ids["owner"]) is None
        assert db.get(UserProfile, retired_profile) is None
        assert db.get(MediaAsset, other_avatar) is not None


def test_protected_rows_and_their_required_dependencies_remain_unchanged(
    previous_installation,
):
    database, settings, ids = previous_installation
    with database.session() as db:
        enrollment = FaceEnrollment(
            user_id=ids["owner"],
            media_asset_id=ids["media"],
            embedding_model="test-only",
            embedding=b"unchanged-vector",
        )
        attachment = db.scalar(
            select(RecordMedia).where(RecordMedia.record_id == ids["record"])
        )
        record_enrollment = FaceRecordEnrollment(
            record_id=ids["record"],
            workspace_id=WORKSPACE,
            media_asset_id=ids["media"],
            record_media_id=attachment.id,
            embedding_model="test-only",
            embedding=b"unchanged-record-vector",
        )
        db.add_all(
            [
                enrollment,
                record_enrollment,
                BiometricConsent(user_id=ids["owner"], notice_version="historical"),
            ]
        )
        db.flush()
        enrollment_id = enrollment.id
        record_enrollment_id = record_enrollment.id
    with database.session() as db:
        retire_memory(db, settings)
        enrollment = db.get(FaceEnrollment, enrollment_id)
        assert enrollment.embedding == b"unchanged-vector"
        assert enrollment.media_asset_id == ids["media"]
        assert db.get(BiometricConsent, ids["owner"]).notice_version == "historical"
        assert db.get(BiometricConsent, ids["owner"]).revoked_at is None
        assert (
            db.get(FaceRecordEnrollment, record_enrollment_id).embedding
            == b"unchanged-record-vector"
        )
        assert db.get(Record, ids["record"]).data == {"owner_edit": True}
        assert db.get(Connection, ids["connection"]).active is False
        assert db.get(Workspace, WORKSPACE).join_pin is None
        assert (
            db.get(MediaAsset, ids["media"]).original_bytes
            == b"isolated historical media bytes"
        )
        assert db.get(User, ids["owner"]).is_active is False
        assert db.query(WorkspaceMember).filter_by(workspace_id=WORKSPACE).count() == 0
        assert db.get(LocalAccessAccount, ids["owner"]) is None


def test_retirement_rolls_back_access_changes_and_deletion_on_failure(
    previous_installation, monkeypatch
):
    database, settings, ids = previous_installation
    original = retirement._delete_selected

    def fail_after_deletion(*args):
        original(*args)
        raise RuntimeError("injected retirement failure")

    with database.session() as db:
        with monkeypatch.context() as failing:
            failing.setattr(retirement, "_delete_selected", fail_after_deletion)
            with pytest.raises(RuntimeError, match="injected retirement failure"):
                retire_memory(db, settings)
        db.expire_all()
        assert db.get(LocalEvaluationState, RECEIPT) is None
        assert db.get(User, ids["owner"]).is_active is True
        assert db.get(Publication, ids["post"]).hidden is False
        assert db.get(Device, ids["device"]).status == DeviceStatus.ACTIVE
        assert db.query(LocalAccessAccount).count() == 9
        assert db.query(RefreshToken).count() == 3
        assert (
            db.get(MediaAsset, ids["media"]).original_bytes
            == b"isolated historical media bytes"
        )
        retire_memory(db, settings)
        assert db.get(Workspace, WORKSPACE) is None


def test_retirement_rejects_server_and_unversioned_databases(tmp_path):
    settings = local_settings(tmp_path, local_evaluation_enabled=True)
    with Database(settings.database_url) as database:
        Base.metadata.create_all(database.engine)
        with database.session() as db:
            with pytest.raises(ValueError, match="local evaluation"):
                retire_memory(
                    db, settings.model_copy(update={"environment": "production"})
                )
            with pytest.raises(ValueError, match="Initialize the local dataset"):
                retire_memory(db, settings)
            assert db.get(LocalEvaluationState, RECEIPT) is None
