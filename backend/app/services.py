from __future__ import annotations

import hashlib
import io
import re
import uuid
from datetime import UTC, datetime, timedelta

from PIL import Image
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.meta import MetaModelClient, MetaProviderError
from app.models import (
    CaptureSession,
    JobStatus,
    MediaAsset,
    MediaKind,
    ObjectAlias,
    ObjectObservation,
    ProcessingJob,
    TrackedObject,
    VerificationStatus,
)
from app.video import extract_representative_frames, probe_video


def normalize(value: str) -> str:
    return " ".join(re.sub(r"[^\wáéíóúñü]+", " ", value.casefold()).split())


_QUERY_STOP_WORDS = {
    "a",
    "al",
    "con",
    "cual",
    "cuál",
    "de",
    "del",
    "donde",
    "dónde",
    "el",
    "en",
    "esta",
    "está",
    "este",
    "la",
    "las",
    "lo",
    "los",
    "me",
    "mi",
    "por",
    "que",
    "qué",
    "se",
    "sobre",
    "un",
    "una",
    "and",
    "at",
    "find",
    "for",
    "from",
    "how",
    "i",
    "in",
    "is",
    "it",
    "locate",
    "my",
    "of",
    "please",
    "the",
    "this",
    "where",
    "with",
    "est",
    "où",
    "ou",
    "dans",
    "mon",
    "ma",
    "le",
    "les",
    "du",
    "des",
    "wo",
    "ist",
    "mein",
    "meine",
    "der",
    "die",
    "das",
}


def search_phrase(question: str) -> str:
    """Keep only meaningful terms before querying a workspace-local index."""

    return " ".join(
        word
        for word in normalize(question).split()
        if len(word) > 2 and word not in _QUERY_STOP_WORDS
    )


def _candidate_ids_statement(
    workspace_id: uuid.UUID, phrase: str, dialect_name: str
):
    """Build a workspace-scoped candidate query for PostgreSQL or SQLite tests."""

    base = (
        select(TrackedObject.id)
        .outerjoin(ObjectAlias, ObjectAlias.object_id == TrackedObject.id)
        .where(TrackedObject.workspace_id == workspace_id)
    )
    if dialect_name == "postgresql":
        object_vector = func.to_tsvector("simple", TrackedObject.canonical_name)
        alias_vector = func.to_tsvector("simple", ObjectAlias.alias)
        tsquery = func.plainto_tsquery("simple", phrase)
        return base.where(
            or_(
                object_vector.op("@@")(tsquery),
                alias_vector.op("@@")(tsquery),
                func.similarity(TrackedObject.canonical_name, phrase) >= 0.24,
                func.similarity(ObjectAlias.alias, phrase) >= 0.24,
            )
        ).distinct()

    clauses = [TrackedObject.canonical_name.ilike(f"%{word}%") for word in phrase.split()]
    alias_clauses = [ObjectAlias.alias.ilike(f"%{word}%") for word in phrase.split()]
    return base.where(or_(and_(*clauses), and_(*alias_clauses))).distinct()


def create_processing_job(
    db: Session, media: MediaAsset, provider: str, version: str = "v1"
) -> ProcessingJob:
    key = f"{media.capture_session_id}:{media.sha256}:{version}"
    existing = db.scalar(
        select(ProcessingJob).where(
            ProcessingJob.workspace_id == media.workspace_id,
            ProcessingJob.idempotency_key == key,
        )
    )
    if existing:
        return existing
    job = ProcessingJob(
        workspace_id=media.workspace_id,
        media_asset_id=media.id,
        capture_session_id=media.capture_session_id,
        idempotency_key=key,
        provider=provider,
    )
    db.add(job)
    db.flush()
    return job


