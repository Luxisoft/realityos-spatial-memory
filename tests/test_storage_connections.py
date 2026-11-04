import hashlib
import io
import uuid

import pytest
from app.models import User
from app.security import hash_password
from app.storage.client import BucketClient, check_key, endpoint_address
from app.storage.models import StorageConnection, StorageImport, StorageSync
from catalog_support import classification_for
from fastapi import HTTPException
from PIL import Image
from sqlalchemy import select
from storage_support import BASE, image_bytes
from storage_support import remote as remote  # noqa: PLC0414 -- pytest fixture export
from storage_support import source as source  # noqa: PLC0414 -- pytest fixture export


def test_import_retry_preserves_original_and_idempotency(
    client, auth_headers, source, remote
):
    path = BASE + "/" + source["id"] + "/imports"
    body = {
        "classifications": {
            key: classification_for(client, source["workspace_id"])
            for key in ["photos/a.png"]
        },
        "request_key": "first",
        "keys": ["photos/a.png"],
    }
    r = client.post(path, headers=auth_headers, json=body)
    assert r.status_code == 202, r.text
    assert r.json()["items"][0]["status"] == "published", r.text
    assert client.post(path, headers=auth_headers, json=body).json() == r.json()
    assert len(remote) == 1
    assert (
        client.post(
            path,
            headers=auth_headers,
            json={
                **body,
                "classifications": {
                    key: classification_for(client, source["workspace_id"])
                    for key in ["photos/b.png"]
                },
                "keys": ["photos/b.png"],
            },
        ).status_code
        == 409
    )
    later = client.post(
        path, headers=auth_headers, json={**body, "request_key": "second"}
    ).json()
    assert later["items"][0]["publication_id"] == r.json()["items"][0]["publication_id"]


def test_cancelled_duplicate_can_be_imported_again_without_losing_history(
    client, auth_headers, source, remote
):
    path = BASE + "/" + source["id"] + "/imports"

    def start(request_key, key):
        response = client.post(
            path,
            headers=auth_headers,
            json={
                "classifications": {
                    key: classification_for(client, source["workspace_id"])
                    for key in [key]
                },
                "request_key": request_key,
                "keys": [key],
            },
        )
        assert response.status_code == 202, response.text
        return response.json()

    start("original", "photos/a.png")
    cancelled_ids = []
    for attempt in range(2):
        run = start(f"cancel-{attempt}", "photos/b.png")
        item = run["items"][0]
        assert item["status"] == "duplicate"
        assert item["upload_id"] not in cancelled_ids
        cancelled_ids.append(item["upload_id"])
        assert (
            client.post(
                "/v1/me/publication-uploads/" + item["upload_id"] + "/cancel",
                headers=auth_headers,
            ).status_code
            == 200
        )
        # Replaying the same request must not restart a cancelled decision.
        replay = start(f"cancel-{attempt}", "photos/b.png")
        assert replay["items"][0]["status"] == "cancelled"

    fresh = start("fresh", "photos/b.png")
    item = fresh["items"][0]
    assert item["status"] == "duplicate" and item["upload_id"] not in cancelled_ids
    assert start("fresh", "photos/b.png") == fresh
    assert (
        start("another-request", "photos/b.png")["items"][0]["upload_id"]
        == item["upload_id"]
    )
    assert (
        client.post(
            "/v1/me/publication-uploads/" + item["upload_id"] + "/confirm",
            headers=auth_headers,
        ).status_code
        == 200
    )
    later = start("after-publication", "photos/b.png")
    assert later["status"] == "completed"
    assert later["items"][0]["upload_id"] == item["upload_id"]
    runs = client.get(path, headers=auth_headers).json()
    for previous in runs:
        if previous["items"][0]["upload_id"] in cancelled_ids:
            assert previous["items"][0]["status"] == "cancelled"


