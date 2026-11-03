import io

from app.models import Role, User, WorkspaceMember
from app.security import hash_password
from PIL import Image


def setup_source(client, auth_headers, name="Hospital"):
    workspace = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": name}
    ).json()["id"]
    result = client.post(
        f"/v1/workspaces/{workspace}/connections",
        headers=auth_headers,
        json={"name": "Clinical source"},
    )
    assert result.status_code == 201, result.text
    return (
        workspace,
        result.json(),
        {"X-RealityOS-Integration-Key": result.json()["integration_key"]},
    )


def batch(version=1, key="batch1", status="active"):
    return {
        "request_key": key,
        "records": [
            {
                "external_id": "patient1",
                "kind": "person",
                "title": "Patient One",
                "version": version,
                "status": status,
                "authorized": True,
                "occurred_at": "2026-11-01T12:00:00Z",
                "data": {"identifier": "P001"},
                "simulated": True,
            }
        ],
    }


def test_import_idempotency_notes_versions_and_tombstones(client, auth_headers):
    ws, _connection, headers = setup_source(client, auth_headers)
    response = client.post("/v1/integrations/imports", headers=headers, json=batch())
    assert response.status_code == 200, response.text
    record = response.json()["records"][0]["id"]
    assert (
        client.post("/v1/integrations/imports", headers=headers, json=batch()).json()
        == response.json()
    )
    assert (
        client.post(
            "/v1/integrations/imports", headers=headers, json=batch(2)
        ).status_code
        == 409
    )
    note = client.post(
        f"/v1/workspaces/{ws}/records/{record}/notes",
        headers=auth_headers,
        json={"text": "Local observation", "occurred_at": "2026-11-01T13:00:00Z"},
    )
    assert note.status_code == 201, note.text
    assert (
        client.post(
            "/v1/integrations/imports", headers=headers, json=batch(2, "batch2")
        ).status_code
        == 200
    )
    detail = client.get(
        f"/v1/workspaces/{ws}/records/{record}", headers=auth_headers
    ).json()
    assert detail["notes"][0]["text"] == "Local observation"
    assert (
        len(
            client.get(
                f"/v1/workspaces/{ws}/records/{record}/revisions", headers=auth_headers
            ).json()
        )
        == 2
    )
    assert (
        client.post(
            "/v1/integrations/imports",
            headers=headers,
            json=batch(3, "batch3", "deleted"),
        ).status_code
        == 200
    )
    assert client.get(f"/v1/workspaces/{ws}/records", headers=auth_headers).json() == []


def test_media_and_records_cannot_cross_workspaces(client, auth_headers):
    ws, _, headers = setup_source(client, auth_headers)
    other, _, other_headers = setup_source(client, auth_headers, "Other")
    record = client.post(
        "/v1/integrations/imports", headers=headers, json=batch()
    ).json()["records"][0]["id"]
    raw = io.BytesIO()
    Image.new("RGB", (20, 20), "blue").save(raw, format="PNG")
    path = f"/v1/integrations/records/{record}/media"
    assert (
        client.post(
            path,
            headers=other_headers,
            data={"external_id": "photo"},
            files={"file": ("photo.png", raw.getvalue(), "image/png")},
        ).status_code
        == 404
    )
    uploaded = client.post(
        path,
        headers=headers,
        data={"external_id": "photo"},
        files={"file": ("photo.png", raw.getvalue(), "image/png")},
    )
    assert uploaded.status_code == 201, uploaded.text
    media_id = uploaded.json()["id"]
    detail = client.get(
        f"/v1/workspaces/{ws}/records/{record}", headers=auth_headers
    ).json()
    assert detail["media"][0]["mime_type"] == "image/png"
    media_url = detail["media"][0]["url"]
    partial = client.get(media_url, headers=auth_headers | {"Range": "bytes=0-7"})
    assert partial.status_code == 206
    assert partial.content == raw.getvalue()[:8]
    assert partial.headers["Content-Range"] == f"bytes 0-7/{len(raw.getvalue())}"
    assert (
        client.get(
            media_url, headers=auth_headers | {"Range": "bytes=99999-"}
        ).status_code
        == 416
    )
    assert (
        client.get(
            f"/v1/workspaces/{other}/record-media/{media_id}", headers=auth_headers
        ).status_code
        == 404
    )
    with client.app.state.database.session_factory() as db:
        user = User(
            email="outsider@example.test",
            display_name="Outsider",
            password_hash=hash_password("SecurePassword123!"),
        )
        db.add(user)
        db.flush()
        import uuid

        db.add(
            WorkspaceMember(
                workspace_id=uuid.UUID(other), user_id=user.id, role=Role.QUERY
            )
        )
        db.commit()
    token = client.post(
        "/v1/auth/login",
        json={"email": "outsider@example.test", "password": "SecurePassword123!"},
    ).json()["access_token"]
    assert (
        client.get(
            f"/v1/workspaces/{ws}/records", headers={"Authorization": "Bearer " + token}
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/v1/workspaces/{ws}/record-media/{media_id}",
            headers={"Authorization": "Bearer " + token},
        ).status_code
        == 403
    )


