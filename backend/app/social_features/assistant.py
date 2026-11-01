from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import (
    select,
)
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models import (
    User,
)
from app.social_features.schemas import AssistantCommand

"""Facebook identities and explicitly shared audiovisual publications."""


router = APIRouter()


@router.post("/assistant")
def assistant(
    payload: AssistantCommand,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    import unicodedata

    from app.query_lang import qtext
    from app.social_features.language_preferences import language_diagnostic

    language = language_diagnostic(request, user, payload.language)

    def response(value):
        return {**value, "response_language": language}

    from app.social_features.gallery import _publication_payload, get_post

    command = "".join(
        c
        for c in unicodedata.normalize("NFD", payload.text.lower())
        if unicodedata.category(c) != "Mn"
    )
    for words, destination in (
        ("abrir gafas", "glasses"),
        ("ir a casa", "home"),
        ("abrir casa", "home"),
        ("ir a trabajo", "work"),
        ("abrir trabajo", "work"),
        ("abrir publico", "public"),
    ):
        if command.strip() == words:
            return response(
                {
                    "type": "navigate",
                    "destination": destination,
                    "message": qtext(language, "open_screen"),
                }
            )
    actions = {"publicar": "public", "compartir": "work", "borrar": "remove", "eliminar": "remove"}
    for word, action in actions.items():
        if command.startswith(word + " ") or command == word:
            if payload.post_id is None:
                return {
                    "type": "message",
                    "response_language": language,
                    "message": qtext(language, "select_post"),
                }
            post = get_post(payload.post_id, user, db)
            if post.owner_id != user.id:
                raise HTTPException(403, "Only the owner can change this publication.")
            return {
                "type": "confirm",
                "response_language": language,
                "action": action,
                "post_id": str(post.id),
                "message": qtext(language, "confirm_post"),
            }
    if payload.audience == "home":
        from app.meta import MetaProviderError, build_meta_client
        from app.models import Workspace
        from app.routes import _answer_query
        from app.schemas import QueryRequest

        home = db.scalar(select(Workspace).where(Workspace.name == f"home:{user.id}"))
        if home is None:
            return {
                "type": "message",
                "response_language": language,
                "message": qtext(language, "register_home"),
            }
        try:
            model = build_meta_client(request.app.state.settings)
        except MetaProviderError:
            model = None
        result = _answer_query(
            QueryRequest(workspace_id=home.id, question=payload.text, language=language),
            user,
            db,
            model,
        )
        return {
            "type": "answer",
            "response_language": language,
            "message": result.message,
            "simulated": result.simulated,
        }
    from app.meta import MetaProviderError, build_meta_client
    from app.social_features.evidence import gallery_results

    try:
        model = build_meta_client(request.app.state.settings)
    except MetaProviderError:
        model = None
    matches = gallery_results(
        db,
        user,
        payload.text,
        model,
        limit=12,
        audience=payload.audience,
        workspace_id=payload.workspace_id,
    )
    from app.social_features.models import Publication

    posts = []
    for evidence in matches:
        post = db.get(Publication, evidence["post_id"])
        item = _publication_payload(post, user, db)
        item.update(
            {
                key: evidence[key]
                for key in (
                    "thumbnail_url",
                    "boxed_url",
                    "image_url",
                    "frame_timestamp_ms",
                    "evidence_id",
                    "matched_labels",
                    "confidence",
                    "match_kind",
                    "localization_quality",
                )
            }
        )
        if not evidence["mime_type"].startswith("video/"):
            item["media_url"] = evidence["image_url"]
        posts.append(item)
    return {
        "type": "results",
        "response_language": language,
        "message": qtext(language, "accessible_matches", count=len(posts)),
        "posts": posts,
    }