def test_confirmed_import_status_is_refreshed_without_writing_on_read(
    client, auth_headers, source, remote
):
    from app.social_features.evidence_models import PublicationUpload
    from sqlalchemy import event

    path = BASE + "/" + source["id"] + "/imports"
    client.post(
        path,
        headers=auth_headers,
        json={
            "classifications": {
                key: classification_for(client, source["workspace_id"])
                for key in ["photos/a.png"]
            },
            "request_key": "first",
            "keys": ["photos/a.png"],
        },
    )
    run = client.post(
        path,
        headers=auth_headers,
        json={
            "classifications": {
                key: classification_for(client, source["workspace_id"])
                for key in ["photos/b.png", "photos/c.png"]
            },
            "request_key": "duplicates",
            "keys": ["photos/b.png", "photos/c.png"],
        },
    ).json()
    with client.app.state.database.session_factory() as db:
        stored = db.get(StorageImport, uuid.UUID(run["id"]))
        original_items = stored.items
    for index, item in enumerate(run["items"]):
        # The second duplicate targets an older media revision; retry its analysis
        # through the existing upload API before confirming replacement.
        if index == 1:
            assert (
                client.post(
                    "/v1/me/publication-uploads/" + item["upload_id"] + "/retry",
                    headers=auth_headers,
                ).status_code
                == 200
            )
        assert (
            client.post(
                "/v1/me/publication-uploads/" + item["upload_id"] + "/confirm",
                headers=auth_headers,
            ).status_code
            == 200
        )
        statements = []
        engine = client.app.state.database.engine

        def record_sql(
            conn, cursor, statement, parameters, context, many, recorded=statements
        ):
            recorded.append(statement.lstrip().split()[0].upper())

        event.listen(engine, "before_cursor_execute", record_sql)
        try:
            result = next(
                r
                for r in client.get(path, headers=auth_headers).json()
                if r["id"] == run["id"]
            )
        finally:
            event.remove(engine, "before_cursor_execute", record_sql)
        assert not {"INSERT", "UPDATE", "DELETE"}.intersection(statements)
        assert result["status"] == ("attention" if index == 0 else "completed")
    with client.app.state.database.session_factory() as db:
        stored = db.get(StorageImport, uuid.UUID(run["id"]))
        assert stored.status == "attention"
        assert stored.items == original_items
        assert all(
            db.get(PublicationUpload, uuid.UUID(i["upload_id"])).status == "published"
            for i in stored.items
        )


def test_candidate_reuse_is_scoped_to_destination(client, auth_headers, source, remote):
    path = BASE + "/" + source["id"] + "/imports"
    ids = []
    for index in range(2):
        workspace = client.post(
            "/v1/workspaces", headers=auth_headers, json={"name": f"Group {index}"}
        ).json()["id"]
        result = client.post(
            path,
            headers=auth_headers,
            json={
                "classifications": {
                    key: classification_for(client, workspace)
                    for key in ["photos/a.png"]
                },
                "request_key": f"group-{index}",
                "keys": ["photos/a.png"],
                "workspace_id": workspace,
            },
        ).json()
        assert result["status"] == "completed"
        ids.append(result["items"][0]["upload_id"])
    assert len(set(ids)) == 2


