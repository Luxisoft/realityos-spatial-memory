"""Public fixture identities, independent of production IDs and credentials."""

import json
import uuid
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[2] / "simulator"
NAMESPACE = uuid.UUID("6fa0d288-5ca3-45cd-8d01-3e098092b192")


def local_id(kind, key):
    return uuid.uuid5(NAMESPACE, f"{kind}:{key}")


def catalog(root=FIXTURES):
    return json.loads((root / "local/catalog.json").read_text())


def accounts():
    return [
        {**user, "workspace_id": group["id"], "workspace_name": group["name"]}
        for group in catalog()["groups"]
        for user in group["users"]
    ]
