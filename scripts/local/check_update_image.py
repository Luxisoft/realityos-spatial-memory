"""Read-only, offline compatibility probe, piped to Python in the installed image."""

import hashlib
import sys
from pathlib import Path


def verify_image(expected: str, root: Path = Path("/")) -> None:
    if sys.version_info[:2] != (3, 13):
        raise SystemExit("Python changed. Run the full local installer first.")
    project = root / "app/pyproject.toml"
    if not project.is_file() or not (root / "scripts/local/bootstrap.py").is_file():
        raise SystemExit("Local image not installed. Run the full local installer.")
    actual = hashlib.sha256(project.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    if actual != expected:
        raise SystemExit("Dependencies changed. Run the full local installer first.")


if __name__ == "__main__":
    verify_image(sys.argv[1])
    print("Installed local image and dependencies verified.")
