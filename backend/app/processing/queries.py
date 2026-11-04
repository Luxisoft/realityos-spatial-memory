from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import (
    HTTPException,
    status,
)
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.dependencies import workspace_member
from app.models import (
    Device,
    DeviceAssignment,
    JobStatus,
    ObjectFact,
    ObjectObservation,
    ProcessingJob,
    ProcessingOperation,
    Role,
    User,
    VerificationStatus,
    Zone,
)
from app.processing.presentation import _object_response, _observation_response
from app.processing.search import (
    exact_term_candidates,
    multilingual_object_candidates,
    verified_candidates,
)
from app.schemas import (
    GalleryMatch,
    QueryRequest,
    QueryResponse,
)
from app.security import (
    create_display_evidence_token,
)

logger = logging.getLogger(__name__)


def _active_assignment(db: Session, device: Device) -> DeviceAssignment | None:
    now = datetime.now(UTC)
    return db.scalar(
        select(DeviceAssignment)
        .where(
            DeviceAssignment.device_id == device.id,
            DeviceAssignment.effective_from <= now,
            (DeviceAssignment.effective_to.is_(None)) | (DeviceAssignment.effective_to > now),
        )
        .order_by(desc(DeviceAssignment.effective_from))
    )


def _segmentation_details(
    db: Session, observation: ObjectObservation
) -> tuple[str, ProcessingJob | None]:
    if observation.mask_asset_id:
        return "ready", None
    job = db.scalar(
        select(ProcessingJob)
        .where(
            ProcessingJob.observation_id == observation.id,
            ProcessingJob.operation == ProcessingOperation.SEGMENTATION,
        )
        .order_by(desc(ProcessingJob.created_at))
    )
    if job is None:
        return "not_requested", None
    if job.status == JobStatus.QUEUED:
        return "queued", job
    if job.status == JobStatus.PROCESSING:
        return "processing", job
    if job.status == JobStatus.FAILED:
        return "failed", job
    if job.result_metadata.get("segmentation_status") == "no_match":
        return "no_match", job
    return "not_requested", job


def _highlight_quality(observation: ObjectObservation) -> str:
    if observation.mask_asset_id:
        return "sam_mask"
    from app.geometry import valid_box

    if valid_box(observation.muse_bounding_box or observation.bounding_box):
        return "approximate_box"
    return "none"


def _fact_rollup(db: Session, workspace_id: uuid.UUID, fact_type: str) -> list[dict]:
    rows = db.execute(
        select(
            ObjectFact.normalized_value,
            ObjectFact.value_text,
            func.count(func.distinct(ObjectFact.object_id)),
        )
        .where(
            ObjectFact.workspace_id == workspace_id,
            ObjectFact.fact_type == fact_type,
            ObjectFact.verification_status == VerificationStatus.VERIFIED,
        )
        .group_by(ObjectFact.normalized_value, ObjectFact.value_text)
        .order_by(desc(func.count(func.distinct(ObjectFact.object_id))))
    ).all()
    return [
        {"value": normalized or display or "unknown", "count": int(count)}
        for normalized, display, count in rows
    ]


def _zone_path(db: Session, zone_id: uuid.UUID | None) -> list[str]:
    result: list[str] = []
    seen: set[uuid.UUID] = set()
    while zone_id and zone_id not in seen:
        seen.add(zone_id)
        zone = db.get(Zone, zone_id)
        if zone is None:
            break
        result.append(zone.name)
        zone_id = zone.parent_id
    return list(reversed(result))


def _gallery_fallback(db: Session, user: User | None, question: str, client):
    """Viewer-visible gallery results with explicit search/indexing status."""
    from app.social_features.evidence import GallerySearch, search_evidence

    if user is None:
        return GallerySearch()
    try:
        result = search_evidence(db, user, question, client, limit=6)
        result.matches = [GalleryMatch(**item) for item in result.matches]
        return result
    except Exception:
        logger.warning("gallery fallback failed", exc_info=True)
        return GallerySearch(status="unavailable", reason="storage_unavailable")


def _gallery_answer(db, user, question, client, language, simulated, tracked=None):
    from app.query_lang import qtext

    result = _gallery_fallback(db, user, question, client)
    if result.matches:
        kinds = {item.match_kind for item in result.matches}
        key = (
            "gallery_related"
            if kinds - {"exact", None}
            else (
                "found_in_publications_one"
                if len(result.matches) == 1
                else "found_in_publications_other"
            )
        )
        text = qtext(language, key, count=len(result.matches))
        if result.status == "partial":
            text += " " + qtext(language, "gallery_partial")
        elif result.status == "unavailable":
            text += " " + qtext(language, "gallery_unavailable")
    else:
        key = {
            "indexing": "gallery_indexing",
            "partial": "gallery_partial_empty",
            "unavailable": "gallery_unavailable",
        }.get(result.status)
        text = (
            qtext(language, key)
            if key
            else (
                qtext(language, "no_observation", name=tracked.canonical_name)
                if tracked
                else qtext(language, "no_evidence")
            )
        )
    return QueryResponse(
        response_language=language,
        found=False,
        message=text,
        tts_text=text,
        gallery_matches=result.matches,
        gallery_search_status=result.status,
        gallery_pending_count=result.pending_count,
        gallery_failed_count=result.failed_count,
        gallery_search_reason=result.reason,
        object=_object_response(tracked) if tracked else None,
        simulated=simulated,
    )


