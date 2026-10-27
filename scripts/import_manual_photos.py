"""Explicitly register staged manual photos through the RealityOS API.

Files are read from a private staging directory and uploaded through the same
capture endpoint as the web panel. Processing is opt-in because Live mode can
call paid Meta models.
"""

from __future__ import annotations

import argparse
import getpass
import mimetypes
import os
import time
from pathlib import Path
from typing import Any

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_ROOT = PROJECT_ROOT / ".runtime" / "manual-captures" / "incoming"
SUPPORTED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


class ImportError(RuntimeError):
    """A safe, actionable error for a manual capture import."""


def staged_images(raw_paths: list[str], input_root: Path) -> list[Path]:
    root = input_root.resolve()
    if not root.is_dir():
        raise ImportError(f"Staging directory does not exist: {root}")
    resolved: list[Path] = []
    for raw_path in raw_paths:
        path = Path(raw_path)
        if path.is_symlink() or not path.is_file():
            raise ImportError(f"Expected a regular image file: {path}")
        full_path = path.resolve()
        try:
            full_path.relative_to(root)
        except ValueError as exc:
            raise ImportError(f"Image must be inside the staging directory: {path}") from exc
        mime_type, _ = mimetypes.guess_type(full_path.name)
        if mime_type not in SUPPORTED_MIME_TYPES:
            raise ImportError(f"Unsupported image format: {full_path.name}")
        if full_path.stat().st_size > MAX_IMAGE_BYTES:
            raise ImportError(f"Image exceeds the 10 MiB limit: {full_path.name}")
        resolved.append(full_path)
    return resolved


def response_json(response: httpx.Response) -> dict[str, Any] | list[dict[str, Any]]:
    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ImportError(f"API {response.request.method} {response.request.url.path}: {detail}")
    return response.json()


def one_named_item(items: list[dict[str, Any]], name: str, label: str) -> dict[str, Any]:
    matches = [item for item in items if item.get("name") == name]
    if len(matches) != 1:
        raise ImportError(f"Expected exactly one {label} named {name!r}; found {len(matches)}.")
    return matches[0]


def import_images(
    api_url: str,
    email: str,
    password: str,
    workspace_name: str,
    zone_name: str | None,
    images: list[Path],
    process: bool,
    wait: bool,
) -> list[dict[str, str]]:
    """Create an explicit capture session, upload files, and optionally process them."""

    base_url = api_url.rstrip("/")
    with httpx.Client(base_url=base_url, timeout=60) as client:
        tokens = response_json(
            client.post("/v1/auth/login", json={"email": email, "password": password})
        )
        assert isinstance(tokens, dict)
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        workspaces = response_json(client.get("/v1/workspaces", headers=headers))
        assert isinstance(workspaces, list)
        workspace = one_named_item(workspaces, workspace_name, "workspace")
        zone_id = None
        if zone_name:
            zones = response_json(
                client.get(f"/v1/workspaces/{workspace['id']}/zones", headers=headers)
            )
            assert isinstance(zones, list)
            zone_id = one_named_item(zones, zone_name, "zone")["id"]
        session = response_json(
            client.post(
                "/v1/sessions",
                headers=headers,
                json={
                    "workspace_id": workspace["id"],
                    "zone_id": zone_id,
                    "consent_confirmed": True,
                },
            )
        )
        assert isinstance(session, dict)
        imported: list[dict[str, str]] = []
        try:
            for image in images:
                mime_type = mimetypes.guess_type(image.name)[0]
                assert mime_type in SUPPORTED_MIME_TYPES
                with image.open("rb") as stream:
                    capture = response_json(
                        client.post(
                            "/v1/captures",
                            headers=headers,
                            data={"session_id": session["id"]},
                            files={"file": (image.name, stream, mime_type)},
                        )
                    )
                assert isinstance(capture, dict)
                item = {"file": image.name, "capture_id": str(capture["id"])}
                if process:
                    job = response_json(
                        client.post(f"/v1/captures/{capture['id']}/process", headers=headers)
                    )
                    assert isinstance(job, dict)
                    item["job_id"] = str(job["id"])
                imported.append(item)
            if wait and process:
                _wait_for_jobs(client, headers, imported)
            return imported
        finally:
            client.post(f"/v1/sessions/{session['id']}/close", headers=headers)


def _wait_for_jobs(
    client: httpx.Client, headers: dict[str, str], imported: list[dict[str, str]]
) -> None:
    pending = {item["job_id"] for item in imported if "job_id" in item}
    deadline = time.monotonic() + 300
    while pending and time.monotonic() < deadline:
        for job_id in tuple(pending):
            job = response_json(client.get(f"/v1/jobs/{job_id}", headers=headers))
            assert isinstance(job, dict)
            if job["status"] == "completed":
                pending.remove(job_id)
            elif job["status"] == "failed":
                raise ImportError(f"Processing job {job_id} failed: {job.get('error_message')}")
        if pending:
            time.sleep(2)
    if pending:
        raise ImportError(f"Timed out waiting for processing jobs: {', '.join(sorted(pending))}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", help="Image paths inside the private staging directory.")
    parser.add_argument("--api-url", default="http://127.0.0.1:8090")
    parser.add_argument("--workspace", default="Taller RealityOS")
    parser.add_argument("--zone", default="Bodega A")
    parser.add_argument("--email", default="admin@realityos.local")
    parser.add_argument("--input-root", type=Path, default=DEFAULT_INPUT_ROOT)
    parser.add_argument("--process", action="store_true", help="Explicitly invoke the Meta pipeline.")
    parser.add_argument("--wait", action="store_true", help="Wait up to five minutes for requested jobs.")
    parser.add_argument(
        "--confirm-consent",
        action="store_true",
        help="Confirm that everyone affected consented to this capture.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.confirm_consent:
        raise ImportError("Refusing upload without --confirm-consent.")
    if args.wait and not args.process:
        raise ImportError("--wait requires --process.")
    password = os.environ.get("REALITYOS_IMPORT_PASSWORD") or getpass.getpass(
        "RealityOS password: "
    )
    if not password:
        raise ImportError("A password is required.")
    images = staged_images(args.images, args.input_root)
    imported = import_images(
        args.api_url,
        args.email,
        password,
        args.workspace,
        args.zone,
        images,
        args.process,
        args.wait,
    )
    for item in imported:
        print(" ".join(f"{key}={value}" for key, value in item.items()))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ImportError, httpx.HTTPError) as exc:
        raise SystemExit(f"Manual import failed: {exc}") from exc
