"""Durable assistant translations. Reads never call a model or enqueue writes."""

import hashlib
import json
import re
from datetime import UTC, datetime, timedelta
from string import Formatter

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.meta import build_meta_client
from app.models import User
from app.query_lang import _TEMPLATES, qtext
from app.social_features.language_preferences import resolved_language
from app.social_features.models import ChatMessage, ChatMessageTranslation
from app.social_features.reply_templates import LOCAL_REPLY_TEMPLATES

router = APIRouter()
LANGUAGES = ("en", "es")
_REPLY_LABELS = {
    "ask_person": {"en": "Person", "es": "Persona"},
    "ask_object": {"en": "Object", "es": "Objeto"},
}


def source_hash(message):
    return hashlib.sha256(
        json.dumps(
            [message.text, message.quick_replies or []], ensure_ascii=False, sort_keys=True
        ).encode()
    ).hexdigest()


def recognize_template(text):
    """Only exact known templates qualify; free text always uses translation."""
    legacy_registration = {
        "Register evidence in Home first.": "en",
        "Registra primero evidencia en Casa.": "es",
    }
    if text in legacy_registration:
        return {"key": "register_home", "values": {}, "source_language": legacy_registration[text]}
    for key, variants in {**_TEMPLATES, **LOCAL_REPLY_TEMPLATES}.items():
        if key == "last_seen":  # Spatial prose embedded in the template also needs translation.
            continue
        for language in LANGUAGES:
            template = variants.get(language)
            if template is None:
                continue
            pattern, fields = "", []
            for literal, field, _, _ in Formatter().parse(template):
                pattern += re.escape(literal)
                if field:
                    fields.append(field)
                    pattern += r"([0-9]+)" if field == "count" else r"(.+?)"
            match = re.fullmatch(pattern, text, flags=re.DOTALL)
            if match:
                return {
                    "key": key,
                    "values": dict(zip(fields, match.groups())),
                    "source_language": language,
                }
    # Gallery results may append one second, known status sentence.
    for language in LANGUAGES:
        for suffix_key in ("gallery_unavailable", "gallery_partial"):
            suffix = " " + qtext(language, suffix_key)
            if text.endswith(suffix):
                head = recognize_template(text[: -len(suffix)])
                if head:
                    return {**head, "suffix": suffix_key}
    return None


def template_text(data, language):
    key = data["key"]
    if key.startswith("chat_face_found"):
        key = (
            "chat_face_found_one" if int(data["values"]["count"]) == 1 else "chat_face_found_other"
        )
    text = (
        LOCAL_REPLY_TEMPLATES[key][language].format(**data["values"])
        if key in LOCAL_REPLY_TEMPLATES
        else qtext(language, key, **data["values"])
    )
    return text + (" " + qtext(language, data["suffix"]) if data.get("suffix") else "")


def known_replies(message, language):
    replies = message.quick_replies or []
    if any(
        reply["id"] not in _REPLY_LABELS
        or reply["label"] not in _REPLY_LABELS[reply["id"]].values()
        for reply in replies
    ):
        return None
    return [{"id": reply["id"], "label": _REPLY_LABELS[reply["id"]][language]} for reply in replies]


def translation_row(db, message, language):
    return db.get(ChatMessageTranslation, (message.id, language, source_hash(message)))


def seed_translations(db, message):
    if message.role != "ai":
        return
    data = recognize_template(message.text)
    message.template_data = data
    if data:
        message.response_language = data["source_language"]
    for language in LANGUAGES:
        existing = translation_row(db, message, language)
        replies = known_replies(message, language)
        if existing is not None:
            if data and replies is not None:
                existing.text = template_text(data, language)
                existing.quick_replies = replies
                existing.status = "ready"
            continue
        ready = (data is not None and replies is not None) or message.response_language == language
        db.add(
            ChatMessageTranslation(
                message_id=message.id,
                language=language,
                source_hash=source_hash(message),
                text=template_text(data, language) if data else (message.text if ready else ""),
                quick_replies=replies
                if replies is not None and data
                else (message.quick_replies or [] if ready else []),
                status="ready" if ready else "pending",
                simulated=message.simulated,
            )
        )
    db.flush()


