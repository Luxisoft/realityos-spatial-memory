"""Offline image compatibility and narrowly scoped source mounts; no Docker calls."""

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_update_image", ROOT / "scripts/local/check_update_image.py"
)
probe = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(probe)


@pytest.fixture
def installed_image(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 13, 2))
    (tmp_path / "app").mkdir()
    (tmp_path / "scripts/local").mkdir(parents=True)
    (tmp_path / "scripts/local/bootstrap.py").touch()
    return tmp_path


@pytest.mark.parametrize("image_newline", ["\n", "\r\n"])
def test_image_hash_ignores_windows_line_endings(installed_image, image_newline):
    project = '[project]\nname = "café"\n'
    (installed_image / "app/pyproject.toml").write_bytes(
        project.replace("\n", image_newline).encode("utf-8")
    )
    expected = hashlib.sha256(project.encode("utf-8")).hexdigest()
    probe.verify_image(expected, installed_image)


def test_dependency_change_requires_installer(installed_image):
    (installed_image / "app/pyproject.toml").write_text("dependencies = ['new']\n")
    with pytest.raises(SystemExit, match="Dependencies changed"):
        probe.verify_image("0" * 64, installed_image)


def test_missing_or_server_image_requires_installer(installed_image):
    with pytest.raises(SystemExit, match="Local image not installed"):
        probe.verify_image("0" * 64, installed_image)
    (installed_image / "app/pyproject.toml").touch()
    (installed_image / "scripts/local/bootstrap.py").unlink()
    with pytest.raises(SystemExit, match="Local image not installed"):
        probe.verify_image("0" * 64, installed_image)


def test_python_change_requires_installer(installed_image, monkeypatch):
    monkeypatch.setattr(sys, "version_info", (3, 14, 0))
    with pytest.raises(SystemExit, match="Python changed"):
        probe.verify_image("0" * 64, installed_image)


def test_only_local_api_and_worker_receive_readonly_source_mounts():
    compose = yaml.safe_load(
        (ROOT / "infrastructure/docker-compose.local.yml").read_text()
    )
    expected = {
        "../backend/app": "/app/app",
        "../backend/alembic": "/app/alembic",
        "../backend/alembic.ini": "/app/alembic.ini",
        "../backend/schema": "/app/schema",
        "../scripts/local": "/scripts/local",
        "../simulator/database": "/simulator/database",
        "../simulator/media": "/simulator/media",
    }
    for name in ("api", "worker"):
        mounts = compose["services"][name]["volumes"]
        assert {item["source"]: item["target"] for item in mounts} == expected
        assert all(
            item["type"] == "bind"
            and item["read_only"] is True
            and item["bind"]["create_host_path"] is False
            for item in mounts
        )
    for name in ("postgres", "redis"):
        assert all(
            isinstance(item, str) for item in compose["services"][name]["volumes"]
        )
    server = (ROOT / "infrastructure/docker-compose.yml").read_text()
    assert "../simulator" not in server