def test_changed_remote_object_retires_previous_copy_and_reimports(
    client, auth_headers, source, monkeypatch
):
    from app.models import MediaAsset
    from app.social_features.models import Publication
    from PIL.PngImagePlugin import PngInfo

    original = image_bytes()
    metadata = PngInfo()
    metadata.add_text("version", "updated original")
    output = io.BytesIO()
    Image.open(io.BytesIO(original)).save(output, "PNG", pnginfo=metadata)
    changed = output.getvalue()
    current = [original]

    def download(bucket, key):
        check_key(bucket.connection, key)
        raw = current[0]
        return raw, "image/png", {"key": key, "sha256": hashlib.sha256(raw).hexdigest()}

    monkeypatch.setattr(BucketClient, "download", download)
    path = BASE + "/" + source["id"] + "/imports"

    def start(request_key):
        response = client.post(
            path,
            headers=auth_headers,
            json={
                "classifications": {
                    key: classification_for(client, source["workspace_id"])
                    for key in ["photos/a.png"]
                },
                "request_key": request_key,
                "keys": ["photos/a.png"],
            },
        )
        assert response.status_code == 202, response.text
        return response.json()["items"][0]

    first = start("original")
    assert first["status"] == "published"
    for request_key, raw in (("changed", changed), ("restored", original)):
        current[0] = raw
        item = start(request_key)
        assert item["status"] == "published"
        assert item["publication_id"] != first["publication_id"]
        with client.app.state.database.session_factory() as db:
            old = db.get(Publication, uuid.UUID(first["publication_id"]))
            assert old.hidden
            post = db.get(Publication, uuid.UUID(item["publication_id"]))
            assert db.get(MediaAsset, post.media_id).original_bytes == raw
        first = item
    again = start("unchanged")
    assert again["status"] == "published"
    assert again["publication_id"] == first["publication_id"]


def test_explicit_reimport_after_removal_creates_a_visible_publication(
    client, auth_headers, source, remote
):
    from app.social_features.models import Publication

    path = BASE + "/" + source["id"] + "/imports"
    body = {
        "classifications": {
            key: classification_for(client, source["workspace_id"])
            for key in ["photos/a.png"]
        },
        "request_key": "first",
        "keys": ["photos/a.png"],
    }
    first = client.post(path, headers=auth_headers, json=body).json()["items"][0]
    assert (
        client.post(
            "/v1/gallery/" + first["publication_id"] + "/remove",
            headers=auth_headers,
        ).status_code
        == 200
    )
    body["request_key"] = "explicit-reimport"
    response = client.post(path, headers=auth_headers, json=body)
    assert response.status_code == 202, response.text
    replacement = response.json()["items"][0]
    assert replacement["status"] == "published"
    assert replacement["publication_id"] != first["publication_id"]
    assert client.post(path, headers=auth_headers, json=body).json() == response.json()
    body["request_key"] = "unchanged"
    assert (
        client.post(path, headers=auth_headers, json=body).json()["items"][0][
            "publication_id"
        ]
        == replacement["publication_id"]
    )
    with client.app.state.database.session_factory() as db:
        assert db.get(Publication, uuid.UUID(first["publication_id"])).hidden
        assert not db.get(Publication, uuid.UUID(replacement["publication_id"])).hidden


@pytest.mark.parametrize(
    ("prefix", "encoded"),
    [
        ("photos/my pictures/", "photos%2Fmy%20pictures%2F"),
        ("photos/niño/", "photos%2Fni%C3%B1o%2F"),
        ("photos/a+b#%/", "photos%2Fa%2Bb%23%25%2F"),
    ],
)
def test_listing_signs_and_sends_the_same_s3_encoded_query(
    client, source, monkeypatch, prefix, encoded
):
    from datetime import UTC, datetime

    import httpx
    from botocore.auth import S3SigV4Auth
    from botocore.awsrequest import AWSRequest
    from botocore.credentials import Credentials

    monkeypatch.setattr(
        "botocore.auth.get_current_datetime", lambda: datetime(2026, 11, 3, tzinfo=UTC)
    )
    monkeypatch.setattr(
        "app.storage.client.endpoint_address",
        lambda url: ("storage.example", "1.1.1.1"),
    )
    query = f"list-type=2&prefix={encoded}&max-keys=100&encoding-type=url&delimiter=%2F&continuation-token=a%2Bb%2F%3D"
    expected = AWSRequest(
        method="GET",
        url="https://storage.example/my-bucket?" + query,
        headers={"Host": "storage.example"},
    )
    S3SigV4Auth(
        Credentials("private-access", "private-secret"), "s3", "us-east-1"
    ).add_auth(expected)
    seen = []

    def upstream(request):
        seen.append(request)
        assert request.url.host == "1.1.1.1"
        assert request.url.query.decode() == query
        assert request.headers["Host"] == "storage.example"
        assert request.headers["Authorization"] == expected.headers["Authorization"]
        assert request.extensions["sni_hostname"] == "storage.example"
        return httpx.Response(200, content=b"<ListBucketResult/>")

    original_client = httpx.Client
    monkeypatch.setattr(
        "app.storage.client.httpx.Client",
        lambda **kwargs: original_client(
            transport=httpx.MockTransport(upstream), **kwargs
        ),
    )
    with client.app.state.database.session_factory() as db:
        row = db.get(StorageConnection, uuid.UUID(source["id"]))
        assert (
            BucketClient(row, client.app.state.settings).objects(prefix, "a+b/=")[
                "items"
            ]
            == []
        )
    assert len(seen) == 1


