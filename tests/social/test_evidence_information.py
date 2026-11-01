"""Display localization is authorized, read-only, and independent of geometry."""

import json
import uuid
from types import SimpleNamespace

import pytest
from app.config import Settings
from app.meta import MetaProviderError
from app.models import User, Workspace
from app.providers.live import LiveMetaModelClient
from app.providers.mock import MockMetaModelClient
from app.security import create_access_token
from app.social_features.evidence import search_evidence
from app.social_features.evidence_models import GalleryEvidence
from app.social_features.legacy_evidence import repair_image
from app.social_features.localizations import prepare_posts
from app.social_features.models import Publication
from sqlalchemy import event, select

from .test_search_recovery import legacy, setup

URL = "/v1/gallery/evidence/information"


def prepare(client):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        post = legacy(
            db, user, workspace, caption="Workshop", note_text="Keep on shelf 2"
        )
        assert repair_image(db, post)
        prepare_posts(db, [post], MockMetaModelClient())
        eid = db.scalar(select(GalleryEvidence.id))
        db.commit()
        return post.id, str(eid)


def payload(eid, language="es"):
    return {
        "language": language,
        "items": [{"evidence_id": eid, "labels": ["crimping tool"]}],
    }


@pytest.mark.parametrize(
    "language,title,note,label",
    [
        ("es-CO", "Taller", "Guardar en el estante 2", "crimpadora"),
        ("en-US", "Workshop", "Keep on shelf 2", "crimping tool"),
    ],
)
def test_information_localizes_without_writes(
    client, auth_headers, language, title, note, label
):
    pid, eid = prepare(client)
    writes = []

    def statement(conn, cursor, sql, parameters, context, executemany):
        if sql.lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")):
            writes.append(sql)

    engine = client.app.state.database.engine
    event.listen(engine, "before_cursor_execute", statement)
    try:
        response = client.post(URL, headers=auth_headers, json=payload(eid, language))
    finally:
        event.remove(engine, "before_cursor_execute", statement)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["language"] == language[:2] and body["simulated"]
    assert body["items"] == [
        {
            "evidence_id": eid,
            "title": title,
            "note_text": note,
            "matched_labels": [label],
        }
    ]
    assert not writes
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, pid)
        evidence = db.get(GalleryEvidence, uuid.UUID(eid))
        assert post.caption == "Workshop" and post.note_text == "Keep on shelf 2"
        assert evidence.detections[0]["label"] == "crimping tool"
    assert (
        client.get(
            f"/v1/gallery/evidence/{eid}?labels=crimping%20tool&full_size=true",
            headers=auth_headers,
        ).status_code
        == 200
    )


def test_information_requires_auth_and_authorizes_whole_batch_before_provider(
    client, auth_headers, monkeypatch
):
    _, eid = prepare(client)
    assert client.post(URL, json=payload(eid)).status_code == 401
    called = []
    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.translate_gallery_texts",
        lambda *args: called.append(True),
    )
    with client.app.state.database.session_factory() as db:
        workspace = db.scalar(select(Workspace))
        other = User(
            email="private-info@test.invalid",
            display_name="Other",
            password_hash="unused",
        )
        db.add(other)
        db.flush()
        post = legacy(db, other, workspace, color="blue")
        assert repair_image(db, post)
        secret = str(
            db.scalar(
                select(GalleryEvidence.id).where(GalleryEvidence.post_id == post.id)
            )
        )
        db.commit()
    request = payload(eid)
    request["items"].append({"evidence_id": secret, "labels": ["crimping tool"]})
    assert client.post(URL, headers=auth_headers, json=request).status_code == 404
    assert not called


def test_membership_revocation_removes_information_access(client, auth_headers):
    from app.models import WorkspaceMember

    pid, eid = prepare(client)
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, pid)
        workspace = db.scalar(select(Workspace))
        viewer = User(
            email="info-member@test.invalid",
            display_name="Member",
            password_hash="unused",
        )
        db.add(viewer)
        db.flush()
        from app.models import Role

        member = WorkspaceMember(
            workspace_id=workspace.id, user_id=viewer.id, role=Role.QUERY
        )
        db.add(member)
        post.audience = "work"
        post.workspace_id = workspace.id
        token = create_access_token(viewer.id, client.app.state.settings)
        uid, wid = viewer.id, workspace.id
        db.commit()
    headers = {"Authorization": "Bearer " + token}
    assert client.post(URL, headers=headers, json=payload(eid)).status_code == 200
    with client.app.state.database.session_factory() as db:
        db.delete(
            db.scalar(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == wid, WorkspaceMember.user_id == uid
                )
            )
        )
        db.commit()
    assert client.post(URL, headers=headers, json=payload(eid)).status_code == 403


