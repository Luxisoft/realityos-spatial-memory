"""Keep active application settings and an immediate image rollback during CI."""

import argparse
import json
import os
import subprocess
from pathlib import Path

CONNECTION_SETTINGS = {
    "META_MODE",
    "META_CONNECTION_MODE",
    "META_GATEWAY_FALLBACK_ENABLED",
    "MODEL_API_KEY",
    "META_API_BASE_URL",
    "META_GATEWAY_BASE_URL",
    "META_GATEWAY_TOKEN",
    "ELEVENLABS_API_KEY",
    "ELEVENLABS_VOICE_ID",
    "ELEVENLABS_MODEL_ID",
}


RETIRED_SETTINGS = {
    "TTS_PROVIDER",
    "TTS_SERVICE_URL",
    "TTS_SERVICE_TOKEN",
    "TTS_LOCAL_ENABLED",
    "TTS_DTYPE",
    "TTS_CPU_THREADS",
    "LOCAL_TTS_MEMORY",
}


def application_environment(container, image):
    defaults = dict(row.split("=", 1) for row in image["Config"].get("Env", []) or [])
    active = dict(row.split("=", 1) for row in container["Config"].get("Env", []) or [])
    return {
        key: value
        for key, value in active.items()
        if defaults.get(key) != value and key not in RETIRED_SETTINGS
    }


def runtime_overlays(inspect):
    preserved, rollback = {}, {}
    for service in ("api", "worker", "scheduler"):
        try:
            container = inspect("infrastructure-" + service + "-1")
        except subprocess.CalledProcessError:
            continue  # First installation has no active container to preserve.
        image = inspect(container["Image"])
        settings = application_environment(container, image)
        preserved[service] = {
            "environment": {
                key: value
                for key, value in settings.items()
                if key not in CONNECTION_SETTINGS
            }
        }
        rollback[service] = {
            "image": container["Config"]["Image"],
            "pull_policy": "never",
            "environment": settings,
        }
    return {"services": preserved}, {"services": rollback}


def preserve_demand_runtime(overlay, config, runtime_root):
    """Keep an explicitly installed demand ingress across image-only upgrades.

    No-op unless .runtime/backend-demand.json exists and points at the
    expected socket files. Keeps the API socket-activated (restart=no) and
    the proxy routed through the demand nginx config plus socket mount.
    """

    nginx = Path(config["nginx_conf"]).resolve()
    expected = (runtime_root / "backend-demand-nginx.conf").resolve()
    if nginx != expected or not nginx.is_file():
        raise ValueError("Invalid installed demand ingress configuration")
    socket_dir = Path(config["socket_dir"])
    if (
        not socket_dir.is_absolute()
        or socket_dir.name != "realityos-socket"
        or not socket_dir.is_dir()
    ):
        raise ValueError("Invalid installed demand socket directory")
    services = overlay.setdefault("services", {})
    services.setdefault("api", {}).update(restart="no")
    services.setdefault("proxy", {})["volumes"] = [
        f"{nginx}:/etc/nginx/conf.d/default.conf:ro",
        f"{socket_dir}:/run/backend-demand:ro",
    ]


def docker_inspect(name):
    result = subprocess.run(
        ["docker", "inspect", name], capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)[0]


def save(path, value):
    # Environment values stay in ignored, root-readable runtime files.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(fd, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")
    os.chmod(path, 0o600)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rollback", type=Path, required=True)
    args = parser.parse_args()
    preserved, rollback = runtime_overlays(docker_inspect)
    runtime_root = Path(__file__).resolve().parents[2] / ".runtime"
    demand_path = runtime_root / "backend-demand.json"
    if demand_path.is_file():
        demand = json.loads(demand_path.read_text())
        # Regenerate from the current API-only proxy template, retaining activation.
        # Validation below prevents binding arbitrary runtime paths.
        preserve_demand_runtime(preserved, demand, runtime_root)
        template = (
            runtime_root.parent / "infrastructure/nginx/default.conf"
        ).read_text()
        Path(demand["nginx_conf"]).write_text(
            "upstream backend_demand_api { server unix:/run/backend-demand/api.sock; }\n"
            + template.replace("http://api:8000", "http://backend_demand_api")
        )
        preserve_demand_runtime(rollback, demand, runtime_root)
    save(args.output, preserved)
    save(args.rollback, rollback)
    print(
        json.dumps(
            {
                "services_preserved": list(preserved["services"]),
                "rollback": str(args.rollback),
            }
        )
    )
