"""Biometric originals are never publication or object-search evidence."""

from fastapi import HTTPException
from sqlalchemy import and_, exists, or_, select

from app.models import MediaAsset, WorkspaceMember
from app.social_features.models import Publication

REFERENCE_SOURCES = ("facebook", "simulator")


def authorized_publications(user_id):
    memberships = select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user_id)
    return or_(
        and_(Publication.audience == "work", Publication.workspace_id.in_(memberships)),
        and_(Publication.audience != "work", Publication.owner_id == user_id),
    )


def private_media_predicate():
    metadata = MediaAsset.extra_metadata
    return or_(
        metadata["origin"].as_string() == "facebook-import",
        metadata["purpose"].as_string() == "biometric-reference",
        metadata["face_profile"].as_boolean().is_(True),
        metadata["retired"].as_boolean().is_(True),
    )


def publication_content():
    return Publication.source.not_in(REFERENCE_SOURCES) & ~exists(
        select(MediaAsset.id).where(
            MediaAsset.id == Publication.media_id, private_media_predicate()
        )
    ).correlate(Publication)


def require_publication_content(post):
    if post.source in REFERENCE_SOURCES:
        raise HTTPException(404, "Publication unavailable.")


def require_ordinary_media(asset, user, db):
    seen = set()
    while asset is not None and asset.id not in seen:
        seen.add(asset.id)
        metadata = asset.extra_metadata or {}
        if (
            metadata.get("origin") == "facebook-import"
            or metadata.get("purpose") == "biometric-reference"
            or metadata.get("face_profile")
            or metadata.get("retired")
        ):
            raise HTTPException(404, "Media not found.")
        asset = db.get(MediaAsset, asset.parent_asset_id) if asset.parent_asset_id else None
