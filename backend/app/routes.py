from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from PIL import Image, ImageDraw
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.meta import MetaProviderError, build_meta_client
from app.models import (
    AuditEvent,
    CaptureSession,
    CaptureStatus,
    JobStatus,
    MediaAsset,
    MediaAssetChunk,
    MediaKind,
    ObjectAlias,
    ObjectObservation,
    ProcessingJob,
    ProcessingOperation,
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
    ObjectAliasCreate,
    ObjectAliasResponse,
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
from app.services import (
    add_postgres_bytea_chunks,
    create_processing_job,
    create_segmentation_job,
    exact_term_candidates,
    media_is_chunked,
    media_sha256,
    multilingual_object_candidates,
    normalize,
    object_candidates,
    verified_candidates,
)
from app.video import VideoProcessingError, probe_video

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
        muse_bounding_box=item.muse_bounding_box,
        bounding_box=item.bounding_box,
        spatial_description=item.spatial_description,
        seen_at=item.seen_at,
        visual_confidence=item.visual_confidence,
        model_name=item.model_name,
        verification_status=item.verification_status.value,
    )


def _job_response(item: ProcessingJob) -> JobResponse:
    return JobResponse(
        id=item.id,
        media_asset_id=item.media_asset_id,
        observation_id=item.observation_id,
        operation=item.operation.value,
        status=item.status.value,
        provider=item.provider,
        attempts=item.attempts,
        error_message=item.error_message,
        result_metadata=item.result_metadata,
        created_at=item.created_at,
    )


def _segmentation_details(
    db: Session, observation: ObjectObservation
) -> tuple[str, ProcessingJob | None]:
    if observation.mask_asset_id:
        return "ready", None
    job = db.scalar(
        select(ProcessingJob)
        .where(
            ProcessingJob.observation_id == observation.id,
            ProcessingJob.operation == ProcessingOperation.SEGMENTATION,
        )
        .order_by(desc(ProcessingJob.created_at))
    )
    if job is None:
        return "not_requested", None
    if job.status == JobStatus.QUEUED:
        return "queued", job
    if job.status == JobStatus.PROCESSING:
        return "processing", job
    if job.status == JobStatus.FAILED:
        return "failed", job
    if job.result_metadata.get("segmentation_status") == "no_match":
        return "no_match", job
    return "not_requested", job


def _highlight_quality(observation: ObjectObservation) -> str:
    if observation.mask_asset_id:
        return "sam_mask"
    if observation.muse_bounding_box or observation.bounding_box:
        return "approximate_box"
    return "none"


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
    request: Request,
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
    image_types = {"image/jpeg", "image/png", "image/webp"}
    video_types = {"video/mp4", "video/quicktime", "video/webm"}
    if file.content_type not in image_types | video_types:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported image or video type.",
        )
    raw = await file.read()
    settings = request.app.state.settings
    is_video = file.content_type in video_types
    limit = settings.max_video_bytes if is_video else settings.max_image_bytes
    if len(raw) == 0 or (limit and len(raw) > limit):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Invalid media size.",
        )
    duration_seconds: float | None = None
    if is_video:
        try:
            video_info = probe_video(raw)
        except VideoProcessingError as exc:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
        if (
            settings.max_video_seconds
            and video_info.duration_seconds > settings.max_video_seconds
        ):
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Video exceeds the {settings.max_video_seconds}-second limit.",
            )
        width, height = video_info.width, video_info.height
        duration_seconds = video_info.duration_seconds
    else:
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
    chunked_video = is_video and len(raw) > settings.video_inline_bytes
    asset = MediaAsset(
        workspace_id=session.workspace_id,
        capture_session_id=session.id,
        kind=MediaKind.VIDEO if is_video else MediaKind.IMAGE,
        mime_type=file.content_type,
        original_bytes=b"" if chunked_video else raw,
        sha256=digest,
        byte_size=len(raw),
        width=width,
        height=height,
        captured_at=captured_at,
        extra_metadata={
            "filename": file.filename or "capture",
            **({"duration_seconds": duration_seconds} if duration_seconds is not None else {}),
        },
    )
    db.add(asset)
    db.flush()
    if chunked_video:
        add_postgres_bytea_chunks(db, asset, raw, settings.video_bytea_chunk_bytes)
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
    return _job_response(job)


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
    return _job_response(job)


