"""Local fixture integrity, isolation, real sessions and restart behavior."""

import io
import uuid
from pathlib import Path

import pytest
from app.db import Base
from app.local_catalog import catalog
from app.local_seed import seed_evaluation
from app.main import create_app
from app.models import MediaAsset, User, Workspace, WorkspaceMember
from app.social_features.models import Publication, UserProfile
from app.workspaces.models import Record, RecordMedia
from conftest import APIClient
from PIL import Image
from sqlalchemy import delete, select
from test_local_access import local_settings


def test_meta_social_starts_empty_with_original_accounts(evaluation):
    group = catalog()["groups"][1]
    assert group["name"] == "Meta Social Media"
    workspace_id = uuid.UUID(group["id"])
    with evaluation.app.state.database.session_factory() as db:
        assert db.query(Publication).filter_by(workspace_id=workspace_id).count() == 0
        assert db.query(Record).filter_by(workspace_id=workspace_id).count() == 0
        assert db.query(MediaAsset).filter_by(workspace_id=workspace_id).count() == 3
        assert {
            db.get(User, uuid.UUID(u["id"])).display_name for u in group["users"]
        } == {"Elena Marquez", "Mateo Rios", "Sarah Chen"}


@pytest.mark.parametrize("cross_workspace", [False, True])
def test_replacement_preserves_profiles_and_is_one_time(
    evaluation, monkeypatch, cross_workspace
):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    from replace_local_hospital import OLD_ID, replace_local_hospital

    group = catalog()["groups"][1]
    destination = uuid.UUID(group["id"])
    settings = evaluation.app.state.settings
    with evaluation.app.state.database.session_factory() as db:
        new = db.get(Workspace, destination)
        db.add(
            Workspace(
                id=OLD_ID,
                name="California Valley Medical Center",
                created_by_id=new.created_by_id,
            )
        )
        db.flush()
        profiles = {}
        for member in db.scalars(
            select(WorkspaceMember).where(WorkspaceMember.workspace_id == destination)
        ):
            member.workspace_id = OLD_ID
            profile = db.get(UserProfile, member.user_id)
            profiles[member.user_id] = (
                profile.headline,
                profile.biography,
                profile.avatar_media_id,
            )
            db.get(MediaAsset, profile.avatar_media_id).workspace_id = OLD_ID
        db.flush()
        db.execute(delete(Workspace).where(Workspace.id == destination))
        post = db.scalar(select(Publication))
        post.workspace_id = OLD_ID
        db.get(MediaAsset, post.media_id).workspace_id = OLD_ID
        removed_post, removed_media = post.id, post.media_id
        record = db.scalar(select(Record))
        record.workspace_id = OLD_ID
        removed_record = record.id
        if cross_workspace:
            other = db.scalar(select(Publication).where(Publication.id != post.id))
            other.shared_from_id = post.id
        db.commit()
        if cross_workspace:
            with pytest.raises(RuntimeError, match="another workspace"):
                replace_local_hospital(db, settings)
            db.rollback()
            assert db.get(Workspace, OLD_ID) is not None
            assert db.get(Publication, removed_post) is not None
            return
        report = replace_local_hospital(db, settings)
        assert report["rows"]["publications"] == 1
        db.commit()
        db.expire_all()
        assert db.get(Workspace, OLD_ID) is None
        assert db.get(Publication, removed_post) is None
        assert db.get(MediaAsset, removed_media) is None
        assert db.get(Record, removed_record) is None
        assert db.query(Publication).count() == 15
        for user_id, snapshot in profiles.items():
            profile = db.get(UserProfile, user_id)
            assert (
                profile.headline,
                profile.biography,
                profile.avatar_media_id,
            ) == snapshot
            assert (
                db.get(MediaAsset, profile.avatar_media_id).workspace_id == destination
            )
        db.get(Workspace, destination).name = "Edited locally"
        db.commit()
        assert replace_local_hospital(db, settings) is None
        assert db.get(Workspace, destination).name == "Edited locally"
        with pytest.raises(ValueError):
            replace_local_hospital(
                db, settings.model_copy(update={"environment": "production"})
            )


@pytest.fixture
def evaluation(tmp_path):
    app = create_app(
        local_settings(tmp_path, local_evaluation_enabled=True, elevenlabs_api_key=None)
    )
    Base.metadata.create_all(app.state.database.engine)
    with app.state.database.session_factory() as db:
        result = seed_evaluation(db, app.state.settings)
        assert result == {
            "initialized": True,
            "groups": 3,
            "users": 9,
            "records": 28,
            "attachments": 20,
            "publications": 16,
        }
        db.commit()
    return APIClient(app)


def test_seed_restart_preserves_edits_and_deletions(evaluation):
    with evaluation.app.state.database.session_factory() as db:
        user = db.scalar(select(User))
        user.display_name = "Edited locally"
        post = db.scalar(select(Publication))
        post.hidden = True
        record = db.scalar(select(Record))
        record.title = "Edited record"
        # Delete a profile, which has no inbound references: restart must not resurrect it.
        db.execute(delete(UserProfile).where(UserProfile.user_id == user.id))
        db.commit()
        assert not seed_evaluation(db, evaluation.app.state.settings)["initialized"]
        assert db.get(User, user.id).display_name == "Edited locally"
        assert db.get(UserProfile, user.id) is None
        assert db.get(Publication, post.id).hidden
        assert db.get(Record, record.id).title == "Edited record"
        assert db.query(Workspace).count() == 3
        assert db.query(RecordMedia).count() == 20


