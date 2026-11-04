from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import (
    User,
)
from app.social_features.chat_localization import dispatch_messages, localized_message
from app.social_features.language_preferences import resolved_language
from app.social_features.models import ChatAudio, ChatMessage
from app.social_features.schemas import ChatAppend, MergeTexts

"""Facebook identities and explicitly shared audiovisual publications."""


router = APIRouter()


@router.post("/chat/append")
def chat_append(
    payload: ChatAppend,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    evidence_url = payload.evidence_url or None
    if evidence_url in {"null", "undefined"}:
        # Defensive: org.json optString leaks JSON null as literal text.
        evidence_url = None
    gallery = []
    for item in payload.gallery:
        if item.thumbnail_url in {"null", "undefined"}:
            continue
        dumped = item.model_dump(mode="json", exclude_unset=True)
        for key in ("media_url", "boxed_url"):
            if dumped.get(key) in {"null", "undefined"}:
                dumped[key] = ""
        gallery.append(dumped)
    message = ChatMessage(
        user_id=user.id,
        role=payload.role,
        response_language=payload.response_language if payload.role == "ai" else None,
        kind=payload.kind if payload.kind in {"text", "voice", "image"} else "text",
        text=payload.text.strip()[:4000],
        evidence_url=evidence_url,
        gallery=gallery,
        simulated=payload.simulated,
        quick_replies=[item.model_dump() for item in payload.quick_replies],
        face_action=payload.face_action,
    )
    db.add(message)
    db.flush()
    if message.role == "ai":
        dispatch_messages(request, db, user, [message])
    return {"id": message.id}


@router.get("/chat/history")
def chat_history(
    limit: int = 10,
    before_id: int | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Newest-first chat page for the authenticated profile (guests included)."""

    clamped = min(max(limit, 1), 50)
    query = select(ChatMessage).where(ChatMessage.user_id == user.id)
    if before_id is not None:
        query = query.where(ChatMessage.id < before_id)
    rows = list(db.scalars(query.order_by(ChatMessage.id.desc()).limit(clamped + 1)))
    page = rows[:clamped]
    audio_rows = (
        db.execute(
            select(ChatAudio.message_id, ChatAudio.id)
            .where(ChatAudio.message_id.in_([row.id for row in page]))
            .order_by(ChatAudio.id)
        ).all()
        if page
        else []
    )
    audio_urls: dict[int, list[str]] = {}
    for message_id, audio_id in audio_rows:
        audio_urls.setdefault(message_id, []).append(f"/v1/chat/audio/{audio_id}")
    from app.social_features.history_evidence import question_before, refreshed_gallery

    return {
        "messages": [
            {
                **localized_message(db, row, resolved_language(user)),
                "source_language": row.response_language,
                "id": row.id,
                "role": row.role,
                "kind": row.kind,
                "text": row.text,
                "evidence_url": row.evidence_url,
                "gallery": refreshed_gallery(
                    db, user, row.gallery, question_before(db, user, row.id) if row.gallery else ""
                ),
                "simulated": bool(row.simulated),
                "quick_replies": row.quick_replies or [],
                "face_action": bool(row.face_action),
                "audio_urls": audio_urls.get(row.id, []),
                "audio_duration_ms": row.audio_duration_ms or 0,
                "created_at": row.created_at.isoformat(),
            }
            for row in page
        ],
        "has_more": len(rows) > clamped,
    }


@router.post("/chat/audio")
async def chat_audio_upload(
    message_id: int = Form(...),
    duration_ms: int = Form(default=0),
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Attach one voice segment to an owned chat turn for later playback."""

    message = db.get(ChatMessage, message_id)
    if message is None or message.user_id != user.id:
        raise HTTPException(404, "Chat turn unavailable.")
    if audio.content_type not in {"audio/mp4", "audio/x-m4a", "audio/m4a", "audio/aac"}:
        raise HTTPException(415, "Only M4A/AAC voice audio is accepted.")
    raw = await audio.read()
    if not raw or len(raw) > 8 * 1024 * 1024:
        raise HTTPException(413, "Invalid audio size.")
    existing = (
        db.scalar(
            select(func.count()).select_from(ChatAudio).where(ChatAudio.message_id == message_id)
        )
        or 0
    )
    if existing >= 8:
        raise HTTPException(422, "Too many audio segments for one turn.")
    part = ChatAudio(
        message_id=message_id,
        user_id=user.id,
        audio=raw,
        mime_type="audio/mp4",
        duration_ms=min(max(duration_ms, 0), 3_600_000),
    )
    db.add(part)
    db.flush()
    message.audio_duration_ms = (message.audio_duration_ms or 0) + part.duration_ms
    return {"id": part.id}


@router.get("/chat/audio/{audio_id}")
def chat_audio_download(
    audio_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from fastapi.responses import Response

    part = db.get(ChatAudio, audio_id)
    if part is None or part.user_id != user.id:
        raise HTTPException(404, "Audio unavailable.")
    return Response(content=part.audio, media_type=part.mime_type)


@router.post("/notes/merge")
def merge_notes(payload: MergeTexts, user: User = Depends(get_current_user)):
    """Join consecutive transcript chunks, dropping boundary repetitions."""
    from app.social_features.notes import merge_transcript_chunks

    cleaned = [text.strip()[:2000] for text in payload.texts if text.strip()]
    return {"text": merge_transcript_chunks(cleaned)}
