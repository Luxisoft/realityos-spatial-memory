"""CI image upgrades retain the active private runtime and a usable rollback."""

import importlib.util
import json
import stat
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(
        name, ROOT / "scripts/deploy" / (name + ".py")
    )
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


update = module("update_runtime_env")
preserve = module("preserve_backend_runtime")


@pytest.mark.parametrize(
    "key", ["REALITYOS_GATEWAY_IMAGE", "REALITYOS_BACKEND_IMAGE", "REALITYOS_TTS_IMAGE"]
)
def test_image_update_preserves_existing_credentials_and_optional_settings(
    tmp_path, key
):
    installed = tmp_path / "runtime.env"
    incoming = tmp_path / "incoming.env"
    installed.write_text(
        f"{key}=previous\nMETA_GATEWAY_TOKEN=existing-private-test-token\nTTS_SERVICE_URL=http://speech:8091/synthesize\n"
    )
    incoming.write_text(
        f"{key}=next\nMETA_GATEWAY_TOKEN=replacement-that-must-not-overwrite\n"
    )
    update.update_runtime(installed, incoming, key)
    result = installed.read_text()
    assert f"{key}=next\n" in result
    assert result.count(key + "=") == 1
    assert "existing-private-test-token" in result
    assert "replacement-that-must-not-overwrite" not in result
    assert "TTS_SERVICE_URL=http://speech:8091/synthesize" in result
    assert stat.S_IMODE(installed.stat().st_mode) == 0o600


def test_first_install_uses_the_supplied_runtime(tmp_path):
    incoming = tmp_path / "incoming.env"
    installed = tmp_path / "runtime.env"
    incoming.write_text(
        "REALITYOS_BACKEND_IMAGE=first\nMETA_GATEWAY_TOKEN=test-token\n"
    )
    update.update_runtime(installed, incoming, "REALITYOS_BACKEND_IMAGE")
    assert installed.read_text() == incoming.read_text()


def test_missing_image_cannot_damage_an_installed_runtime(tmp_path):
    incoming = tmp_path / "incoming.env"
    installed = tmp_path / "runtime.env"
    installed.write_text("REALITYOS_BACKEND_IMAGE=current\n")
    incoming.write_text("META_GATEWAY_TOKEN=test-token\n")
    with pytest.raises(KeyError):
        update.update_runtime(installed, incoming, "REALITYOS_BACKEND_IMAGE")
    assert installed.read_text() == "REALITYOS_BACKEND_IMAGE=current\n"


def test_backend_overlay_retains_live_engine_auth_and_gateway_settings():
    old_image = {"Config": {"Env": ["PATH=/old-image", "PYTHONPATH=/app"]}}
    settings = [
        "PATH=/old-image",
        "PYTHONPATH=/app",
        "META_MODE=live",
        "FACE_ENGINE=insightface",
        "META_GATEWAY_TOKEN=private-test-token",
        "FACEBOOK_APP_SECRET=test-app-secret",
        "MODEL_API_KEY=",
    ]
    container = {
        "Image": "sha256:previous",
        "Config": {"Image": "realityos-backend:previous", "Env": settings},
    }

    def inspect(name):
        return old_image if name.startswith("sha256:") else container

    runtime, rollback = preserve.runtime_overlays(inspect)
    for service in ("api", "worker"):
        env = runtime["services"][service]["environment"]
        assert env["FACE_ENGINE"] == "insightface"
        assert env["FACEBOOK_APP_SECRET"] == "test-app-secret"
        assert "META_GATEWAY_TOKEN" not in env
        assert "MODEL_API_KEY" not in env
        assert "PATH" not in env and "PYTHONPATH" not in env
        assert "image" not in runtime["services"][service]
        assert rollback["services"][service]["image"] == "realityos-backend:previous"
        assert rollback["services"][service]["pull_policy"] == "never"
        assert (
            rollback["services"][service]["environment"]["META_GATEWAY_TOKEN"]
            == "private-test-token"
        )


def test_meta_key_can_be_preserved_for_private_rollback():
    env = preserve.application_environment(
        {"Config": {"Env": ["MODEL_API_KEY=private-test-key"]}},
        {"Config": {"Env": []}},
    )
    assert env["MODEL_API_KEY"] == "private-test-key"


def test_first_install_has_no_previous_containers():
    def missing(name):
        raise subprocess.CalledProcessError(1, ["docker", "inspect", name])

    assert preserve.runtime_overlays(missing) == ({"services": {}}, {"services": {}})


def test_private_overlay_permissions_and_round_trip(tmp_path):
    path = tmp_path / "runtime.json"
    path.write_text("old")
    path.chmod(0o644)
    value = {"services": {"api": {"environment": {"FACE_ENGINE": "insightface"}}}}
    preserve.save(path, value)
    assert json.loads(path.read_text()) == value
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
