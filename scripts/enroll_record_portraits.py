"""Enroll authorized person-record portraits through the faces API.

No direct SQL. Requires a worker user token with ADMIN/REGISTER in the
workspace and biometric consent granted. Portraits are the 'portrait'
attachments from simulator/workspaces manifests.
"""

import argparse
import json
from pathlib import Path

import httpx


def enroll(base_url: str, token: str, workspace_id: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    with httpx.Client(base_url=base_url.rstrip("/") + "/", headers=headers, timeout=180) as client:
        records = client.get(
            f"v1/workspaces/{workspace_id}/records", params={"kind": "person"}
        )
        records.raise_for_status()
        enrolled = []
        for row in records.json():
            if not row.get("biometric_authorized"):
                continue
            detail = client.get(f"v1/workspaces/{workspace_id}/records/{row['id']}")
            detail.raise_for_status()
            media = [m for m in detail.json().get("media", []) if m.get("external_id") == "portrait"]
            if not media:
                continue
            response = client.post(
                "v1/faces/record-enroll",
                json={"record_id": row["id"], "record_media_id": media[0]["id"]},
            )
            response.raise_for_status()
            enrolled.append({"record": row["external_id"], **response.json()})
        return {"workspace_id": workspace_id, "enrolled": enrolled}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--token", required=True, help="Worker user Bearer token (private, never commit)")
    parser.add_argument("--workspace-id", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = enroll(args.base_url, args.token, args.workspace_id)
    text = json.dumps(result, indent=2)
    print(text)
    if args.output:
        args.output.write_text(text + "\n")


if __name__ == "__main__":
    main()
