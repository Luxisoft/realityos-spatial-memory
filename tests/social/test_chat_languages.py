"""Regression: Spanish selected, spoken pliers/hammer requests returned English."""

import io

import pytest
from app.models import Role, User, Workspace, WorkspaceMember
from app.query_lang import qtext
from app.social_features.models import ChatMessage, ChatMessageTranslation
from PIL import Image
from sqlalchemy import func, select

from .support import _guest_headers, _wav_bytes


def preference(client, headers, language, initialize=False):
    return client.request(
        "PATCH",
        "/v1/me/preferences" + ("?initialize=true" if initialize else ""),
        headers=headers,
        json={"preferred_language": language},
    )


def workspace(client):
    with client.app.state.database.session_factory() as db:
        owner = db.scalar(select(User).where(User.email == "admin@example.test"))
        space = Workspace(name="Language workshop", created_by_id=owner.id)
        db.add(space)
        db.flush()
        db.add(
            WorkspaceMember(workspace_id=space.id, user_id=owner.id, role=Role.ADMIN)
        )
        db.commit()
        return str(space.id)


def old_message(client, text, role="ai", **kwargs):
    with client.app.state.database.session_factory() as db:
        user = db.scalar(select(User).where(User.email == "admin@example.test"))
        row = ChatMessage(user_id=user.id, role=role, text=text, **kwargs)
        db.add(row)
        db.commit()
        return row.id


def test_preference_is_owned_normalized_and_initialization_never_overwrites(
    client, auth_headers
):
    assert client.get("/v1/me/preferences", headers=auth_headers).json() == {
        "preferred_language": None
    }
    assert (
        preference(client, auth_headers, "es-CO").json()["preferred_language"] == "es"
    )
    assert (
        preference(client, auth_headers, "en", initialize=True).json()[
            "preferred_language"
        ]
        == "es"
    )
    assert preference(client, auth_headers, "xx").status_code == 422
    guest = _guest_headers(client, "language-other-account")
    assert (
        client.get("/v1/me/preferences", headers=guest).json()["preferred_language"]
        is None
    )
    assert client.get("/v1/me/preferences").status_code == 401
    assert preference(client, auth_headers, "en").json()["preferred_language"] == "en"


@pytest.mark.parametrize(
    "question",
    [
        "Buenos días, necesito que por favor me ayudes a buscar un alicate.",
        "Aunque sabes qué, mejor quiero un martillo, un martillo. Ayúdeme a buscar un martillo, por favor.",
        "Please find my hammer",
    ],
)
def test_account_spanish_overrides_old_english_request(client, auth_headers, question):
    wid = workspace(client)
    preference(client, auth_headers, "es")
    response = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": wid, "question": question, "language": "en"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["response_language"] == "es"
    assert response.json()["message"] == qtext("es", "no_evidence")
    assert response.json()["tts_text"] == response.json()["message"]
    guest = _guest_headers(client, "language-workspace-isolation")
    assert (
        client.post(
            "/v1/queries",
            headers=guest,
            json={"workspace_id": wid, "question": question},
        ).status_code
        == 403
    )


def test_legacy_explicit_language_still_works_and_audio_uses_account(
    client, auth_headers
):
    wid = workspace(client)
    response = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": wid, "question": "hammer", "language": "es"},
    )
    assert response.json()["response_language"] == "es"
    preference(client, auth_headers, "es")
    response = client.post(
        "/v1/queries/audio",
        headers=auth_headers,
        data={"workspace_id": wid, "language": "en"},
        files={"audio": ("voice.wav", _wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["response_language"] == "es"
    preference(client, auth_headers, "en")
    response = client.post(
        "/v1/queries",
        headers=auth_headers,
        json={"workspace_id": wid, "question": "busca martillo", "language": "es"},
    )
    assert response.json()["message"] == qtext("en", "no_evidence")


def test_image_empty_analysis_resolves_account_language(
    client, auth_headers, monkeypatch
):
    from app.providers.mock import MockMetaModelClient
    from app.schemas import ImageAnalysis

    monkeypatch.setattr(
        MockMetaModelClient,
        "analyze_image",
        lambda *args, **kwargs: ImageAnalysis(
            model="mock", simulated=True, detections=[]
        ),
    )
    wid = workspace(client)
    preference(client, auth_headers, "es")
    output = io.BytesIO()
    Image.new("RGB", (20, 20)).save(output, "PNG")
    response = client.post(
        "/v1/queries/image",
        headers=auth_headers,
        data={"workspace_id": wid, "language": "en"},
        files={"image": ("probe.png", output.getvalue(), "image/png")},
    )
    assert response.status_code == 200, response.text
    assert response.json()["message"] == qtext("es", "no_visual_info")
    assert response.json()["response_language"] == "es"


def test_old_template_history_is_spanish_without_model_and_preparation_is_durable(
    client, auth_headers, monkeypatch
):
    mid = old_message(client, qtext("en", "gallery_related", count=4))
    uid = old_message(client, "Please find my hammer", role="user")
    preference(client, auth_headers, "es")
    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.prepare_gallery_languages",
        lambda *args: pytest.fail("Template must not call a provider"),
    )
    page = client.get("/v1/chat/history", headers=auth_headers).json()["messages"]
    assert next(row for row in page if row["id"] == mid)["localized_text"] == qtext(
        "es", "gallery_related", count=4
    )
    assert (
        next(row for row in page if row["id"] == uid)["localized_text"]
        == "Please find my hammer"
    )
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(ChatMessageTranslation)) == 0
    result = client.post(
        "/v1/chat/history/prepare", headers=auth_headers, json={"message_ids": [mid]}
    )
    assert result.status_code == 200, result.text
    with client.app.state.database.session_factory() as db:
        assert db.scalar(select(func.count()).select_from(ChatMessageTranslation)) == 2
        assert db.get(ChatMessage, mid).text == qtext("en", "gallery_related", count=4)
    preference(client, auth_headers, "en")
    assert client.get(
        f"/v1/chat/history/translations?ids={mid}", headers=auth_headers
    ).json()["messages"][0]["localized_text"] == qtext("en", "gallery_related", count=4)


def test_free_text_translation_persists_both_languages_and_retries_failure(
    client, auth_headers, monkeypatch
):
    mid = old_message(
        client,
        "The hammer was last seen near shelf 2.",
        quick_replies=[{"id": "custom", "label": "Show shelf"}],
    )
    preference(client, auth_headers, "es")
    calls = []

    def broken(*args):
        raise RuntimeError("Provider unavailable")

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.prepare_gallery_languages", broken
    )
    response = client.post(
        "/v1/chat/history/prepare", headers=auth_headers, json={"message_ids": [mid]}
    )
    assert response.json()["messages"][0]["translation_status"] == "failed"
    assert response.json()["messages"][0]["localized_text"] is None

    def translate(self, texts):
        calls.append(texts)
        return {
            "en": texts,
            "es": {
                "message": "El martillo fue visto por última vez cerca del estante 2.",
                "reply_0": "Mostrar estante",
            },
        }

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.prepare_gallery_languages", translate
    )
    for _ in range(2):
        response = client.post(
            "/v1/chat/history/prepare",
            headers=auth_headers,
            json={"message_ids": [mid]},
        )
        assert response.json()["messages"][0]["translation_status"] == "ready"
        assert response.json()["messages"][0]["localized_quick_replies"] == [
            {"id": "custom", "label": "Mostrar estante"}
        ]
    assert len(calls) == 1
    with client.app.state.database.session_factory() as db:
        message = db.get(ChatMessage, mid)
        message.text = "The source was edited."
        db.commit()
    row = client.get(
        f"/v1/chat/history/translations?ids={mid}", headers=auth_headers
    ).json()["messages"][0]
    assert row["translation_status"] == "pending"  # Old hash cannot leak stale text.


