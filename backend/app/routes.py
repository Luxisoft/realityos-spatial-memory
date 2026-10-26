from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from PIL import Image, ImageDraw
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.meta import MetaProviderError, build_meta_client
from app.models import (
    AuditEvent,
    CaptureSession,
    CaptureStatus,
    MediaAsset,
    MediaKind,
    ObjectObservation,
    ProcessingJob,
    Role,
    TrackedObject,
    User,
    VerificationStatus,
    Workspace,
    WorkspaceMember,
    Zone,
)
from app.schemas import (
    CaptureResponse,
    JobResponse,
    LoginRequest,
    ObjectResponse,
    ObservationResponse,
    ObservationUpdate,
    QueryRequest,
    QueryResponse,
    RefreshRequest,
    SessionCreate,
    SessionResponse,
    TokenResponse,
    UserResponse,
    WorkspaceCreate,
    WorkspaceResponse,
    ZoneCreate,
    ZoneResponse,
)
from app.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.services import create_processing_job, media_sha256, object_candidates

router = APIRouter()


def _audit(
    db: Session,
    event_type: str,
    entity_type: str,
    actor_id: uuid.UUID | None,
    entity_id: uuid.UUID | None = None,
    workspace_id: uuid.UUID | None = None,
) -> None:
    db.add(
        AuditEvent(
            workspace_id=workspace_id,
            actor_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
        )
    )


def _session_response(item: CaptureSession) -> SessionResponse:
    return SessionResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        zone_id=item.zone_id,
        status=item.status.value,
        started_at=item.started_at,
        closed_at=item.closed_at,
        consent_confirmed=item.consent_confirmed,
    )


def _capture_response(item: MediaAsset) -> CaptureResponse:
    return CaptureResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        capture_session_id=item.capture_session_id,
        kind=item.kind.value,
        mime_type=item.mime_type,
        sha256=item.sha256,
        byte_size=item.byte_size,
        width=item.width,
        height=item.height,
        created_at=item.created_at,
    )


def _observation_response(item: ObjectObservation) -> ObservationResponse:
    return ObservationResponse(
        id=item.id,
        object_id=item.object_id,
        zone_id=item.zone_id,
        media_asset_id=item.media_asset_id,
        bounding_box=item.bounding_box,
        spatial_description=item.spatial_description,
        seen_at=item.seen_at,
        visual_confidence=item.visual_confidence,
        model_name=item.model_name,
        verification_status=item.verification_status.value,
    )


def _object_response(item: TrackedObject) -> ObjectResponse:
    return ObjectResponse(
        id=item.id,
        canonical_name=item.canonical_name,
        category=item.category,
        attributes=item.attributes,
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, request: Request, db: Session = Depends(get_db)
) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.casefold()))
    if (
        user is None
        or not user.is_active
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password."
        )
    settings = request.app.state.settings
    refresh_token, jti, expires_at = create_refresh_token(user.id, settings)
    from app.models import RefreshToken

    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
    _audit(db, "auth.login", "user", user.id, user.id)
    return TokenResponse(
        access_token=create_access_token(user.id, settings), refresh_token=refresh_token
    )


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest, request: Request, db: Session = Depends(get_db)
) -> TokenResponse:
    from app.models import RefreshToken

    try:
        claims = decode_token(payload.refresh_token, request.app.state.settings, "refresh")
        user_id = uuid.UUID(str(claims["sub"]))
        token = db.scalar(select(RefreshToken).where(RefreshToken.jti == str(claims["jti"])))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token."
        )
    if token is None or token.revoked_at is not None or token.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Expired or revoked refresh token."
        )
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or unknown user."
        )
    token.revoked_at = datetime.now(UTC)
    new_token, jti, expires_at = create_refresh_token(user.id, request.app.state.settings)
    db.add(RefreshToken(user_id=user.id, jti=jti, expires_at=expires_at))
    return TokenResponse(
        access_token=create_access_token(user.id, request.app.state.settings),
        refresh_token=new_token,
    )


@router.get("/auth/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/workspaces", response_model=list[WorkspaceResponse])
async def list_workspaces(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.name)
    ).all()
    return [
        WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            created_at=workspace.created_at,
            role=role.value,
        )
        for workspace, role in rows
    ]


