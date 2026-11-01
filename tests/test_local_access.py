"""Local password entry cannot affect production or cross workspace boundaries."""

import pytest
from app.config import Settings
from app.db import Base
from app.local_runtime import create_local_account
from app.main import create_app
from app.models import (
    CaptureSession,
    Device,
    MediaAsset,
    User,
    Workspace,
    WorkspaceMember,
)
from app.security import hash_password
from conftest import APIClient
from sqlalchemy import select


def local_settings(tmp_path, **changes):
    values = {
        "_env_file": None,
        "environment": "local",
        "local_login_enabled": True,
        "database_url": f"sqlite:///{tmp_path / 'local.db'}",
        "jwt_secret": "local-test-secret-with-more-than-24-characters",
        "meta_mode": "live",
        "face_engine": "insightface",
        "model_api_key": "local-unit-test-key",
        "tts_service_url": "http://seamless-tts:8091/synthesize",
        "tts_service_token": "local-speech-test-token-long-enough",
        "enqueue_processing": False,
    }
    return Settings(**(values | changes))


@pytest.fixture
def local_client(tmp_path):
    app = create_app(local_settings(tmp_path))
    Base.metadata.create_all(app.state.database.engine)
    with app.state.database.session_factory() as db:
        create_local_account(
            db,
            app.state.settings,
            "owner@local.test",
            "LocalPassword123!",
            "Local owner",
        )
        db.commit()
    yield APIClient(app)
    Base.metadata.drop_all(app.state.database.engine)


def test_local_login_issues_real_credentials_without_biometrics(
    local_client, monkeypatch
):
    def forbidden(*args, **kwargs):
        raise AssertionError("Password entry must not run a biometric operation")

    monkeypatch.setattr("app.faces.build_face_engine", forbidden)
    monkeypatch.setattr("app.faces.delete_selfie_enrollments", forbidden)
    monkeypatch.setattr(
        "app.social_features.gallery.delete_selfie_enrollments", forbidden
    )
    r = local_client.post(
        "/v1/auth/local-login",
        json={"email": "owner@local.test", "password": "LocalPassword123!"},
    )
    assert r.status_code == 200
    assert r.headers["cache-control"] == "no-store"
    data = r.json()
    assert data["local_access"] is True and data["access_token"]
    profile = data["capture_profile"]
    headers = {"Authorization": "Bearer " + data["access_token"]}
    assert local_client.get("/v1/me/profile", headers=headers).status_code == 200
    assert local_client.get("/v1/auth/local-session", headers=headers).json() == {
        "local_access": True
    }
    assert local_client.get("/v1/auth/local-session").status_code == 401
    assert (
        local_client.get("/v1/chat/history", headers=headers).json()["messages"] == []
    )
    assert (
        local_client.post(
            "/v1/auth/refresh", json={"refresh_token": data["refresh_token"]}
        ).status_code
        == 200
    )
    device_headers = {
        "X-RealityOS-Device-ID": profile["device_id"],
        "X-RealityOS-Device-Key": profile["device_key"],
    }
    result = local_client.post("/v1/device/sessions", headers=device_headers, json={})
    assert result.status_code == 201, result.text
    with local_client.app.state.database.session_factory() as db:
        assert db.query(MediaAsset).count() == 0
        user = db.scalar(select(User).where(User.email == "owner@local.test"))
        session = db.query(CaptureSession).one()
        assert session.created_by_id == user.id
        device = db.query(Device).one()
        assert device.metadata_json == {"local_owner": str(user.id)}


@pytest.mark.parametrize(
    "environment,enabled",
    [("production", True), ("development", True), ("local", False)],
)
def test_local_route_is_absent_elsewhere(tmp_path, environment, enabled):
    app = create_app(
        local_settings(tmp_path, environment=environment, local_login_enabled=enabled)
    )
    client = APIClient(app)
    assert (
        client.post(
            "/v1/auth/local-login",
            json={"email": "owner@local.test", "password": "LocalPassword123!"},
        ).status_code
        == 404
    )
    assert "/v1/auth/local-login" not in client.get("/v1/openapi.json").json()["paths"]


