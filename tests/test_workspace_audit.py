"""Regression cases found by auditing the complete workspace delivery."""

import io
import uuid
from datetime import UTC, datetime, timedelta

from app.models import User
from app.workspaces.models import Connection, Record
from PIL import Image
from test_workspace_imports import batch, setup_source


def test_inactive_connection_owner_cannot_ingest(client, auth_headers):
    _, source, headers = setup_source(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        connection = db.get(Connection, uuid.UUID(source["id"]))
        db.get(User, connection.created_by_id).is_active = False
        db.commit()
    assert (
        client.post(
            "/v1/integrations/imports", headers=headers, json=batch()
        ).status_code
        == 401
    )


def test_person_search_includes_related_history_and_notes_only_in_its_source(
    client, auth_headers, monkeypatch
):
    ws, _, headers = setup_source(client, auth_headers)
    _, _, other_headers = setup_source(client, auth_headers, "Other workspace")
    payload = batch()
    payload["records"].append(
        {
            **payload["records"][0],
            "external_id": "visit1",
            "kind": "event",
            "title": "Follow-up",
            "related_ids": ["person1"],
            "data": {"note": "Recorded follow-up observation"},
        }
    )
    rows = client.post(
        "/v1/integrations/imports", headers=headers, json=payload
    ).json()["records"]
    client.post("/v1/integrations/imports", headers=other_headers, json=batch())
    client.post(
        f"/v1/workspaces/{ws}/records/{rows[1]['id']}/notes",
        headers=auth_headers,
        json={
            "text": "Notebook kept in cabinet Delta",
            "occurred_at": "2026-11-02T12:00:00Z",
        },
    )
    from app.providers.contracts import ProfileAnswer

    calls = []

    def answer(self, question, candidates, language=None):
        calls.append(candidates)
        return ProfileAnswer(
            text="Supplied context", matched_user_ids=[], simulated=True
        )

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.answer_profile_question", answer
    )
    response = client.post(
        f"/v1/workspaces/{ws}/records/search",
        headers=auth_headers,
        json={"question": "Person One"},
    )
    assert response.status_code == 200
    assert {c["name"] for c in calls[-1]} == {"Person One", "Follow-up"}
    assert "cabinet Delta" in str(calls[-1])
    response = client.post(
        f"/v1/workspaces/{ws}/records/search",
        headers=auth_headers,
        json={"question": "cabinet Delta"},
    )
    assert response.status_code == 200
    assert "cabinet Delta" in str(calls[-1]) and len(calls) == 2


def test_search_can_find_a_matching_record_older_than_500_newer_records(
    client, auth_headers, monkeypatch
):
    ws, source, _ = setup_source(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        now = datetime.now(UTC)
        for i in range(501):
            db.add(
                Record(
                    workspace_id=uuid.UUID(ws),
                    connection_id=uuid.UUID(source["id"]),
                    external_id=f"r{i}",
                    kind="object",
                    title="UniqueChronometer" if i == 0 else "Notebook",
                    data={},
                    related_ids=[],
                    status="active",
                    version=1,
                    occurred_at=now + timedelta(minutes=i),
                    updated_at=now,
                )
            )
        db.commit()
    from app.providers.contracts import ProfileAnswer

    def answer(self, question, candidates, language=None):
        assert [c["name"] for c in candidates] == ["UniqueChronometer"]
        return ProfileAnswer(
            text="UniqueChronometer", matched_user_ids=[], simulated=True
        )

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.answer_profile_question", answer
    )
    response = client.post(
        f"/v1/workspaces/{ws}/records/search",
        headers=auth_headers,
        json={"question": "UniqueChronometer"},
    )
    assert response.status_code == 200
    assert len(response.json()["records"]) == 1


def test_attachment_detects_actual_format_and_preserves_retry_author(
    client, auth_headers, monkeypatch
):
    ws, _source, headers = setup_source(client, auth_headers)
    record = client.post(
        "/v1/integrations/imports", headers=headers, json=batch()
    ).json()["records"][0]["id"]
    raw = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(raw, format="GIF")
    path = f"/v1/integrations/records/{record}/media"
    assert (
        client.post(
            path,
            headers=headers,
            data={"external_id": "bad"},
            files={"file": ("a.png", raw.getvalue(), "image/png")},
        ).status_code
        == 422
    )
    monkeypatch.setattr("app.tasks.index_gallery_media.delay", lambda *a: None)
    raw = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(raw, format="PNG")
    created = client.post(
        path,
        headers=headers,
        data={"external_id": "good", "publish": "true"},
        files={"file": ("a.png", raw.getvalue(), "image/png")},
    )
    assert created.status_code == 201
    from app.models import Role, WorkspaceMember
    from app.security import hash_password

    with client.app.state.database.session_factory() as db:
        person = User(
            email="second-author@example.test",
            display_name="Second author",
            password_hash=hash_password("SecurePassword123!"),
        )
        db.add(person)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=uuid.UUID(ws), user_id=person.id, role=Role.REGISTER
            )
        )
        other = str(person.id)
        db.commit()
    changed = client.post(
        path,
        headers=headers,
        data={"external_id": "good", "publish": "true", "author_id": other},
        files={"file": ("a.png", raw.getvalue(), "image/png")},
    )
    assert changed.status_code == 409