def test_other_account_cannot_access_connections_or_media(
    client, auth_headers, source, remote
):
    with client.app.state.database.session_factory() as db:
        db.add(
            User(
                email="other@x.test",
                display_name="Other",
                password_hash=hash_password("VerySecurePass123!"),
            )
        )
        db.commit()
    token = client.post(
        "/v1/auth/login",
        json={"email": "other@x.test", "password": "VerySecurePass123!"},
    ).json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    assert client.get(BASE, headers=headers).json() == []
    for suffix in ["/objects", "/content?key=photos/a.png", "/imports", "/syncs"]:
        assert (
            client.get(BASE + "/" + source["id"] + suffix, headers=headers).status_code
            == 404
        )
    assert not remote


def test_destination_and_prefix_checked_before_download(
    client, auth_headers, source, remote
):
    path = BASE + "/" + source["id"] + "/imports"
    for body in [
        {"keys": ["photos-other/a.png"]},
        {"keys": ["photos/../private/a.png"]},
        {"keys": ["photos/./a.png"]},
        {
            "keys": ["photos/a.png"],
            "workspace_id": str(uuid.uuid4()),
        },
    ]:
        r = client.post(path, headers=auth_headers, json={"request_key": "bad", **body})
        assert r.status_code in {403, 404, 422}
    assert remote == []


def test_remote_content_ranges_are_private_and_bounded(
    client, auth_headers, source, remote
):
    path = BASE + "/" + source["id"] + "/content?key=photos/a.png"
    response = client.get(path, headers=auth_headers | {"Range": "bytes=2-8"})
    assert response.status_code == 206
    assert response.content == image_bytes()[2:9]
    assert response.headers["Content-Range"] == f"bytes 2-8/{len(image_bytes())}"
    assert response.headers["Cache-Control"] == "private, no-store"
    assert (
        client.get(path, headers=auth_headers | {"Range": "bytes=999999-"}).status_code
        == 416
    )


def test_disconnect_retires_copies_and_cancels_sync(
    client, auth_headers, source, remote
):
    path = BASE + "/" + source["id"]
    run = client.post(
        path + "/imports",
        headers=auth_headers,
        json={
            "classifications": {
                key: classification_for(client, source["workspace_id"])
                for key in ["photos/a.png"]
            },
            "request_key": "one",
            "keys": ["photos/a.png"],
        },
    ).json()
    client.post(path + "/syncs", headers=auth_headers, json={"enabled": True})
    assert client.request("DELETE", path, headers=auth_headers).status_code == 200
    assert client.get(path + "/objects", headers=auth_headers).status_code == 404
    with client.app.state.database.session_factory() as db:
        assert db.get(StorageImport, uuid.UUID(run["id"])).status == "completed"
        assert not db.scalar(select(StorageSync)).enabled
        assert db.get(StorageConnection, uuid.UUID(source["id"])).secret == ""


@pytest.mark.parametrize(
    "url",
    [
        "http://example.com",
        "https://user:pw@example.com",
        "https://example.com:8443",
        "https://example.com/path",
        "https://example.com?foo=1",
    ],
)
def test_unsafe_endpoint(url):
    with pytest.raises(HTTPException):
        endpoint_address(url)


