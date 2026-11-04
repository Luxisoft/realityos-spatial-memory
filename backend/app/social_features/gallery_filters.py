"""Authorized gallery filtering before pagination."""

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select

from app.dependencies import get_current_user, get_db, workspace_member
from app.models import User, Workspace, WorkspaceMember
from app.social_features.classification_service import term_json
from app.social_features.models import Publication, PublicationTag, PublicationTerm
from app.social_features.publication_visibility import authorized_publications, publication_content

router = APIRouter()


def gallery_scope(db, user, workspace_id):
    query = select(Publication).where(
        Publication.hidden.is_(False),
        publication_content(),
        authorized_publications(user.id),
    )
    if workspace_id:
        workspace_member(workspace_id, user, db)
        query = query.where(Publication.workspace_id == workspace_id)
    if user.is_guest:
        query = query.where(
            Publication.owner_id.in_(
                select(User.id).where(or_(User.id == user.id, User.is_guest.is_(True)))
            )
        )
    return query


class GalleryFilters:
    def __init__(
        self,
        category_ids: list[uuid.UUID] = Query(default=[]),
        tag_ids: list[uuid.UUID] = Query(default=[]),
        owner_ids: list[uuid.UUID] = Query(default=[]),
        published_from: datetime | None = None,
        published_before: datetime | None = None,
        description_q: str = Query(default="", max_length=500),
    ):
        self.category_ids, self.tag_ids, self.owner_ids = category_ids, tag_ids, owner_ids
        self.start, self.end = published_from, published_before
        self.text = description_q.strip()
        for value in (self.start, self.end):
            if value is not None and value.tzinfo is None:
                raise HTTPException(422, "Publication dates must include a timezone.")
        if self.start and self.end and self.start >= self.end:
            raise HTTPException(422, "The end date must follow the start date.")
        if any(len(values) > 200 for values in (category_ids, tag_ids, owner_ids)):
            raise HTTPException(422, "Too many filter values.")

    def apply(self, query):
        if self.category_ids:
            query = query.where(Publication.category_id.in_(self.category_ids))
        if self.tag_ids:
            query = query.where(
                Publication.id.in_(
                    select(PublicationTag.post_id).where(PublicationTag.term_id.in_(self.tag_ids))
                )
            )
        if self.owner_ids:
            query = query.where(Publication.owner_id.in_(self.owner_ids))
        if self.start:
            query = query.where(Publication.published_at >= self.start.astimezone(UTC))
        if self.end:
            query = query.where(Publication.published_at < self.end.astimezone(UTC))
        if self.text:
            query = query.where(
                or_(
                    Publication.caption.icontains(self.text, autoescape=True),
                    Publication.note_text.icontains(self.text, autoescape=True),
                )
            )
        return query


@router.get("/gallery/filter-options")
def gallery_filter_options(
    workspace_id: uuid.UUID | None = None, user=Depends(get_current_user), db=Depends(get_db)
):
    query = gallery_scope(db, user, workspace_id)
    post_ids = query.with_only_columns(Publication.id).order_by(None)
    category_ids = query.with_only_columns(Publication.category_id).order_by(None)
    tags = select(PublicationTag.term_id).where(PublicationTag.post_id.in_(post_ids))
    terms = db.scalars(
        select(PublicationTerm)
        .where(or_(PublicationTerm.id.in_(category_ids), PublicationTerm.id.in_(tags)))
        .order_by(PublicationTerm.name_key)
    )
    groups = dict(
        db.execute(
            select(Workspace.id, Workspace.name)
            .join(WorkspaceMember)
            .where(WorkspaceMember.user_id == user.id)
        ).all()
    )
    result = {"categories": [], "tags": [], "owners": []}
    for term in terms:
        result["categories" if term.kind == "category" else "tags"].append(
            {**term_json(term), "workspace_name": groups.get(term.workspace_id, "")}
        )
    owners = db.scalars(
        select(User)
        .where(User.id.in_(query.with_only_columns(Publication.owner_id).order_by(None)))
        .order_by(User.display_name, User.id)
    )
    result["owners"] = [{"id": str(owner.id), "name": owner.display_name} for owner in owners]
    return result
