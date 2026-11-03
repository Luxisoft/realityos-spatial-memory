"""Validate the rendered production worker without real runtime secrets."""

import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest


def test_replacement_preserves_runtime_without_mutating_snapshot():
    root = Path(__file__).resolve().parents[1]
    module_spec = importlib.util.spec_from_file_location(
        "worker_resources", root / "scripts/deploy/worker_resources.py"
    )
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    original = {
        "Image": "sha256:installed",
        "Config": {
            "Image": "tag:mutable",
            "Env": ["PRIVATE_VALUE=example"],
            "Hostname": "old",
            "Labels": {"project": "production"},
        },
        "HostConfig": {"Memory": 0, "Mounts": [], "NetworkMode": "internal"},
        "NetworkSettings": {"Networks": {"internal": {"Aliases": ["worker"]}}},
    }
    before = json.dumps(original, sort_keys=True)
    release = module.worker_spec(original)
    assert release["Image"] == "sha256:installed"
    assert release["Env"] == ["PRIVATE_VALUE=example"]
    assert release["Labels"] == {"project": "production"}
    assert release["NetworkingConfig"]["EndpointsConfig"] == {
        "internal": {"Aliases": ["worker"]}
    }
    assert release["HostConfig"]["MemorySwap"] == release["HostConfig"]["Memory"]
    assert "Hostname" not in release
    assert json.dumps(original, sort_keys=True) == before


def test_worker_has_no_model_processes_at_rest(tmp_path):
    if not shutil.which("docker"):
        pytest.skip("Docker Compose is required")
    root = Path(__file__).resolve().parents[1]
    infrastructure = tmp_path / "infrastructure"
    infrastructure.mkdir()
    shutil.copy(root / "infrastructure/docker-compose.yml", infrastructure)
    (tmp_path / ".env").write_text("POSTGRES_PASSWORD=test-password\n")
    env = {k: v for k, v in os.environ.items() if not k.startswith("COMPOSE_")}
    env["POSTGRES_PASSWORD"] = "test-password"
    config = json.loads(
        subprocess.check_output(
            [
                "docker",
                "compose",
                "-f",
                str(infrastructure / "docker-compose.yml"),
                "config",
                "--format",
                "json",
            ],
            env=env,
            text=True,
        )
    )
    worker = config["services"]["worker"]
    assert "--autoscale=1,0" in worker["command"]
    assert "--max-tasks-per-child=1" in worker["command"]
    assert "--prefetch-multiplier=1" in worker["command"]
    assert int(worker["mem_limit"]) == 1536 * 1024 * 1024
    assert float(worker["cpus"]) == 2
    assert worker["pids_limit"] == 128
