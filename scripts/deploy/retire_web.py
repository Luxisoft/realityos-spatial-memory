"""Remove only the two retired web containers after the proxy cutover."""

import json
import subprocess


def retire(project="infrastructure"):
    for service in ("frontend", "display"):
        name = f"{project}-{service}-1"
        result = subprocess.run(
            ["docker", "inspect", name], capture_output=True, text=True, check=False
        )
        if result.returncode:
            continue
        labels = json.loads(result.stdout)[0]["Config"].get("Labels", {})
        if (
            labels.get("com.docker.compose.project") != project
            or labels.get("com.docker.compose.service") != service
        ):
            raise RuntimeError(f"Unexpected ownership of {name}")
        subprocess.run(["docker", "stop", name], check=True)
        subprocess.run(["docker", "rm", name], check=True)


if __name__ == "__main__":
    retire()