def test_private_dns_and_mixed_answers_rejected(monkeypatch):
    monkeypatch.setattr(
        "socket.getaddrinfo",
        lambda *a, **kw: [(None, None, None, None, ("127.0.0.1", 443))],
    )
    with pytest.raises(HTTPException):
        endpoint_address("https://example.com")


def test_failed_download_is_retryable_without_extra_publication(
    client, auth_headers, source, remote, monkeypatch
):
    download = BucketClient.download

    def fail(*a):
        raise HTTPException(502, "secret upstream must not be stored")

    monkeypatch.setattr(BucketClient, "download", fail)
    path = BASE + "/" + source["id"] + "/imports"
    run = client.post(
        path,
        headers=auth_headers,
        json={
            "classifications": {
                key: classification_for(client, source["workspace_id"])
                for key in ["photos/a.png"]
            },
            "request_key": "retry",
            "keys": ["photos/a.png"],
        },
    ).json()
    assert run["status"] == "attention" and "secret upstream" not in str(run)
    monkeypatch.setattr(BucketClient, "download", download)
    r = client.post(path + "/" + run["id"] + "/retry", headers=auth_headers)
    assert r.status_code == 200, r.text
    assert r.json()["items"][0]["status"] == "published"


@pytest.mark.parametrize("queued", [False, True])
def test_sync_processes_and_reuses_unchanged_page(
    client, auth_headers, source, remote, monkeypatch, queued
):
    from app.storage.service import process_import

    client.app.state.settings.enqueue_processing = queued
    dispatched = []
    monkeypatch.setattr(
        "app.storage.service.dispatch", lambda run, settings: dispatched.append(run.id)
    )
    monkeypatch.setattr(
        BucketClient,
        "objects",
        lambda *a, **kw: {
            "items": [
                {
                    "key": "photos/a.png",
                    "etag": "one",
                    "size": 12,
                    "modified_at": "today",
                }
            ],
            "next_cursor": None,
        },
    )
    path = BASE + "/" + source["id"]
    rule = client.post(
        path + "/syncs", headers=auth_headers, json={"enabled": False}
    ).json()
    first = client.post(
        path + "/syncs/" + rule["id"] + "/run", headers=auth_headers
    ).json()
    if queued:
        assert (
            client.get(path + "/imports", headers=auth_headers).json()[0]["status"]
            == "pending"
        )
        assert not remote
        with client.app.state.database.session_factory() as db:
            process_import(db, uuid.UUID(first["import_id"]), client.app.state.settings)
    completed = client.get(path + "/imports", headers=auth_headers).json()[0]
    assert completed["id"] == first["import_id"]
    assert completed["status"] == "attention"
    assert completed["items"][0]["status"] == "awaiting_classification"
    assert not completed["items"][0]["publication_id"]
    second = client.post(
        path + "/syncs/" + rule["id"] + "/run", headers=auth_headers
    ).json()
    assert first["import_id"] == second["import_id"]
    assert len(remote) == 1
    assert dispatched == [uuid.UUID(first["import_id"])] * 2


