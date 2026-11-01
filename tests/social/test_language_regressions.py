"""Whole-product language regressions: mislabelled local replies and spatial prose."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from app.social_features.chat_localization import source_hash
from app.social_features.models import ChatMessage, ChatMessageTranslation
from app.social_features.query_localization import spatial_detail
from app.social_features.reply_templates import LOCAL_REPLY_TEMPLATES

from .test_chat_languages import old_message, preference, workspace


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize(
    "key",
    ["ui_guests_cannot_search_for_meta_people", "chat_query_failed", "chat_greeting"],
)
def test_mislabelled_local_reply_overrides_stale_saved_translation_without_model(
    client, auth_headers, monkeypatch, language, key
):
    source = LOCAL_REPLY_TEMPLATES[key]["es"]
    mid = old_message(client, source, response_language="en")
    with client.app.state.database.session_factory() as db:
        message = db.get(ChatMessage, mid)
        db.add(
            ChatMessageTranslation(
                message_id=mid,
                language="en",
                source_hash=source_hash(message),
                text=source,
                quick_replies=[],
                status="ready",
                simulated=False,
            )
        )
        db.commit()
    preference(client, auth_headers, language)
    monkeypatch.setattr(
        "app.providers.mock.MockMetaModelClient.prepare_gallery_languages",
        lambda *args: pytest.fail("Local replies require no provider"),
    )
    expected = LOCAL_REPLY_TEMPLATES[key][language]
    for path in ["/v1/chat/history", f"/v1/chat/history/translations?ids={mid}"]:
        response = client.get(path, headers=auth_headers)
        assert response.status_code == 200
        row = next(row for row in response.json()["messages"] if row["id"] == mid)
        assert row["localized_text"] == expected
        assert row["response_language"] == language
    with client.app.state.database.session_factory() as db:
        assert db.get(ChatMessage, mid).text == source
        # GET did not fix or overwrite the database.
        assert db.get(ChatMessage, mid).response_language == "en"
    for _ in range(2):
        response = client.post(
            "/v1/chat/history/prepare",
            headers=auth_headers,
            json={"message_ids": [mid]},
        )
        assert response.json()["messages"][0]["localized_text"] == expected
    with client.app.state.database.session_factory() as db:
        message = db.get(ChatMessage, mid)
        assert message.text == source
        assert message.response_language == "es"
        assert (
            db.get(ChatMessageTranslation, (mid, "en", source_hash(message))).text
            == LOCAL_REPLY_TEMPLATES[key]["en"]
        )


@pytest.mark.parametrize("language", ["en", "es"])
def test_selected_language_overrides_opposite_language_for_voice_query(
    client, auth_headers, language
):
    from app.query_lang import qtext

    from .support import _wav_bytes

    wid = workspace(client)
    preference(client, auth_headers, language)
    response = client.post(
        "/v1/queries/audio",
        headers=auth_headers,
        data={"workspace_id": wid, "language": "es" if language == "en" else "en"},
        files={"audio": ("voice.wav", _wav_bytes(), "audio/wav")},
    )
    assert response.status_code == 200
    assert response.json()["response_language"] == language
    assert (
        response.json()["message"]
        == response.json()["tts_text"]
        == qtext(language, "no_evidence")
    )


def test_spatial_prose_uses_translation_but_does_not_mutate_original():
    class Provider:
        def translate_gallery_texts(self, texts, language):
            assert texts == {"detail": "junto a la caja azul"}
            assert language == "en"
            return {"detail": "next to the blue box"}

    assert (
        spatial_detail(Provider(), "junto a la caja azul", "en")
        == "next to the blue box"
    )
    assert (
        spatial_detail(None, "junto a la caja azul", "en")
        == "no additional spatial detail"
    )


def test_android_resources_have_both_languages_and_matching_format_arguments():
    import re

    root = Path(__file__).resolve().parents[2] / "android/app/src/main/res"
    resources = []
    for folder in ("values", "values-es"):
        tree = ET.parse(root / folder / "strings.xml").getroot()
        rows = tree.findall("string")
        assert len(rows) == len({row.attrib["name"] for row in rows})
        resources.append(
            {
                row.attrib["name"]: row.text or ""
                for row in rows
                if row.attrib.get("translatable") != "false"
            }
        )
        for plural in tree.findall("plurals"):
            for item in plural.findall("item"):
                resources[-1][f"{plural.attrib['name']}.{item.attrib['quantity']}"] = (
                    item.text or ""
                )
    en, es = resources
    assert en.keys() == es.keys()
    for key in en:
        assert sorted(re.findall(r"%(?:[0-9]+\$)?[dsf]", en[key])) == sorted(
            re.findall(r"%(?:[0-9]+\$)?[dsf]", es[key])
        ), key


@pytest.mark.parametrize("language", ["en", "es"])
@pytest.mark.parametrize("count", [0, 1, 2])
def test_historical_face_count_has_natural_plural_without_changing_names(
    language, count
):
    from app.social_features.chat_localization import recognize_template, template_text

    legacy = f"Encontré {count} persona(s): Ana, José"
    data = recognize_template(legacy)
    value = template_text(data, language)
    noun = (
        ("person" if count == 1 else "people")
        if language == "en"
        else ("persona" if count == 1 else "personas")
    )
    prefix = "I found" if language == "en" else "Encontré"
    assert value == f"{prefix} {count} {noun}: Ana, José"
    assert template_text(recognize_template(value), language) == value