def process_job(
    db: Session,
    job_id: uuid.UUID,
    client: MetaModelClient,
    *,
    sam_min_confidence: float = 0.65,
    video_segment_seconds: int = 120,
    video_frames_per_segment: int = 8,
) -> ProcessingJob:
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise ValueError("Processing job not found.")
    if job.status == JobStatus.COMPLETED:
        return job
    media = db.get(MediaAsset, job.media_asset_id)
    if media is None:
        job.status = JobStatus.FAILED
        job.error_message = "Source media no longer exists."
        return job
    job.status = JobStatus.PROCESSING
    job.attempts += 1
    job.started_at = datetime.now(UTC)
    try:
        if media.kind == MediaKind.VIDEO:
            # All derived frames and their observations either persist together
            # or roll back together; the original video remains available for a
            # safe retry if any provider call fails.
            with db.begin_nested():
                result_metadata = _process_video_asset(
                    db,
                    media,
                    client,
                    sam_min_confidence,
                    video_segment_seconds,
                    video_frames_per_segment,
                )
        elif media.kind == MediaKind.IMAGE:
            result_metadata = _process_image_asset(db, media, client, sam_min_confidence)
        else:
            raise ValueError(f"Unsupported media kind for processing: {media.kind.value}")
        job.status = JobStatus.COMPLETED
        job.result_metadata = result_metadata
        job.error_message = None
        job.completed_at = datetime.now(UTC)
    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error_message = str(exc)[:1000]
        job.completed_at = datetime.now(UTC)
    return job


def _process_video_asset(
    db: Session,
    video: MediaAsset,
    client: MetaModelClient,
    sam_min_confidence: float,
    video_segment_seconds: int,
    video_frames_per_segment: int,
) -> dict[str, object]:
    info = probe_video(video.original_bytes)
    frames = extract_representative_frames(
        video.original_bytes,
        info,
        segment_seconds=video_segment_seconds,
        frames_per_segment=video_frames_per_segment,
    )
    frame_results: list[dict[str, object]] = []
    existing_frames = {
        int(frame.extra_metadata.get("frame_index", -1)): frame
        for frame in db.scalars(
            select(MediaAsset).where(MediaAsset.parent_asset_id == video.id)
        )
    }
    for extracted in frames:
        frame = existing_frames.get(extracted.index)
        if frame is None:
            digest = media_sha256(extracted.bytes)
            with Image.open(io.BytesIO(extracted.bytes)) as image:
                width, height = image.size
            base_time = video.captured_at or video.created_at
            frame = MediaAsset(
                workspace_id=video.workspace_id,
                # Derived frames may be byte-identical at different timestamps.
                # Keep their traceability through parent_asset_id instead of the
                # source session's hash-deduplication constraint.
                capture_session_id=None,
                parent_asset_id=video.id,
                kind=MediaKind.IMAGE,
                mime_type="image/jpeg",
                original_bytes=extracted.bytes,
                sha256=digest,
                byte_size=len(extracted.bytes),
                width=width,
                height=height,
                captured_at=base_time + timedelta(seconds=extracted.timestamp_seconds),
                extra_metadata={
                    "filename": f"{video.extra_metadata.get('filename', 'video')}-frame-{extracted.index + 1:03d}.jpg",
                    "parent_video_id": str(video.id),
                    "source_capture_session_id": str(video.capture_session_id),
                    "frame_index": extracted.index,
                    "video_segment_index": extracted.segment.index,
                    "segment_start_seconds": round(extracted.segment.start_seconds, 3),
                    "segment_duration_seconds": round(extracted.segment.duration_seconds, 3),
                    "video_timestamp_seconds": round(extracted.timestamp_seconds, 3),
                    "timestamp_is_approximate": True,
                },
            )
            db.add(frame)
            db.flush()
        report = _process_image_asset(db, frame, client, sam_min_confidence)
        frame_results.append(
            {
                "frame_asset_id": str(frame.id),
                "segment_index": extracted.segment.index,
                "timestamp_seconds": round(extracted.timestamp_seconds, 3),
                **report,
            }
        )
    return {
        "simulated": all(bool(item["simulated"]) for item in frame_results),
        "source_kind": "video",
        "duration_seconds": round(info.duration_seconds, 3),
        "segment_seconds": video_segment_seconds,
        "segments_processed": len({frame.segment.index for frame in frames}),
        "frames_extracted": len(frame_results),
        "frames": frame_results,
        "objects_created": [
            object_id for item in frame_results for object_id in item["objects_created"]
        ],
        "segmentation_count": sum(int(item["segmentation_count"]) for item in frame_results),
    }


