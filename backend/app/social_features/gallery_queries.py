"""Cursor paging and bounded projections of already authorized publications."""

from __future__ import annotations

import base64
import json
import uuid
from collections import defaultdict
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.orm import Session, load_only

from app.models import MediaAsset, User
from app.social_features.classification_service import term_json
from app.social_features.models import (
    FacebookProfile,
    Publication,
    PublicationTag,
    PublicationTerm,
    Reaction,
    UserProfile,
)
from app.stored_display import display_text


def _encode_gallery_cursor(post: Publication) -> str:
    payload = json.dumps(
        [post.published_at.isoformat(), str(post.id)], separators=(",", ":")
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def _decode_gallery_cursor(value: str) -> tuple[datetime, uuid.UUID]:
    try:
        padded = value + "=" * (-len(value) % 4)
        timestamp, post_id = json.loads(base64.urlsafe_b64decode(padded).decode())
        parsed = datetime.fromisoformat(timestamp)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed, uuid.UUID(post_id)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(422, "Invalid gallery cursor.") from exc


def publication_payloads(posts: list[Publication], viewer: User, db: Session) -> list[dict]:
    """Read page metadata in four queries, without loading media or private CVs.

    The caller authorizes the publication scope before passing rows here. This
    projection does not widen that scope or fetch a full public profile per row.
    """
    if not posts:
        return []
    post_ids = [post.id for post in posts]
    details = {
        row.id: row
        for row in db.execute(
            select(
                Publication.id,
                MediaAsset.mime_type,
                User.display_name,
                UserProfile.avatar_media_id,
                UserProfile.headline,
                FacebookProfile.picture_url,
            )
            .select_from(Publication)
            .outerjoin(MediaAsset, Publication.media_id == MediaAsset.id)
            .outerjoin(User, Publication.owner_id == User.id)
            .outerjoin(UserProfile, UserProfile.user_id == User.id)
            .outerjoin(FacebookProfile, FacebookProfile.user_id == User.id)
            .where(Publication.id.in_(post_ids))
        )
    }
    categories = {
        term.id: term_json(term)
        for term in db.scalars(
            select(PublicationTerm).where(
                PublicationTerm.id.in_({post.category_id for post in posts if post.category_id})
            )
        )
    }
    tags = defaultdict(list)
    for post_id, term in db.execute(
        select(PublicationTag.post_id, PublicationTerm)
        .join(PublicationTerm, PublicationTerm.id == PublicationTag.term_id)
        .where(PublicationTag.post_id.in_(post_ids))
        .order_by(PublicationTerm.name_key)
    ):
        tags[post_id].append(term_json(term))
    reactions = {
        post_id: (count, bool(liked))
        for post_id, count, liked in db.execute(
            select(
                Reaction.post_id,
                func.count(),
                func.max(case((Reaction.user_id == viewer.id, 1), else_=0)),
            )
            .where(Reaction.post_id.in_(post_ids))
            .group_by(Reaction.post_id)
        )
    }
    result = []
    for post in posts:
        detail = details[post.id]
        likes, liked = reactions.get(post.id, (0, False))
        result.append(
            {
                "id": str(post.id),
                "original_id": str(post.shared_from_id or post.id),
                "caption": post.caption,
                "display_text": display_text(post),
                "category": categories.get(post.category_id),
                "tags": tags[post.id],
                "note_text": post.note_text,
                "note_source": post.note_source,
                "workspace_id": str(post.workspace_id) if post.workspace_id else None,
                "mime_type": detail.mime_type or "application/octet-stream",
                "media_url": f"gallery/{post.id}/media",
                "thumbnail_url": f"gallery/{post.id}/thumbnail",
                "owned": post.owner_id == viewer.id,
                "liked": liked,
                "likes": likes,
                "published_at": post.published_at.isoformat(),
                "source": post.source,
                "owner": {
                    "user_id": str(post.owner_id),
                    "display_name": detail.display_name or "",
                    "picture_url": (
                        f"/v1/profiles/{post.owner_id}/avatar"
                        if detail.avatar_media_id
                        else detail.picture_url
                    ),
                    "headline": detail.headline or "",
                },
            }
        )
    return result


def _publication_payload(post: Publication, viewer: User, db: Session) -> dict:
    return publication_payloads([post], viewer, db)[0]


def _gallery_page(query, limit: int, cursor: str | None, viewer: User, db: Session) -> dict:
    page_size = min(max(limit, 1), 30)
    if cursor:
        published_at, post_id = _decode_gallery_cursor(cursor)
        query = query.where(
            or_(
                Publication.published_at < published_at,
                and_(Publication.published_at == published_at, Publication.id < post_id),
            )
        )
    rows = list(
        db.scalars(
            query.options(
                load_only(
                    Publication.id,
                    Publication.shared_from_id,
                    Publication.caption,
                    Publication.display_text,
                    Publication.category_id,
                    Publication.note_text,
                    Publication.note_source,
                    Publication.workspace_id,
                    Publication.owner_id,
                    Publication.published_at,
                    Publication.source,
                )
            )
            .order_by(Publication.published_at.desc(), Publication.id.desc())
            .limit(page_size + 1)
        )
    )
    has_more = len(rows) > page_size
    rows = rows[:page_size]
    return {
        "items": publication_payloads(rows, viewer, db),
        "next_cursor": _encode_gallery_cursor(rows[-1]) if has_more and rows else None,
    }
