"""Install socket activation for the existing API without rebuilding its image."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

from worker_resources import container_spec, docker, private_json


def run(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def enable(gateway_source: Path, receipt: Path, root: Path):
    receipt.mkdir(mode=0o700, parents=True)
    api = docker("GET", "/containers/infrastructure-api-1/json")
    proxy = docker("GET", "/containers/infrastructure-proxy-1/json")
    private_json(receipt / "api-before.json", api)
    private_json(receipt / "proxy-before.json", proxy)
    network = next(
        name
        for name in proxy["NetworkSettings"]["Networks"]
        if name.endswith("_internal") and name in api["NetworkSettings"]["Networks"]
    )
    source = gateway_source.read_bytes()
    digest = hashlib.sha256(source).hexdigest()
    private_root = Path.home() / ".local/share/backend-demand"
    socket_dir = private_root / "realityos-socket"
    socket_dir.mkdir(mode=0o755, parents=True, exist_ok=True)
    release = private_root / "releases" / digest
    release.mkdir(mode=0o700, parents=True, exist_ok=True)
    script = release / "docker-gateway.mjs"
    script.write_bytes(source)
    config = private_root / "realityos.json"
    desired_config = {
        "container": "infrastructure-api-1",
        "network": network,
        "idleMs": 60000,
        "dependencies": ["infrastructure-postgres-1", "infrastructure-redis-1"],
    }
    if config.exists():
        if json.loads(config.read_text()) != desired_config:
            raise RuntimeError("Existing gateway configuration differs")
    else:
        private_json(config, desired_config)
    units = Path.home() / ".config/systemd/user"
    units.mkdir(parents=True, exist_ok=True)
    unit = "backend-demand-realityos"
    (units / (unit + ".service")).write_text(f"""[Unit]
Description=RealityOS socket-activated API ingress
Requires={unit}.socket
After={unit}.socket

[Service]
Type=exec
ExecStart=/usr/bin/node {script} {config}
Restart=on-failure
RestartSec=3
TimeoutStopSec=600
MemoryMax=128M
TasksMax=128
UMask=0077
""")
    (units / (unit + ".socket")).write_text(f"""[Unit]
Description=RealityOS API activation socket

[Socket]
ListenStream={socket_dir}/api.sock
SocketMode=0666
Accept=no
Service={unit}.service
Backlog=128

[Install]
WantedBy=sockets.target
""")
    original = run(
        "docker",
        "exec",
        "infrastructure-proxy-1",
        "cat",
        "/etc/nginx/conf.d/default.conf",
    )
    # API, health, Swagger and its OAuth callback must share the same upstream.
    if original.count("http://api:8000") != 4:
        raise RuntimeError("Unrecognized proxy configuration; no cutover performed")
    nginx_path = root / ".runtime/backend-demand-nginx.conf"
    nginx_path.write_text(
        "upstream backend_demand_api { server unix:/run/backend-demand/api.sock; }\n"
        + original.replace("http://api:8000", "http://backend_demand_api")
    )
    # Validate before touching the live proxy or port.
    run(
        "docker",
        "run",
        "--rm",
        "--network",
        network,
        "--entrypoint",
        "nginx",
        "--mount",
        f"type=bind,src={nginx_path},dst=/etc/nginx/conf.d/default.conf,readonly",
        proxy["Image"],
        "-t",
    )
    spec = container_spec(proxy)
    binds = spec["HostConfig"].get("Binds", [])
    replacement = [
        f"{nginx_path}:/etc/nginx/conf.d/default.conf:ro"
        if ":/etc/nginx/conf.d/default.conf:" in bind
        else bind
        for bind in binds
    ]
    if replacement == binds:
        raise RuntimeError("Expected a read-only Nginx config bind")
    spec["HostConfig"]["Binds"] = [*replacement, f"{socket_dir}:/run/backend-demand:ro"]
    run("systemctl", "--user", "daemon-reload")
    run("systemctl", "--user", "enable", "--now", unit + ".socket")
    backup = "infrastructure-proxy-1-demand-rollback-" + str(int(time.time()))
    old_id = proxy["Id"]
    new_id = None
    try:
        docker("POST", f"/containers/{old_id}/stop?t=30")
        docker("POST", f"/containers/{old_id}/rename?name={backup}")
        new_id = docker("POST", "/containers/create?name=infrastructure-proxy-1", spec)[
            "Id"
        ]
        docker("POST", f"/containers/{new_id}/start")
        bindings = proxy["NetworkSettings"]["Ports"]["80/tcp"]
        host_port = bindings[0]["HostPort"]
        deadline = time.monotonic() + 30
        while True:
            try:
                with urlopen(
                    f"http://127.0.0.1:{host_port}/health/ready", timeout=3
                ) as response:
                    if response.status == 200:
                        break
            except OSError:
                if time.monotonic() >= deadline:
                    raise RuntimeError("On-demand proxy readiness failed") from None
                time.sleep(0.2)
        docker(
            "POST",
            "/containers/infrastructure-api-1/update",
            {
                "RestartPolicy": {"Name": "no"},
                "Memory": 1536 * 1024**2,
                "MemorySwap": 1536 * 1024**2,
                "NanoCpus": 2_000_000_000,
            },
        )
        private_json(
            root / ".runtime/backend-demand.json",
            {
                "nginx_conf": str(nginx_path),
                "socket_dir": str(socket_dir),
                "unit": unit,
                "gateway_sha256": digest,
            },
        )
        private_json(receipt / "release.json", {"rollback_proxy": backup, "unit": unit})
    except BaseException:
        if new_id:
            docker("DELETE", f"/containers/{new_id}?force=true")
        docker("POST", f"/containers/{old_id}/rename?name=infrastructure-proxy-1")
        docker("POST", f"/containers/{old_id}/start")
        run("systemctl", "--user", "disable", "--now", unit + ".socket")
        run("systemctl", "--user", "stop", unit + ".service")
        raise
    print(
        json.dumps(
            {
                "unit": unit,
                "gateway_sha256": digest,
                "rollback_proxy": backup,
                "idle_seconds": 60,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    enable(
        args.gateway.resolve(),
        args.receipt.resolve(),
        Path(__file__).resolve().parents[2],
    )