def test_selector_issues_session_and_cannot_cross_groups(evaluation):
    listing = evaluation.get("/v1/auth/local-accounts")
    assert listing.status_code == 200 and listing.headers["cache-control"] == "no-store"
    accounts = listing.json()["accounts"]
    assert len(accounts) == 9
    response = evaluation.post(
        "/v1/auth/local-select", json={"user_id": accounts[0]["id"]}
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["capture_profile"]["workspace_id"] == accounts[0]["workspace_id"]
    headers = {"Authorization": "Bearer " + payload["access_token"]}
    assert evaluation.get("/v1/me/profile", headers=headers).status_code == 200
    assert (
        evaluation.post(
            "/v1/auth/refresh", json={"refresh_token": payload["refresh_token"]}
        ).status_code
        == 200
    )
    other = accounts[-1]["workspace_id"]
    assert evaluation.get(
        f"/v1/groups/{other}/publication-catalog", headers=headers
    ).status_code in {403, 404}
    assert (
        evaluation.post(
            "/v1/auth/local-select", json={"user_id": str(uuid.uuid4())}
        ).status_code
        == 404
    )
    with evaluation.app.state.database.session_factory() as db:
        assert db.query(Workspace).count() == 3
        db.execute(
            delete(WorkspaceMember).where(
                WorkspaceMember.user_id == uuid.UUID(accounts[0]["id"])
            )
        )
        db.commit()
    assert (
        evaluation.post(
            "/v1/auth/local-select", json={"user_id": accounts[0]["id"]}
        ).status_code
        == 403
    )


def test_local_external_routes_are_unavailable(evaluation):
    paths = evaluation.get("/v1/openapi.json").json()["paths"]
    for path in paths:
        assert not any(
            part in path
            for part in (
                "storage-connections",
                "/connections",
                "/facebook",
                "/integrations/",
            )
        )
    assert "/v1/agent/tts" not in paths
    assert (
        "/v1/faces/consent" in paths
    )  # Local entry never removes the protected feature.


def test_selector_disabled_on_production_and_legacy_local(tmp_path):
    for settings in (
        local_settings(tmp_path),
        local_settings(
            tmp_path, environment="production", local_evaluation_enabled=True
        ),
    ):
        client = APIClient(create_app(settings))
        assert client.get("/v1/auth/local-accounts").status_code == 404
        user_id = catalog()["groups"][0]["users"][0]["id"]
        assert (
            client.get(f"/v1/auth/local-accounts/{user_id}/avatar").status_code == 404
        )
        assert (
            client.post(
                "/v1/auth/local-select",
                json={"user_id": catalog()["groups"][0]["users"][0]["id"]},
            ).status_code
            == 404
        )


def test_selector_serves_only_profile_thumbnails(evaluation):
    accounts = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
    for account in accounts:
        response = evaluation.get(account["picture_url"])
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert response.headers["cache-control"] == "no-store"
        with Image.open(io.BytesIO(response.content)) as image:
            assert max(image.size) <= 192
    assert (
        evaluation.get(f"/v1/auth/local-accounts/{uuid.uuid4()}/avatar").status_code
        == 404
    )


@pytest.mark.parametrize(
    "unavailable", ["missing", "corrupt", "inactive", "membership", "other_group"]
)
def test_selector_avatar_rechecks_availability_and_scope(evaluation, unavailable):
    accounts = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
    account = accounts[0]
    user_id = uuid.UUID(account["id"])
    with evaluation.app.state.database.session_factory() as db:
        profile = db.get(UserProfile, user_id)
        if unavailable == "missing":
            profile.avatar_media_id = None
        elif unavailable == "corrupt":
            db.get(MediaAsset, profile.avatar_media_id).original_bytes = b"not an image"
        elif unavailable == "inactive":
            db.get(User, user_id).is_active = False
        elif unavailable == "membership":
            db.execute(
                delete(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
            )
        else:
            other = db.get(UserProfile, uuid.UUID(accounts[-1]["id"]))
            profile.avatar_media_id = other.avatar_media_id
        db.commit()
    assert evaluation.get(account["picture_url"]).status_code == 404
    if unavailable == "missing":
        listing = evaluation.get("/v1/auth/local-accounts").json()["accounts"]
        assert (
            next(row for row in listing if row["id"] == account["id"])["picture_url"]
            is None
        )


def test_queue_dispatch_resumes_without_repeating_successful_jobs(
    evaluation, monkeypatch
):
    from app.local_seed import enqueue_initial_media

    calls = []

    def dispatch(post_id):
        if len(calls) == 3:
            raise RuntimeError("queue temporarily unavailable")
        calls.append(post_id)

    monkeypatch.setattr("app.tasks.index_gallery_media.delay", dispatch)
    with evaluation.app.state.database.session_factory() as db:
        with pytest.raises(RuntimeError, match="queue temporarily"):
            enqueue_initial_media(db)
        assert len(calls) == 3
        monkeypatch.setattr("app.tasks.index_gallery_media.delay", calls.append)
        assert enqueue_initial_media(db) == {"dispatched": 16}
        assert len(set(calls)) == len(calls) == 16
        assert enqueue_initial_media(db) == {"dispatched": 16}
        assert len(calls) == 16
