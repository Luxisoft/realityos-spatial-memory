import importlib.util
from pathlib import Path

import pytest


def module():
    path = (
        Path(__file__).resolve().parents[1]
        / "scripts/deploy/preserve_backend_runtime.py"
    )
    spec = importlib.util.spec_from_file_location("preserve_demand", path)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def test_image_upgrade_retains_demand_ingress_without_overwriting_environment(tmp_path):
    nginx = tmp_path / "backend-demand-nginx.conf"
    nginx.write_text("server {}")
    socket_dir = tmp_path / "realityos-socket"
    socket_dir.mkdir()
    overlay = {
        "services": {
            "api": {"environment": {"FACE_ENGINE": "insightface"}},
            "worker": {"image": "installed-worker"},
        }
    }
    module().preserve_demand_runtime(
        overlay, {"nginx_conf": str(nginx), "socket_dir": str(socket_dir)}, tmp_path
    )
    assert overlay["services"]["api"]["restart"] == "no"
    assert overlay["services"]["api"]["environment"] == {"FACE_ENGINE": "insightface"}
    assert overlay["services"]["worker"] == {"image": "installed-worker"}
    assert overlay["services"]["proxy"]["volumes"] == [
        str(nginx) + ":/etc/nginx/conf.d/default.conf:ro",
        str(socket_dir) + ":/run/backend-demand:ro",
    ]


def test_demand_overlay_cannot_bind_an_arbitrary_host_file(tmp_path):
    with pytest.raises(ValueError):
        module().preserve_demand_runtime({}, {"nginx_conf": "/etc/passwd"}, tmp_path)