def test_import_retry_uses_current_upload_status(
    client, auth_headers, source, remote, monkeypatch
):
    path = BASE + "/" + source["id"] + "/imports"
    client.post(
        path,
        headers=auth_headers,
        json={
            "classifications": {
                key: classification_for(client, source["workspace_id"])
                for key in ["photos/a.png"]
            },
            "request_key": "original",
            "keys": ["photos/a.png"],
        },
    )
    run = client.post(
        path,
        headers=auth_headers,
        json={
            "classifications": {
                key: classification_for(client, source["workspace_id"])
                for key in ["photos/b.png"]
            },
            "request_key": "duplicate",
            "keys": ["photos/b.png"],
        },
    ).json()
    item = run["items"][0]
    assert item["status"] == "duplicate"

    def fail_analysis(db, upload_id, meta):
        from app.social_features.evidence_models import PublicationUpload

        upload = db.get(PublicationUpload, upload_id)
        upload.status = "failed"
        upload.error = "Temporary analysis failure"

    # Retrying the duplicate from the upload dialog can fail independently of
    # the stored import snapshot. The import retry must recover that failure.
    with monkeypatch.context() as patch:
        patch.setattr("app.social_features.uploads.process_upload", fail_analysis)
        response = client.post(
            "/v1/me/publication-uploads/" + item["upload_id"] + "/retry",
            headers=auth_headers,
        )
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    refreshed = next(
        row
        for row in client.get(path, headers=auth_headers).json()
        if row["id"] == run["id"]
    )
    assert refreshed["items"][0]["status"] == "failed"
    attempts = len(remote)
    response = client.post(path + "/" + run["id"] + "/retry", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["items"][0]["status"] == "duplicate"
    assert len(remote) == attempts + 1


def test_sync_continues_pages_and_skips_documents(
    client, auth_headers, source, remote, monkeypatch
):
    seen = []

    def page(bucket, prefix, cursor, recursive):
        seen.append((prefix, cursor, recursive))
        keys = ["photos/a.png", "photos/cv.pdf"] if cursor is None else ["photos/b.png"]
        return {
            "items": [
                {"key": key, "etag": key, "size": 12, "modified_at": "today"}
                for key in keys
            ],
            "next_cursor": "page-two" if cursor is None else None,
        }

    monkeypatch.setattr(BucketClient, "objects", page)
    path = BASE + "/" + source["id"]
    rule = client.post(path + "/syncs", headers=auth_headers, json={}).json()
    first = client.post(path + "/syncs/" + rule["id"] + "/run", headers=auth_headers)
    second = client.post(path + "/syncs/" + rule["id"] + "/run", headers=auth_headers)
    assert first.status_code == second.status_code == 202
    assert first.json()["has_more"] and not second.json()["has_more"]
    assert first.json()["import_id"] != second.json()["import_id"]
    assert remote == ["photos/a.png", "photos/b.png"]
    assert seen == [("photos/", None, True), ("photos/", "page-two", True)]
    stored = client.get(path + "/syncs", headers=auth_headers).json()[0]
    assert stored["cursor"] is None
    assert not stored["enabled"]


def test_sync_rechecks_membership_before_listing(
    client, auth_headers, source, remote, monkeypatch
):
    from app.models import WorkspaceMember
    from sqlalchemy import delete

    workspace = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Temporary sync group"}
    ).json()["id"]
    path = BASE + "/" + source["id"]
    rule = client.post(
        path + "/syncs",
        headers=auth_headers,
        json={"workspace_id": workspace},
    ).json()
    with client.app.state.database.session_factory() as db:
        db.execute(
            delete(WorkspaceMember).where(
                WorkspaceMember.workspace_id == uuid.UUID(workspace)
            )
        )
        db.commit()
    monkeypatch.setattr(
        BucketClient, "objects", lambda *a, **kw: pytest.fail("Revoked group listed")
    )
    response = client.post(path + "/syncs/" + rule["id"] + "/run", headers=auth_headers)
    assert response.status_code == 403
    assert not remote
    assert client.get(path + "/imports", headers=auth_headers).json() == []


def test_membership_removed_after_download_prevents_publication(
    client, auth_headers, source, remote, monkeypatch
):
    from app.models import WorkspaceMember
    from sqlalchemy import delete

    workspace = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Temporary group"}
    ).json()["id"]
    original = BucketClient.download

    def revoked(bucket, key):
        result = original(bucket, key)
        with client.app.state.database.session_factory() as db:
            db.execute(
                delete(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == uuid.UUID(workspace)
                )
            )
            db.commit()
        return result

    monkeypatch.setattr(BucketClient, "download", revoked)
    result = client.post(
        BASE + "/" + source["id"] + "/imports",
        headers=auth_headers,
        json={
            "classifications": {
                key: classification_for(client, workspace) for key in ["photos/a.png"]
            },
            "request_key": "revoked",
            "keys": ["photos/a.png"],
            "workspace_id": workspace,
        },
    ).json()
    assert result["items"][0]["status"] == "failed"
    assert not result["items"][0].get("publication_id")


