"""Keep identity reference media separate from user-created publications."""

from fastapi import HTTPException
from sqlalchemy import or_, select

from app.models import MediaAsset, WorkspaceMember
from app.social_features.models import Publication

REFERENCE_SOURCES = ("facebook", "simulator")


def publication_content():
    """SQL predicate shared by feeds, retrieval and duplicate detection."""
    return Publication.source.not_in(REFERENCE_SOURCES)


def require_publication_content(post):
    if post.source in REFERENCE_SOURCES:
        raise HTTPException(404, "Publication unavailable.")


def require_ordinary_media(asset: MediaAsset, user, db):
    """Block raw reference URLs, allowing separately published copies by permission.

    Avatar and consented facial-result endpoints authorize their own resources;
    they deliberately do not use the ordinary media route.
    """
    ancestry = {asset.id}
    imported = (asset.extra_metadata or {}).get("origin") == "facebook-import"
    parent_id = asset.parent_asset_id
    while parent_id is not None and parent_id not in ancestry:
        ancestry.add(parent_id)
        parent = db.execute(
            select(MediaAsset.parent_asset_id, MediaAsset.extra_metadata).where(
                MediaAsset.id == parent_id
            )
        ).one_or_none()
        if parent is None:
            break
        imported |= (parent.extra_metadata or {}).get("origin") == "facebook-import"
        parent_id = parent.parent_asset_id
    reference = db.scalar(
        select(Publication.id)
        .where(
            Publication.media_id.in_(ancestry),
            Publication.source.in_(REFERENCE_SOURCES),
        )
        .limit(1)
    )
    if not reference and not imported:
        return
    memberships = select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user.id)
    accessible = db.scalar(
        select(Publication.id)
        .where(
            Publication.media_id.in_(ancestry),
            publication_content(),
            Publication.hidden.is_(False),
            or_(
                Publication.owner_id == user.id,
                Publication.audience == "public",
                (Publication.audience == "work") & Publication.workspace_id.in_(memberships),
            ),
        )
        .limit(1)
    )
    if accessible is None:
        raise HTTPException(404, "Media not found.")
