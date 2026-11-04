"""Source edits are atomic; retired imports cannot reappear through workers or shares."""

import uuid

import pytest
from app.models import MediaAsset
from app.social_features.evidence_models import PublicationUpload
from app.social_features.models import Publication
from app.storage.client import BucketClient
from app.storage.lifecycle import check_upload_source
from app.storage.models import StorageConnection
from app.storage.provenance_models import StorageObject
from catalog_support import classification_for
from fastapi import HTTPException
from sqlalchemy import select
from test_storage_connections import BASE, image_bytes
from test_storage_connections import remote as remote  # noqa: PLC0414 -- pytest fixture export
from test_storage_connections import source as source  # noqa: PLC0414 -- pytest fixture export


def imported(client, headers, connection, key="photos/one.png"):
    response = client.post(
        BASE + "/" + connection["id"] + "/imports",
        headers=headers,
        json={
            "request_key": str(uuid.uuid4()),
            "keys": [key],
            "classifications": {
                key: classification_for(client, connection["workspace_id"])
            },
        },
    )
    assert response.status_code == 202, response.text
    return response.json()["items"][0]


def test_failed_source_edit_preserves_old_then_success_retires_shared_copies(
    client, auth_headers, source, remote, monkeypatch
):
    original = imported(client, auth_headers, source)
    group = client.post(
        "/v1/groups", headers=auth_headers, json={"name": "Copied group"}
    ).json()["id"]
    shared = client.post(
        f"/v1/groups/{group}/publications/import",
        headers=auth_headers,
        json={
            "publication_ids": [original["publication_id"]],
            "classifications": {
                original["publication_id"]: classification_for(client, group)
            },
        },
    ).json()["items"][0]["id"]
    path = BASE + "/" + source["id"]
    change = {
        **source,
        "provider": "r2",
        "endpoint": "https://demo.r2.cloudflarestorage.com",
        "bucket": "different-bucket",
    }

    def unavailable(*args, **kwargs):
        raise HTTPException(502, "Remote unavailable")

    monkeypatch.setattr(BucketClient, "objects", unavailable)
    assert (
        client.request("PUT", path, headers=auth_headers, json=change).status_code
        == 502
    )
    assert (
        client.get(f"/v1/gallery/{shared}/media", headers=auth_headers).content
        == image_bytes()
    )
    with client.app.state.database.session_factory() as db:
        assert db.get(StorageConnection, uuid.UUID(source["id"])).revision == 1

    monkeypatch.setattr(
        BucketClient, "objects", lambda *a, **k: {"items": [], "next_cursor": None}
    )
    updated = client.request("PUT", path, headers=auth_headers, json=change)
    assert updated.status_code == 200, updated.text
    assert updated.json()["revision"] == 2
    for post_id in (original["publication_id"], shared):
        assert (
            client.get(f"/v1/gallery/{post_id}/media", headers=auth_headers).status_code
            == 404
        )
    with client.app.state.database.session_factory() as db:
        upload = db.get(PublicationUpload, uuid.UUID(original["upload_id"]))
        assert upload.status == "cancelled" and not upload.original_bytes
        with pytest.raises(HTTPException) as rejected:
            check_upload_source(db, upload)
        assert rejected.value.status_code == 409
        asset = db.get(MediaAsset, db.get(Publication, uuid.UUID(shared)).media_id)
        assert not asset.original_bytes


def test_credential_rotation_keeps_copies_and_default_sync(
    client, auth_headers, source, remote, monkeypatch
):
    original = imported(client, auth_headers, source)
    path = BASE + "/" + source["id"]
    monkeypatch.setattr(
        BucketClient, "objects", lambda *a, **k: {"items": [], "next_cursor": None}
    )
    changed = client.request(
        "PUT",
        path,
        headers=auth_headers,
        json={**source, "access_key": "rotated-key", "secret_key": "rotated-secret"},
    )
    assert changed.status_code == 200 and changed.json()["revision"] == 1
    assert (
        client.get(
            f"/v1/gallery/{original['publication_id']}/media", headers=auth_headers
        ).status_code
        == 200
    )
    rules = client.get(path + "/syncs", headers=auth_headers).json()
    assert (
        len(rules) == 1 and rules[0]["enabled"] and rules[0]["interval_minutes"] == 15
    )


def test_only_a_complete_scan_retires_missing_remote_keys(
    client, auth_headers, source, remote, monkeypatch
):
    original = imported(client, auth_headers, source)
    path = BASE + "/" + source["id"]
    rule = client.get(path + "/syncs", headers=auth_headers).json()[0]
    monkeypatch.setattr(
        BucketClient,
        "objects",
        lambda *a, **k: {"items": [], "next_cursor": "last-page"},
    )
    assert (
        client.post(path + f"/syncs/{rule['id']}/run", headers=auth_headers).status_code
        == 202
    )
    assert (
        client.get(
            f"/v1/gallery/{original['publication_id']}/media", headers=auth_headers
        ).status_code
        == 200
    )
    monkeypatch.setattr(
        BucketClient, "objects", lambda *a, **k: {"items": [], "next_cursor": None}
    )
    assert (
        client.post(path + f"/syncs/{rule['id']}/run", headers=auth_headers).status_code
        == 202
    )
    assert (
        client.get(
            f"/v1/gallery/{original['publication_id']}/media", headers=auth_headers
        ).status_code
        == 404
    )
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(StorageObject)).retired
