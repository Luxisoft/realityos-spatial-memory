import io
import uuid

from app.models import (
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from catalog_support import classification_for, classified_destination, published_item
from PIL import Image

from .support import (
    _chat_append,
    _guest_headers,
    _wav_bytes,
)


def test_transcribe_maps_missing_speech_to_422(client, auth_headers, monkeypatch):
    from app import meta as meta_module

    class SilentClient:
        def transcribe_wav(self, audio):
            raise meta_module.MetaProviderError(
                "Muse Voice Transcribe returned no transcript."
            )

    monkeypatch.setattr(
        meta_module, "build_meta_client", lambda settings: SilentClient()
    )
    response = client.post(
        "/v1/notes/transcribe",
        headers=auth_headers,
        files={"audio": ("nota.wav", _wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 422, response.text
    assert "speech" in response.json()["detail"]


def test_publications_accept_voice_or_text_notes(client, auth_headers):
    output = io.BytesIO()
    Image.new("RGB", (48, 32), "yellow").save(output, format="PNG")

    invalid = client.post(
        "/v1/me/publication-uploads",
        headers=auth_headers,
        files={"file": ("nota.png", output.getvalue(), "image/png")},
        data={
            "note_text": "Hola",
            "note_source": "carrier-pigeon",
            "request_key": str(uuid.uuid4()),
        },
    )
    assert invalid.status_code == 422, invalid.text

    response = client.post(
        "/v1/me/publication-uploads",
        headers=auth_headers,
        files={"file": ("nota.png", output.getvalue(), "image/png")},
        data={
            "note_text": "Revisar el cableado",
            "note_source": "text",
            **classified_destination(client, auth_headers, "Notes group"),
            "request_key": str(uuid.uuid4()),
        },
    )
    assert response.status_code == 202, response.text
    assert (
        published_item(client, auth_headers, response)["note_text"]
        == "Revisar el cableado"
    )
    assert published_item(client, auth_headers, response)["note_source"] == "text"

    with client.app.state.database.session_factory() as db:
        owner = db.query(User).first()
        workspace = Workspace(name="Taller con notas", created_by_id=owner.id)
        db.add(workspace)
        db.flush()
        db.add(
            WorkspaceMember(
                workspace_id=workspace.id, user_id=owner.id, role=Role.ADMIN
            )
        )
        db.commit()
        workspace_id = str(workspace.id)

    spoken = client.post(
        "/v1/me/publication-uploads",
        headers=auth_headers,
        files={"file": ("nota.png", output.getvalue(), "image/png")},
        data={
            "workspace_id": workspace_id,
            **classification_for(client, workspace_id, multipart=True),
            "note_text": "Motor cambiado en el turno nocturno",
            "note_source": "voice",
            "request_key": str(uuid.uuid4()),
        },
    )
    assert spoken.status_code == 202, spoken.text
    assert (
        published_item(client, auth_headers, spoken)["note_text"]
        == "Motor cambiado en el turno nocturno"
    )
    assert published_item(client, auth_headers, spoken)["note_source"] == "voice"


def test_chat_history_pages_newest_first_per_profile(client, auth_headers):
    for index in range(12):
        role = "user" if index % 2 == 0 else "ai"
        _chat_append(client, auth_headers, role, f"turno {index}")
    first = client.get("/v1/chat/history?limit=10", headers=auth_headers)
    assert first.status_code == 200, first.text
    page = first.json()
    assert page["has_more"] is True
    assert [row["text"] for row in page["messages"]] == [
        f"turno {index}" for index in range(11, 1, -1)
    ]
    oldest = page["messages"][-1]["id"]
    second = client.get(
        f"/v1/chat/history?limit=10&before_id={oldest}", headers=auth_headers
    )
    rest = second.json()
    assert rest["has_more"] is False
    assert [row["text"] for row in rest["messages"]] == ["turno 1", "turno 0"]


def test_chat_history_is_isolated_between_profiles(client, auth_headers):
    _chat_append(client, auth_headers, "user", "hola muse")
    guest = _guest_headers(client, "chat-history-guest")
    assert client.get("/v1/chat/history", headers=guest).json()["messages"] == []
    _chat_append(client, guest, "user", "pregunta invitada")
    mine = client.get("/v1/chat/history", headers=auth_headers).json()["messages"]
    assert [row["text"] for row in mine] == ["hola muse"]
    theirs = client.get("/v1/chat/history", headers=guest).json()["messages"]
    assert [row["text"] for row in theirs] == ["pregunta invitada"]


def test_chat_audio_roundtrip_and_isolation(client, auth_headers):
    message_id = _chat_append(client, auth_headers, "user", "nota de voz")
    first = client.request(
        "POST",
        "/v1/chat/audio",
        headers=auth_headers,
        data={"message_id": str(message_id), "duration_ms": "1200"},
        files={"audio": ("voz.m4a", b"fake-audio-bytes", "audio/mp4")},
    )
    assert first.status_code == 200, first.text
    second = client.request(
        "POST",
        "/v1/chat/audio",
        headers=auth_headers,
        data={"message_id": str(message_id), "duration_ms": "800"},
        files={"audio": ("voz2.m4a", b"more-bytes", "audio/mp4")},
    )
    assert second.status_code == 200, second.text

    page = client.get("/v1/chat/history", headers=auth_headers).json()["messages"]
    assert len(page[0]["audio_urls"]) == 2
    assert page[0]["audio_duration_ms"] == 2000

    heard = client.get(page[0]["audio_urls"][0], headers=auth_headers)
    assert heard.status_code == 200
    assert heard.content == b"fake-audio-bytes"

    guest = _guest_headers(client, "chat-audio-guest")
    assert client.get(page[0]["audio_urls"][0], headers=guest).status_code == 404
    assert (
        client.request(
            "POST",
            "/v1/chat/audio",
            headers=guest,
            data={"message_id": str(message_id)},
            files={"audio": ("x.m4a", b"zz", "audio/mp4")},
        ).status_code
        == 404
    )
    assert (
        client.request(
            "POST",
            "/v1/chat/audio",
            headers=auth_headers,
            data={"message_id": "999999"},
            files={"audio": ("x.m4a", b"zz", "audio/mp4")},
        ).status_code
        == 404
    )


def test_notes_merge_drops_boundary_repetitions(client, auth_headers):
    merged = client.post(
        "/v1/notes/merge",
        headers=auth_headers,
        json={
            "texts": [
                "hola cómo estás estás",
                "estás buscando el martillo",
                "el martillo rojo",
            ]
        },
    )
    assert merged.status_code == 200, merged.text
    assert merged.json()["text"] == "hola cómo estás estás buscando el martillo rojo"
    single = client.post(
        "/v1/notes/merge", headers=auth_headers, json={"texts": ["  solo una  "]}
    )
    assert single.json()["text"] == "solo una"
    assert (
        client.post(
            "/v1/notes/merge", headers=auth_headers, json={"texts": []}
        ).status_code
        == 422
    )


def test_chat_append_validates_turns(client, auth_headers):
    assert (
        client.post(
            "/v1/chat/append", headers=auth_headers, json={"role": "user", "text": ""}
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/v1/chat/append",
            headers=auth_headers,
            json={"role": "system", "text": "hola"},
        ).status_code
        == 422
    )


def test_chat_history_preserves_gallery_and_simulated(client, auth_headers):
    gallery = [
        {
            "thumbnail_url": "/v1/gallery/x/thumbnail",
            "media_url": "/v1/gallery/x/media",
            "caption": "taladro",
            "boxed_url": "/v1/gallery/x/boxed?labels=taladro",
            "image_url": "/v1/gallery/evidence/x?labels=taladro&full_size=true",
            "match_kind": "family",
            "localization_quality": "approximate_box",
        }
    ]
    response = client.post(
        "/v1/chat/append",
        headers=auth_headers,
        json={
            "role": "ai",
            "kind": "text",
            "text": "Encontré 1 foto",
            "gallery": gallery,
            "simulated": True,
        },
    )
    assert response.status_code == 200, response.text
    rows = client.get("/v1/chat/history", headers=auth_headers).json()["messages"]
    assert rows[0]["gallery"] == gallery
    assert rows[0]["simulated"] is True


def test_chat_append_sanitizes_null_text_leaks(client, auth_headers):
    response = client.post(
        "/v1/chat/append",
        headers=auth_headers,
        json={
            "role": "ai",
            "kind": "text",
            "text": "hola",
            "evidence_url": "null",
            "gallery": [
                {
                    "thumbnail_url": "null",
                    "media_url": "null",
                    "caption": "x",
                    "boxed_url": "null",
                }
            ],
        },
    )
    assert response.status_code == 200, response.text
    rows = client.get("/v1/chat/history", headers=auth_headers).json()["messages"]
    assert rows[0]["evidence_url"] is None
    assert rows[0]["gallery"] == []


def test_chat_history_preserves_quick_replies_and_face_action(client, auth_headers):
    replies = [
        {"id": "ask_person", "label": "Persona"},
        {"id": "ask_object", "label": "Objeto"},
    ]
    response = client.post(
        "/v1/chat/append",
        headers=auth_headers,
        json={
            "role": "ai",
            "kind": "text",
            "text": "¿Buscas una persona o un objeto?",
            "quick_replies": replies,
            "face_action": True,
        },
    )
    assert response.status_code == 200, response.text
    rows = client.get("/v1/chat/history", headers=auth_headers).json()["messages"]
    assert rows[0]["quick_replies"] == replies
    assert rows[0]["face_action"] is True
