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

from app.models import MediaAsset, MediaKind, User
from app.providers.contracts import MetaModelClient, MetaProviderError
from app.services import search_phrase

FACE_TOKENS = ("persona", "personas", "rostro", "rostros", "face", "faces", "person", "people")


def _count_faces(face_engine, image: bytes) -> int:
    if face_engine is None or not image:
        return 0
    try:
        return len(face_engine.detect_faces(image))
    except Exception:
        return 0


def index_publication(
    db: Session,
    publication_id: uuid.UUID,
    client: MetaModelClient,
    face_engine=None,
    *,
    force: bool = False,
    deduplicate: bool = True,
    checkpoint: bool = False,
    recover_legacy: bool = False,
    review_only: bool = False,
):
    """Run one bounded AI pass over a publication's media and store the index.

    Safe to retry by publication id. A provider failure keeps the publication
    visible with ``indexed_at`` unset so a later backfill can pick it up.
    """

    from app.social_features.models import Publication

    publication = db.get(Publication, publication_id)
    if publication is None:
        return None
    from app.social_features.publication_visibility import REFERENCE_SOURCES

    if publication.hidden or publication.source in REFERENCE_SOURCES:
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

            scope_lock(db, publication.owner_id, publication.workspace_id)
            match = duplicate(
                db,
                client,
                asset.original_bytes,
                publication.owner_id,
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


def _visible_scope(viewer: User, workspace_id: uuid.UUID | None):
    from app.social_features.models import Publication
    from app.social_features.publication_visibility import (
        authorized_publications,
        publication_content,
    )

    statement = select(Publication).where(
        publication_content(), Publication.hidden.is_(False), authorized_publications(viewer.id)
    )
    if workspace_id is not None:
        statement = statement.where(Publication.workspace_id == workspace_id)
    return statement


def _known_tags(db: Session, viewer: User) -> list[str]:
    from app.social_features.models import Publication

    rows = db.scalars(
        _visible_scope(viewer, None).order_by(Publication.published_at.desc()).limit(2000)
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
    workspace_id: uuid.UUID | None = None,
):
    """Return viewer-visible publications matching the question, newest first."""

    from app.social_features.models import Publication
    from app.social_features.publication_access import visible

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
        _visible_scope(viewer, workspace_id)
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
