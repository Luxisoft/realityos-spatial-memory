"""Install the image's build/runtime requirements from its sole package manifest."""

import subprocess
import sys
import tomllib
from pathlib import Path


def requirements(path: Path) -> list[str]:
    with path.open("rb") as source:
        configuration = tomllib.load(source)
    project = configuration["project"]
    return list(
        dict.fromkeys(
            [
                *configuration["build-system"]["requires"],
                *project["dependencies"],
                *project["optional-dependencies"]["faces"],
            ]
        )
    )


def install(path: Path = Path("pyproject.toml")) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-cache-dir",
            "--root-user-action=ignore",
            *requirements(path),
        ],
        check=True,
    )


if __name__ == "__main__":
    install()
