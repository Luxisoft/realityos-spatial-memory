from __future__ import annotations

import io
import uuid

from app.meta import MockMetaModelClient
from app.models import (
    ObjectObservation,
    ProcessingJob,
    Role,
    TrackedObject,
    User,
    WorkspaceMember,
)
from app.security import hash_password
from app.services import process_job
from PIL import Image
from sqlalchemy import select


def png_bytes() -> bytes:
    image = Image.new("RGB", (80, 60), color=(241, 198, 36))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def create_workspace(client, headers) -> str:
    response = client.post(
        "/v1/workspaces",
        headers=headers,
        json={"name": "Taller RealityOS", "description": "Taller de prueba"},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def register_and_process(client, headers, workspace_id: str) -> tuple[str, str]:
    zone = client.post(
        f"/v1/workspaces/{workspace_id}/zones",
        headers=headers,
        json={"name": "Bodega A", "kind": "zone"},
    )
    assert zone.status_code == 201, zone.text
    session = client.post(
        "/v1/sessions",
        headers=headers,
        json={
            "workspace_id": workspace_id,
            "zone_id": zone.json()["id"],
            "consent_confirmed": True,
        },
    )
    assert session.status_code == 201, session.text
    upload = client.post(
        "/v1/captures",
        headers=headers,
        data={"session_id": session.json()["id"]},
        files={"file": ("taladro_amarillo.png", png_bytes(), "image/png")},
    )
    assert upload.status_code == 201, upload.text
    capture_id = upload.json()["id"]
    job = client.post(f"/v1/captures/{capture_id}/process", headers=headers)
    assert job.status_code == 200, job.text
    with client.app.state.database.session_factory() as db:
        process_job(
            db, uuid.UUID(job.json()["id"]), MockMetaModelClient()
        )
        db.commit()
    return capture_id, job.json()["id"]


def test_health_and_authentication(client, auth_headers):
    assert client.get("/health/live").json() == {"status": "ok"}
    assert client.get("/health/ready").json() == {"status": "ready"}
    assert (
        client.get("/v1/auth/me", headers=auth_headers).json()["email"]
        == "admin@example.test"
    )


def test_capture_is_bytea_backed_and_hash_is_stable(client, auth_headers):
    workspace_id = create_workspace(client, auth_headers)
    capture_id, _ = register_and_process(client, auth_headers, workspace_id)
    original = client.get(f"/v1/media/{capture_id}", headers=auth_headers)
    assert original.status_code == 200
    assert original.content == png_bytes()
    capture = client.get(f"/v1/captures/{capture_id}", headers=auth_headers).json()
    assert len(capture["sha256"]) == 64
    assert capture["byte_size"] == len(original.content)


def test_query_returns_last_verified_evidence_and_highlight(client, auth_headers):
    workspace_id = create_workspace(client, auth_headers)
    capture_id, _ = register_and_process(client, auth_headers, workspace_id)
    result = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={
            "workspace_id": workspace_id,
            "question": "¿Dónde está el taladro amarillo?",
        },
    )
    assert result.status_code == 200, result.text
    answer = result.json()
    assert answer["found"] is True
    assert "was last seen" in answer["message"]
    assert answer["media_id"] == capture_id
    assert answer["simulated"] is True
    highlighted = client.get(answer["highlighted_media_url"], headers=auth_headers)
    assert highlighted.status_code == 200
    assert highlighted.headers["content-type"] == "image/png"
    assert highlighted.content != png_bytes()


def test_missing_query_and_query_role_cannot_capture(client, auth_headers):
    workspace_id = create_workspace(client, auth_headers)
    missing = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": workspace_id, "question": "¿Dónde está el casco rojo?"},
    )
    assert missing.status_code == 200
    assert missing.json()["found"] is False
    with client.app.state.database.session_factory() as db:
        query_user = User(
            email="query@example.test",
            display_name="Query User",
            password_hash=hash_password("AnotherSecurePass123!"),
        )
        db.add(query_user)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=__import__("uuid").UUID(workspace_id),
                user_id=query_user.id,
                role=Role.QUERY,
            )
        )
        db.commit()
    login = client.post(
        "/v1/auth/login",
        json={"email": "query@example.test", "password": "AnotherSecurePass123!"},
    ).json()
    query_headers = {"Authorization": f"Bearer {login['access_token']}"}
    denied = client.post(
        "/v1/sessions",
        headers=query_headers,
        json={"workspace_id": workspace_id, "consent_confirmed": True},
    )
    assert denied.status_code == 403


