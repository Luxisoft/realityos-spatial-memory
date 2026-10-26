from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import or_, select
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


def process_job(db: Session, job_id: uuid.UUID, client: MetaModelClient) -> ProcessingJob:
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
        for detection in analysis.detections:
            object_name = normalize(detection.label)
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
                    attributes={"simulated": analysis.simulated},
                )
                db.add(tracked)
                db.flush()
                db.add(ObjectAlias(object_id=tracked.id, alias=object_name))
            duplicate = db.scalar(
                select(ObjectObservation).where(
                    ObjectObservation.object_id == tracked.id,
                    ObjectObservation.media_asset_id == media.id,
                )
            )
            if duplicate:
                continue
            observation = ObjectObservation(
                workspace_id=media.workspace_id,
                object_id=tracked.id,
                media_asset_id=media.id,
                capture_session_id=media.capture_session_id,
                zone_id=capture_session.zone_id if capture_session else None,
                created_by_id=capture_session.created_by_id if capture_session else None,
                bounding_box=detection.bounding_box,
                spatial_description=detection.spatial_description,
                seen_at=media.captured_at or media.created_at,
                visual_confidence=detection.confidence,
                model_name=analysis.model,
                verification_status=(
                    VerificationStatus.VERIFIED
                    if analysis.simulated
                    else VerificationStatus.PENDING
                ),
            )
            db.add(observation)
            created.append(str(observation.id))
        job.status = JobStatus.COMPLETED
        job.result_metadata = {"simulated": analysis.simulated, "objects_created": created}
        job.completed_at = datetime.now(UTC)
    except Exception as exc:
        job.status = JobStatus.FAILED
        job.error_message = str(exc)[:1000]
        job.completed_at = datetime.now(UTC)
    return job


def object_candidates(db: Session, workspace_id: uuid.UUID, question: str) -> list[TrackedObject]:
    query = normalize(question)
    words = [word for word in query.split() if len(word) > 2 and word not in {"donde", "esta"}]
    if not words:
        return []
    clauses = [TrackedObject.canonical_name.ilike(f"%{word}%") for word in words]
    alias_clauses = [ObjectAlias.alias.ilike(f"%{word}%") for word in words]
    return list(
        db.scalars(
            select(TrackedObject)
            .outerjoin(ObjectAlias, ObjectAlias.object_id == TrackedObject.id)
            .where(
                TrackedObject.workspace_id == workspace_id,
                or_(*clauses, *alias_clauses),
            )
            .distinct()
        )
    )


def media_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
