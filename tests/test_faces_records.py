import io
import uuid

from app.faces import MockFaceEngine
from app.models import Role, User, WorkspaceMember
from app.security import create_access_token, hash_password
from PIL import Image


def _png(color: str, size=(64, 48)) -> bytes:
    output = io.BytesIO()
    Image.new("RGB", size, color).save(output, format="PNG")
    return output.getvalue()


def _single_face_png() -> bytes:
    engine = MockFaceEngine()
    for color in ("blue", "red", "green", "black", "white", "yellow", "cyan", "magenta"):
        for size in ((64, 48), (80, 60), (96, 72), (48, 48)):
            data = _png(color, size)
            if len(engine.detect_faces(data)) == 1:
                return data
    raise AssertionError("No single-face fixture found for the mock engine")


def _setup_workspace(client, auth_headers, name="Clinic"):
    workspace = client.post("/v1/workspaces", headers=auth_headers, json={"name": name}).json()["id"]
    connection = client.post(
        f"/v1/workspaces/{workspace}/connections",
        headers=auth_headers,
        json={"name": "Clinical source"},
    )
    assert connection.status_code == 201, connection.text
    key = connection.json()["integration_key"]
    return workspace, {"X-RealityOS-Integration-Key": key}


def _person_batch(key="face-batch-1", biometric=True):
    record: dict = {
        "external_id": "patient-face-1",
        "kind": "person",
        "title": "Ana Solis",
        "version": 1,
        "status": "active",
        "authorized": True,
        "occurred_at": "2026-11-01T12:00:00Z",
        "data": {"identifier": "P001"},
        "simulated": True,
    }
    if biometric:
        record["biometric_authorized"] = True
        record["biometric_basis"] = "jury-test-consent"
    return {"request_key": key, "records": [record]}


def _consent(client, headers):
    response = client.post("/v1/faces/consent", headers=headers, json={"confirm": True})
    assert response.status_code == 200, response.text


def test_verify_identity_pending_without_facebook_not_failed(client, auth_headers):
    _consent(client, auth_headers)
    data = _single_face_png()
    enrolled = client.request(
        "POST",
        "/v1/faces/profile-photo",
        headers=auth_headers,
        files={"file": ("face.png", data, "image/png")},
    )
    assert enrolled.status_code == 201, enrolled.text
    for _ in range(3):
        response = client.post("/v1/faces/verify-identity", headers=auth_headers)
        assert response.status_code == 200, response.text
        assert response.json()["status"] == "pending"
        assert response.json()["verified"] is False


def test_import_biometric_validation_and_preservation(client, auth_headers):
    workspace, headers = _setup_workspace(client, auth_headers)
    payload = _person_batch()
    payload["records"][0]["kind"] = "object"
    assert client.post("/v1/integrations/imports", headers=headers, json=payload).status_code == 422
    payload = _person_batch()
    del payload["records"][0]["biometric_basis"]
    assert client.post("/v1/integrations/imports", headers=headers, json=payload).status_code == 422
    assert (
        client.post("/v1/integrations/imports", headers=headers, json=_person_batch()).status_code
        == 200
    )
    rows = client.get(f"/v1/workspaces/{workspace}/records", headers=auth_headers).json()
    assert rows[0]["biometric_authorized"] is True
    assert rows[0]["biometric_basis"] == "jury-test-consent"
    # Absent biometric fields preserve the stored decision on reimport.
    update = _person_batch(key="face-batch-2")
    update["records"][0]["version"] = 2
    del update["records"][0]["biometric_authorized"]
    del update["records"][0]["biometric_basis"]
    assert (
        client.post("/v1/integrations/imports", headers=headers, json=update).status_code == 200
    )
    rows = client.get(f"/v1/workspaces/{workspace}/records", headers=auth_headers).json()
    assert rows[0]["biometric_authorized"] is True