def test_workspaces_are_isolated(client, auth_headers):
    workspace_id = create_workspace(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        outsider = User(
            email="outsider@example.test",
            display_name="Outsider",
            password_hash=hash_password("OutsiderSecurePass123!"),
        )
        db.add(outsider)
        db.commit()
    login = client.post(
        "/v1/auth/login",
        json={"email": "outsider@example.test", "password": "OutsiderSecurePass123!"},
    ).json()
    response = client.get(
        f"/v1/workspaces/{workspace_id}/zones",
        headers={"Authorization": f"Bearer {login['access_token']}"},
    )
    assert response.status_code == 403


def test_processing_job_is_idempotent_and_records_mock_sam_geometry(client, auth_headers):
    workspace_id = create_workspace(client, auth_headers)
    capture_id, job_id = register_and_process(client, auth_headers, workspace_id)
    repeated = client.post(f"/v1/captures/{capture_id}/process", headers=auth_headers)
    assert repeated.status_code == 200
    assert repeated.json()["id"] == job_id
    with client.app.state.database.session_factory() as db:
        process_job(db, uuid.UUID(job_id), MockMetaModelClient())
        db.commit()
        job = db.get(ProcessingJob, uuid.UUID(job_id))
        observations = list(
            db.scalars(
                select(ObjectObservation).where(
                    ObjectObservation.media_asset_id == uuid.UUID(capture_id)
                )
            )
        )
    assert job is not None
    assert job.attempts == 1
    assert job.result_metadata["segmentation_count"] == 1
    assert len(observations) == 1
    assert observations[0].relationships == [{"relation": "on", "object": "black box"}]
    assert observations[0].model_name.endswith("+sam-3.1")


def test_object_search_uses_aliases_and_returns_ambiguity(client, auth_headers):
    workspace_id = create_workspace(client, auth_headers)
    _, _ = register_and_process(client, auth_headers, workspace_id)
    with client.app.state.database.session_factory() as db:
        drill = db.scalar(
            select(TrackedObject).where(TrackedObject.workspace_id == uuid.UUID(workspace_id))
        )
        assert drill is not None
        drill_id = str(drill.id)
        db.add(
            TrackedObject(
                workspace_id=uuid.UUID(workspace_id),
                canonical_name="blue drill",
                category="power tool",
            )
        )
        db.add(
            TrackedObject(
                workspace_id=uuid.UUID(workspace_id),
                canonical_name="perforadora",
                category="generated label collision",
            )
        )
        db.commit()
    alias_response = client.post(
        f"/v1/objects/{drill_id}/aliases",
        headers=auth_headers,
        json={"alias": "Perforadora"},
    )
    assert alias_response.status_code == 201, alias_response.text
    assert alias_response.json()["alias"] == "perforadora"
    by_alias = client.get(
        "/v1/objects",
        headers=auth_headers,
        params={"workspace_id": workspace_id, "q": "perforadora"},
    )
    assert by_alias.status_code == 200
    assert [item["canonical_name"] for item in by_alias.json()] == ["perforadora", "yellow drill"]
    answer_by_alias = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": workspace_id, "question": "Where is the perforadora?"},
    )
    assert answer_by_alias.status_code == 200
    assert answer_by_alias.json()["found"] is True
    assert answer_by_alias.json()["message"].startswith("Yellow drill was last seen")
    exact_alias_beats_broad_match = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": workspace_id, "question": "Where is the perforadora?"},
    )
    assert exact_alias_beats_broad_match.status_code == 200
    assert exact_alias_beats_broad_match.json()["ambiguous"] is False
    french = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": workspace_id, "question": "Où est la perceuse jaune ?"},
    )
    assert french.status_code == 200
    assert french.json()["found"] is True
    assert french.json()["object"]["canonical_name"] == "yellow drill"
    ambiguous = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": workspace_id, "question": "Where is the drill?"},
    )
    assert ambiguous.status_code == 200
    assert ambiguous.json()["ambiguous"] is True