def _process_image_asset(
    db: Session,
    media: MediaAsset,
    client: MetaModelClient,
    sam_min_confidence: float,
) -> dict[str, object]:
    existing = db.scalar(
        select(ObjectObservation.id).where(ObjectObservation.media_asset_id == media.id).limit(1)
    )
    if existing:
        return {
            "simulated": bool(media.extra_metadata.get("simulated", False)),
            "objects_created": [],
            "segmentation_count": 0,
            "already_processed": True,
        }
    with db.begin_nested():
        source_session_id = media.capture_session_id
        if source_session_id is None and media.parent_asset_id:
            parent = db.get(MediaAsset, media.parent_asset_id)
            source_session_id = parent.capture_session_id if parent else None
        capture_session = db.get(CaptureSession, source_session_id) if source_session_id else None
        context = str(media.extra_metadata.get("filename", ""))
        analysis = client.analyze_image(media.original_bytes, media.mime_type, context)
        created: list[str] = []
        segmentation_count = 0
        for detection in analysis.detections:
            object_name = normalize(detection.label)
            if not object_name:
                continue
            tracked = db.scalar(
                select(TrackedObject).where(
                    TrackedObject.workspace_id == media.workspace_id,
                    TrackedObject.canonical_name == object_name,
                )
            )
            if tracked is None:
                tracked = TrackedObject(
                    workspace_id=media.workspace_id,
                    canonical_name=object_name,
                    category=detection.category,
                    attributes={"simulated": analysis.simulated},
                )
                db.add(tracked)
                db.flush()
                db.add(ObjectAlias(object_id=tracked.id, alias=object_name))
            elif tracked.category is None and detection.category:
                tracked.category = detection.category
            segment = None
            if detection.confidence >= sam_min_confidence:
                segments = client.segment(media.original_bytes, media.mime_type, detection.label)
                segment = next((item for item in segments if item.bounding_box), None)
            if segment:
                segmentation_count += 1
            observation = ObjectObservation(
                workspace_id=media.workspace_id,
                object_id=tracked.id,
                media_asset_id=media.id,
                capture_session_id=source_session_id,
                zone_id=capture_session.zone_id if capture_session else None,
                created_by_id=capture_session.created_by_id if capture_session else None,
                bounding_box=segment.bounding_box if segment else detection.bounding_box,
                spatial_description=detection.spatial_description or (
                    segment.spatial_description if segment else None
                ),
                relationships=detection.relationships,
                seen_at=media.captured_at or media.created_at,
                visual_confidence=detection.confidence,
                model_name=f"{analysis.model}+sam-3.1" if segment else analysis.model,
                verification_status=(
                    VerificationStatus.VERIFIED
                    if analysis.simulated
                    else VerificationStatus.PENDING
                ),
            )
            db.add(observation)
            db.flush()
            created.append(str(observation.id))
        media.extra_metadata = {**media.extra_metadata, "simulated": analysis.simulated}
        return {
            "simulated": analysis.simulated,
            "objects_created": created,
            "segmentation_count": segmentation_count,
        }


def object_candidates(
    db: Session,
    workspace_id: uuid.UUID,
    question: str,
    *,
    additional_terms: list[str] | None = None,
) -> list[TrackedObject]:
    phrases = list(
        dict.fromkeys(
            phrase
            for source in [question, *(additional_terms or [])]
            if (phrase := search_phrase(source))
        )
    )
    if not phrases:
        return []
    dialect_name = db.get_bind().dialect.name
    object_ids = list(
        dict.fromkeys(
            object_id
            for phrase in phrases
            for object_id in db.scalars(
                _candidate_ids_statement(workspace_id, phrase, dialect_name)
            ).unique()
        )
    )
    if not object_ids:
        return []
    return list(
        db.scalars(
            select(TrackedObject)
            .where(TrackedObject.id.in_(object_ids))
            .order_by(TrackedObject.canonical_name)
        )
    )


