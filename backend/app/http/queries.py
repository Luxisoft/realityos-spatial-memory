from __future__ import annotations

import io
import logging
import uuid

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from PIL import Image
from sqlalchemy.orm import Session

from app.dependencies import get_current_device, get_current_user, get_db, workspace_member
from app.meta import MetaProviderError, build_meta_client
from app.models import (
    Device,
    Role,
    User,
)
from app.processing.queries import _answer_query
from app.schemas import (
    QueryRequest,
    QueryResponse,
    SearchRouteRequest,
)
from app.social_features.language_preferences import language_diagnostic

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/queries", response_model=QueryResponse)
def query(
    payload: QueryRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryResponse:
    language_diagnostic(request, user, payload.language)
    try:
        client = build_meta_client(request.app.state.settings)
    except MetaProviderError:
        client = None
    return _answer_query(payload, user, db, client)


@router.post("/queries/image", response_model=QueryResponse)
def image_query(
    request: Request,
    workspace_id: uuid.UUID = Form(...),
    image: UploadFile = File(...),
    question: str = Form(default=""),
    language: str = Form(default="en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryResponse:
    """Identify an object from an ephemeral image, then query existing evidence only."""

    language = language_diagnostic(request, user, language)
    workspace_member(workspace_id, user, db, {Role.ADMIN, Role.QUERY})
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG or WebP images are accepted.")
    # Provider analysis and evidence lookup are synchronous. Run this route
    # in FastAPI's worker pool so other requests remain responsive.
    raw = image.file.read(20 * 1024 * 1024 + 1)
    if not raw or len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Invalid image size.")
    try:
        with Image.open(io.BytesIO(raw)) as decoded:
            decoded.verify()
    except (OSError, ValueError):
        raise HTTPException(status_code=422, detail="The image cannot be decoded.") from None
    question_text = question.strip()
    try:
        client = build_meta_client(request.app.state.settings)
        analysis = client.analyze_image(
            raw,
            image.content_type,
            context=question_text or "Identify the object the user wants to find.",
        )
    except MetaProviderError as exc:
        if not question_text:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        # The user already named the target: answer from authorized local
        # evidence instead of failing the whole search.
        logger.warning("image query analysis unavailable; using text fallback")
        return _answer_query(
            QueryRequest(workspace_id=workspace_id, question=question_text, language=language),
            user,
            db,
            None,
        )
    from app.query_lang import qtext

    labels = list(
        dict.fromkeys(item.label.strip() for item in analysis.detections if item.label.strip())
    )
    if not labels:
        text = qtext(language, "no_visual_info")
        return QueryResponse(
            found=False,
            message=text,
            tts_text=text,
            simulated=analysis.simulated,
            response_language=language,
        )
    combined = " ".join(part for part in [question_text, *labels] if part)[:500]
    result = _answer_query(
        QueryRequest(workspace_id=workspace_id, question=combined, language=language),
        user,
        db,
        client,
    )
    return result.model_copy(update={"simulated": analysis.simulated or result.simulated})


@router.post("/search/classify")
def classify_search_probe(
    request: Request,
    workspace_id: uuid.UUID = Form(...),
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Decide whether a captured probe looks like a person, an object, or is
    ambiguous. Probe bytes stay ephemeral; detection boxes are never stored."""

    from app.faces import FaceEngineError, build_face_engine

    workspace_member(workspace_id, user, db)
    if image.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(status_code=415, detail="Only JPEG, PNG or WebP images are accepted.")
    raw = image.file.read(20 * 1024 * 1024 + 1)
    if not raw or len(raw) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Invalid image size.")
    try:
        with Image.open(io.BytesIO(raw)) as decoded:
            decoded.verify()
    except (OSError, ValueError):
        raise HTTPException(status_code=422, detail="The image cannot be decoded.") from None
    try:
        engine = build_face_engine(request.app.state.settings)
        faces = engine.detect_faces(raw)
    except FaceEngineError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    try:
        client = build_meta_client(request.app.state.settings)
        analysis = client.analyze_image(
            raw,
            image.content_type,
            context="List the distinct non-person objects visible in this image.",
        )
    except MetaProviderError:
        # Object labels are auxiliary: the face count alone already routes
        # person probes, so a provider outage must not hide detected faces.
        logger.warning("search classify object analysis unavailable")
        analysis = None
    labels = (
        list(
            dict.fromkeys(item.label.strip() for item in analysis.detections if item.label.strip())
        )
        if analysis is not None
        else []
    )
    return {
        "faces": len(faces),
        "object_labels": labels,
        "simulated": bool(
            getattr(engine, "simulated", False) or (analysis.simulated if analysis else False)
        ),
    }


@router.post("/search/route")
def route_search_text(
    payload: SearchRouteRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Route free text to person search, object search, or a clarifying question.

    Ephemeral: the text is classified and never stored as a query or capture.
    """

    try:
        client = build_meta_client(request.app.state.settings)
        intent = client.classify_intent(payload.text.strip())
    except MetaProviderError:
        from app.providers.mock import MockMetaModelClient

        # Deterministic keyword routing keeps chat usable during an outage;
        # it is explicitly labelled simulated.
        logger.warning("search route intent unavailable; using keyword fallback")
        intent = MockMetaModelClient().classify_intent(payload.text.strip())
        return {"target": intent.target, "simulated": True}
    return {"target": intent.target, "simulated": intent.simulated}


@router.post("/device/queries", response_model=QueryResponse)
def device_query(
    payload: QueryRequest,
    request: Request,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> QueryResponse:
    try:
        client = build_meta_client(request.app.state.settings)
    except MetaProviderError:
        client = None
    return _answer_query(
        payload,
        None,
        db,
        client,
        authorized_workspace_id=device.workspace_id,
        device_view=True,
        display_device=device,
        settings=request.app.state.settings,
    )


@router.post("/queries/audio", response_model=QueryResponse)
def audio_query(
    request: Request,
    workspace_id: uuid.UUID = Form(...),
    audio: UploadFile = File(...),
    language: str = Form(default="en"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryResponse:
    language = language_diagnostic(request, user, language)
    workspace_member(workspace_id, user, db, {Role.ADMIN, Role.QUERY})
    if audio.content_type not in {"audio/wav", "audio/x-wav"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only WAV audio is accepted."
        )
    raw = audio.file.read(32 * 1024 * 1024 + 1)
    if not raw or len(raw) > 32 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Invalid audio size."
        )
    try:
        client = build_meta_client(request.app.state.settings)
        transcription = client.transcribe_wav(raw)
    except MetaProviderError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    result = _answer_query(
        QueryRequest(workspace_id=workspace_id, question=transcription.text, language=language),
        user,
        db,
        client,
    )
    return result.model_copy(update={"simulated": transcription.simulated or result.simulated})
