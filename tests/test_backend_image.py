"""Code-only changes reuse image dependencies and preserve runtime packaging."""

import sys
import tomllib
from pathlib import Path

import pytest
from install_dependencies import install, requirements

ROOT = Path(__file__).resolve().parents[1]


def test_image_dependencies_include_build_backend_and_faces_but_not_dev():
    path = ROOT / "backend/pyproject.toml"
    configuration = tomllib.loads(path.read_text())
    selected = requirements(path)
    assert len(selected) == len(set(selected))
    assert set(configuration["build-system"]["requires"]) <= set(selected)
    assert set(configuration["project"]["dependencies"]) <= set(selected)
    assert set(configuration["project"]["optional-dependencies"]["faces"]) <= set(
        selected
    )
    assert not set(configuration["project"]["optional-dependencies"]["dev"]) & set(
        selected
    )


def test_installer_uses_changed_manifest_without_another_requirements_list(
    tmp_path, monkeypatch
):
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text(
        '[build-system]\nrequires = ["build-backend>=3"]\n'
        '[project]\ndependencies = ["runtime>=2", "shared>=1"]\n'
        "[project.optional-dependencies]\n"
        'faces = ["face-runtime>=4", "shared>=1"]\n'
        'dev = ["test-runner>=5"]\n'
    )
    calls = []
    monkeypatch.setattr(
        "install_dependencies.subprocess.run",
        lambda arguments, **kwargs: calls.append((arguments, kwargs)),
    )
    install(manifest)
    assert calls == [
        (
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                "--no-cache-dir",
                "--root-user-action=ignore",
                "build-backend>=3",
                "runtime>=2",
                "shared>=1",
                "face-runtime>=4",
            ],
            {"check": True},
        )
    ]


def test_missing_required_extra_fails_before_installation(tmp_path, monkeypatch):
    manifest = tmp_path / "pyproject.toml"
    manifest.write_text(
        '[build-system]\nrequires = ["builder"]\n'
        "[project]\ndependencies = []\n"
        "[project.optional-dependencies]\n"
    )
    monkeypatch.setattr(
        "install_dependencies.subprocess.run",
        lambda *args, **kwargs: pytest.fail("An incomplete manifest must not install."),
    )
    with pytest.raises(KeyError, match="faces"):
        install(manifest)


def test_expensive_image_layers_precede_application_and_local_resources():
    dockerfile = (ROOT / "backend/Dockerfile").read_text()
    metadata = dockerfile.index("COPY backend/pyproject.toml")
    dependencies = dockerfile.index("python /build/install_dependencies.py")
    model = dockerfile.index("RUN python -c")
    application = dockerfile.index("COPY backend/app")
    package = dockerfile.index(
        "RUN pip install --no-index --no-deps --no-build-isolation"
    )
    local = dockerfile.index("FROM base AS local")
    assert metadata < dependencies < model < application < package < local
    assert "COPY backend/alembic" not in dockerfile[:model]
    assert "COPY backend/schema" not in dockerfile[:model]
    assert "simulator" not in dockerfile[:local]
    assert "apt-get install --no-install-recommends -y ffmpeg g++" in dockerfile
    assert (
        "FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])"
        in dockerfile
    )
    assert "app.prepare(ctx_id=0)" in dockerfile
    assert '".[faces]"' in dockerfile[package:local]
    assert "PYTHONPATH=/app" in dockerfile


def test_server_image_keeps_source_and_excludes_local_fixtures():
    dockerfile = (ROOT / "backend/Dockerfile").read_text()
    base, local = dockerfile.split("FROM base AS local", 1)
    fixtures, server = local.split("FROM base AS server", 1)
    assert "COPY backend/app ./app" in base
    assert "COPY backend/schema ./schema" in base
    assert "COPY scripts/local /scripts/local" in fixtures
    assert "COPY simulator/database /simulator/database" in fixtures
    assert "COPY simulator/media /simulator/media" in fixtures
    assert "COPY" not in server
    assert "simulator" not in base