def workspace_terms(db: Session, workspace_id: uuid.UUID) -> list[str]:
    """Return workspace-local vocabulary only; this is never cross-tenant data."""

    canonical = list(
        db.scalars(
            select(TrackedObject.canonical_name)
            .where(TrackedObject.workspace_id == workspace_id)
            .order_by(TrackedObject.canonical_name)
        )
    )
    aliases = list(
        db.scalars(
            select(ObjectAlias.alias)
            .join(TrackedObject, TrackedObject.id == ObjectAlias.object_id)
            .where(TrackedObject.workspace_id == workspace_id)
            .order_by(ObjectAlias.alias)
        )
    )
    # The request stays bounded even in very large authorized workspaces while
    # preserving all canonical terms before optional aliases.
    return list(dict.fromkeys([*canonical, *aliases]))[:1000]


def exact_term_candidates(
    db: Session, workspace_id: uuid.UUID, question: str
) -> list[TrackedObject]:
    """Prefer an authorized human name/alias over broad lexical similarity."""

    requested = search_phrase(question)
    if not requested:
        return []
    tracked = list(
        db.scalars(
            select(TrackedObject)
            .where(TrackedObject.workspace_id == workspace_id)
            .order_by(TrackedObject.canonical_name)
        )
    )
    aliases_by_object: dict[uuid.UUID, list[str]] = {}
    for object_id, alias in db.execute(
        select(ObjectAlias.object_id, ObjectAlias.alias)
        .join(TrackedObject, TrackedObject.id == ObjectAlias.object_id)
        .where(TrackedObject.workspace_id == workspace_id)
    ):
        aliases_by_object.setdefault(object_id, []).append(alias)
    alias_matches = [
        item
        for item in tracked
        if any(search_phrase(alias) == requested for alias in aliases_by_object.get(item.id, []))
    ]
    if alias_matches:
        return alias_matches
    return [item for item in tracked if search_phrase(item.canonical_name) == requested]


def verified_candidates(
    db: Session, workspace_id: uuid.UUID, candidates: list[TrackedObject]
) -> list[TrackedObject]:
    """Keep exact-name collisions honest without hiding multiple verified items."""

    if not candidates:
        return []
    verified_ids = set(
        db.scalars(
            select(ObjectObservation.object_id)
            .where(
                ObjectObservation.workspace_id == workspace_id,
                ObjectObservation.object_id.in_([candidate.id for candidate in candidates]),
                ObjectObservation.verification_status == VerificationStatus.VERIFIED,
            )
            .distinct()
        )
    )
    return [candidate for candidate in candidates if candidate.id in verified_ids]


def multilingual_object_candidates(
    db: Session,
    workspace_id: uuid.UUID,
    question: str,
    client: MetaModelClient | None,
) -> tuple[list[TrackedObject], bool]:
    """Use the provider only to select existing terms; evidence remains local."""

    exact_candidates = exact_term_candidates(db, workspace_id, question)
    if exact_candidates:
        return exact_candidates, False

    interpreted_terms: list[str] = []
    simulated = False
    if client is not None:
        try:
            interpretation = client.interpret_query(question, workspace_terms(db, workspace_id))
            interpreted_terms = interpretation.terms
            simulated = interpretation.simulated
        except MetaProviderError:
            # Local trigram/FTS search is a safe degraded mode: it never invents
            # a match or makes an unavailable provider look successful.
            pass
    if interpreted_terms:
        return object_candidates(db, workspace_id, interpreted_terms[0], additional_terms=interpreted_terms[1:]), simulated
    return object_candidates(db, workspace_id, question), simulated


def media_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
