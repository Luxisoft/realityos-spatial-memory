import hashlib
import io
import uuid

import pytest
from app.storage.client import BucketClient, check_key
from app.storage.models import StorageConnection
from PIL import Image
from pydantic import SecretStr

BASE = "/v1/me/storage-connections"


@pytest.fixture
def source(client, auth_headers, monkeypatch):
    client.app.state.settings.storage_encryption_key = SecretStr(
        "test-storage-encryption-key"
    )
    monkeypatch.setattr(
        "app.storage.routes.endpoint_address",
        lambda url: ("storage.example", "1.1.1.1"),
    )
    body = {
        "workspace_id": client.post(
            "/v1/groups", headers=auth_headers, json={"name": "Bucket group"}
        ).json()["id"],
        "name": "My bucket",
        "provider": "s3",
        "endpoint": "https://storage.example",
        "bucket": "my-bucket",
        "region": "us-east-1",
        "prefix": "photos",
        "access_key": "private-access",
        "secret_key": "private-secret",
    }
    with monkeypatch.context() as validation:
        validation.setattr(
            BucketClient, "objects", lambda *a, **kw: {"items": [], "next_cursor": None}
        )
        response = client.post(BASE, headers=auth_headers, json=body)
    assert response.status_code == 201, response.text
    result = response.json()
    assert "secret" not in response.text and "private-access" not in response.text
    with client.app.state.database.session_factory() as db:
        row = db.get(StorageConnection, uuid.UUID(result["id"]))
        assert "private-secret" not in row.secret
    return result


def image_bytes():
    out = io.BytesIO()
    Image.new("RGB", (80, 80), "red").save(out, "PNG")
    return out.getvalue()


@pytest.fixture
def remote(monkeypatch):
    calls = []

    def download(self, key):
        check_key(self.connection, key)
        raw = image_bytes()
        calls.append(key)
        return (
            raw,
            "image/png",
            {"key": key, "sha256": hashlib.sha256(raw).hexdigest(), "etag": '"one"'},
        )

    monkeypatch.setattr(BucketClient, "download", download)
    return calls