def test_missing_labels_bounds_and_hidden_resources(client, auth_headers):
    pid, eid = prepare(client)
    bad = payload(eid)
    bad["items"][0]["labels"] = ["invented label"]
    assert client.post(URL, headers=auth_headers, json=bad).status_code == 404
    too_many = payload(eid)
    too_many["items"] *= 7
    assert client.post(URL, headers=auth_headers, json=too_many).status_code == 422
    assert (
        client.post(
            URL, headers=auth_headers, json=payload(str(uuid.uuid4()))
        ).status_code
        == 404
    )
    with client.app.state.database.session_factory() as db:
        db.get(Publication, pid).hidden = True
        db.commit()
    assert client.post(URL, headers=auth_headers, json=payload(eid)).status_code == 404


def test_read_never_calls_provider_and_missing_translation_is_pending(
    client, auth_headers, monkeypatch
):
    pid, eid = prepare(client)

    def forbidden(*args, **kwargs):
        raise AssertionError("Viewer must not call a model")

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.prepare_gallery_languages", forbidden
    )
    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.translate_gallery_texts", forbidden
    )
    assert (
        client.post(URL, headers=auth_headers, json=payload(eid)).json()["status"]
        == "ready"
    )
    with client.app.state.database.session_factory() as db:
        db.get(Publication, pid).note_text = "A new untranslated note"
        db.commit()
    response = client.post(URL, headers=auth_headers, json=payload(eid)).json()
    assert response["status"] == "pending" and response["items"] == []


def test_new_opening_reads_updated_note_and_target_language(client, auth_headers):
    pid, eid = prepare(client)
    first = client.post(URL, headers=auth_headers, json=payload(eid)).json()
    assert first["items"][0]["note_text"] == "Guardar en el estante 2"
    with client.app.state.database.session_factory() as db:
        post = db.get(Publication, pid)
        post.note_text = "Guardar en el estante 2"
        prepare_posts(db, [post], MockMetaModelClient())
        db.commit()
    second = client.post(URL, headers=auth_headers, json=payload(eid, "en")).json()
    assert second["items"][0]["note_text"] == "Keep on shelf 2"


def test_live_translation_uses_responses_and_rejects_unstructured_output(monkeypatch):
    model = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_gateway_base_url="https://example.invalid/v1",
            meta_gateway_token="fixture",
        )
    )
    captured = []

    def request(method, route, **kwargs):
        assert method == "POST" and route == "responses"
        captured.append(kwargs["json"])
        return SimpleNamespace(json=dict)

    monkeypatch.setattr(model, "_request", request)
    monkeypatch.setattr(model, "_output_text", lambda _: '{"label":"crimpadora"}')
    assert model.translate_gallery_texts({"label": "crimping tool"}, "es") == {
        "label": "crimpadora"
    }
    assert (
        captured[0]["store"] is False
        and json.loads(captured[0]["input"])["language"] == "es"
    )
    monkeypatch.setattr(model, "_output_text", lambda _: '{"unknown":"invented"}')
    with pytest.raises(MetaProviderError):
        model.translate_gallery_texts({"label": "crimping tool"}, "es")


def test_global_confidence_order_applies_before_result_limit(client):
    with client.app.state.database.session_factory() as db:
        user, workspace = setup(db)
        exact = legacy(db, user, workspace, "pliers", "blue")
        exact.ai_detections = [{**exact.ai_detections[0], "confidence": 0.71}]
        family = legacy(db, user, workspace, "crimping tool", "green")
        similar = legacy(db, user, workspace, "clamp", "red")
        similar.ai_detections = [{**similar.ai_detections[0], "confidence": 0.99}]
        db.flush()
        for post in (exact, family, similar):
            assert repair_image(db, post)
        result = search_evidence(db, user, "alicate", None, limit=2)
        assert [r["confidence"] for r in result.matches] == [0.99, 0.97]
        assert [r["match_kind"] for r in result.matches] == ["similar", "family"]
