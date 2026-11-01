"""Read-only maintenance inventory; unaffected publications never invoke models."""

from sqlalchemy import select
from sqlalchemy.orm import defer

from app.social_features.evidence import usable_detection
from app.social_features.evidence_models import GalleryEvidence, GalleryIndexRun
from app.social_features.index_reviews import prior_candidates
from app.social_features.models import Publication
from app.social_features.retrieval_terms import contains, phrase
from app.social_features.visual import overlap


def current_evidence(db, post):
    rows = db.scalars(
        select(GalleryEvidence)
        .options(defer(GalleryEvidence.image_bytes))
        .where(GalleryEvidence.post_id == post.id, GalleryEvidence.media_id == post.media_id)
        .order_by(GalleryEvidence.version.desc(), GalleryEvidence.created_at.desc())
    )
    selected = []
    for evidence in rows:
        if post.active_index_run_id:
            if evidence.index_run_id != post.active_index_run_id:
                continue
        elif evidence.index_run_id or (evidence.version < 2 and post.evidence_version >= 2):
            continue
        detections = [
            d
            for d in evidence.detections
            if usable_detection(d)
            and (
                d in (post.ai_detections or [])
                or {**d, "frame_timestamp_ms": evidence.frame_timestamp_ms}
                in (post.ai_detections or [])
            )
        ]
        if detections:
            selected.append((evidence, detections))
    return selected


def omitted(db, post):
    current = [(e.frame_timestamp_ms, d) for e, ds in current_evidence(db, post) for d in ds]
    reviewed = {}
    if post.active_index_run_id:
        reviewed = db.get(GalleryIndexRun, post.active_index_run_id).progress.get("reviews", {})
    missing = []
    for candidate in prior_candidates(db, post, True):
        if reviewed.get(candidate["id"]) in {"confirmed", "rejected", "retained"}:
            continue
        old = candidate["detection"]
        if any(
            timestamp == candidate["timestamp"]
            and overlap(d["box"], old["box"]) >= 0.25
            and (
                contains(phrase(d["label"]), phrase(old["label"]))
                or contains(phrase(old["label"]), phrase(d["label"]))
            )
            for timestamp, d in current
        ):
            continue
        missing.append(candidate)
    return missing


def inventory(db):
    items = []
    for post in db.scalars(select(Publication).where(Publication.hidden.is_(False))):
        missing = omitted(db, post) if post.evidence_version >= 2 else []
        if not post.index_error and post.evidence_version >= 2 and not missing:
            continue
        hammer = any(
            any(
                contains(phrase(c["detection"]["label"]), word)
                for word in ("hammer", "hammers", "martillo", "martillos")
            )
            for c in missing
        )
        reason = (
            "failed_analysis"
            if post.index_error
            else "unindexed"
            if post.evidence_version < 2
            else "omitted_detection"
        )
        items.append(
            {
                "post_id": str(post.id),
                "reason": reason,
                "omitted_count": len(missing),
                "priority": 0
                if hammer
                else 1
                if post.source == "workshop"
                else 2
                if post.index_error
                else 3,
                "review_only": post.evidence_version >= 2,
            }
        )
    return sorted(items, key=lambda item: (item["priority"], item["post_id"]))


def pending_inventory(db):
    """Only unfinished search work, including reviews on an active generation."""
    items = []
    for post in db.scalars(select(Publication).where(Publication.hidden.is_(False))):
        active = (
            db.get(GalleryIndexRun, post.active_index_run_id) if post.active_index_run_id else None
        )
        if (
            post.index_error
            or post.evidence_version < 2
            or active
            and active.progress.get("review_pending")
        ):
            items.append(
                {
                    "post_id": str(post.id),
                    "media_id": str(post.media_id),
                    "review_only": post.evidence_version >= 2,
                }
            )
    return sorted(items, key=lambda item: (not item["review_only"], item["post_id"]))
