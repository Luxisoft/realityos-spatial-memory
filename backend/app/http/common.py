from __future__ import annotations

import io
import logging
import uuid
from datetime import UTC, datetime

from fastapi import (
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from PIL import Image, ImageDraw
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.dependencies import workspace_member
from app.models import (
    AuditEvent,
    CaptureSession,
    CaptureStatus,
    Device,
    DeviceAssignment,
    JobStatus,
    MediaAsset,
    MediaKind,
    ObjectFact,
    ObjectObservation,
    ObjectTrack,
    ObjectTrackFrame,
    ProcessingJob,
    ProcessingOperation,
    Role,
    TrackedObject,
    User,
    VerificationStatus,
    Zone,
)
from app.schemas import (
    CaptureResponse,
    DeviceAssignmentResponse,
    DeviceResponse,
    GalleryMatch,
    JobResponse,
    ObjectFactResponse,
    ObjectResponse,
    ObservationResponse,
    QueryRequest,
    QueryResponse,
    SessionResponse,
    TrackFrameResponse,
    TrackResponse,
)
from app.security import (
    create_display_evidence_token,
)
from app.services import (
    add_postgres_bytea_chunks,
    exact_term_candidates,
    media_sha256,
    multilingual_object_candidates,
    verified_candidates,
)
from app.video import VideoProcessingError, probe_video

logger = logging.getLogger(__name__)


def _audit(
    db: Session,
    event_type: str,
    entity_type: str,
    actor_id: uuid.UUID | None,
    entity_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
) -> None:
    db.add(
        AuditEvent(
            workspace_id=workspace_id,
            actor_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            device_id=device_id,
        )
    )


def _session_response(item: CaptureSession) -> SessionResponse:
    return SessionResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        zone_id=item.zone_id,
        status=item.status.value,
        started_at=item.started_at,
        closed_at=item.closed_at,
        consent_confirmed=item.consent_confirmed,
    )


def _capture_response(item: MediaAsset) -> CaptureResponse:
    return CaptureResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        capture_session_id=item.capture_session_id,
        kind=item.kind.value,
        mime_type=item.mime_type,
        sha256=item.sha256,
        byte_size=item.byte_size,
        width=item.width,
        height=item.height,
        created_at=item.created_at,
    )


def _device_response(item: Device) -> DeviceResponse:
    return DeviceResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        device_identifier=item.device_identifier,
        label=item.label,
        status=item.status.value,
        last_seen_at=item.last_seen_at,
        revoked_at=item.revoked_at,
        metadata=item.metadata_json,
    )


def _assignment_response(item: DeviceAssignment) -> DeviceAssignmentResponse:
    return DeviceAssignmentResponse(
        id=item.id,
        device_id=item.device_id,
        operator_label=item.operator_label,
        external_reference=item.external_reference,
        effective_from=item.effective_from,
        effective_to=item.effective_to,
        notice_version=item.notice_version,
    )


def _fact_response(item: ObjectFact) -> ObjectFactResponse:
    return ObjectFactResponse(
        id=item.id,
        object_id=item.object_id,
        observation_id=item.observation_id,
        fact_type=item.fact_type,
        value_text=item.value_text,
        normalized_value=item.normalized_value,
        numeric_value=item.numeric_value,
        unit=item.unit,
        confidence=item.confidence,
        provenance=item.provenance.value,
        evidence_geometry=item.evidence_geometry,
        model_name=item.model_name,
        verification_status=item.verification_status.value,
    )


def _track_response(item: ObjectTrack) -> TrackResponse:
    return TrackResponse(
        id=item.id,
        object_id=item.object_id,
        source_media_asset_id=item.source_media_asset_id,
        model_name=item.model_name,
        status=item.status,
        last_seen_at=item.last_seen_at,
        last_seen_pts_seconds=item.last_seen_pts_seconds,
        metadata=item.metadata_json,
    )


def _track_frame_response(item: ObjectTrackFrame) -> TrackFrameResponse:
    return TrackFrameResponse(
        id=item.id,
        track_id=item.track_id,
        source_frame_index=item.source_frame_index,
        pts_seconds=item.pts_seconds,
        visible=item.visible,
        bounding_box=item.bounding_box,
        confidence=item.confidence,
        simulated=item.simulated,
    )


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


def _observation_response(item: ObjectObservation) -> ObservationResponse:
    return ObservationResponse(
        id=item.id,
        object_id=item.object_id,
        zone_id=item.zone_id,
        media_asset_id=item.media_asset_id,
        muse_bounding_box=item.muse_bounding_box,
        bounding_box=item.bounding_box,
        spatial_description=item.spatial_description,
        seen_at=item.seen_at,
        visual_confidence=item.visual_confidence,
        model_name=item.model_name,
        verification_status=item.verification_status.value,
    )


