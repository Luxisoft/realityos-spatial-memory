"""Account language is authoritative for human queries; device APIs stay compatible."""

import logging
import re
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import User
from app.query_lang import normalize_language

router = APIRouter()
logger = logging.getLogger("uvicorn.error.language")


class LanguagePreference(BaseModel):
    preferred_language: Literal["en", "es"]

    @field_validator("preferred_language", mode="before")
    @classmethod
    def regional_language(cls, value):
        return (
            value.strip().lower().replace("_", "-").split("-")[0]
            if isinstance(value, str)
            else value
        )


@router.get("/me/preferences")
def read_preferences(user: User = Depends(get_current_user)):
    return {"preferred_language": user.preferred_language}


@router.patch("/me/preferences")
def update_preferences(
    payload: LanguagePreference,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    initialize: bool = False,
):
    # Initialization must not overwrite a preference saved by another installation.
    current = db.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not initialize or current.preferred_language is None:
        current.preferred_language = payload.preferred_language
    db.flush()
    return {"preferred_language": current.preferred_language}


def resolved_language(user: User | None, requested: str | None = None) -> str:
    return normalize_language(
        user.preferred_language if user and user.preferred_language else requested
    )


def language_diagnostic(request: Request, user: User | None, requested: str | None):
    language = resolved_language(user, requested)
    logger.info(
        "query_language request_id=%s endpoint=%s client=%s requested=%s account=%s resolved=%s",
        str(uuid.uuid4()),
        request.url.path,
        re.sub(r"[^a-zA-Z0-9._:-]", "", request.headers.get("x-client-version", "legacy"))[:100],
        re.sub(r"[^a-zA-Z0-9_-]", "", requested or "unset")[:16],
        user.preferred_language if user else None,
        language,
    )
    return language
