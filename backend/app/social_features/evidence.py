"""Read-only, authorized annotation rendering and unique search results."""

from __future__ import annotations

import io
import math
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from PIL import Image, ImageDraw
from sqlalchemy import select
from sqlalchemy.orm import Session, defer

from app.dependencies import get_current_user, get_db
from app.models import MediaAsset, User
from app.social_features.evidence_models import (
    GalleryEvidence,
    GalleryIndexRun,
    PublicationDuplicate,
)
from app.social_features.visual import MIN_CONFIDENCE, valid_box

router = APIRouter()


def readable_post(db, post_id, user):
    from app.social_features.publication_access import get_post

    alias = db.get(PublicationDuplicate, post_id)
    return get_post(alias.canonical_id if alias else post_id, user, db)


def term_matches(label, terms):
    from app.services import search_phrase

    name = " " + search_phrase(label) + " "
    return any(" " + search_phrase(term) + " " in name for term in terms if search_phrase(term))


def usable_detection(d):
    if not isinstance(d, dict):
        return False
    confidence = d.get("confidence", 0)
    return (
        isinstance(d.get("label"), str)
        and bool(d["label"].strip())
        and isinstance(confidence, (int, float))
        and math.isfinite(confidence)
        and MIN_CONFIDENCE <= confidence <= 1
        and valid_box(d.get("box")) is not None
    )


@dataclass
class GallerySearch:
    matches: list = field(default_factory=list)
    status: str = "not_searched"
    pending_count: int = 0
    failed_count: int = 0
    reason: str = "none"


def search_evidence(db, user, question, client, limit=6, *, workspace_id=None):
    from app.gallery_index import _visible_scope
    from app.social_features.models import Publication
    from app.social_features.publication_access import visible
    from app.social_features.retrieval_terms import KINDS, classify_terms

    scope = _visible_scope(user, workspace_id).where(Publication.hidden.is_(False))
    posts = []
    for post in db.scalars(scope.order_by(Publication.published_at.desc())):
        try:
            visible(post, user, db)
        except HTTPException:
            continue
        posts.append(post)
    authorized = {p.id: p for p in posts}
    failed = sum(
        bool(p.index_error)
        or (
            bool(p.active_index_run_id)
            and bool(db.get(GalleryIndexRun, p.active_index_run_id).progress.get("review_pending"))
        )
        for p in posts
    )
    pending = sum(p.evidence_version < 2 and not p.index_error for p in posts)
    candidates = defaultdict(list)
    vocabulary = set()
    for e in db.scalars(
        select(GalleryEvidence)
        .options(defer(GalleryEvidence.image_bytes))
        .where(GalleryEvidence.post_id.in_(scope.with_only_columns(Publication.id)))
        .order_by(GalleryEvidence.version.desc(), GalleryEvidence.created_at.desc())
    ):
        post = authorized.get(e.post_id)
        if post is None or e.media_id != post.media_id:
            continue
        if post.active_index_run_id:
            if e.index_run_id != post.active_index_run_id:
                continue
        elif e.index_run_id is not None or (e.version < 2 and post.evidence_version >= 2):
            continue
        current = post.ai_detections or []
        detections = [
            d
            for d in e.detections
            if usable_detection(d)
            and (d in current or {**d, "frame_timestamp_ms": e.frame_timestamp_ms} in current)
        ]
        if detections:
            candidates[post.id].append((e, detections))
            vocabulary.update(d["label"] for d in detections)
    terms = classify_terms(question, sorted(vocabulary), client)
    results = []
    for post in posts:
        ranked = []
        for evidence, detections in candidates[post.id]:
            matches = [d for d in detections if d["label"] in terms.labels]
            if matches:
                kind_rank = min(KINDS.index(terms.labels[d["label"]]) for d in matches)
                # Only annotate labels at the best semantic relation for this photo.
                matches = [d for d in matches if KINDS.index(terms.labels[d["label"]]) == kind_rank]
                ranked.append(
                    (
                        kind_rank,
                        -evidence.version,
                        -max(d["confidence"] for d in matches),
                        evidence.frame_timestamp_ms or 0,
                        evidence,
                        matches,
                    )
                )
        if not ranked:
            continue
        kind_rank, _, negative_score, _, evidence, matches = min(ranked, key=lambda row: row[:4])
        asset = db.get(MediaAsset, post.media_id, options=[defer(MediaAsset.original_bytes)])
        labels = list(dict.fromkeys(d["label"] for d in matches))
        query = urlencode({"labels": ",".join(labels)})
        url = f"/v1/gallery/evidence/{evidence.id}?{query}"
        results.append(
            dict(
                post_id=post.id,
                media_id=asset.id,
                evidence_id=evidence.id,
                caption=post.caption or "",
                ai_caption=post.ai_caption or "",
                thumbnail_url=url,
                boxed_url=url,
                media_url=f"/v1/gallery/{post.id}/media",
                image_url=url + "&full_size=true",
                mime_type=asset.mime_type,
                frame_timestamp_ms=evidence.frame_timestamp_ms,
                note_text=post.note_text or "",
                note_source=post.note_source or "",
                matched_labels=labels,
                confidence=-negative_score,
                match_kind=KINDS[kind_rank],
                localization_quality="sam" if evidence.version >= 2 else "approximate_box",
                content_key=(asset.extra_metadata or {}).get("visual_identity", asset.sha256)
                if evidence.frame_timestamp_ms is None
                else evidence.content_hash,
                pixel_key=evidence.content_hash if evidence.frame_timestamp_ms is None else "",
                published_at=post.published_at.isoformat(),
                simulated=any(d.get("simulated") for d in matches),
            )
        )
    # Stable ties retain semantic relation, grounding quality and recent dates;
    # confidence is the primary order before deduplication and the result limit.
    results.sort(key=lambda r: r["published_at"], reverse=True)
    results.sort(key=lambda r: r["localization_quality"] != "sam")
    results.sort(key=lambda r: KINDS.index(r["match_kind"]))
    results.sort(key=lambda r: r["confidence"], reverse=True)
    unique, seen = [], set()
    for item in results:
        key, pixel_key = item.pop("content_key"), item.pop("pixel_key")
        if key in seen or (pixel_key and pixel_key in seen):
            continue
        seen.add(key)
        if pixel_key:
            seen.add(pixel_key)
        unique.append(item)
        if len(unique) >= limit:
            break
    from app.social_features.localizations import LANGUAGES, display_information, stored_rows

    translations = stored_rows(db, [item["post_id"] for item in unique])
    for item in unique:
        item["localized_information"] = {}
        for language in LANGUAGES:
            text = display_information(
                translations,
                item["post_id"],
                item["post_id"],
                language,
                item["caption"],
                item["note_text"],
                item["matched_labels"],
            )
            if text is not None:
                item["localized_information"][language] = text
    if terms.unavailable:
        status, reason = ("partial" if unique else "unavailable"), "semantic_unavailable"
    elif failed or pending:
        status, reason = ("partial" if unique or failed else "indexing"), "incomplete_index"
    else:
        status, reason = ("ready" if unique else "no_match"), "none"
    return GallerySearch(unique, status, pending, failed, reason)


