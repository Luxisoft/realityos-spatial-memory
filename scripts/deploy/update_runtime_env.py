"""Update one image reference while retaining the installed private runtime."""

import argparse
import os
import tempfile
from pathlib import Path


def update_runtime(existing: Path, incoming: Path, image_key: str):
    if image_key not in {
        "REALITYOS_GATEWAY_IMAGE",
        "REALITYOS_BACKEND_IMAGE",
    }:
        raise ValueError("Unsupported image setting")
    values = dict(
        row.split("=", 1) for row in incoming.read_text().splitlines() if "=" in row
    )
    image = values[image_key]
    if not image.strip() or "\n" in image:
        raise ValueError("Missing image reference")
    if existing.exists() and existing.stat().st_size:
        rows = existing.read_text().splitlines()
        retired = {
            "REALITYOS_TTS_IMAGE",
            "TTS_SERVICE_URL",
            "TTS_SERVICE_TOKEN",
            "TTS_LOCAL_ENABLED",
            "TTS_PROVIDER",
        }
        rows = [
            row for row in rows if row.split("=", 1)[0] not in retired | {image_key}
        ]
        content = "\n".join([*rows, image_key + "=" + image]) + "\n"
    else:
        content = incoming.read_text()
    fd, filename = tempfile.mkstemp(prefix=".runtime-", dir=existing.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            stream.write(content)
        os.chmod(filename, 0o600)
        os.replace(filename, existing)
    finally:
        if os.path.exists(filename):
            os.unlink(filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("existing", type=Path)
    parser.add_argument("incoming", type=Path)
    parser.add_argument("image_key")
    args = parser.parse_args()
    update_runtime(args.existing, args.incoming, args.image_key)
