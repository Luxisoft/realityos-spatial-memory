"""Replace only an idle worker, preserving its image, secrets and networks.

Uses the existing Docker socket; never reads private host env files or rebuilds
the application. The original container remains stopped for immediate rollback.
"""

from __future__ import annotations

import argparse
import copy
import http.client
import json
import os
import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import quote


class DockerConnection(http.client.HTTPConnection):
    def __init__(self):
        super().__init__("localhost", timeout=620)

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect("/var/run/docker.sock")


def docker(method, path, body=None):
    connection = DockerConnection()
    try:
        connection.request(
            method,
            "/v1.45" + path,
            json.dumps(body).encode() if body is not None else None,
            {"Content-Type": "application/json"},
        )
        response = connection.getresponse()
        data = response.read()
        if response.status >= 400:
            # Docker errors must not expose serialized environment values.
            raise RuntimeError(
                f"Docker {method} {path.split('?')[0]}: {response.status}"
            )
        return json.loads(data) if data else None
    finally:
        connection.close()


def container_spec(original):
    spec = copy.deepcopy(original["Config"])
    spec.pop("Hostname", None)
    spec["Image"] = original["Image"]  # exact installed digest, no pull or build
    host = copy.deepcopy(original["HostConfig"])
    if not host.get("Mounts"):
        host.pop("Mounts", None)
    spec["HostConfig"] = host
    spec["NetworkingConfig"] = {
        "EndpointsConfig": {
            name: {"Aliases": network.get("Aliases", [])}
            for name, network in original["NetworkSettings"]["Networks"].items()
        }
    }
    return spec


def worker_spec(original):
    spec = container_spec(original)
    spec["Cmd"] = [
        "celery",
        "-A",
        "app.tasks.celery_app",
        "worker",
        "--loglevel=INFO",
        "--autoscale=1,0",
        "--max-tasks-per-child=1",
        "--prefetch-multiplier=1",
    ]
    host = spec["HostConfig"]
    host.update(
        Memory=1536 * 1024**2,
        MemorySwap=1536 * 1024**2,
        NanoCpus=2_000_000_000,
        PidsLimit=128,
    )
    return spec


def private_json(path, value):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump(value, stream)


def replace_worker(name, receipt):
    original = docker("GET", f"/containers/{quote(name)}/json")
    if original["Mounts"]:
        raise RuntimeError("Worker mounts require explicit release review")
    probe = (
        "import json; from app.tasks import celery_app; "
        "i=celery_app.control.inspect(timeout=2); "
        "print(json.dumps([i.active(),i.reserved(),i.scheduled()]))"
    )
    result = subprocess.run(
        ["docker", "exec", name, "python", "-c", probe],
        capture_output=True,
        text=True,
        check=True,
    )
    queues = json.loads(result.stdout)
    if any(not reply or any(reply.values()) for reply in queues):
        raise RuntimeError("Worker is busy or unreachable; replacement deferred")
    spec = worker_spec(original)
    receipt.mkdir(parents=True, exist_ok=True, mode=0o700)
    receipt.chmod(0o700)
    backup = name + "-resources-rollback-" + str(int(time.time()))
    private_json(receipt / "before.json", original)
    private_json(receipt / "release.json", {"worker": name, "rollback": backup})
    old_id = original["Id"]
    docker("POST", f"/containers/{old_id}/stop?t=600")
    docker("POST", f"/containers/{old_id}/rename?name={quote(backup)}")
    new_id = None
    try:
        new_id = docker("POST", f"/containers/create?name={quote(name)}", spec)["Id"]
        docker("POST", f"/containers/{new_id}/start")
        # Verify the actual broker consumer, rather than just a running container.
        deadline = time.monotonic() + 40
        while True:
            check = subprocess.run(
                [
                    "docker",
                    "exec",
                    name,
                    "python",
                    "-c",
                    (
                        "from app.tasks import celery_app; "
                        "r=celery_app.control.inspect(timeout=3).stats(); "
                        "assert r and all(x.get('autoscaler',{}).get('max')==1 "
                        "and x['autoscaler']['min']==0 for x in r.values())"
                    ),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if check.returncode == 0:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("New worker did not confirm broker readiness")
            time.sleep(1)

    except BaseException:
        if new_id:
            docker("DELETE", f"/containers/{new_id}?force=true")
        docker("POST", f"/containers/{old_id}/rename?name={quote(name)}")
        docker("POST", f"/containers/{old_id}/start")
        raise
    print(
        json.dumps(
            {
                "worker": name,
                "rollback_container": backup,
                "image": original["Image"],
                "receipt": str(receipt),
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--container", default="infrastructure-worker-1")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    replace_worker(args.container, args.receipt)
