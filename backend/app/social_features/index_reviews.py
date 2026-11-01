"""Review omitted detections on the immutable source before changing search."""

import hashlib
import json
import math
import uuid

from sqlalchemy import select
from sqlalchemy.orm import defer

from app.meta import MetaProviderError
from app.schemas import MetaDetection
from app.social_features.evidence_models import GalleryEvidence, GalleryIndexRun
from app.social_features.review_localization import localize
from app.social_features.visual import MIN_CONFIDENCE, normalize, overlap, valid_box


def prior_candidates(db, post, recover_legacy=False):
    from app.social_features.evidence import usable_detection

    rows = db.scalars(
        select(GalleryEvidence)
        .options(defer(GalleryEvidence.image_bytes))
        .where(GalleryEvidence.post_id == post.id, GalleryEvidence.media_id == post.media_id)
        .order_by(GalleryEvidence.version.desc(), GalleryEvidence.created_at.desc())
    )
    selected, seen = [], set()
    for evidence in rows:
        if evidence.index_run_id and evidence.index_run_id != post.active_index_run_id:
            old_run = db.get(GalleryIndexRun, evidence.index_run_id)
            if not recover_legacy or old_run.status != "ready":
                continue
        for detection in evidence.detections:
            if not usable_detection(detection):
                continue
            active = (
                (
                    evidence.index_run_id == post.active_index_run_id
                    and evidence.index_run_id is not None
                )
                or (not post.active_index_run_id and detection in (post.ai_detections or []))
                or (
                    not post.active_index_run_id
                    and {**detection, "frame_timestamp_ms": evidence.frame_timestamp_ms}
                    in (post.ai_detections or [])
                )
            )
            if not active and not recover_legacy:
                continue
            key = hashlib.sha256(
                json.dumps([evidence.frame_timestamp_ms, detection], sort_keys=True).encode()
            ).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            selected.append(
                {
                    "id": key,
                    "evidence_id": str(evidence.id),
                    "timestamp": evidence.frame_timestamp_ms,
                    "active": active,
                    "detection": detection,
                }
            )
    return selected


def review_omissions(db, post, asset, client, run, pending, checkpoint):
    previous = run.progress.get("prior", [])
    reviews = dict(run.progress.get("reviews", {}))
    details = dict(run.progress.get("review_details", {}))

    def save_reviews():
        run.progress = {
            **run.progress,
            "reviews": reviews,
            "review_details": details,
            "review_pending": sum(value == "uncertain" for value in reviews.values()),
        }
        checkpoint()

    by_frame = {}
    for candidate in previous:
        old = candidate["detection"]
        fresh = [
            d
            for evidence in pending
            if evidence.frame_timestamp_ms == candidate["timestamp"]
            for d in evidence.detections
        ]
        if any(
            d["label"].casefold() == old["label"].casefold()
            and overlap(d["box"], old["box"]) >= 0.25
            for d in fresh
        ):
            reviews[candidate["id"]] = "retained"
            continue
        if reviews.get(candidate["id"]) in {"confirmed", "rejected"}:
            continue
        by_frame.setdefault(candidate["timestamp"], []).append(candidate)
    uncertain = False
    for timestamp, candidates in by_frame.items():
        source = db.get(GalleryEvidence, uuid.UUID(candidates[0]["evidence_id"]))
        raw = asset.original_bytes if timestamp is None else source.image_bytes
        image, width, height, digest, _ = normalize(raw)
        if timestamp is None and source.content_hash != digest:
            raise MetaProviderError(
                "Previous evidence belongs to different image pixels.", phase="review"
            )
        selected = [
            {"id": c["id"], "label": c["detection"]["label"], "box": c["detection"]["box"]}
            for c in candidates
        ]
        result = client.review_gallery_objects(image, selected)
        if len(result) != len(selected) or {r["id"] for r in result} != {c["id"] for c in selected}:
            raise MetaProviderError("Incomplete object review.", phase="review")
        confirmed = []
        for answer in result:
            details[answer["id"]] = {
                key: answer.get(key) for key in ("verdict", "confidence", "box")
            }
            candidate = next(c for c in candidates if c["id"] == answer["id"])
            verdict = answer["verdict"]
            if verdict == "rejected" and answer["confidence"] >= 0.8:
                reviews[answer["id"]] = "rejected"
            elif (
                verdict == "confirmed"
                and answer["confidence"] >= MIN_CONFIDENCE
                and valid_box(answer.get("box"))
            ):
                confirmed.append(
                    (
                        {**candidate, "crop": answer.get("_crop")},
                        MetaDetection(
                            label=candidate["detection"]["label"],
                            confidence=answer["confidence"],
                            bounding_box=valid_box(answer["box"]),
                        ),
                    )
                )
            else:
                reviews[answer["id"]] = "uncertain"
                uncertain |= candidate.get("active", True)
        localized = []
        for candidate, item in confirmed:
            value, method = localize(client, image, width, height, item, candidate.get("crop"))
            details[candidate["id"]]["localization_method"] = method
            localized.append(value)
        if len(localized) != len(confirmed):
            raise MetaProviderError("Incomplete reviewed localization.", phase="review")
        detections = []
        for (candidate, item), mask in zip(confirmed, localized):
            box = valid_box(mask.bounding_box) if mask else None
            details[candidate["id"]]["localization_confidence"] = (
                mask.confidence
                if mask and (mask.confidence is None or math.isfinite(mask.confidence))
                else None
            )
            if (
                mask is None
                or box is None
                or not any(mask.mask)
                or (
                    mask.confidence is not None
                    and (not math.isfinite(mask.confidence) or mask.confidence < MIN_CONFIDENCE)
                )
            ):
                reviews[candidate["id"]] = "uncertain"
                uncertain |= candidate.get("active", True)
                continue
            detections.append(
                dict(
                    label=item.label,
                    box=box,
                    confidence=item.confidence,
                    localization_confidence=mask.confidence,
                    model=mask.model,
                    simulated=mask.simulated,
                )
            )
            reviews[candidate["id"]] = "confirmed"
        if detections:
            evidence = GalleryEvidence(
                post_id=post.id,
                media_id=asset.id,
                image_bytes=image,
                content_hash=digest,
                frame_timestamp_ms=timestamp,
                detections=detections,
                version=2,
                index_run_id=run.id,
            )
            db.add(evidence)
            pending.append(evidence)
        save_reviews()
    if not by_frame:
        # Resumed evidence can resolve every prior object before model review.
        # Persist those verdicts too, otherwise the old warning never clears.
        save_reviews()
    return uncertain