@router.post("/workspaces", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
async def create_workspace(
    payload: WorkspaceCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> WorkspaceResponse:
    existing = db.scalar(select(Workspace).where(Workspace.name == payload.name.strip()))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Workspace name already exists."
        )
    workspace = Workspace(
        name=payload.name.strip(),
        description=payload.description,
        created_by_id=user.id,
    )
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN))
    _audit(db, "workspace.created", "workspace", user.id, workspace.id, workspace.id)
    return WorkspaceResponse(
        id=workspace.id,
        name=workspace.name,
        description=workspace.description,
        created_at=workspace.created_at,
        role=Role.ADMIN.value,
    )


@router.get("/workspaces/{workspace_id}/zones", response_model=list[ZoneResponse])
async def list_zones(
    workspace_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    workspace_member(workspace_id, user, db)
    return list(
        db.scalars(
            select(Zone)
            .where(Zone.workspace_id == workspace_id)
            .order_by(Zone.sort_order, Zone.name)
        )
    )


@router.post(
    "/workspaces/{workspace_id}/zones",
    response_model=ZoneResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_zone(
    workspace_id: uuid.UUID,
    payload: ZoneCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    if payload.parent_id:
        parent = db.get(Zone, payload.parent_id)
        if parent is None or parent.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Parent zone not found."
            )
    zone = Zone(workspace_id=workspace_id, **payload.model_dump())
    db.add(zone)
    db.flush()
    _audit(db, "zone.created", "zone", user.id, zone.id, workspace_id)
    return zone


@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: SessionCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    workspace_member(payload.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    if not payload.consent_confirmed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Explicit capture consent is required.",
        )
    if payload.zone_id:
        zone = db.get(Zone, payload.zone_id)
        if zone is None or zone.workspace_id != payload.workspace_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found.")
    session = CaptureSession(created_by_id=user.id, **payload.model_dump())
    db.add(session)
    db.flush()
    _audit(
        db, "capture_session.opened", "capture_session", user.id, session.id, session.workspace_id
    )
    return _session_response(session)


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = db.get(CaptureSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Capture session not found."
        )
    workspace_member(session.workspace_id, user, db)
    return _session_response(session)


@router.post("/sessions/{session_id}/close", response_model=SessionResponse)
async def close_session(
    session_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = db.get(CaptureSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Capture session not found."
        )
    workspace_member(session.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    if session.status == CaptureStatus.OPEN:
        session.status = CaptureStatus.CLOSED
        session.closed_at = datetime.now(UTC)
        _audit(
            db,
            "capture_session.closed",
            "capture_session",
            user.id,
            session.id,
            session.workspace_id,
        )
    return _session_response(session)


@router.post("/captures", response_model=CaptureResponse, status_code=status.HTTP_201_CREATED)
async def create_capture(
    session_id: uuid.UUID = Form(...),
    captured_at: datetime | None = Form(default=None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CaptureResponse:
    session = db.get(CaptureSession, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Capture session not found."
        )
    workspace_member(session.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    if session.status != CaptureStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Capture session is closed."
        )
    allowed = {"image/jpeg", "image/png", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported image type."
        )
    raw = await file.read()
    limit = 10 * 1024 * 1024
    if len(raw) == 0 or len(raw) > limit:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Invalid image size."
        )
    try:
        with Image.open(io.BytesIO(raw)) as image:
            width, height = image.size
            image.verify()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid image data."
        )
    digest = media_sha256(raw)
    existing = db.scalar(
        select(MediaAsset).where(
            MediaAsset.capture_session_id == session.id,
            MediaAsset.sha256 == digest,
        )
    )
    if existing:
        return _capture_response(existing)
    asset = MediaAsset(
        workspace_id=session.workspace_id,
        capture_session_id=session.id,
        kind=MediaKind.IMAGE,
        mime_type=file.content_type,
        original_bytes=raw,
        sha256=digest,
        byte_size=len(raw),
        width=width,
        height=height,
        captured_at=captured_at,
        extra_metadata={"filename": file.filename or "capture"},
    )
    db.add(asset)
    db.flush()
    _audit(db, "capture.created", "media_asset", user.id, asset.id, session.workspace_id)
    return _capture_response(asset)


@router.get("/captures/{capture_id}", response_model=CaptureResponse)
async def get_capture(
    capture_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    asset = db.get(MediaAsset, capture_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capture not found.")
    workspace_member(asset.workspace_id, user, db)
    return _capture_response(asset)


@router.post("/captures/{capture_id}/process", response_model=JobResponse)
async def process_capture(
    capture_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = db.get(MediaAsset, capture_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capture not found.")
    workspace_member(asset.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    job = create_processing_job(db, asset, provider=request.app.state.settings.meta_mode)
    _audit(
        db, "capture.processing_requested", "processing_job", user.id, job.id, asset.workspace_id
    )
    db.commit()
    if request.app.state.settings.enqueue_processing:
        try:
            from app.tasks import process_media

            process_media.delay(str(job.id))
        except Exception:
            # The durable job remains queued for a worker to pick up; do not claim it completed.
            pass
    return JobResponse(
        id=job.id,
        media_asset_id=job.media_asset_id,
        status=job.status.value,
        provider=job.provider,
        attempts=job.attempts,
        error_message=job.error_message,
        created_at=job.created_at,
    )


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    job = db.get(ProcessingJob, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Processing job not found."
        )
    workspace_member(job.workspace_id, user, db)
    return JobResponse(
        id=job.id,
        media_asset_id=job.media_asset_id,
        status=job.status.value,
        provider=job.provider,
        attempts=job.attempts,
        error_message=job.error_message,
        created_at=job.created_at,
    )


@router.get("/objects", response_model=list[ObjectResponse])
async def list_objects(
    workspace_id: uuid.UUID,
    q: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db)
    statement = select(TrackedObject).where(TrackedObject.workspace_id == workspace_id)
    if q:
        statement = statement.where(TrackedObject.canonical_name.ilike(f"%{q.casefold()}%"))
    return list(db.scalars(statement.order_by(TrackedObject.canonical_name)))


@router.get("/objects/{object_id}", response_model=ObjectResponse)
async def get_object(
    object_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    tracked = db.get(TrackedObject, object_id)
    if tracked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found.")
    workspace_member(tracked.workspace_id, user, db)
    return _object_response(tracked)


@router.get("/objects/{object_id}/history", response_model=list[ObservationResponse])
async def object_history(
    object_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    tracked = db.get(TrackedObject, object_id)
    if tracked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found.")
    workspace_member(tracked.workspace_id, user, db)
    return list(
        db.scalars(
            select(ObjectObservation)
            .where(ObjectObservation.object_id == object_id)
            .order_by(desc(ObjectObservation.seen_at))
        )
    )


@router.patch("/observations/{observation_id}", response_model=ObservationResponse)
async def verify_observation(
    observation_id: uuid.UUID,
    payload: ObservationUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    observation = db.get(ObjectObservation, observation_id)
    if observation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found.")
    workspace_member(observation.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    observation.verification_status = VerificationStatus(payload.verification_status)
    observation.verified_by_id = user.id
    observation.verified_at = datetime.now(UTC)
    if payload.spatial_description is not None:
        observation.spatial_description = payload.spatial_description
    _audit(
        db,
        "observation.verified",
        "object_observation",
        user.id,
        observation.id,
        observation.workspace_id,
    )
    return _observation_response(observation)


def _zone_path(db: Session, zone_id: uuid.UUID | None) -> list[str]:
    result: list[str] = []
    seen: set[uuid.UUID] = set()
    while zone_id and zone_id not in seen:
        seen.add(zone_id)
        zone = db.get(Zone, zone_id)
        if zone is None:
            break
        result.append(zone.name)
        zone_id = zone.parent_id
    return list(reversed(result))


def _answer_query(payload: QueryRequest, user: User, db: Session) -> QueryResponse:
    workspace_member(payload.workspace_id, user, db, {Role.ADMIN, Role.QUERY})
    candidates = object_candidates(db, payload.workspace_id, payload.question)
    if not candidates:
        text = "No hay evidencia suficiente de ese objeto en este espacio."
        return QueryResponse(found=False, message=text, tts_text=text)
    if len(candidates) > 1:
        names = ", ".join(candidate.canonical_name for candidate in candidates[:3])
        text = f"Hay varias coincidencias: {names}. Indica cuál buscas."
        return QueryResponse(found=False, ambiguous=True, message=text, tts_text=text)
    tracked = candidates[0]
    observation = db.scalar(
        select(ObjectObservation)
        .where(
            ObjectObservation.workspace_id == payload.workspace_id,
            ObjectObservation.object_id == tracked.id,
            ObjectObservation.verification_status == VerificationStatus.VERIFIED,
        )
        .order_by(desc(ObjectObservation.seen_at))
    )
    if observation is None:
        text = f"No hay una observación verificada para {tracked.canonical_name}."
        return QueryResponse(
            found=False, message=text, object=_object_response(tracked), tts_text=text
        )
    path = _zone_path(db, observation.zone_id)
    location = ", ".join(path) if path else "ubicación sin detalle"
    detail = observation.spatial_description or "sin detalle espacial adicional"
    text = (
        f"{tracked.canonical_name.capitalize()} fue visto por última vez en {location}, "
        f"{detail}. Observado el {observation.seen_at.date().isoformat()}."
    )
    return QueryResponse(
        found=True,
        message=text,
        object=_object_response(tracked),
        observation=_observation_response(observation),
        zone_path=path,
        media_id=observation.media_asset_id,
        highlighted_media_url=f"/v1/media/{observation.media_asset_id}/highlighted",
        retrieval_confidence=observation.visual_confidence,
        tts_text=text,
        simulated=observation.model_name.startswith("mock-"),
    )


@router.post("/queries", response_model=QueryResponse)
async def query(
    payload: QueryRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> QueryResponse:
    return _answer_query(payload, user, db)


@router.post("/queries/audio", response_model=QueryResponse)
async def audio_query(
    request: Request,
    workspace_id: uuid.UUID = Form(...),
    audio: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryResponse:
    workspace_member(workspace_id, user, db, {Role.ADMIN, Role.QUERY})
    if audio.content_type not in {"audio/wav", "audio/x-wav"}:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Only WAV audio is accepted."
        )
    raw = await audio.read()
    if not raw or len(raw) > 32 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Invalid audio size."
        )
    try:
        transcription = build_meta_client(request.app.state.settings).transcribe_wav(raw)
    except MetaProviderError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    result = _answer_query(
        QueryRequest(workspace_id=workspace_id, question=transcription.text), user, db
    )
    return result.model_copy(update={"simulated": transcription.simulated or result.simulated})


@router.get("/media/{media_id}")
async def get_media(
    media_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    asset = db.get(MediaAsset, media_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    workspace_member(asset.workspace_id, user, db)
    return Response(
        content=asset.original_bytes,
        media_type=asset.mime_type,
        headers={"Content-Disposition": f'inline; filename="{asset.id}"'},
    )


@router.get("/media/{media_id}/highlighted")
async def highlighted_media(
    media_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    asset = db.get(MediaAsset, media_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    workspace_member(asset.workspace_id, user, db)
    observation = db.scalar(
        select(ObjectObservation)
        .where(
            ObjectObservation.media_asset_id == media_id,
            ObjectObservation.verification_status == VerificationStatus.VERIFIED,
        )
        .order_by(desc(ObjectObservation.seen_at))
    )
    if observation is None or not observation.bounding_box:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No verified highlight is available."
        )
    try:
        with Image.open(io.BytesIO(asset.original_bytes)).convert("RGBA") as image:
            box = observation.bounding_box
            x = int(float(box["x"]) * image.width)
            y = int(float(box["y"]) * image.height)
            right = int((float(box["x"]) + float(box["width"])) * image.width)
            bottom = int((float(box["y"]) + float(box["height"])) * image.height)
            drawing = ImageDraw.Draw(image)
            drawing.rectangle(
                (x, y, right, bottom), outline=(255, 199, 0, 255), width=max(3, image.width // 120)
            )
            output = io.BytesIO()
            image.save(output, format="PNG")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Media cannot be highlighted."
        )
    return Response(content=output.getvalue(), media_type="image/png")
