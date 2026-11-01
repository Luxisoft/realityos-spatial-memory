"""Read prepared information and explicitly recover missing historical languages."""

import asyncio
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, defer

from app.dependencies import get_current_user, get_db
from app.models import User
from app.social_features.evidence import readable_post, usable_detection
from app.social_features.evidence_models import GalleryEvidence
from app.social_features.localizations import display_information, stored_rows

router = APIRouter()


class InformationSelection(BaseModel):
    evidence_id: uuid.UUID
    labels: list[str] = Field(min_length=1, max_length=32)


class InformationRequest(BaseModel):
    language: str = Field(default="en", max_length=16)
    items: list[InformationSelection] = Field(min_length=1, max_length=6)


class EvidenceInformation(BaseModel):
    evidence_id: uuid.UUID
    title: str
    note_text: str
    matched_labels: list[str]


class InformationResponse(BaseModel):
    language: str
    items: list[EvidenceInformation]
    status: Literal["ready", "pending", "unavailable"] = "ready"
    simulated: bool = False


def authorize_selections(payload, user, db):
    selections = []
    for selection in payload.items:
        evidence = db.get(
            GalleryEvidence, selection.evidence_id, options=[defer(GalleryEvidence.image_bytes)]
        )
        if evidence is not None and evidence.index_run_id:
            from app.social_features.evidence_models import GalleryIndexRun

            if db.get(GalleryIndexRun, evidence.index_run_id).status != "ready":
                raise HTTPException(404, "Evidence unavailable.")
        if evidence is None:
            raise HTTPException(404, "Evidence unavailable.")
        post = readable_post(db, evidence.post_id, user)
        labels = {d["label"] for d in evidence.detections if usable_detection(d)}
        chosen = list(dict.fromkeys(selection.labels))
        if any(label not in labels for label in chosen):
            raise HTTPException(404, "No matching annotation.")
        selections.append((evidence, post, chosen))
    return selections


def read_information(payload, user, db):
    from app.social_features.language_preferences import resolved_language

    language = (
        resolved_language(user, payload.language)
        if user.preferred_language
        else payload.language.lower().replace("_", "-").split("-")[0]
    )
    if language not in ("en", "es"):
        raise HTTPException(422, "Only English and Spanish publication information is available.")
    selections = authorize_selections(payload, user, db)
    rows = stored_rows(
        db, {key for evidence, post, _ in selections for key in (evidence.post_id, post.id)}
    )
    items, simulated = [], False
    for evidence, post, labels in selections:
        text = display_information(
            rows,
            post.id,
            evidence.post_id,
            language,
            post.caption or "",
            post.note_text or "",
            labels,
        )
        if text is not None:
            simulated |= text.pop("simulated")
            items.append(EvidenceInformation(evidence_id=evidence.id, **text))
    return InformationResponse(
        language=language,
        items=items,
        simulated=simulated,
        status="ready" if len(items) == len(selections) else "pending",
    )


@router.post("/gallery/evidence/information", response_model=InformationResponse)
async def evidence_information(
    payload: InformationRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return read_information(payload, user, db)


@router.post("/gallery/evidence/information/prepare", response_model=InformationResponse)
async def prepare_evidence_information(
    payload: InformationRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Explicit recovery action for missing historical translations; Query stays read-only."""
    existing = read_information(payload, user, db)
    if existing.status == "ready":
        return existing
    user_id = user.id
    database, settings = request.app.state.database, request.app.state.settings

    def prepare():
        from app.meta import MetaProviderError, build_meta_client
        from app.social_features.history_evidence import persist_refreshed_history
        from app.social_features.localizations import (
            LANGUAGES,
            persist,
            prepare_languages,
            text_hash,
        )

        with database.session_factory() as session:
            current = session.get(User, user_id)
            if current is None or not current.is_active:
                raise HTTPException(403, "Account unavailable.")
            selected = authorize_selections(payload, current, session)
            from sqlalchemy import select

            from app.social_features.models import Publication

            list(
                session.scalars(
                    select(Publication)
                    .where(
                        Publication.id.in_(
                            {
                                pid
                                for evidence, post, _ in selected
                                for pid in (evidence.post_id, post.id)
                            }
                        )
                    )
                    .order_by(Publication.id)
                    .with_for_update()
                    .execution_options(populate_existing=True)
                )
            )
            session.refresh(current)
            if not current.is_active:
                raise HTTPException(403, "Account unavailable.")
            selected = authorize_selections(payload, current, session)
            rows = stored_rows(
                session,
                {pid for evidence, post, _ in selected for pid in (evidence.post_id, post.id)},
            )
            targets = {}
            for evidence, post, labels in selected:
                targets.setdefault(post.id, set()).update(
                    t for t in (post.caption or "", post.note_text or "") if t.strip()
                )
                targets.setdefault(evidence.post_id, set()).update(labels)
            missing = {
                t
                for pid, texts in targets.items()
                for t in texts
                if any((pid, language, text_hash(t)) not in rows for language in LANGUAGES)
            }
            try:
                client = build_meta_client(settings)
                translated = prepare_languages(client, missing)
            except MetaProviderError:
                return InformationResponse(
                    language=existing.language, items=[], status="unavailable"
                )
            session.expire_all()
            if not current.is_active:
                raise HTTPException(403, "Account unavailable.")
            authorize_selections(payload, current, session)
            for pid, texts in targets.items():
                hashes = {text_hash(t) for t in texts}
                persist(
                    session,
                    pid,
                    {
                        language: {key: text for key, text in values.items() if key in hashes}
                        for language, values in translated.items()
                    },
                    settings.meta_mode == "mock",
                )
            persist_refreshed_history(session, current)
            session.commit()
            return read_information(payload, current, session)

    return await asyncio.to_thread(prepare)