def test_unresolved_reference_atomic_and_credential_revocation(client, auth_headers):
    ws, connection, headers = setup_source(client, auth_headers)
    payload = batch()
    payload["records"][0]["related_ids"] = ["missing"]
    assert (
        client.post(
            "/v1/integrations/imports", headers=headers, json=payload
        ).status_code
        == 422
    )
    assert client.get(f"/v1/workspaces/{ws}/records", headers=auth_headers).json() == []
    assert (
        client.request(
            "DELETE",
            f"/v1/workspaces/{ws}/connections/{connection['id']}",
            headers=auth_headers,
        ).status_code
        == 200
    )
    assert (
        client.post(
            "/v1/integrations/imports", headers=headers, json=batch()
        ).status_code
        == 401
    )


def test_record_search_never_uses_another_workspace_or_facebook(
    client, auth_headers, monkeypatch
):
    ws, _, headers = setup_source(client, auth_headers)
    _other, _, other_headers = setup_source(client, auth_headers, "Private team")
    assert (
        client.post(
            "/v1/integrations/imports", headers=headers, json=batch()
        ).status_code
        == 200
    )
    private = batch()
    private["records"][0]["title"] = "Private Patient One"
    assert (
        client.post(
            "/v1/integrations/imports", headers=other_headers, json=private
        ).status_code
        == 200
    )
    from app.providers.contracts import ProfileAnswer

    def answer(self, question, candidates, language=None):
        assert len(candidates) == 1
        assert candidates[0]["name"] == "Patient One"
        assert "Private" not in str(candidates)
        return ProfileAnswer(
            text="Patient One, patient1", matched_user_ids=[], simulated=True
        )

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.answer_profile_question", answer
    )
    response = client.post(
        f"/v1/workspaces/{ws}/records/search",
        headers=auth_headers,
        json={"question": "Patient One", "language": "es"},
    )
    assert response.status_code == 200, response.text
    assert len(response.json()["records"]) == 1


