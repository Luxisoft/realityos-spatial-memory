from __future__ import annotations

import hashlib
import io
import re
import tempfile
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from PIL import Image
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.meta import (
    MetaModelClient,
    MetaProviderError,
    MetaProviderUncertainError,
    VideoTrackPrompt,
)
from app.models import (
    CaptureSession,
    FactProvenance,
    JobStatus,
    MediaAsset,
    MediaAssetChunk,
    MediaKind,
    ObjectAlias,
    ObjectFact,
    ObjectObservation,
    ObjectTrack,
    ObjectTrackFrame,
    ObjectTrackSegment,
    ProcessingJob,
    ProcessingOperation,
    TrackedObject,
    VerificationStatus,
)
from app.video import (
    extract_representative_frames_from_file,
    materialized_video_clips,
    probe_video_file,
)

CHUNKED_POSTGRES_BYTEA = "chunked_postgres_bytea"


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
    db: Session,
    media: MediaAsset,
    provider: str,
    version: str = "v1",
    *,
    profile: str = "basic",
    priority_terms: list[str] | None = None,
) -> ProcessingJob:
    """Create an idempotent analysis job with an explicit processing profile."""

    normalized_priorities = sorted({normalize(item) for item in (priority_terms or []) if normalize(item)})
    priority_digest = hashlib.sha256(",".join(normalized_priorities).encode()).hexdigest()[:16]
    key = f"{media.capture_session_id}:{media.sha256}:{version}:{profile}:{priority_digest}"
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
        operation=ProcessingOperation.ANALYSIS,
        result_metadata={"profile": profile, "priority_terms": normalized_priorities},
    )
    db.add(job)
    db.flush()
    return job


def create_segmentation_job(
    db: Session, observation: ObjectObservation, provider: str
) -> ProcessingJob:
    """Return the one durable SAM refinement job for an observation.

    A completed mask is immutable evidence derived from a particular source
    asset. The unique key makes repeated button presses and concurrent clients
    reuse the same result instead of sending paid SAM requests again.
    """

    media = db.get(MediaAsset, observation.media_asset_id)
    if media is None:
        raise ValueError("Source media no longer exists.")
    key = f"segmentation:{observation.id}:sam-3.1:{media.sha256}"
    existing = db.scalar(
        select(ProcessingJob).where(
            ProcessingJob.workspace_id == observation.workspace_id,
            ProcessingJob.idempotency_key == key,
        )
    )
    if existing:
        return existing
    job = ProcessingJob(
        workspace_id=observation.workspace_id,
        media_asset_id=media.id,
        capture_session_id=observation.capture_session_id,
        observation_id=observation.id,
        operation=ProcessingOperation.SEGMENTATION,
        idempotency_key=key,
        provider=provider,
        status=JobStatus.COMPLETED if observation.mask_asset_id else JobStatus.QUEUED,
        result_metadata={"segmentation_status": "ready"}
        if observation.mask_asset_id
        else {},
        completed_at=datetime.now(UTC) if observation.mask_asset_id else None,
    )
    try:
        with db.begin_nested():
            db.add(job)
            db.flush()
    except IntegrityError:
        existing = db.scalar(
            select(ProcessingJob).where(
                ProcessingJob.workspace_id == observation.workspace_id,
                ProcessingJob.idempotency_key == key,
            )
        )
        if existing is None:
            raise
        return existing
    return job


