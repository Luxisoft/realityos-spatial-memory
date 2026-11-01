"""AI index over gallery publications.

Every published photo/video gets one bounded worker pass: Meta describes the
visible objects and a local face engine counts faces (presence only, never an
identity lookup). Search then matches synonyms through the model instead of
only the user's own caption.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from itertools import groupby

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.meta import MetaModelClient, MetaProviderError
from app.models import MediaAsset, MediaAssetChunk, MediaKind, User, WorkspaceMember
from app.services import materialized_media_file, media_is_chunked, search_phrase

MAX_VIDEO_FRAMES = 120
MAX_SEARCH_TEXT_CHARS = 8000
FACE_TOKENS = ("persona", "personas", "rostro", "rostros", "face", "faces", "person", "people")


def _asset_bytes(db: Session, asset: MediaAsset) -> bytes:
    if not media_is_chunked(asset):
        return asset.original_bytes
    return b"".join(
        db.scalars(
            select(MediaAssetChunk.content)
            .where(MediaAssetChunk.asset_id == asset.id)
            .order_by(MediaAssetChunk.chunk_index)
        )
    )


def _count_faces(face_engine, image: bytes) -> int:
    if face_engine is None or not image:
        return 0
    try:
        return len(face_engine.detect_faces(image))
    except Exception:
        return 0


def _index_texts(caption: str, labels: list[str], detail_parts: list[str], face_count: int):
    seen: list[str] = []
    for label in labels:
        cleaned = " ".join(label.split())
        if cleaned and cleaned.casefold() not in {item.casefold() for item in seen}:
            seen.append(cleaned)
    parts = [caption.strip(), *seen, *detail_parts]
    if face_count > 0:
        parts.extend(FACE_TOKENS)
    search_text = " ".join(part for part in parts if part)[:MAX_SEARCH_TEXT_CHARS]
    caption_bits = [caption.strip()] if caption.strip() else []
    caption_bits.extend(seen[:12])
    if face_count > 0:
        caption_bits.append(f"{face_count} rostro(s)")
    ai_caption = "; ".join(caption_bits)[:1000]
    return seen, search_text, ai_caption


def index_publication(
    db: Session,
    publication_id: uuid.UUID,
    client: MetaModelClient,
    face_engine=None,
    *,
    force: bool = False,
    max_video_frames: int = MAX_VIDEO_FRAMES,
    deduplicate: bool = True,
    checkpoint: bool = False,
    recover_legacy: bool = False,
    review_only: bool = False,
):
    """Run one bounded AI pass over a publication's media and store the index.

    Safe to retry by publication id. A provider failure keeps the publication
    visible with ``indexed_at`` unset so a later backfill can pick it up.
    """

    from app.social import Publication

    publication = db.get(Publication, publication_id)
    if publication is None:
        return None
    if publication.hidden:
        return publication
    if publication.indexed_at is not None and not force:
        from app.social_features.localizations import prepare_posts

        try:
            prepare_posts(db, [publication], client)
        except MetaProviderError as exc:
            publication.index_error = str(exc)[:1000]
        return publication
    asset = db.get(MediaAsset, publication.media_id)
    if asset is None:
        publication.index_error = "Source media no longer exists."
        return publication

    try:
        from app.social_features.index_runs import process_run

        if deduplicate and asset.kind == MediaKind.IMAGE:
            from app.social_features.maintenance import retire
            from app.social_features.upload_service import duplicate, scope_lock

            scope_lock(db, publication.owner_id, publication.audience, publication.workspace_id)
            match = duplicate(
                db,
                client,
                asset.original_bytes,
                publication.owner_id,
                publication.audience,
                publication.workspace_id,
                older_than=publication,
            )
            if match:
                with db.begin_nested():
                    retire(db, publication, match)
                    from app.social_features.localizations import prepare_posts

                    prepare_posts(db, [match], client)
                return publication
        completed = process_run(
            db,
            publication,
            client,
            checkpoint=checkpoint,
            recover_legacy=recover_legacy,
            review_only=review_only,
        )
        if completed is None:
            return publication
        if publication.index_error:
            return publication
        if asset.kind == MediaKind.IMAGE and face_engine is not None:
            publication.face_count = _count_faces(face_engine, asset.original_bytes)
        publication.index_error = None
    except (MetaProviderError, ValueError, OSError) as exc:
        publication.index_error = str(exc)[:1000]
        return publication
    publication.indexed_at = datetime.now(UTC)
    return publication


def _collect_detections(
    client,
    image: bytes,
    mime_type: str,
    caption: str,
    labels,
    details,
    detections,
    frame_index: int,
) -> None:
    analysis = client.analyze_image(
        image,
        mime_type,
        caption.strip() or "Describe every distinct object visible in this image.",
    )
    for detection in analysis.detections:
        labels.append(detection.label)
        if detection.category:
            labels.append(detection.category)
        box = detection.bounding_box or {}
        try:
            x, y = float(box.get("x", 0.0)), float(box.get("y", 0.0))
            width, height = float(box.get("width", 0.0)), float(box.get("height", 0.0))
        except (TypeError, ValueError):
            x = y = width = height = 0.0
        if width > 0 and height > 0:
            detections.append(
                {
                    "label": detection.label,
                    "box": {"x": x, "y": y, "width": width, "height": height},
                    "confidence": detection.confidence,
                    "frame_index": frame_index,
                }
            )
        fact_bits = [
            fact.value_text or fact.normalized_value or ""
            for fact in detection.facts
            if fact.value_text or fact.normalized_value
        ]
        if detection.spatial_description:
            details.append(detection.spatial_description[:300])
        details.extend(bit[:200] for bit in fact_bits if bit)


def _index_video(
    db, asset, caption, client, face_engine, labels, details, detections, max_video_frames
) -> int:
    from app.video import (
        VideoProcessingError,
        extract_representative_frames_from_file,
        probe_video_file,
    )

    if max_video_frames < 1:
        raise MetaProviderError("Video indexing needs at least one frame.")
    try:
        with materialized_media_file(db, asset) as source:
            info = probe_video_file(source)
            frames = extract_representative_frames_from_file(
                source,
                info,
                segment_seconds=10**9,
                frames_per_segment=max_video_frames,
            )
    except VideoProcessingError as exc:
        raise MetaProviderError(str(exc)) from exc
    face_count = 0
    for frame in frames[:max_video_frames]:
        face_count = max(face_count, _count_faces(face_engine, frame.bytes))
        _collect_detections(
            client,
            frame.bytes,
            "image/jpeg",
            caption,
            labels,
            details,
            detections,
            frame_index=frame.index,
        )
    return face_count


def _visible_scope(viewer: User, audience: str | None, workspace_id: uuid.UUID | None):
    from app.social import Publication

    statement = select(Publication)
    if audience is not None:
        statement = statement.where(Publication.audience == audience)
    if workspace_id is not None:
        statement = statement.where(Publication.workspace_id == workspace_id)
    memberships = select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == viewer.id)
    return statement.where(
        or_(
            Publication.owner_id == viewer.id,
            Publication.audience == "public",
            (Publication.audience == "work") & (Publication.workspace_id.in_(memberships)),
        )
    )


def _known_tags(db: Session, viewer: User) -> list[str]:
    from app.social import Publication

    rows = db.scalars(
        _visible_scope(viewer, None, None).order_by(Publication.published_at.desc()).limit(2000)
    )
    tags: list[str] = []
    for publication in rows:
        for label in publication.ai_labels or []:
            if label not in tags:
                tags.append(label)
        if publication.face_count:
            for token in FACE_TOKENS:
                if token not in tags:
                    tags.append(token)
    return tags


def expand_terms(question: str, known_tags: list[str], client: MetaModelClient | None) -> list[str]:
    """Local phrase plus model-mapped synonyms; the provider only picks terms."""

    phrase = search_phrase(question)
    terms = list(dict.fromkeys([phrase, *phrase.split()] if phrase else []))
    if client is None:
        return terms
    try:
        interpreted = client.interpret_gallery_terms(question, known_tags)
    except MetaProviderError:
        return terms
    for term in interpreted.terms:
        cleaned = search_phrase(term) or term.strip()
        if cleaned and cleaned not in terms:
            terms.append(cleaned)
    return terms


def search_gallery(
    db: Session,
    viewer: User,
    question: str,
    client: MetaModelClient | None,
    *,
    limit: int = 8,
    audience: str | None = None,
    workspace_id: uuid.UUID | None = None,
):
    """Return viewer-visible publications matching the question, newest first."""

    from app.social import Publication, visible

    terms = expand_terms(question, _known_tags(db, viewer), client)
    if not terms:
        return []
    dialect = db.get_bind().dialect.name
    clauses = []
    for term in terms:
        lowered = func.lower(Publication.search_text).contains(term.casefold())
        if dialect == "postgresql":
            clauses.append(or_(lowered, func.similarity(Publication.search_text, term) >= 0.24))
        else:
            clauses.append(lowered)
    # Relevance ranks in Python, so the SQL window must be wide enough to
    # contain the best matches instead of only the newest rows.
    headroom = min(max(limit * 25, 500), 2000)
    candidates = db.scalars(
        _visible_scope(viewer, audience, workspace_id)
        .where(or_(*clauses))
        .order_by(Publication.published_at.desc())
        .limit(headroom)
    )
    scored: list[tuple[int, Publication, list[str]]] = []
    for publication in candidates:
        try:
            visible(publication, viewer, db)
        except Exception:
            continue
        haystack = (publication.search_text or "").casefold()
        matched = [term for term in terms if term.casefold() in haystack]
        rank = min(terms.index(term) for term in matched) if matched else len(terms)
        scored.append((rank, publication, matched))
    scored.sort(key=lambda item: (item[0], item[1].published_at), reverse=False)
    # Prefer textual matches: trigram-only candidates (rank == len(terms)) are
    # kept only when nothing matched a term directly, so unrelated photos do
    # not dilute real matches.
    textual = [item for item in scored if item[0] < len(terms)]
    ranked = textual or scored
    # Newest first within the same relevance rank.
    best: list[tuple[Publication, list[str]]] = []
    for _rank, group in groupby(ranked, key=lambda item: item[0]):
        group = sorted(group, key=lambda item: item[1].published_at, reverse=True)
        best.extend((publication, matched) for _, publication, matched in group)
    return best[:limit]


def queue_publication_index(publication_id: uuid.UUID, *, force: bool = False) -> None:
    """Enqueue worker indexing; a broker outage must never break publishing."""

    try:
        from app.tasks import index_gallery_media

        index_gallery_media.delay(str(publication_id), force=force)
    except Exception:
        pass