def test_wrong_or_inactive_local_account_is_rejected(local_client):
    assert (
        local_client.post(
            "/v1/auth/local-login",
            json={"email": "owner@local.test", "password": "wrong-password"},
        ).status_code
        == 401
    )
    with local_client.app.state.database.session_factory() as db:
        user = db.scalar(select(User).where(User.email == "owner@local.test"))
        user.is_active = False
        db.commit()
    assert (
        local_client.post(
            "/v1/auth/local-login",
            json={"email": "owner@local.test", "password": "LocalPassword123!"},
        ).status_code
        == 401
    )


def test_local_account_restart_preserves_password_and_empty_workspace(local_client):
    with local_client.app.state.database.session_factory() as db:
        before = db.query(User).one().password_hash
        result = create_local_account(
            db,
            local_client.app.state.settings,
            "owner@local.test",
            "LocalPassword123!",
            "Changed display name",
        )
        assert result["account_created"] is False
        assert db.query(User).one().password_hash == before
        assert db.query(Workspace).count() == 1
        with pytest.raises(ValueError, match="no account was changed"):
            create_local_account(
                db,
                local_client.app.state.settings,
                "owner@local.test",
                "DifferentPassword123!",
                "Owner",
            )
        assert db.query(User).one().password_hash == before


def test_local_profile_does_not_join_another_owners_matching_workspace(local_client):
    with local_client.app.state.database.session_factory() as db:
        owner = db.query(User).one()
        other = User(
            email="other@local.test",
            display_name="Other",
            password_hash=hash_password("OtherPassword123!"),
        )
        db.add(other)
        db.flush()
        rogue = Workspace(name=f"home:{owner.id}", created_by_id=other.id)
        db.add(rogue)
        db.flush()
        db.add(WorkspaceMember(workspace_id=rogue.id, user_id=other.id, role="admin"))
        rogue_id = str(rogue.id)
        db.commit()
    result = local_client.post(
        "/v1/auth/local-login",
        json={"email": "owner@local.test", "password": "LocalPassword123!"},
    )
    assert result.status_code == 409
    with local_client.app.state.database.session_factory() as db:
        assert db.query(Device).count() == 0
    tokens = local_client.post(
        "/v1/auth/login",
        json={"email": "owner@local.test", "password": "LocalPassword123!"},
    ).json()
    headers = {"Authorization": "Bearer " + tokens["access_token"]}
    assert local_client.get(
        "/v1/zones?workspace_id=" + rogue_id, headers=headers
    ).status_code in {403, 404}


@pytest.mark.parametrize(
    "changes",
    [
        {"meta_mode": "mock"},
        {"face_engine": "mock"},
        {"tts_service_token": None},
        {"model_api_key": None},
    ],
)
def test_local_runtime_cannot_silently_use_demo_engines(tmp_path, changes):
    with pytest.raises((ValueError, RuntimeError)):
        create_app(local_settings(tmp_path, **changes))


def test_local_provisioning_is_denied_for_production(local_client):
    s = local_client.app.state.settings.model_copy(update={"environment": "production"})
    with local_client.app.state.database.session_factory() as db:
        with pytest.raises(ValueError):
            create_local_account(
                db, s, "new@local.test", "DifferentPassword123!", "New"
            )
        assert db.query(User).count() == 1


def test_runtime_precision_defaults_and_cpu_fallback(monkeypatch):
    from app.providers.seamless_service import speech_precision

    monkeypatch.delenv("TTS_DTYPE", raising=False)
    assert speech_precision() == "bfloat16"
    assert speech_precision("auto", "flags avx2") == "float32"
    assert speech_precision("auto", "flags avx512_bf16") == "bfloat16"
    assert speech_precision("auto", "flags amx_bf16") == "bfloat16"
    with pytest.raises(ValueError):
        speech_precision("mock")