def test_translation_selection_rejects_other_owners_and_malformed_ids(
    client, auth_headers
):
    mid = old_message(client, "Some historical response")
    guest = _guest_headers(client, "history-languages-isolation")
    assert (
        client.post(
            "/v1/chat/history/prepare", headers=guest, json={"message_ids": [mid]}
        ).status_code
        == 404
    )
    assert (
        client.get(
            f"/v1/chat/history/translations?ids={mid}", headers=guest
        ).status_code
        == 404
    )
    assert (
        client.get(
            "/v1/chat/history/translations?ids=1,garbage", headers=auth_headers
        ).status_code
        == 422
    )


def test_new_template_is_bilingual_when_appended(client, auth_headers):
    preference(client, auth_headers, "es")
    response = client.post(
        "/v1/chat/append",
        headers=auth_headers,
        json={
            "role": "ai",
            "text": qtext("es", "gallery_unavailable"),
            "response_language": "es",
        },
    )
    assert response.status_code == 200, response.text
    with client.app.state.database.session_factory() as db:
        rows = list(
            db.scalars(
                select(ChatMessageTranslation).where(
                    ChatMessageTranslation.message_id == response.json()["id"]
                )
            )
        )
        assert len(rows) == 2
        assert all(row.status == "ready" for row in rows)


def test_profile_answers_obey_selected_language(client, auth_headers, monkeypatch):
    from app.providers.contracts import ProfileAnswer

    def answer(self, question, candidates, language=None):
        assert language == "es"
        return ProfileAnswer(
            text="Respuesta en español", matched_user_ids=[], simulated=True
        )

    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.answer_profile_question", answer
    )
    preference(client, auth_headers, "es")
    response = client.post(
        "/v1/profiles/search",
        headers=auth_headers,
        json={"question": "Who works here?", "language": "en"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["response_language"] == "es"
    assert response.json()["answer"] == "Respuesta en español"


def test_queued_translation_deduplicates_and_failed_retry_returns_pending(
    client, auth_headers, monkeypatch
):
    from app.social_features.models import ChatMessageTranslation

    client.app.state.settings.enqueue_processing = True
    jobs = []
    monkeypatch.setattr(
        "app.tasks.prepare_chat_languages.delay", lambda *args: jobs.append(args)
    )
    mid = old_message(client, "A free form historical reply")
    preference(client, auth_headers, "es")
    for _ in range(2):
        response = client.post(
            "/v1/chat/history/prepare",
            headers=auth_headers,
            json={"message_ids": [mid]},
        )
        assert response.json()["messages"][0]["translation_status"] == "pending"
    assert len(jobs) == 1
    with client.app.state.database.session_factory() as db:
        rows = list(
            db.scalars(
                select(ChatMessageTranslation).where(
                    ChatMessageTranslation.message_id == mid
                )
            )
        )
        for row in rows:
            row.status = "failed"
        db.commit()
    response = client.post(
        "/v1/chat/history/prepare", headers=auth_headers, json={"message_ids": [mid]}
    )
    assert response.json()["messages"][0]["translation_status"] == "pending"
    assert len(jobs) == 2