def test_content_preview_is_ephemeral(client, auth_headers, source, remote):
    from app.models import MediaAsset
    from sqlalchemy import func

    response = client.get(
        BASE + "/" + source["id"] + "/content?key=photos/a.png&preview=true",
        headers=auth_headers,
    )
    assert (
        response.status_code == 200
        and response.headers["cache-control"] == "private, no-store"
    )
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(MediaAsset)) == 0


def test_download_uses_head_precondition_and_limits(
    client, auth_headers, source, monkeypatch
):
    calls = []

    def request(self, method, key, **kwargs):
        calls.append((method, kwargs))
        return (b"" if method == "HEAD" else b"image"), {
            "content-length": "5",
            "etag": '"a"',
        }

    monkeypatch.setattr(BucketClient, "request", request)
    with client.app.state.database.session_factory() as db:
        row = db.get(StorageConnection, uuid.UUID(source["id"]))
        bucket = BucketClient(row, client.app.state.settings)
        raw, mime, metadata = bucket.download("photos/a.png")
        assert raw == b"image" and mime == "image/png"
        assert calls[1][1]["etag"] == '"a"'
        assert metadata["sha256"] == hashlib.sha256(raw).hexdigest()


def test_listing_pagination_unicode_and_xml_rejection(
    client, auth_headers, source, monkeypatch
):
    xml = b'<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Contents><Key>photos%2Fni%C3%B1o.png</Key><Size>12</Size><ETag>one</ETag><LastModified>today</LastModified></Contents><NextContinuationToken>opaque</NextContinuationToken></ListBucketResult>'
    monkeypatch.setattr(BucketClient, "request", lambda *a, **kw: (xml, {}))
    path = BASE + "/" + source["id"] + "/objects"
    r = client.get(path, headers=auth_headers)
    assert r.json()["items"][0]["key"] == "photos/niño.png"
    assert r.json()["next_cursor"] == "opaque"
    xml = b'<!DOCTYPE x [<!ENTITY test "bad">]><x/>'
    assert client.get(path, headers=auth_headers).status_code == 502


def test_s3_transport_pins_ip_but_signs_hostname(
    client, auth_headers, source, monkeypatch
):
    from contextlib import contextmanager

    seen = {}

    class Reply:
        status_code = 200

        def __init__(self):
            self.headers = {"content-length": "2"}

        def iter_bytes(self):
            yield b"ok"

    class Transport:
        def __init__(self, **kwargs):
            assert kwargs["follow_redirects"] is False and kwargs["trust_env"] is False

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        @contextmanager
        def stream(self, method, url, **kwargs):
            seen.update(url=url, **kwargs)
            yield Reply()

    monkeypatch.setattr(
        "app.storage.client.endpoint_address",
        lambda endpoint: ("storage.example", "1.1.1.1"),
    )
    monkeypatch.setattr("app.storage.client.httpx.Client", Transport)
    with client.app.state.database.session_factory() as db:
        row = db.get(StorageConnection, uuid.UUID(source["id"]))
        BucketClient(row, client.app.state.settings).request("GET", "photos/niño.png")
    assert seen["url"].host == "1.1.1.1"
    assert seen["headers"]["Host"] == "storage.example"
    assert seen["headers"]["Authorization"].startswith("AWS4-HMAC-SHA256 ")
    assert seen["extensions"]["sni_hostname"] == "storage.example"