def gallery_results(db, user, question, client, limit=6, *, workspace_id=None):
    return search_evidence(db, user, question, client, limit, workspace_id=workspace_id).matches


@router.get("/gallery/evidence/{evidence_id}")
def evidence_image(
    evidence_id: uuid.UUID,
    labels: str = "",
    full_size: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    evidence = db.get(GalleryEvidence, evidence_id)
    if evidence is None:
        raise HTTPException(404, "Evidence unavailable.")
    readable_post(db, evidence.post_id, user)
    if evidence.index_run_id and db.get(GalleryIndexRun, evidence.index_run_id).status != "ready":
        raise HTTPException(404, "Evidence unavailable.")
    # Exact stored labels only: no arbitrary caption-based annotations.
    names = {name.strip().casefold() for name in labels.split(",") if name.strip()}
    detections = [
        d
        for d in evidence.detections
        if d.get("label", "").casefold() in names and usable_detection(d)
    ]
    if not detections:
        raise HTTPException(404, "No matching annotation.")
    with Image.open(io.BytesIO(evidence.image_bytes)) as original:
        picture = original.convert("RGB")
        draw = ImageDraw.Draw(picture)
        w, h = picture.size
        for detection in detections:
            b = valid_box(detection["box"])
            draw.rectangle(
                [b["x"] * w, b["y"] * h, (b["x"] + b["width"]) * w, (b["y"] + b["height"]) * h],
                outline=(255, 196, 0),
                width=max(2, min(w, h) // 150),
            )
        if not full_size:
            picture.thumbnail((360, 480))
        output = io.BytesIO()
        picture.save(output, "JPEG", quality=95 if full_size else 85)
    return Response(
        output.getvalue(),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=300"},
    )