def test_record_pagination_and_inactive_records(client, auth_headers):
    ws, source, _ = setup_source(client, auth_headers)
    with client.app.state.database.session_factory() as db:
        now = datetime.now(UTC)
        for i in range(55):
            db.add(
                Record(
                    workspace_id=uuid.UUID(ws),
                    connection_id=uuid.UUID(source["id"]),
                    external_id=f"r{i}",
                    kind="case",
                    title=f"Case {i}",
                    status="active" if i < 54 else "deleted",
                    version=1,
                    occurred_at=now,
                    updated_at=now,
                )
            )
        db.commit()
    first = client.get(f"/v1/workspaces/{ws}/records", headers=auth_headers).json()
    second = client.get(
        f"/v1/workspaces/{ws}/records?offset=50", headers=auth_headers
    ).json()
    assert len(first) == 50 and len(second) == 4
    assert not ({r["id"] for r in first} & {r["id"] for r in second})


def test_pull_pins_public_address_and_rechecks_revocation(
    client, auth_headers, monkeypatch
):
    import httpx
    from pydantic import SecretStr

    settings = client.app.state.settings
    settings.integration_source_hosts = "source.example"
    settings.integration_encryption_key = SecretStr("test-key-not-production")
    monkeypatch.setattr(
        "app.workspaces.sync.socket.getaddrinfo",
        lambda *a, **k: [(2, 1, 6, "", ("93.184.216.34", 443))],
    )
    ws = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Pinned source"}
    ).json()["id"]
    response = client.post(
        f"/v1/workspaces/{ws}/connections",
        headers=auth_headers,
        json={
            "name": "Feed",
            "source_url": "https://source.example/records",
            "source_token": "synthetic-token",
        },
    )
    source_id = response.json()["id"]
    original = httpx.AsyncClient

    def upstream(request):
        assert request.url.host == "93.184.216.34"
        assert request.headers["Host"] == "source.example"
        assert request.extensions["sni_hostname"] == "source.example"
        with client.app.state.database.session_factory() as db:
            db.get(Connection, uuid.UUID(source_id)).active = False
            db.commit()
        return httpx.Response(200, json=batch())

    def factory(*args, **kwargs):
        if "transport" not in kwargs:
            kwargs["transport"] = httpx.MockTransport(upstream)
        return original(*args, **kwargs)

    monkeypatch.setattr("app.workspaces.sync.httpx.AsyncClient", factory)
    response = client.post(
        f"/v1/workspaces/{ws}/connections/{source_id}/sync", headers=auth_headers
    )
    assert response.status_code == 401
    assert client.get(f"/v1/workspaces/{ws}/records", headers=auth_headers).json() == []


def test_invalid_source_port_is_validation_error(client, auth_headers):
    ws, _, _ = setup_source(client, auth_headers)
    assert (
        client.post(
            f"/v1/workspaces/{ws}/connections",
            headers=auth_headers,
            json={"name": "Invalid URL", "source_url": "https://source.example:bad/"},
        ).status_code
        == 422
    )


def test_related_context_respects_provider_budget_and_reports_partial(
    client, auth_headers, monkeypatch
):
    ws, _, headers = setup_source(client, auth_headers)
    payload = batch()
    payload["records"] += [
        {
            **payload["records"][0],
            "external_id": f"visit{i}",
            "title": f"Follow-up {i}",
            "kind": "event",
            "related_ids": ["person1"],
        }
        for i in range(10)
    ]
    client.post("/v1/integrations/imports", headers=headers, json=payload)
    from app.providers.contracts import ProfileAnswer

    def answer(self, question, candidates, language=None):
        assert len(candidates) == 8
        assert "partial" in question
        assert candidates[0]["name"] == "Person One"
        assert any(c["name"].startswith("Follow-up") for c in candidates)
        return ProfileAnswer(
            text="Partial recorded context", matched_user_ids=[], simulated=True
        )

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.answer_profile_question", answer
    )
    r = client.post(
        f"/v1/workspaces/{ws}/records/search",
        headers=auth_headers,
        json={"question": "Person One"},
    )
    assert r.status_code == 200
    assert r.json()["context_truncated"]