def _answer_query(
    payload: QueryRequest,
    user: User | None,
    db: Session,
    client=None,
    *,
    authorized_workspace_id: uuid.UUID | None = None,
    device_view: bool = False,
    display_device: Device | None = None,
    settings: Settings | None = None,
) -> QueryResponse:
    from app.query_lang import qtext
    from app.social_features.language_preferences import resolved_language
    from app.social_features.query_localization import spatial_detail

    language = resolved_language(user, payload.language)
    if user is None:
        if payload.search_scope == "gallery":
            raise HTTPException(403, "Gallery search requires a user account.")
        if authorized_workspace_id != payload.workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied."
            )
        can_refine = False
    else:
        member = workspace_member(payload.workspace_id, user, db, {Role.ADMIN, Role.QUERY})
        can_refine = member.role in {Role.ADMIN, Role.REGISTER}
    if payload.search_scope == "gallery":
        return _gallery_answer(db, user, payload.question, client, language, False)
    candidates, interpretation_simulated = multilingual_object_candidates(
        db, payload.workspace_id, payload.question, client
    )
    # A generic model label can collide with an explicit human alias. Resolve
    # only that exact-name collision; broad requests must remain ambiguous.
    exact_matches = exact_term_candidates(db, payload.workspace_id, payload.question)
    if len(candidates) > 1 and len(exact_matches) > 1:
        verified = verified_candidates(db, payload.workspace_id, candidates)
        if len(verified) == 1:
            candidates = verified
    if not candidates:
        if payload.search_scope == "registry":
            text = qtext(language, "no_evidence")
            return QueryResponse(
                found=False,
                message=text,
                tts_text=text,
                response_language=language,
                simulated=interpretation_simulated,
            )
        return _gallery_answer(
            db, user, payload.question, client, language, interpretation_simulated
        )
    if len(candidates) > 1:
        names = ", ".join(candidate.canonical_name for candidate in candidates[:3])
        text = qtext(language, "several_matches", names=names)
        return QueryResponse(
            response_language=language,
            found=False,
            ambiguous=True,
            message=text,
            tts_text=text,
            simulated=interpretation_simulated,
        )
    tracked = candidates[0]
    observation = db.scalar(
        select(ObjectObservation)
        .where(
            ObjectObservation.workspace_id == payload.workspace_id,
            ObjectObservation.object_id == tracked.id,
            ObjectObservation.verification_status == VerificationStatus.VERIFIED,
        )
        .order_by(desc(ObjectObservation.seen_at))
    )
    if observation is None:
        if payload.search_scope == "registry":
            text = qtext(language, "no_evidence")
            return QueryResponse(
                found=False,
                message=text,
                tts_text=text,
                response_language=language,
                simulated=interpretation_simulated,
            )
        return _gallery_answer(
            db, user, payload.question, client, language, interpretation_simulated, tracked
        )
    path = _zone_path(db, observation.zone_id)
    location = ", ".join(path) if path else qtext(language, "unknown_location")
    detail = spatial_detail(client, observation.spatial_description, language)
    name = tracked.canonical_name[:1].upper() + tracked.canonical_name[1:]
    text = qtext(
        language,
        "last_seen",
        name=name,
        location=location,
        detail=detail,
        date=observation.seen_at.date().isoformat(),
    )
    segmentation_status, segmentation_job = _segmentation_details(db, observation)
    highlight_quality = _highlight_quality(observation)
    has_highlight = highlight_quality != "none"
    display_media_url = None
    if has_highlight and display_device is not None and settings is not None:
        token = create_display_evidence_token(observation.id, display_device.id, settings)
        display_media_url = (
            f"/v1/device/display/observations/{observation.id}/highlighted?token={token}"
        )
    return QueryResponse(
        response_language=language,
        found=True,
        message=text,
        object=_object_response(tracked),
        observation=_observation_response(observation),
        zone_path=path,
        media_id=observation.media_asset_id,
        highlighted_media_url=(
            (
                f"/v1/device/observations/{observation.id}/highlighted"
                if device_view
                else f"/v1/observations/{observation.id}/highlighted"
            )
            if has_highlight
            else None
        ),
        display_media_url=display_media_url,
        highlight_quality=highlight_quality,
        segmentation_status=segmentation_status,
        segmentation_job_id=segmentation_job.id if segmentation_job else None,
        can_refine=can_refine
        and segmentation_status in {"not_requested", "failed"}
        and highlight_quality == "approximate_box",
        retrieval_confidence=observation.visual_confidence,
        tts_text=text,
        simulated=observation.model_name.startswith("mock-") or interpretation_simulated,
    )
