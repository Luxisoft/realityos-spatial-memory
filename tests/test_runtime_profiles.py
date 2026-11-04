"""Local and server capabilities are composed independently of URL spelling."""

import json
from pathlib import Path

import pytest
from app.config import Settings, get_settings
from app.main import create_app
from app.runtime.worker import ServerTaskDispatcher, create_worker


def local_settings(**changes):
    return Settings(
        **{
            "environment": "local",
            "database_url": "sqlite://",
            "local_login_enabled": True,
            "local_evaluation_enabled": True,
            "meta_mode": "live",
            "face_engine": "insightface",
            "model_api_key": "test-key",
            **changes,
        }
    )


def test_local_contract_and_composition_do_not_change_server_routes():
    local = create_app(local_settings())
    server = create_app(Settings(database_url="sqlite://"))
    try:
        contract = Path(__file__).parent / "contracts/openapi.local.json"
        assert local.openapi() == json.loads(contract.read_text())
        assert "/v1/auth/facebook" in server.openapi()["paths"]
        assert "/v1/auth/facebook" not in local.openapi()["paths"]
        assert "/v1/auth/logout" in local.openapi()["paths"]
        retired = "/v1/workspaces/{workspace_id}/records/{person_id}/medication-check"
        for app in (local, server):
            assert retired not in app.openapi()["paths"]
            assert "MedicationCheck" not in app.openapi()["components"]["schemas"]
    finally:
        local.state.database.engine.dispose()
        server.state.database.engine.dispose()


def test_capabilities_are_independent_of_the_configured_api_prefix():
    application = create_app(local_settings(api_prefix="/custom"))
    try:
        paths = application.openapi()["paths"]
        assert "/custom/auth/register" not in paths
        assert "/custom/auth/guest" not in paths
        assert "/custom/agent/tts" not in paths
        assert "/custom/auth/local-select" in paths
        assert "/custom/faces/consent" in paths
        assert "/custom/gallery/page" in paths
    finally:
        application.state.database.engine.dispose()


def test_local_worker_never_imports_or_dispatches_server_integrations():
    settings = local_settings()
    worker = create_worker(settings)
    try:
        assert worker.conf.imports == ()
        assert worker.conf.beat_schedule == {}
        remote = ServerTaskDispatcher(
            worker, settings, "realityos.import_facebook_media"
        )
        with pytest.raises(RuntimeError, match="unavailable"):
            remote.delay("account")
    finally:
        worker.close()


def test_server_worker_registers_its_own_integrations():
    worker = create_worker(Settings())
    try:
        assert set(worker.conf.imports) == {
            "app.storage.tasks",
            "app.runtime.server_tasks",
        }
        assert (
            worker.conf.beat_schedule["storage-sync"]["task"]
            == "realityos.storage_tick"
        )
    finally:
        worker.close()


def test_environment_file_is_explicit_and_never_discovered(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text(
        "ENVIRONMENT=production\nMODEL_API_KEY=do-not-load\n"
    )
    selected = tmp_path / "selected.env"
    selected.write_text("ENVIRONMENT=local\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("REALITYOS_ENV_FILE", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    get_settings.cache_clear()
    try:
        assert get_settings().environment == "development"
        monkeypatch.setenv("REALITYOS_ENV_FILE", str(selected))
        get_settings.cache_clear()
        assert get_settings().environment == "local"
    finally:
        get_settings.cache_clear()


def test_missing_explicit_environment_never_uses_default_credentials(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("REALITYOS_ENV_FILE", str(tmp_path / "missing.env"))
    get_settings.cache_clear()
    try:
        with pytest.raises(FileNotFoundError, match="explicitly selected"):
            get_settings()
    finally:
        get_settings.cache_clear()