def test_medication_check_reports_discrepancy_and_missing_data_without_writing(
    client, auth_headers
):
    ws, _, headers = setup_source(client, auth_headers)
    payload = batch()
    rx = {
        **payload["records"][0],
        "external_id": "rx1",
        "kind": "prescription",
        "title": "Test prescription",
        "related_ids": ["patient1"],
        "data": {
            "ingredient": "DEMO",
            "concentration": "10 mg",
            "state": "active",
            "valid_from": "2026-11-01T00:00:00Z",
            "valid_until": "2026-12-01T00:00:00Z",
        },
    }
    payload["records"].append(rx)
    result = client.post(
        "/v1/integrations/imports", headers=headers, json=payload
    ).json()
    person, prescription = [r["id"] for r in result["records"]]
    response = client.post(
        f"/v1/workspaces/{ws}/records/{person}/medication-check",
        headers=auth_headers,
        json={
            "prescription_id": prescription,
            "observed_ingredient": "DEMO",
            "observed_concentration": "20 mg",
            "checked_at": "2026-11-02T12:00:00Z",
            "patient_confirmed": False,
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert "concentration_mismatch" in body["issues"]
    assert "patient_confirmation" in body["missing"]
    assert not body["administration_recorded"]
    assert (
        len(client.get(f"/v1/workspaces/{ws}/records", headers=auth_headers).json())
        == 2
    )


def test_query_role_cannot_add_notes_or_manage_sources(client, auth_headers):
    ws, _, headers = setup_source(client, auth_headers)
    record = client.post(
        "/v1/integrations/imports", headers=headers, json=batch()
    ).json()["records"][0]["id"]
    import uuid

    with client.app.state.database.session_factory() as db:
        viewer = User(
            email="viewer@example.test",
            display_name="Viewer",
            password_hash=hash_password("SecurePassword123!"),
        )
        db.add(viewer)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=uuid.UUID(ws), user_id=viewer.id, role=Role.QUERY
            )
        )
        db.commit()
    token = client.post(
        "/v1/auth/login",
        json={"email": "viewer@example.test", "password": "SecurePassword123!"},
    ).json()["access_token"]
    h = {"Authorization": "Bearer " + token}
    assert (
        client.get(f"/v1/workspaces/{ws}/records/{record}", headers=h).status_code
        == 200
    )
    assert client.get(f"/v1/workspaces/{ws}/connections", headers=h).status_code == 403
    assert (
        client.post(
            f"/v1/workspaces/{ws}/records/{record}/notes",
            headers=h,
            json={"text": "No", "occurred_at": "2026-11-02T12:00:00Z"},
        ).status_code
        == 403
    )


def test_pull_sources_reject_unapproved_hosts(client, auth_headers):
    ws = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Safe source"}
    ).json()["id"]
    for url in (
        "http://127.0.0.1",
        "https://127.0.0.1",
        "https://example.com",
        "file:///etc/passwd",
    ):
        assert (
            client.post(
                f"/v1/workspaces/{ws}/connections",
                headers=auth_headers,
                json={"name": "Unapproved", "source_url": url},
            ).status_code
            == 422
        )


def test_pull_sync_encrypts_credentials_and_uses_real_contract(
    client, auth_headers, monkeypatch
):
    import httpx
    from app.workspaces.models import Connection

    settings = client.app.state.settings
    settings.integration_source_hosts = "source.example"
    from pydantic import SecretStr

    settings.integration_encryption_key = SecretStr("isolated-test-encryption-material")
    monkeypatch.setattr(
        "app.workspaces.sync.socket.getaddrinfo",
        lambda *args, **kwargs: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    original = httpx.AsyncClient
    requests = []

    def upstream(request):
        requests.append(request)
        assert request.headers["Authorization"] == "Bearer private-source-token"
        assert "X-RealityOS-Integration-Key" not in request.headers
        return httpx.Response(200, json=batch())

    def factory(*args, **kwargs):
        if "transport" not in kwargs:
            kwargs["transport"] = httpx.MockTransport(upstream)
        return original(*args, **kwargs)

    monkeypatch.setattr("app.workspaces.sync.httpx.AsyncClient", factory)
    ws = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Pull source"}
    ).json()["id"]
    response = client.post(
        f"/v1/workspaces/{ws}/connections",
        headers=auth_headers,
        json={
            "name": "Clinical feed",
            "source_url": "https://source.example/batch",
            "source_token": "private-source-token",
        },
    )
    assert response.status_code == 201, response.text
    assert "private-source-token" not in response.text
    import uuid

    with client.app.state.database.session_factory() as db:
        connection = db.get(Connection, uuid.UUID(response.json()["id"]))
        assert (
            connection.secret_encrypted
            and "private-source-token" not in connection.secret_encrypted
        )
    path = f"/v1/workspaces/{ws}/connections/{response.json()['id']}/sync"
    first = client.post(path, headers=auth_headers)
    assert first.status_code == 200, first.text
    assert client.post(path, headers=auth_headers).json() == first.json()
    assert len(requests) == 2
    assert (
        len(client.get(f"/v1/workspaces/{ws}/records", headers=auth_headers).json())
        == 1
    )
