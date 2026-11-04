"""Exercise generated storage requests without external credentials or bucket writes."""

import json
import re
import uuid
from pathlib import Path

import pytest
from app.models import User
from app.security import create_access_token
from app.storage.client import BucketClient
from pydantic import SecretStr

ROOT = Path(__file__).resolve().parents[1]
BASE = "/v1/me/storage-connections"


@pytest.mark.parametrize("index,prefix", [(0, "server"), (1, "localhost")])
def test_storage_templates_supply_credentials_and_explicit_destination(
    client, auth_headers, monkeypatch, index, prefix
):
    collection = json.loads(
        (ROOT / "docs/postman/RealityOS.postman_collection.json").read_text()
    )
    templates = {
        item["name"]: item["request"]
        for folder in collection["item"][index]["item"]
        if not folder["name"].startswith("00 ")
        for item in folder["item"]
    }
    workspace = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Storage check"}
    ).json()
    values = {
        "workspace_id": workspace["id"],
        "storage_endpoint": "https://account.r2.cloudflarestorage.com",
        "storage_bucket": "account-media",
        "storage_prefix": "pictures/",
        "storage_access_key": "private-test-access",
        "storage_secret_key": "private-test-secret",
    }

    def body(name):
        return json.loads(
            re.sub(
                r"{{" + prefix + r"_([^}]+)}}",
                lambda m: values[m[1]],
                templates[name]["body"]["raw"],
            )
        )

    client.app.state.settings.storage_encryption_key = SecretStr(
        "test-storage-encryption-key"
    )
    monkeypatch.setattr(
        "app.storage.routes.endpoint_address",
        lambda url: ("storage.example", "1.1.1.1"),
    )
    monkeypatch.setattr(
        BucketClient,
        "objects",
        lambda *args, **kwargs: {"items": [], "next_cursor": None},
    )
    created = client.post(BASE, headers=auth_headers, json=body("POST " + BASE))
    assert created.status_code == 201, created.text
    assert created.json()["workspace_id"] == workspace["id"]
    assert "private-test" not in created.text
    connection_id = created.json()["id"]
    updated = client.request(
        "PUT",
        BASE + "/" + connection_id,
        headers=auth_headers,
        json=body("PUT " + BASE + "/{connection_id}"),
    )
    assert updated.status_code == 200, updated.text
    sync = client.post(
        BASE + "/" + connection_id + "/syncs",
        headers=auth_headers,
        json=body("POST " + BASE + "/{connection_id}/syncs"),
    )
    assert sync.status_code == 201, sync.text
    assert sync.json()["enabled"] is False
    with client.app.state.database.session_factory() as db:
        outsider = User(
            email="outsider@storage.test",
            display_name="Outside",
            password_hash="unused",
        )
        db.add(outsider)
        db.commit()
        other_headers = {
            "Authorization": "Bearer "
            + create_access_token(outsider.id, client.app.state.settings)
        }
    assert (
        client.get(
            BASE + "/" + connection_id + "/objects", headers=other_headers
        ).status_code
        == 404
    )
    denied = client.post(BASE, headers=other_headers, json=body("POST " + BASE))
    assert denied.status_code == 403
    assert uuid.UUID(connection_id)


def test_storage_credentials_are_empty_and_marked_secret_in_both_environments():
    for name, prefix in [("public", "server"), ("local", "localhost")]:
        environment = json.loads(
            (
                ROOT / f"docs/postman/RealityOS.{name}.postman_environment.json"
            ).read_text()
        )
        values = {v["key"]: v for v in environment["values"]}
        for key in (
            "storage_access_key",
            "storage_secret_key",
            "device_key",
            "integration_key",
        ):
            assert values[prefix + "_" + key]["value"] == ""
            assert values[prefix + "_" + key]["type"] == "secret"