def test_scheduler_recovers_expired_jobs_but_respects_pause_and_live_lease(
    client, auth_headers, source, remote, monkeypatch
):
    from datetime import timedelta

    from app.storage import tasks
    from app.storage.service import now, process_import

    path = BASE + "/" + source["id"]
    jobs = []
    for index in range(3):
        result = client.post(
            path + "/imports",
            headers=auth_headers,
            json={
                "classifications": {
                    key: classification_for(client, source["workspace_id"])
                    for key in ["photos/a.png"]
                },
                "request_key": f"recovery-{index}",
                "keys": ["photos/a.png"],
            },
        ).json()
        jobs.append(uuid.UUID(result["id"]))
    client.post(path + "/syncs", headers=auth_headers, json={"enabled": False})
    with client.app.state.database.session_factory() as db:
        for index, job_id in enumerate(jobs):
            job = db.get(StorageImport, job_id)
            job.status = "pending" if index == 0 else "running"
            job.lease_until = now() + timedelta(minutes=-1 if index == 1 else 30)
        db.commit()
        count = len(remote)
        process_import(db, jobs[2], client.app.state.settings)
        assert len(remote) == count
    dispatched = []
    monkeypatch.setattr(tasks, "get_settings", lambda: client.app.state.settings)
    monkeypatch.setattr(
        tasks, "dispatch", lambda run, settings: dispatched.append(run.id)
    )
    monkeypatch.setattr(
        tasks, "sync_page", lambda *args: pytest.fail("Paused rule executed")
    )
    tasks.storage_tick()
    assert set(dispatched) == set(jobs[:2])


def test_invalid_credentials_are_never_echoed_in_validation_response(
    client, auth_headers
):
    response = client.post(
        BASE,
        headers=auth_headers,
        json={
            "name": "Invalid",
            "endpoint": "https://example.com",
            "bucket": "demo-bucket",
            "access_key": "secret-that-must-not-return",
        },
    )
    assert response.status_code == 422
    assert "secret-that-must-not-return" not in response.text
    assert "input" not in response.json()["detail"][0]


@pytest.mark.parametrize("disconnect", [False, True])
def test_connection_operations_remain_available_during_analysis(
    client, auth_headers, source, remote, monkeypatch, disconnect
):
    from app.models import MediaAsset
    from app.social_features.evidence_models import PublicationUpload
    from app.social_features.models import Publication
    from app.storage import service
    from sqlalchemy import func

    path = BASE + "/" + source["id"]
    process = service.process_upload
    responses = []

    def analyze(db, upload_id, meta):
        # A second request uses an independent DB session while the provider
        # call is in flight. The import must not hold its connection lock here.
        if disconnect:
            response = client.request("DELETE", path, headers=auth_headers)
        else:
            client.app.state.settings.enqueue_processing = True
            try:
                response = client.post(
                    path + "/imports",
                    headers=auth_headers,
                    json={
                        "classifications": {
                            key: classification_for(client, source["workspace_id"])
                            for key in ["photos/b.png"]
                        },
                        "request_key": "queued",
                        "keys": ["photos/b.png"],
                    },
                )
            finally:
                client.app.state.settings.enqueue_processing = False
        responses.append(response.status_code)
        return process(db, upload_id, meta)

    monkeypatch.setattr(service, "process_upload", analyze)
    monkeypatch.setattr("app.storage.routes.dispatch", lambda *args: None)
    result = client.post(
        path + "/imports",
        headers=auth_headers,
        json={
            "classifications": {
                key: classification_for(client, source["workspace_id"])
                for key in ["photos/a.png"]
            },
            "request_key": "processing",
            "keys": ["photos/a.png"],
        },
    )
    assert responses == [200 if disconnect else 202]
    assert result.status_code == 202
    assert result.json()["items"][0]["status"] == (
        "cancelled" if disconnect else "published"
    )
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(Publication)) == (
            0 if disconnect else 1
        )
        assert db.scalar(select(func.count()).select_from(MediaAsset)) == (
            0 if disconnect else 1
        )
        upload = db.scalar(select(PublicationUpload))
        assert upload.status == ("cancelled" if disconnect else "published")
