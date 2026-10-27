from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.meta import MetaModelClient
from app.models import (
    CaptureSession,
    JobStatus,
    MediaAsset,
    ObjectAlias,
    ObjectObservation,
    ProcessingJob,
    TrackedObject,
    VerificationStatus,
)


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
    return base.where(or_(*clauses, *alias_clauses)).distinct()


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
        capture_session = (
            db.get(CaptureSession, media.capture_session_id) if media.capture_session_id else None
        )
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
            duplicate = db.scalar(
                select(ObjectObservation).where(
                    ObjectObservation.object_id == tracked.id,
                    ObjectObservation.media_asset_id == media.id,
                )
            )
            if duplicate:
                continue
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
                capture_session_id=media.capture_session_id,
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
            created.append(str(observation.id))
        job.status = JobStatus.COMPLETED
        job.result_metadata = {
            "simulated": analysis.simulated,
            "objects_created": created,
            "segmentation_count": segmentation_count,
        }
        job.completed_at = datetime.now(UTC)
    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error_message = str(exc)[:1000]
        job.completed_at = datetime.now(UTC)
    return job


def object_candidates(db: Session, workspace_id: uuid.UUID, question: str) -> list[TrackedObject]:
    phrase = search_phrase(question)
    if not phrase:
        return []
    dialect_name = db.get_bind().dialect.name
    object_ids = list(
        db.scalars(_candidate_ids_statement(workspace_id, phrase, dialect_name)).unique()
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


def media_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