def process_job(
    db: Session,
    job_id: uuid.UUID,
    client: MetaModelClient,
    *,
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
        if job.operation == ProcessingOperation.SEGMENTATION:
            result_metadata = _process_segmentation_job(db, job, media, client)
        elif media.kind == MediaKind.VIDEO:
            # All derived frames and their observations either persist together
            # or roll back together; the original video remains available for a
            # safe retry if any provider call fails.
            with db.begin_nested():
                result_metadata = _process_video_asset(
                    db,
                    media,
                    client,
                    video_segment_seconds,
                    video_frames_per_segment,
                    job=job,
                )
        elif media.kind == MediaKind.IMAGE:
            result_metadata = _process_image_asset(db, media, client)
        else:
            raise ValueError(f"Unsupported media kind for processing: {media.kind.value}")
        job.status = JobStatus.COMPLETED
        job.result_metadata = {**job.result_metadata, **result_metadata}
        job.error_message = None
        job.completed_at = datetime.now(UTC)
    except MetaProviderUncertainError as exc:
        job.status = JobStatus.UNCERTAIN
        job.error_message = str(exc)[:1000]
        job.result_metadata = {**job.result_metadata, "external_request_state": "uncertain"}
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
    video_segment_seconds: int,
    video_frames_per_segment: int,
    *,
    job: ProcessingJob,
) -> dict[str, object]:
    with materialized_media_file(db, video) as source:
        info = probe_video_file(source)
        frames = extract_representative_frames_from_file(
            source,
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
        report = _process_image_asset(db, frame, client)
        frame_results.append(
            {
                "frame_asset_id": str(frame.id),
                "segment_index": extracted.segment.index,
                "timestamp_seconds": round(extracted.timestamp_seconds, 3),
                **report,
            }
        )
    result: dict[str, object] = {
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
    if job.result_metadata.get("profile") == "detailed":
        result["detailed_tracking"] = _process_detailed_video_tracking(
            db,
            video,
            info,
            client,
            job,
            segment_seconds=video_segment_seconds,
        )
    return result


def _priority_matches(name: str, terms: list[str]) -> bool:
    normalized_name = normalize(name)
    return any(term == normalized_name or term in normalized_name or normalized_name in term for term in terms)


def _process_detailed_video_tracking(
    db: Session,
    video: MediaAsset,
    info,
    client: MetaModelClient,
    job: ProcessingJob,
    *,
    segment_seconds: int,
) -> dict[str, object]:
    """Track explicitly selected objects across every decoded frame of each clip.

    The original video stays in PostgreSQL; temporary faststart MP4 clips are
    deleted by the worker and Meta Files API is used only by the live provider.
    """

    priorities = [normalize(value) for value in job.result_metadata.get("priority_terms", [])]
    priorities = [value for value in priorities if value]
    if not priorities:
        return {"status": "skipped", "reason": "detailed mode requires priority_terms"}
    rows = list(
        db.execute(
            select(TrackedObject, ObjectObservation, MediaAsset)
            .join(ObjectObservation, ObjectObservation.object_id == TrackedObject.id)
            .join(MediaAsset, MediaAsset.id == ObjectObservation.media_asset_id)
            .where(
                ObjectObservation.workspace_id == video.workspace_id,
                MediaAsset.parent_asset_id == video.id,
            )
            .order_by(ObjectObservation.seen_at)
        )
    )
    candidates: dict[uuid.UUID, tuple[TrackedObject, list[tuple[ObjectObservation, MediaAsset]]]] = {}
    for tracked, observation, frame in rows:
        if not _priority_matches(tracked.canonical_name, priorities):
            continue
        current = candidates.setdefault(tracked.id, (tracked, []))
        current[1].append((observation, frame))
    if not candidates:
        return {"status": "skipped", "reason": "no priority object observed in representative frames"}
    if len(candidates) > 16:
        return {"status": "skipped", "reason": "more than 16 priority objects require separate jobs"}

    tracks: dict[uuid.UUID, ObjectTrack] = {}
    for object_id, (tracked, _) in candidates.items():
        track = db.scalar(
            select(ObjectTrack).where(
                ObjectTrack.source_media_asset_id == video.id, ObjectTrack.object_id == object_id
            )
        )
        if track is None:
            track = ObjectTrack(
                workspace_id=video.workspace_id,
                object_id=object_id,
                source_media_asset_id=video.id,
                processing_job_id=job.id,
                model_name="sam-3.1" if job.provider == "live" else "mock-sam-3.1",
                status="processing",
                metadata_json={"priority_terms": priorities},
            )
            db.add(track)
            db.flush()
        tracks[object_id] = track

    last_boxes: dict[uuid.UUID, dict[str, float]] = {}
    for object_id, track in tracks.items():
        latest = db.scalar(
            select(ObjectTrackFrame)
            .where(ObjectTrackFrame.track_id == track.id, ObjectTrackFrame.visible.is_(True))
            .order_by(desc(ObjectTrackFrame.pts_seconds))
        )
        if latest and latest.bounding_box:
            last_boxes[object_id] = latest.bounding_box

    total_frames = 0
    visible_frames = 0
    clips_processed = 0
    with materialized_media_file(db, video) as source:
        with materialized_video_clips(source, info, segment_seconds=segment_seconds) as clips:
            for clip in clips:
                prompt_by_object: dict[uuid.UUID, VideoTrackPrompt] = {}
                for object_id, (_, observations) in candidates.items():
                    seed = next(
                        (
                            (observation, frame)
                            for observation, frame in observations
                            if int(frame.extra_metadata.get("video_segment_index", -1))
                            == clip.segment.index
                            and (observation.muse_bounding_box or observation.bounding_box)
                        ),
                        None,
                    )
                    if seed:
                        observation, frame = seed
                        timestamp = float(frame.extra_metadata.get("video_timestamp_seconds", clip.segment.start_seconds))
                        relative = max(0.0, timestamp - clip.segment.start_seconds)
                        frame_index = min(
                            clip.frame_count - 1,
                            int(relative / max(clip.segment.duration_seconds, 0.001) * clip.frame_count),
                        )
                        prompt_by_object[object_id] = VideoTrackPrompt(
                            object_id=str(tracks[object_id].id),
                            frame_index=frame_index,
                            bounding_box=observation.muse_bounding_box or observation.bounding_box,
                        )
                    elif object_id in last_boxes:
                        prompt_by_object[object_id] = VideoTrackPrompt(
                            object_id=str(tracks[object_id].id),
                            frame_index=0,
                            bounding_box=last_boxes[object_id],
                        )
                if not prompt_by_object:
                    continue
                segments: dict[uuid.UUID, ObjectTrackSegment] = {}
                for object_id in prompt_by_object:
                    track = tracks[object_id]
                    segment = db.scalar(
                        select(ObjectTrackSegment).where(
                            ObjectTrackSegment.track_id == track.id,
                            ObjectTrackSegment.segment_index == clip.segment.index,
                        )
                    )
                    if segment is None:
                        segment = ObjectTrackSegment(
                            track_id=track.id,
                            segment_index=clip.segment.index,
                            start_pts_seconds=clip.segment.start_seconds,
                            end_pts_seconds=clip.segment.start_seconds + clip.segment.duration_seconds,
                            request_state="submitted",
                        )
                        db.add(segment)
                        db.flush()
                    segments[object_id] = segment
                # The live implementation uploads once, streams once and never retries this call.
                tracking = client.track_video(
                    clip.path,
                    width=info.width or 1,
                    height=info.height or 1,
                    frame_count=clip.frame_count,
                    prompts=list(prompt_by_object.values()),
                )
                result_by_track_frame = {
                    (item.object_id, item.frame_index): item for item in tracking.frames
                }
                for object_id, segment in segments.items():
                    track = tracks[object_id]
                    segment.provider_file_id = tracking.provider_file_id
                    segment.request_state = "completed"
                    existing = set(
                        db.scalars(
                            select(ObjectTrackFrame.source_frame_index).where(
                                ObjectTrackFrame.track_id == track.id,
                                ObjectTrackFrame.source_frame_index >= clip.source_frame_offset,
                                ObjectTrackFrame.source_frame_index
                                < clip.source_frame_offset + clip.frame_count,
                            )
                        )
                    )
                    for frame_index in range(clip.frame_count):
                        source_index = clip.source_frame_offset + frame_index
                        if source_index in existing:
                            continue
                        item = result_by_track_frame.get((str(track.id), frame_index))
                        rel_pts = (
                            clip.frame_pts_seconds[frame_index]
                            if frame_index < len(clip.frame_pts_seconds)
                            else frame_index
                            / max(info.frame_rate or (clip.frame_count / clip.segment.duration_seconds), 0.001)
                        )
                        pts = clip.segment.start_seconds + rel_pts
                        db.add(
                            ObjectTrackFrame(
                                track_id=track.id,
                                track_segment_id=segment.id,
                                source_frame_index=source_index,
                                pts_seconds=pts,
                                visible=item is not None,
                                bounding_box=item.bounding_box if item else None,
                                mask_rle=item.mask_rle if item else None,
                                mask_width=item.mask_width if item else None,
                                mask_height=item.mask_height if item else None,
                                confidence=item.confidence if item else None,
                                simulated=tracking.simulated,
                            )
                        )
                        total_frames += 1
                        if item and item.bounding_box:
                            visible_frames += 1
                            last_boxes[object_id] = item.bounding_box
                            track.last_seen_pts_seconds = pts
                            base_time = video.captured_at or video.created_at
                            track.last_seen_at = base_time + timedelta(seconds=pts)
                clips_processed += 1
    for track in tracks.values():
        track.status = "completed"
    return {
        "status": "completed",
        "tracks": len(tracks),
        "clips_processed": clips_processed,
        "frames_persisted": total_frames,
        "visible_frames": visible_frames,
        "simulated": job.provider == "mock",
        "mask_encoding": "realityos-rle-v1",
    }


def _process_image_asset(
    db: Session,
    media: MediaAsset,
    client: MetaModelClient,
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
            observation = ObjectObservation(
                workspace_id=media.workspace_id,
                object_id=tracked.id,
                media_asset_id=media.id,
                capture_session_id=source_session_id,
                zone_id=capture_session.zone_id if capture_session else None,
                created_by_id=capture_session.created_by_id if capture_session else None,
                muse_bounding_box=detection.bounding_box,
                bounding_box=detection.bounding_box,
                spatial_description=detection.spatial_description,
                relationships=detection.relationships,
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
            db.flush()
            fact_summary = dict(tracked.attributes or {})
            for fact in detection.facts:
                value = fact.value_text or fact.normalized_value
                db.add(
                    ObjectFact(
                        workspace_id=media.workspace_id,
                        object_id=tracked.id,
                        observation_id=observation.id,
                        fact_type=fact.fact_type,
                        value_text=fact.value_text,
                        normalized_value=normalize(fact.normalized_value or value or "") or None,
                        numeric_value=fact.numeric_value,
                        unit=fact.unit,
                        confidence=fact.confidence,
                        provenance=FactProvenance(fact.provenance),
                        evidence_geometry=detection.bounding_box,
                        model_name=analysis.model,
                        verification_status=(
                            VerificationStatus.VERIFIED
                            if analysis.simulated
                            else VerificationStatus.PENDING
                        ),
                    )
                )
                if fact.fact_type != "visible_count" and value:
                    fact_summary[fact.fact_type] = value
                elif fact.fact_type == "visible_count" and fact.numeric_value is not None:
                    fact_summary["visible_count"] = fact.numeric_value
            tracked.attributes = fact_summary
            created.append(str(observation.id))
        media.extra_metadata = {**media.extra_metadata, "simulated": analysis.simulated}
        return {
            "simulated": analysis.simulated,
            "objects_created": created,
            "segmentation_count": segmentation_count,
        }


def _mask_png(mask: bytes, width: int, height: int) -> bytes:
    """Persist SAM's decoded one-bit raster as a compact PostgreSQL PNG."""

    if width < 1 or height < 1 or len(mask) != width * height:
        raise ValueError("SAM returned an invalid mask raster.")
    # The official parser returns one byte per pixel (0 or 1). PNG mode 1
    # stores the final evidence compactly without losing its binary geometry.
    pixels = bytes(255 if value else 0 for value in mask)
    image = Image.frombytes("L", (width, height), pixels).convert("1")
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


def _process_segmentation_job(
    db: Session,
    job: ProcessingJob,
    media: MediaAsset,
    client: MetaModelClient,
) -> dict[str, object]:
    """Create a cached SAM mask without changing the observation's evidence."""

    if job.observation_id is None:
        raise ValueError("Segmentation job has no observation.")
    observation = db.get(ObjectObservation, job.observation_id)
    if observation is None or observation.workspace_id != job.workspace_id:
        raise ValueError("Observation no longer exists.")
    if observation.media_asset_id != media.id:
        raise ValueError("Segmentation source does not match its observation.")
    if observation.mask_asset_id:
        return {"segmentation_status": "ready", "already_segmented": True}
    if media.kind not in {MediaKind.IMAGE, MediaKind.FRAME}:
        raise ValueError("SAM refinement requires an image observation.")
    source_box = observation.muse_bounding_box or observation.bounding_box
    if not source_box:
        raise ValueError("The observation has no approximate box to refine.")
    tracked = db.get(TrackedObject, observation.object_id)
    if tracked is None:
        raise ValueError("Tracked object no longer exists.")
    with Image.open(io.BytesIO(media.original_bytes)) as image:
        width, height = image.size
    result = client.segment(
        media.original_bytes,
        media.mime_type,
        prompt=tracked.canonical_name,
        width=width,
        height=height,
        bounding_box=source_box,
    )
    if result is None:
        return {"segmentation_status": "no_match", "model": "sam-3.1"}
    png = _mask_png(result.mask, result.mask_width, result.mask_height)
    mask_asset = MediaAsset(
        workspace_id=media.workspace_id,
        capture_session_id=None,
        parent_asset_id=media.id,
        kind=MediaKind.MASK,
        mime_type="image/png",
        original_bytes=png,
        sha256=media_sha256(png),
        byte_size=len(png),
        width=result.mask_width,
        height=result.mask_height,
        captured_at=media.captured_at,
        extra_metadata={
            "source_observation_id": str(observation.id),
            "source_media_id": str(media.id),
            "model": result.model,
            "prompt": tracked.canonical_name,
            "prompt_type": "box",
            "simulated": result.simulated,
            "mask_encoding": "one_bit",
            "source_width": width,
            "source_height": height,
            "sam_bounding_box": result.bounding_box,
            "sam_confidence": result.confidence,
        },
    )
    db.add(mask_asset)
    db.flush()
    observation.mask_asset_id = mask_asset.id
    observation.bounding_box = result.bounding_box
    return {
        "segmentation_status": "ready",
        "mask_asset_id": str(mask_asset.id),
        "model": result.model,
        "simulated": result.simulated,
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


def media_is_chunked(asset: MediaAsset) -> bool:
    return asset.extra_metadata.get("storage") == CHUNKED_POSTGRES_BYTEA


def add_postgres_bytea_chunks(
    db: Session, asset: MediaAsset, content: bytes, chunk_bytes: int
) -> None:
    """Keep an oversized original entirely in PostgreSQL without one huge BYTEA."""

    if chunk_bytes < 1:
        raise ValueError("chunk_bytes must be positive.")
    if not content:
        raise ValueError("content must not be empty.")
    asset.original_bytes = b""
    asset.extra_metadata = {
        **asset.extra_metadata,
        "storage": CHUNKED_POSTGRES_BYTEA,
        "chunk_size_bytes": chunk_bytes,
        "chunk_count": (len(content) + chunk_bytes - 1) // chunk_bytes,
    }
    db.add_all(
        MediaAssetChunk(
            asset_id=asset.id,
            chunk_index=index,
            content=content[offset : offset + chunk_bytes],
            byte_size=min(chunk_bytes, len(content) - offset),
        )
        for index, offset in enumerate(range(0, len(content), chunk_bytes))
    )


@contextmanager
def materialized_media_file(db: Session, asset: MediaAsset):
    """Materialize BYTEA chunks only in a scoped worker temp file for FFmpeg."""

    with tempfile.TemporaryDirectory(prefix="realityos-media-") as directory:
        path = Path(directory) / "source-media"
        with path.open("wb") as output:
            if media_is_chunked(asset):
                chunks = db.scalars(
                    select(MediaAssetChunk.content)
                    .where(MediaAssetChunk.asset_id == asset.id)
                    .order_by(MediaAssetChunk.chunk_index)
                )
                total = 0
                for chunk in chunks:
                    output.write(chunk)
                    total += len(chunk)
                if total != asset.byte_size:
                    raise ValueError("Stored media chunks do not match the recorded byte size.")
            else:
                output.write(asset.original_bytes)
        yield path
