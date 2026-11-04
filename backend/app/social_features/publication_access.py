"""Authorize existing publications and destinations for every entry point."""

import uuid

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.dependencies import workspace_member
from app.models import MediaAsset, User, Workspace
from app.social_features.models import Publication
from app.social_features.publication_visibility import (
    require_ordinary_media,
    require_publication_content,
)


def visible(post: Publication, user: User, db: Session) -> Publication:

    require_publication_content(post)
    asset = db.get(MediaAsset, post.media_id)
    if asset is None:
        raise HTTPException(404, "Publication unavailable.")
    require_ordinary_media(asset, user, db)
    if post.hidden:
        raise HTTPException(404, "Publication unavailable.")
    if user.is_guest and post.owner_id != user.id:
        owner = db.get(User, post.owner_id)
        if owner is None or not owner.is_guest:
            raise HTTPException(404, "Publication unavailable.")
    workspace_member(post.workspace_id, user, db)
    return post


def get_post(post_id: uuid.UUID, user: User, db: Session):

    from app.social_features.evidence_models import PublicationDuplicate

    original = db.get(Publication, post_id)
    if original is not None:
        require_publication_content(original)
        require_ordinary_media(db.get(MediaAsset, original.media_id), user, db)
    alias = db.get(PublicationDuplicate, post_id)
    if alias is not None:
        post_id = alias.canonical_id
    post = db.get(Publication, post_id)
    if post is None:
        raise HTTPException(404, "Publication unavailable.")
    return visible(post, user, db)


def check_destination(db, user, workspace_id):
    if not workspace_id:
        raise HTTPException(422, "Join or create a work group before publishing.")
    workspace_member(workspace_id, user, db)
    space = db.get(Workspace, workspace_id)
    if not space or space.name.startswith("home:"):
        raise HTTPException(422, "Choose a work group.")