def localized_message(db, message, language):
    if message.role != "ai":
        return {
            "localized_text": message.text,
            "localized_quick_replies": message.quick_replies or [],
            "translation_status": "ready",
            "response_language": language,
        }
    data, replies = recognize_template(message.text), known_replies(message, language)
    if data and replies is not None:
        return {
            "localized_text": template_text(data, language),
            "localized_quick_replies": replies,
            "translation_status": "ready",
            "response_language": language,
        }
    row = translation_row(db, message, language)
    if row and row.status == "ready":
        return {
            "translation_simulated": bool(row.simulated),
            "localized_text": row.text,
            "localized_quick_replies": row.quick_replies,
            "translation_status": "ready",
            "response_language": language,
        }
    status = "pending" if row and row.status == "queued" else (row.status if row else "pending")
    if row and row.updated_at.replace(tzinfo=UTC) < datetime.now(UTC) - timedelta(minutes=2):
        status = "failed"
    return {
        "localized_text": None,
        "localized_quick_replies": [],
        "translation_status": status,
        "response_language": language,
    }


def prepare_message(db, message, client):
    """Caller locks the owned message. Concurrent workers skip that lock."""
    seed_translations(db, message)
    pending = [
        row for lang in LANGUAGES if (row := translation_row(db, message, lang)).status != "ready"
    ]
    if not pending:
        return
    texts = {
        "message": message.text,
        **{f"reply_{i}": reply["label"] for i, reply in enumerate(message.quick_replies or [])},
    }
    try:
        versions = client.prepare_gallery_languages(texts)
        for row in pending:
            values = versions[row.language]
            if set(values) != set(texts) or any(
                not isinstance(value, str) or not value.strip() for value in values.values()
            ):
                raise ValueError("Incomplete chat translation")
        # Validate both versions before publishing either.
        for row in pending:
            values = versions[row.language]
            row.text = values["message"]
            row.quick_replies = [
                {"id": reply["id"], "label": values[f"reply_{i}"]}
                for i, reply in enumerate(message.quick_replies or [])
            ]
            row.status = "ready"
            row.simulated = bool(message.simulated or client.__class__.__name__.startswith("Mock"))
            row.updated_at = datetime.now(UTC)
    except Exception:
        for row in pending:
            row.status = "failed"
            row.updated_at = datetime.now(UTC)


def dispatch_messages(request, db, user, messages):
    """Commit job rows before a worker can fetch them; duplicates are harmless."""
    from app.tasks import prepare_chat_languages

    pending = []
    for message in messages:
        seed_translations(db, message)
        rows = [translation_row(db, message, lang) for lang in LANGUAGES]
        now = datetime.now(UTC)
        missing = [row for row in rows if row.status != "ready"]
        if missing and any(
            row.status != "queued"
            or row.updated_at.replace(tzinfo=UTC) < now - timedelta(minutes=2)
            for row in missing
        ):
            for row in missing:
                row.status = "queued"
                row.updated_at = now
            pending.append(message)
    db.commit()
    for message in pending:
        if not request.app.state.settings.enqueue_processing:
            try:
                client = build_meta_client(request.app.state.settings)
            except Exception:
                client = None
            prepare_message(db, message, client)
        else:
            try:
                prepare_chat_languages.delay(str(user.id), message.id)
            except Exception:
                for lang in LANGUAGES:
                    row = translation_row(db, message, lang)
                    if row.status != "ready":
                        row.status = "failed"
    db.flush()


class HistoryPreparation(BaseModel):
    message_ids: list[int] = Field(min_length=1, max_length=50)


@router.post("/chat/history/prepare")
def prepare_history(
    payload: HistoryPreparation,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ids = set(payload.message_ids)
    messages = list(
        db.scalars(
            select(ChatMessage)
            .where(ChatMessage.user_id == user.id, ChatMessage.id.in_(ids))
            .order_by(ChatMessage.id)
            .with_for_update()
        )
    )
    if len(messages) != len(ids):
        raise HTTPException(404, "Messages unavailable.")
    ai_messages = [message for message in messages if message.role == "ai"]
    dispatch_messages(request, db, user, ai_messages)
    language = resolved_language(user)
    return {
        "messages": [
            {"id": message.id, **localized_message(db, message, language)} for message in messages
        ]
    }


@router.get("/chat/history/translations")
def read_history_translations(
    ids: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if len(ids) > 1024 or not re.fullmatch(r"[0-9]+(?:,[0-9]+){0,49}", ids):
        raise HTTPException(422, "Invalid message selection.")
    selected = {int(value) for value in ids.split(",")}
    if any(value < 1 or value > 9223372036854775807 for value in selected):
        raise HTTPException(422, "Invalid message selection.")
    messages = list(
        db.scalars(
            select(ChatMessage).where(ChatMessage.user_id == user.id, ChatMessage.id.in_(selected))
        )
    )
    if len(messages) != len(selected):
        raise HTTPException(404, "Messages unavailable.")
    language = resolved_language(user)
    return {
        "messages": [
            {"id": message.id, **localized_message(db, message, language)} for message in messages
        ]
    }
