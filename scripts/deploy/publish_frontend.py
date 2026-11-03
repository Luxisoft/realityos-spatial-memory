"""Publish a CI-built frontend without replacing application files or backend services."""

import fcntl
import json
import os
import re
import subprocess
import sys
import tarfile
from pathlib import Path


def main():
    sha, root = sys.argv[1], Path(sys.argv[2]).resolve()
    if (
        not re.fullmatch("[0-9a-f]{40}", sha)
        or not (root / "infrastructure/docker-compose.yml").is_file()
    ):
        raise ValueError("Invalid release or checkout")
    os.umask(0o077)
    stage = root / ".runtime" / f"web-{sha}"
    stage.mkdir(exist_ok=True)
    with tarfile.open(f"/tmp/realityos-web-{sha}.tar.gz") as archive:
        archive.extractall(stage, filter="data")
    (stage / "Dockerfile").write_text(
        "FROM nginx:1.27-alpine\nCOPY dist /usr/share/nginx/html\n"
    )
    # Open existing shared build lock read-only: Linux protected_regular rejects
    # root write-opens of a lock owned by the interactive deployment user.
    with open("/run/lock/luxipanel-assistant-build.lock", "r") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        old = json.loads(
            subprocess.check_output(["docker", "inspect", "infrastructure-frontend-1"])
        )[0]
        image = f"realityos-frontend:workspace-{sha[:12]}"
        subprocess.run(["docker", "build", "-t", image, str(stage)], check=True)
        release = stage / "release.json"
        rollback = stage / "rollback.json"
        release.write_text(
            json.dumps(
                {"services": {"frontend": {"image": image, "pull_policy": "never"}}}
            )
        )
        if not rollback.exists():
            rollback.write_text(
                json.dumps(
                    {
                        "services": {
                            "frontend": {"image": old["Image"], "pull_policy": "never"}
                        }
                    }
                )
            )
        command = [
            "docker",
            "compose",
            "--project-name",
            "infrastructure",
            "--env-file",
            str(root / ".env"),
            "-f",
            str(root / "infrastructure/docker-compose.yml"),
            "-f",
            str(root / "infrastructure/docker-compose.production.yml"),
            "-f",
            str(release),
            "up",
            "-d",
            "--no-deps",
            "--no-build",
            "frontend",
        ]
        subprocess.run(command, cwd=root, check=True)
        (stage / "receipt.json").write_text(
            json.dumps({"image": image, "rollback": str(rollback), "commit": sha})
        )
    Path(f"/tmp/realityos-web-{sha}.tar.gz").unlink()
    print(json.dumps({"frontend_image": image, "rollback": str(rollback)}))


if __name__ == "__main__":
    main()
