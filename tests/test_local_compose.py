"""Render the standalone stack without starting a container or reading real secrets."""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_standalone_compose_isolated_and_real(tmp_path):
    if not shutil.which("docker"):
        pytest.skip("Docker Compose CLI required for static rendering")
    version = subprocess.run(
        ["docker", "compose", "version"], capture_output=True, check=False
    )
    if version.returncode:
        pytest.skip("Docker Compose plugin required")
    infrastructure = tmp_path / "infrastructure"
    infrastructure.mkdir()
    shutil.copy(
        ROOT / "infrastructure/docker-compose.local.yml",
        infrastructure / "docker-compose.local.yml",
    )
    text = (ROOT / ".env.local.example").read_text()
    secrets = {
        "POSTGRES_PASSWORD": "postgres-local-test-secret",
        "JWT_SECRET": "local-unit-test-secret-with-enough-length",
        "DEVICE_CREDENTIAL_PEPPER": "local-unit-test-pepper-with-enough-length",
        "ELEVENLABS_API_KEY": "local-unit-test-speech-api-key",
        "MODEL_API_KEY": "local-unit-test-meta-key",
    }
    for key, value in secrets.items():
        text = text.replace(key + "=\n", key + "=" + value + "\n")
    (tmp_path / ".env.local").write_text(text)
    (tmp_path / ".env").write_text(
        "MODEL_API_KEY=unrelated-server-key-must-not-appear\n"
    )
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in secrets and not k.startswith(("COMPOSE_", "LOCAL_"))
    }
    output = subprocess.check_output(
        [
            "docker",
            "compose",
            "--project-name",
            "realityos-local",
            "--env-file",
            str(tmp_path / ".env.local"),
            "--file",
            str(infrastructure / "docker-compose.local.yml"),
            "config",
            "--format",
            "json",
        ],
        env=env,
        text=True,
    )
    config = json.loads(output)
    assert set(config["services"]) == {"postgres", "redis", "api", "worker"}
    assert config["name"] == "realityos-local"
    assert "unrelated-server-key-must-not-appear" not in output
    for name in ("api", "worker"):
        service = config["services"][name]
        assert service["image"] == "realityos-local-backend:dev"
        assert service["environment"]["ENVIRONMENT"] == "local"
        assert service["environment"]["META_MODE"] == "live"
        assert service["environment"]["FACE_ENGINE"] == "insightface"
        assert service["environment"]["META_GATEWAY_FALLBACK_ENABLED"] == "false"
    assert (
        config["services"]["api"]["environment"]["ELEVENLABS_API_KEY"]
        == ""
    )
    assert config["services"]["api"]["ports"][0]["host_ip"] == "127.0.0.1"
    assert all(
        not config["services"][name].get("ports")
        for name in ("postgres", "redis", "worker")
    )
    assert all(
        volume["name"].startswith("realityos-local_")
        for volume in config["volumes"].values()
    )