def test_record_enroll_search_isolation_and_lifecycle(client, auth_headers):
    workspace, headers = _setup_workspace(client, auth_headers)
    other, other_headers = _setup_workspace(client, auth_headers, "Other clinic")
    record_id = (
        client.post("/v1/integrations/imports", headers=headers, json=_person_batch())
        .json()["records"][0]["id"]
    )
    other_id = (
        client.post("/v1/integrations/imports", headers=other_headers, json=_person_batch())
        .json()["records"][0]["id"]
    )
    _consent(client, auth_headers)
    data = _single_face_png()
    uploaded = client.post(
        f"/v1/integrations/records/{record_id}/media",
        headers=headers,
        data={"external_id": "portrait"},
        files={"file": ("portrait.png", data, "image/png")},
    )
    assert uploaded.status_code == 201, uploaded.text
    link_id = uploaded.json()["id"]
    enrolled = client.post(
        "/v1/faces/record-enroll",
        headers=auth_headers,
        json={"record_id": record_id, "record_media_id": link_id},
    )
    assert enrolled.status_code == 201, enrolled.text
    assert enrolled.json()["faces_enrolled"] == 1
    enrollment_id = enrolled.json()["enrollment_ids"][0]
    listed = client.get(
        f"/v1/faces/record-enrollments?workspace_id={workspace}", headers=auth_headers
    )
    assert listed.status_code == 200, listed.text
    assert len(listed.json()) == 1
    # Search finds the record in its own workspace with the same probe bytes.
    found = client.request(
        "POST",
        "/v1/faces/search",
        headers=auth_headers,
        data={"workspace_id": workspace},
        files={"probe": ("probe.png", data, "image/png")},
    )
    assert found.status_code == 200, found.text
    body = found.json()
    assert body["matches_records"][0]["record_id"] == record_id
    assert body["matches_records"][0]["similarity"] == 1.0
    assert body["matches_records"][0]["record_url"].endswith(f"/records/{record_id}")
    assert body["found"] is True
    # Other workspace cannot see this enrollment.
    missing = client.request(
        "POST",
        "/v1/faces/search",
        headers=auth_headers,
        data={"workspace_id": other},
        files={"probe": ("probe.png", data, "image/png")},
    )
    assert missing.json()["matches_records"] == []
    assert (
        client.get(
            f"/v1/faces/record-enrollments?workspace_id={other}", headers=auth_headers
        ).json()
        == []
    )
    # Outsider without membership is rejected.
    with client.app.state.database.session_factory() as db:
        outsider = User(
            email="record-outsider@example.test",
            display_name="Outsider",
            password_hash=hash_password("SecurePassword123!"),
        )
        db.add(outsider)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=uuid.UUID(other), user_id=outsider.id, role=Role.QUERY
            )
        )
        db.commit()
        outsider_id = outsider.id
    outsider_headers = {
        "Authorization": "Bearer "
        + create_access_token(outsider_id, client.app.state.settings)
    }
    _consent(client, outsider_headers)
    assert (
        client.request(
            "POST",
            "/v1/faces/search",
            headers=outsider_headers,
            data={"workspace_id": workspace},
            files={"probe": ("probe.png", data, "image/png")},
        ).status_code
        == 403
    )
    assert (
        client.get(
            f"/v1/faces/record-enrollments?workspace_id={workspace}", headers=outsider_headers
        ).status_code
        == 403
    )
    # Thumbnail requires membership and record authorization.
    thumb = client.get(
        f"/v1/faces/record-enrollments/{enrollment_id}/thumbnail", headers=auth_headers
    )
    assert thumb.status_code == 200, thumb.text
    assert thumb.headers["content-type"] == "image/jpeg"
    assert (
        client.get(
            f"/v1/faces/record-enrollments/{enrollment_id}/thumbnail", headers=outsider_headers
        ).status_code
        == 403
    )
    # Deleting the record hides it from search without deleting notes.
    note = client.post(
        f"/v1/workspaces/{workspace}/records/{record_id}/notes",
        headers=auth_headers,
        json={"text": "Local observation", "occurred_at": "2026-11-01T13:00:00Z"},
    )
    assert note.status_code == 201, note.text
    tombstone = _person_batch(key="face-batch-3")
    tombstone["records"][0]["version"] = 2
    tombstone["records"][0]["status"] = "deleted"
    del tombstone["records"][0]["biometric_authorized"]
    del tombstone["records"][0]["biometric_basis"]
    assert (
        client.post("/v1/integrations/imports", headers=headers, json=tombstone).status_code == 200
    )
    gone = client.request(
        "POST",
        "/v1/faces/search",
        headers=auth_headers,
        data={"workspace_id": workspace},
        files={"probe": ("probe.png", data, "image/png")},
    ).json()
    assert gone["matches_records"] == []
    assert (
        client.get(
            f"/v1/faces/record-enrollments/{enrollment_id}/thumbnail", headers=auth_headers
        ).status_code
        == 403
    )
    assert other_id != record_id


def test_record_enroll_requires_authorization_and_consent(client, auth_headers):
    workspace, headers = _setup_workspace(client, auth_headers)
    payload = _person_batch(biometric=False)
    record_id = (
        client.post("/v1/integrations/imports", headers=headers, json=payload)
        .json()["records"][0]["id"]
    )
    data = _single_face_png()
    uploaded = client.post(
        f"/v1/integrations/records/{record_id}/media",
        headers=headers,
        data={"external_id": "portrait"},
        files={"file": ("portrait.png", data, "image/png")},
    )
    link_id = uploaded.json()["id"]
    # Without biometric consent the enroll route is forbidden.
    assert (
        client.post(
            "/v1/faces/record-enroll",
            headers=auth_headers,
            json={"record_id": record_id, "record_media_id": link_id},
        ).status_code
        == 403
    )
    _consent(client, auth_headers)
    # Without record authorization the enroll route requires a basis.
    assert (
        client.post(
            "/v1/faces/record-enroll",
            headers=auth_headers,
            json={"record_id": record_id, "record_media_id": link_id},
        ).status_code
        == 409
    )
    authorized = client.post(
        "/v1/faces/record-enroll",
        headers=auth_headers,
        json={
            "record_id": record_id,
            "record_media_id": link_id,
            "biometric_basis": "nurse-confirmed-consent",
        },
    )
    assert authorized.status_code == 201, authorized.text
    rows = client.get(f"/v1/workspaces/{workspace}/records", headers=auth_headers).json()
    assert rows[0]["biometric_authorized"] is True
    assert rows[0]["biometric_basis"] == "nurse-confirmed-consent"
