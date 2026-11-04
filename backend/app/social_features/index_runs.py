"""Checkpointed candidate generations; only completed runs can replace search."""

import os
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.models import MediaAsset
from app.providers.contracts import MetaProviderError
from app.social_features.evidence_models import GalleryEvidence, GalleryIndexRun
from app.social_features.index_reviews import prior_candidates, review_omissions
from app.social_features.visual import INDEX_VERSION


class ReviewPending(MetaProviderError):
    pass


def error_details(error, phase):
    return {
        "stage": getattr(error, "phase", None) or phase,
        "status_code": getattr(error, "status_code", None),
        "retryable": bool(getattr(error, "retryable", False)),
        "message": str(error)[:1000],
    }


def configuration():
    return {
        "revision": 1,
        "max_frames": os.environ.get("GALLERY_MAX_VIDEO_FRAMES", "120"),
        "step": os.environ.get("GALLERY_VIDEO_STEP_SECONDS", "2"),
    }


def process_run(db, post, client, *, checkpoint=False, recover_legacy=False, review_only=False):
    from app.social_features.evidence_index import stage_evidence
    from app.social_features.localizations import prepare_posts

    db.flush()
    db.refresh(post, with_for_update=True)
    if post.hidden:
        return []
    asset = db.get(MediaAsset, post.media_id)
    if asset is None:
        raise MetaProviderError("Source media unavailable.", phase="source")
    now = datetime.now(UTC)
    run = db.scalar(
        select(GalleryIndexRun)
        .where(
            GalleryIndexRun.post_id == post.id,
            GalleryIndexRun.media_id == asset.id,
            GalleryIndexRun.source_hash == asset.sha256,
            GalleryIndexRun.status.in_(["running", "failed", "needs_review"]),
        )
        .order_by(GalleryIndexRun.created_at.desc())
        .limit(1)
        .with_for_update()
    )
    if (
        run
        and run.status == "running"
        and run.lease_until
        and run.lease_until.replace(tzinfo=UTC) > now
    ):
        return None  # A second task must not repeat live inference.
    if run and run.progress.get("configuration") != configuration():
        run.status = "superseded"
        run = None
    if run is None:
        run = GalleryIndexRun(
            post_id=post.id,
            media_id=asset.id,
            source_hash=asset.sha256,
            status="running",
            stage="detection",
            attempt=1,
            lease=str(uuid.uuid4()),
            lease_until=now + timedelta(minutes=30),
            progress={
                "configuration": configuration(),
                "prior": prior_candidates(db, post, recover_legacy),
                "completed_frames": [],
            },
        )
        db.add(run)
        db.flush()
    else:
        run.status = "running"
        run.attempt += 1
        run.lease = str(uuid.uuid4())
        run.lease_until = now + timedelta(minutes=30)
        run.error = None
        if recover_legacy:
            merged = {c["id"]: c for c in run.progress.get("prior", [])}
            merged.update({c["id"]: c for c in prior_candidates(db, post, True)})
            run.progress = {**run.progress, "prior": list(merged.values())}
    lease = run.lease
    source_id, source_hash = asset.id, asset.sha256

    def save():
        run.updated_at = datetime.now(UTC)
        run.lease_until = run.updated_at + timedelta(minutes=30)
        db.flush()
        if checkpoint:
            db.commit()
            db.refresh(post, with_for_update=True)
            db.refresh(run, with_for_update=True)
            db.refresh(asset)
        if (
            post.hidden
            or post.media_id != source_id
            or asset.sha256 != source_hash
            or run.lease != lease
        ):
            raise MetaProviderError("Publication changed while analyzing.", phase="source")

    save()
    try:
        if review_only and not run.progress.get("frames_complete"):
            from app.social_features.repair_inventory import current_evidence

            for evidence, detections in current_evidence(db, post):
                db.add(
                    GalleryEvidence(
                        post_id=post.id,
                        media_id=asset.id,
                        image_bytes=evidence.image_bytes,
                        content_hash=evidence.content_hash,
                        frame_timestamp_ms=evidence.frame_timestamp_ms,
                        detections=detections,
                        version=evidence.version,
                        index_run_id=run.id,
                    )
                )
            run.progress = {**run.progress, "frames_complete": True}
            save()
        if not run.progress.get("frames_complete"):
            stage_evidence(db, post, client, run, save)
        pending = list(
            db.scalars(select(GalleryEvidence).where(GalleryEvidence.index_run_id == run.id))
        )
        run.stage = "review"
        if review_omissions(db, post, asset, client, run, pending, save):
            raise ReviewPending("Some previous objects require review.", phase="review")
        run.stage = "translation"
        # All visible mirrors and both language maps are activated together.
        with db.begin_nested():
            collected = [
                {**d, "frame_timestamp_ms": e.frame_timestamp_ms}
                for e in pending
                for d in e.detections
            ]
            post.ai_detections = collected
            post.ai_labels = list(dict.fromkeys(d["label"] for d in collected))
            post.ai_caption = "; ".join(post.ai_labels)[:1000]
            post.search_text = " ".join([post.caption or "", *post.ai_labels])[:8000]
            prepare_posts(db, [post], client)
            post.active_index_run_id = run.id
            post.evidence_version = INDEX_VERSION
            post.indexed_at = datetime.now(UTC)
            post.index_error = None
            asset.extra_metadata = {
                **(asset.extra_metadata or {}),
                "gallery_index_version": INDEX_VERSION,
                **{
                    key: run.progress[key]
                    for key in ("visual_hash", "pixel_hash")
                    if key in run.progress
                },
            }
            run.status = "ready"
            run.stage = "complete"
            run.error = None
            run.lease_until = None
            db.flush()
        if checkpoint:
            db.commit()
        return pending
    except (MetaProviderError, ValueError, OSError) as error:
        details = error_details(error, run.stage)
        run.status = "needs_review" if isinstance(error, ReviewPending) else "failed"
        run.error = details
        run.lease_until = None
        post.index_error = f"{details['stage']}: {details['message']}"[:1000]
        db.flush()
        if checkpoint:
            db.commit()
        return []