@router.get("/objects", response_model=list[ObjectResponse])
async def list_objects(
    workspace_id: uuid.UUID,
    q: str | None = None,
    category: str | None = None,
    zone_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db)
    statement = select(TrackedObject).where(TrackedObject.workspace_id == workspace_id)
    if q:
        candidate_ids = [item.id for item in object_candidates(db, workspace_id, q)]
        if not candidate_ids:
            return []
        statement = statement.where(TrackedObject.id.in_(candidate_ids))
    if category:
        statement = statement.where(TrackedObject.category == category.strip())
    if zone_id:
        zone = db.get(Zone, zone_id)
        if zone is None or zone.workspace_id != workspace_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found.")
        statement = statement.join(
            ObjectObservation, ObjectObservation.object_id == TrackedObject.id
        ).where(ObjectObservation.zone_id == zone_id)
    return list(db.scalars(statement.order_by(TrackedObject.canonical_name)).unique())


@router.get("/objects/{object_id}", response_model=ObjectResponse)
async def get_object(
    object_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    tracked = db.get(TrackedObject, object_id)
    if tracked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found.")
    workspace_member(tracked.workspace_id, user, db)
    return _object_response(tracked)


@router.post(
    "/objects/{object_id}/aliases",
    response_model=ObjectAliasResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_object_alias(
    object_id: uuid.UUID,
    payload: ObjectAliasCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ObjectAlias:
    tracked = db.get(TrackedObject, object_id)
    if tracked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found.")
    workspace_member(tracked.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    alias_value = normalize(payload.alias)
    if len(alias_value) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Alias must contain at least two meaningful characters.",
        )
    existing = db.scalar(
        select(ObjectAlias).where(
            ObjectAlias.object_id == object_id,
            ObjectAlias.alias == alias_value,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Object alias already exists.")
    alias = ObjectAlias(object_id=object_id, alias=alias_value)
    db.add(alias)
    db.flush()
    _audit(db, "object.alias_created", "object_alias", user.id, alias.id, tracked.workspace_id)
    return alias


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


@router.post("/observations/{observation_id}/segment", response_model=JobResponse, status_code=202)
async def request_observation_segmentation(
    observation_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Explicitly refine one verified evidence item; Query users cannot invoke this."""

    observation = db.get(ObjectObservation, observation_id)
    if observation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found.")
    workspace_member(observation.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    if observation.verification_status != VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only verified observations can be refined with SAM.",
        )
    if not (observation.muse_bounding_box or observation.bounding_box):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This observation has no approximate geometry to refine.",
        )
    try:
        job = create_segmentation_job(db, observation, request.app.state.settings.meta_mode)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    _audit(
        db,
        "observation.segmentation_requested",
        "processing_job",
        user.id,
        job.id,
        observation.workspace_id,
    )
    db.commit()
    if request.app.state.settings.enqueue_processing and job.status != JobStatus.COMPLETED:
        try:
            from app.tasks import process_media

            process_media.delay(str(job.id))
        except Exception:
            # The durable job remains visible and can be picked up later.
            pass
    return _job_response(job)


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


def _answer_query(
    payload: QueryRequest,
    user: User,
    db: Session,
    client=None,
) -> QueryResponse:
    member = workspace_member(payload.workspace_id, user, db, {Role.ADMIN, Role.QUERY})
    candidates, interpretation_simulated = multilingual_object_candidates(
        db, payload.workspace_id, payload.question, client
    )
    # A generic model label can collide with an explicit human alias. Resolve
    # only that exact-name collision; broad requests must remain ambiguous.
    exact_matches = exact_term_candidates(db, payload.workspace_id, payload.question)
    if len(candidates) > 1 and len(exact_matches) > 1:
        verified = verified_candidates(db, payload.workspace_id, candidates)
        if len(verified) == 1:
            candidates = verified
    if not candidates:
        text = "There is not enough evidence of that object in this workspace."
        return QueryResponse(
            found=False,
            message=text,
            tts_text=text,
            simulated=interpretation_simulated,
        )
    if len(candidates) > 1:
        names = ", ".join(candidate.canonical_name for candidate in candidates[:3])
        text = f"There are several matches: {names}. Please specify which one you need."
        return QueryResponse(
            found=False,
            ambiguous=True,
            message=text,
            tts_text=text,
            simulated=interpretation_simulated,
        )
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
        text = f"There is no verified observation for {tracked.canonical_name}."
        return QueryResponse(
            found=False,
            message=text,
            object=_object_response(tracked),
            tts_text=text,
            simulated=interpretation_simulated,
        )
    path = _zone_path(db, observation.zone_id)
    location = ", ".join(path) if path else "location has no detail"
    detail = (observation.spatial_description or "no additional spatial detail").rstrip(". ")
    text = (
        f"{tracked.canonical_name[:1].upper() + tracked.canonical_name[1:]} was last seen in "
        f"{location}, {detail}. Observed on {observation.seen_at.date().isoformat()}."
    )
    segmentation_status, segmentation_job = _segmentation_details(db, observation)
    highlight_quality = _highlight_quality(observation)
    return QueryResponse(
        found=True,
        message=text,
        object=_object_response(tracked),
        observation=_observation_response(observation),
        zone_path=path,
        media_id=observation.media_asset_id,
        highlighted_media_url=(
            f"/v1/observations/{observation.id}/highlighted"
            if highlight_quality != "none"
            else None
        ),
        highlight_quality=highlight_quality,
        segmentation_status=segmentation_status,
        segmentation_job_id=segmentation_job.id if segmentation_job else None,
        can_refine=member.role in {Role.ADMIN, Role.REGISTER}
        and segmentation_status in {"not_requested", "failed"}
        and highlight_quality == "approximate_box",
        retrieval_confidence=observation.visual_confidence,
        tts_text=text,
        simulated=observation.model_name.startswith("mock-") or interpretation_simulated,
    )


@router.post("/queries", response_model=QueryResponse)
async def query(
    payload: QueryRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QueryResponse:
    try:
        client = build_meta_client(request.app.state.settings)
    except MetaProviderError:
        client = None
    return _answer_query(payload, user, db, client)


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
        client = build_meta_client(request.app.state.settings)
        transcription = client.transcribe_wav(raw)
    except MetaProviderError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    result = _answer_query(
        QueryRequest(workspace_id=workspace_id, question=transcription.text), user, db, client
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
    headers = {"Content-Disposition": f'inline; filename="{asset.id}"'}
    if media_is_chunked(asset):
        def chunk_stream():
            for chunk in db.scalars(
                select(MediaAssetChunk.content)
                .where(MediaAssetChunk.asset_id == asset.id)
                .order_by(MediaAssetChunk.chunk_index)
            ):
                yield chunk

        return StreamingResponse(chunk_stream(), media_type=asset.mime_type, headers=headers)
    return Response(content=asset.original_bytes, media_type=asset.mime_type, headers=headers)


def _render_highlight(
    db: Session, observation: ObjectObservation, asset: MediaAsset
) -> Response:
    """Render an ephemeral overlay; original evidence and binary mask stay immutable."""

    if observation.workspace_id != asset.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    try:
        with Image.open(io.BytesIO(asset.original_bytes)).convert("RGBA") as image:
            if observation.mask_asset_id:
                mask_asset = db.get(MediaAsset, observation.mask_asset_id)
                if mask_asset is None or mask_asset.workspace_id != observation.workspace_id:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="SAM mask is no longer available.",
                    )
                with Image.open(io.BytesIO(mask_asset.original_bytes)).convert("L") as mask:
                    resized_mask = mask.resize(image.size, Image.Resampling.NEAREST)
                alpha = resized_mask.point(lambda value: 128 if value else 0)
                overlay = Image.new("RGBA", image.size, (255, 199, 0, 0))
                overlay.putalpha(alpha)
                image.alpha_composite(overlay)
                box = observation.bounding_box
                if box:
                    _draw_box(image, box, color=(255, 235, 90, 255))
            else:
                box = observation.muse_bounding_box or observation.bounding_box
                if not box:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="No highlight geometry is available.",
                    )
                _draw_box(image, box, color=(255, 199, 0, 255))
            output = io.BytesIO()
            image.save(output, format="PNG")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Media cannot be highlighted."
        )
    return Response(content=output.getvalue(), media_type="image/png")


def _draw_box(image: Image.Image, box: dict, color: tuple[int, int, int, int]) -> None:
    x = int(float(box["x"]) * image.width)
    y = int(float(box["y"]) * image.height)
    right = int((float(box["x"]) + float(box["width"])) * image.width)
    bottom = int((float(box["y"]) + float(box["height"])) * image.height)
    ImageDraw.Draw(image).rectangle(
        (x, y, right, bottom), outline=color, width=max(3, image.width // 120)
    )


@router.get("/observations/{observation_id}/highlighted")
async def highlighted_observation(
    observation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    observation = db.get(ObjectObservation, observation_id)
    if observation is None or observation.verification_status != VerificationStatus.VERIFIED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found.")
    workspace_member(observation.workspace_id, user, db)
    asset = db.get(MediaAsset, observation.media_asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    return _render_highlight(db, observation, asset)


@router.get("/media/{media_id}/highlighted")
async def highlighted_media(
    media_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> Response:
    """Compatibility endpoint; queries now use an observation-specific overlay."""

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
    if observation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No verified highlight is available."
        )
    return _render_highlight(db, observation, asset)
