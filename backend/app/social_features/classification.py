"""Group-owned publication vocabulary and explicit human classification."""

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.dependencies import get_current_user, get_db, workspace_member
from app.models import Workspace
from app.social_features.classification_schemas import ClassificationInput as ClassificationInput
from app.social_features.classification_schemas import TermInput as TermInput
from app.social_features.classification_schemas import TermUpdate as TermUpdate
from app.social_features.classification_service import add_term as add_term
from app.social_features.classification_service import classification_json as classification_json
from app.social_features.classification_service import (
    require_catalog_owner as require_catalog_owner,
)
from app.social_features.classification_service import set_classification as set_classification
from app.social_features.classification_service import term_json as term_json
from app.social_features.classification_service import (
    validate_classification as validate_classification,
)
from app.social_features.models import PublicationTerm

router = APIRouter()


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
    from app.social_features.publication_access import get_post

    post = get_post(post_id, user, db)
    if post.owner_id != user.id:
        raise HTTPException(403, "Only the author can classify this publication.")
    db.refresh(post, with_for_update=True)
    previous = classification_json(db, post)
    set_classification(db, post, payload.category_id, payload.tag_ids)
    db.add(PublicationRevision(post_id=post.id, previous={"classification": previous}))
    return classification_json(db, post)