def _job_response(item: ProcessingJob) -> JobResponse:
    return JobResponse(
        id=item.id,
        media_asset_id=item.media_asset_id,
        observation_id=item.observation_id,
        operation=item.operation.value,
        status=item.status.value,
        provider=item.provider,
        attempts=item.attempts,
        error_message=item.error_message,
        result_metadata=item.result_metadata,
        created_at=item.created_at,
        started_at=item.started_at,
        completed_at=item.completed_at,
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
    from app.social_features.visual import valid_box

    if valid_box(observation.muse_bounding_box or observation.bounding_box):
        return "approximate_box"
    return "none"


def _object_response(item: TrackedObject) -> ObjectResponse:
    return ObjectResponse(
        id=item.id,
        canonical_name=item.canonical_name,
        category=item.category,
        attributes=item.attributes,
    )


async def _store_capture(
    request: Request,
    session: CaptureSession,
    captured_at: datetime | None = Form(default=None),
    file: UploadFile = File(...),
    *,
    db: Session,
    actor_id: uuid.UUID | None,
    device_id: uuid.UUID | None = None,
) -> CaptureResponse:
    if session.status != CaptureStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Capture session is closed."
        )
    image_types = {"image/jpeg", "image/png", "image/webp"}
    video_types = {"video/mp4", "video/quicktime", "video/webm"}
    if file.content_type not in image_types | video_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image or video type.",
        )
    raw = await file.read()
    settings = request.app.state.settings
    is_video = file.content_type in video_types
    limit = settings.max_video_bytes if is_video else settings.max_image_bytes
    if len(raw) == 0 or (limit and len(raw) > limit):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Invalid media size.",
        )
    duration_seconds: float | None = None
    if is_video:
        try:
            video_info = probe_video(raw)
        except VideoProcessingError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
        if settings.max_video_seconds and video_info.duration_seconds > settings.max_video_seconds:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Video exceeds the {settings.max_video_seconds}-second limit.",
            )
        width, height = video_info.width, video_info.height
        duration_seconds = video_info.duration_seconds
    else:
        try:
            with Image.open(io.BytesIO(raw)) as image:
                width, height = image.size
                image.verify()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image data."
            )
    digest = media_sha256(raw)
    existing = db.scalar(
        select(MediaAsset).where(
            MediaAsset.capture_session_id == session.id,
            MediaAsset.sha256 == digest,
        )
    )
    if existing:
        return _capture_response(existing)
    chunked_video = is_video and len(raw) > settings.video_inline_bytes
    asset = MediaAsset(
        workspace_id=session.workspace_id,
        capture_session_id=session.id,
        kind=MediaKind.VIDEO if is_video else MediaKind.IMAGE,
        mime_type=file.content_type,
        original_bytes=b"" if chunked_video else raw,
        sha256=digest,
        byte_size=len(raw),
        width=width,
        height=height,
        captured_at=captured_at,
        extra_metadata={
            "filename": file.filename or "capture",
            **({"duration_seconds": duration_seconds} if duration_seconds is not None else {}),
        },
    )
    db.add(asset)
    db.flush()
    if chunked_video:
        add_postgres_bytea_chunks(db, asset, raw, settings.video_bytea_chunk_bytes)
    if session.created_by_id is not None:
        from app.social import Publication

        db.add(Publication(owner_id=session.created_by_id, media_id=asset.id, audience="home"))
    _audit(
        db,
        "capture.created",
        "media_asset",
        actor_id,
        asset.id,
        session.workspace_id,
        device_id,
    )
    return _capture_response(asset)


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


def _render_highlight(db: Session, observation: ObjectObservation, asset: MediaAsset) -> Response:
    """Render an ephemeral overlay; original evidence and binary mask stay immutable."""

    if observation.workspace_id != asset.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    try:
        with Image.open(io.BytesIO(asset.original_bytes)).convert("RGBA") as image:
            if observation.mask_asset_id:
                mask_asset = db.get(MediaAsset, observation.mask_asset_id)
                if mask_asset is None or mask_asset.workspace_id != observation.workspace_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="SAM mask is no longer available.",
                    )
                with Image.open(io.BytesIO(mask_asset.original_bytes)).convert("L") as mask:
                    resized_mask = mask.resize(image.size, Image.Resampling.NEAREST)
                alpha = resized_mask.point(lambda value: 128 if value else 0)
                overlay = Image.new("RGBA", image.size, (255, 199, 0, 0))
                overlay.putalpha(alpha)
                image.alpha_composite(overlay)
                box = observation.bounding_box
                if box:
                    _draw_box(image, box, color=(255, 235, 90, 255))
            else:
                box = observation.muse_bounding_box or observation.bounding_box
                if not box:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No highlight geometry is available.",
                    )
                _draw_box(image, box, color=(255, 199, 0, 255))
            output = io.BytesIO()
            image.save(output, format="PNG")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Media cannot be highlighted."
        )
    return Response(content=output.getvalue(), media_type="image/png")


def _draw_box(image: Image.Image, box: dict, color: tuple[int, int, int, int]) -> None:
    x = int(float(box["x"]) * image.width)
    y = int(float(box["y"]) * image.height)
    right = int((float(box["x"]) + float(box["width"])) * image.width)
    bottom = int((float(box["y"]) + float(box["height"])) * image.height)
    ImageDraw.Draw(image).rectangle(
        (x, y, right, bottom), outline=color, width=max(3, image.width // 120)
    )
