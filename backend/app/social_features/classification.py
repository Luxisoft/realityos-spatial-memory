"""Group-owned publication vocabulary and explicit human classification."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import delete, select

from app.dependencies import get_current_user, get_db, workspace_member
from app.models import Workspace
from app.social_features.models import PublicationTag, PublicationTerm

router = APIRouter()


class ClassificationInput(BaseModel):
    category_id: uuid.UUID
    tag_ids: list[uuid.UUID] = Field(min_length=1, max_length=20)


class TermInput(BaseModel):
    name: str = Field(min_length=1, max_length=80)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value):
        value = " ".join(value.split())
        if not value:
            raise ValueError("A name is required.")
        return value


class TermUpdate(TermInput):
    active: bool = True


def term_json(term):
    return {
        "id": str(term.id),
        "name": term.name,
        "active": term.active,
        "workspace_id": str(term.workspace_id),
    }


def require_catalog_owner(db, user, workspace_id):
    workspace_member(workspace_id, user, db)
    workspace = db.get(Workspace, workspace_id)
    if workspace.created_by_id != user.id:
        raise HTTPException(403, "Only the group owner can manage its publication catalog.")
    # Serialize name uniqueness, archiving and publication validation with the group.
    db.refresh(workspace, with_for_update=True)
    return workspace


def add_term(db, workspace_id, kind, name):
    name = TermInput(name=name).name
    key = name.casefold()
    existing = db.scalar(
        select(PublicationTerm).where(
            PublicationTerm.workspace_id == workspace_id,
            PublicationTerm.kind == kind,
            PublicationTerm.name_key == key,
        )
    )
    if existing:
        raise HTTPException(409, "This name already exists in the group catalog.")
    term = PublicationTerm(workspace_id=workspace_id, kind=kind, name=name, name_key=key)
    db.add(term)
    db.flush()
    return term


def validate_classification(db, workspace_id, category_id, tag_ids):
    if not workspace_id or not category_id or not tag_ids:
        raise HTTPException(422, "Choose a group category and at least one tag.")
    try:
        category_id = uuid.UUID(str(category_id))
        tags = list(dict.fromkeys(uuid.UUID(str(key)) for key in tag_ids))
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, "Invalid category or tags.") from exc
    if len(tags) > 20:
        raise HTTPException(422, "Select at most 20 tags.")
    group = db.get(Workspace, workspace_id)
    if group is None:
        raise HTTPException(422, "Group unavailable.")
    db.refresh(group, with_for_update=True)
    terms = {
        term.id: term
        for term in db.scalars(
            select(PublicationTerm).where(
                PublicationTerm.workspace_id == workspace_id,
                PublicationTerm.id.in_([category_id, *tags]),
                PublicationTerm.active.is_(True),
            )
        )
    }
    if (
        category_id not in terms
        or terms[category_id].kind != "category"
        or any(key not in terms or terms[key].kind != "tag" for key in tags)
    ):
        raise HTTPException(422, "Select active categories and tags from the destination group.")
    return category_id, tags


def set_classification(db, post, category_id, tag_ids):
    category, tags = validate_classification(db, post.workspace_id, category_id, tag_ids)
    post.category_id = category
    db.flush()
    db.execute(delete(PublicationTag).where(PublicationTag.post_id == post.id))
    db.add_all(PublicationTag(post_id=post.id, term_id=key) for key in tags)
    db.flush()


def classification_json(db, post):
    category = db.get(PublicationTerm, post.category_id) if post.category_id else None
    tags = db.scalars(
        select(PublicationTerm)
        .join(PublicationTag, PublicationTag.term_id == PublicationTerm.id)
        .where(PublicationTag.post_id == post.id)
        .order_by(PublicationTerm.name_key)
    )
    return {
        "category": term_json(category) if category else None,
        "tags": [term_json(tag) for tag in tags],
    }


@router.get("/groups/{workspace_id}/publication-catalog")
def publication_catalog(
    workspace_id: uuid.UUID, user=Depends(get_current_user), db=Depends(get_db)
):
    workspace_member(workspace_id, user, db)
    group = db.get(Workspace, workspace_id)
    terms = list(
        db.scalars(
            select(PublicationTerm)
            .where(PublicationTerm.workspace_id == workspace_id)
            .order_by(PublicationTerm.name_key)
        )
    )
    return {
        "can_manage": group.created_by_id == user.id,
        "categories": [term_json(t) for t in terms if t.kind == "category"],
        "tags": [term_json(t) for t in terms if t.kind == "tag"],
    }


@router.post("/groups/{workspace_id}/publication-catalog/{kind}", status_code=201)
def create_publication_term(
    workspace_id: uuid.UUID,
    kind: Literal["category", "tag"],
    payload: TermInput,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    require_catalog_owner(db, user, workspace_id)
    return term_json(add_term(db, workspace_id, kind, payload.name))


@router.patch("/groups/{workspace_id}/publication-catalog/{term_id}")
def update_publication_term(
    workspace_id: uuid.UUID,
    term_id: uuid.UUID,
    payload: TermUpdate,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    require_catalog_owner(db, user, workspace_id)
    term = db.get(PublicationTerm, term_id)
    if term is None or term.workspace_id != workspace_id:
        raise HTTPException(404, "Catalog value unavailable.")
    duplicate = db.scalar(
        select(PublicationTerm.id).where(
            PublicationTerm.workspace_id == workspace_id,
            PublicationTerm.kind == term.kind,
            PublicationTerm.name_key == payload.name.casefold(),
            PublicationTerm.id != term.id,
        )
    )
    if duplicate:
        raise HTTPException(409, "This name already exists in the group catalog.")
    term.name, term.name_key, term.active = payload.name, payload.name.casefold(), payload.active
    return term_json(term)


@router.patch("/gallery/{post_id}/classification")
def update_publication_classification(
    post_id: uuid.UUID,
    payload: ClassificationInput,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    from app.social_features.evidence_models import PublicationRevision
    from app.social_features.gallery import get_post

    post = get_post(post_id, user, db)
    if post.owner_id != user.id:
        raise HTTPException(403, "Only the author can classify this publication.")
    db.refresh(post, with_for_update=True)
    previous = classification_json(db, post)
    set_classification(db, post, payload.category_id, payload.tag_ids)
    db.add(PublicationRevision(post_id=post.id, previous={"classification": previous}))
    return classification_json(db, post)
