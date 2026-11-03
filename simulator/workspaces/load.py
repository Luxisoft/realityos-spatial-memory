"""Import fixtures exclusively through RealityOS HTTP API.

Credentials file (private, never commit): {base_url, integration_key, worker_ids}.
"""

import argparse
import json
import mimetypes
from pathlib import Path

import httpx


def load(manifest_path, credentials_path):
    manifest = json.loads(manifest_path.read_text())
    config = json.loads(credentials_path.read_text())
    with httpx.Client(
        base_url=config["base_url"].rstrip("/") + "/",
        headers={"X-RealityOS-Integration-Key": config["integration_key"]},
        timeout=180,
    ) as client:
        response = client.post("integrations/imports", json=manifest["batch"])
        response.raise_for_status()
        imported = response.json()
        ids = {r["external_id"]: r["id"] for r in imported["records"]}
        for item in manifest["attachments"]:
            path = manifest_path.parent / item["path"]
            with path.open("rb") as stream:
                response = client.post(
                    f"integrations/records/{ids[item['record']]}/media",
                    data={
                        "external_id": item["external_id"],
                        "publish": str(item["publish"]).lower(),
                        "author_id": config["worker_ids"][item["author"]],
                    },
                    files={"file": (path.name, stream, mimetypes.guess_type(path)[0])},
                )
            response.raise_for_status()
        print(
            json.dumps(
                {
                    "workspace": manifest["workspace_name"],
                    "import_id": imported["id"],
                    "records": len(ids),
                    "attachments": len(manifest["attachments"]),
                }
            )
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--credentials", type=Path, required=True)
    args = parser.parse_args()
    load(args.manifest, args.credentials)
