from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from PIL import Image, ImageDraw
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_device, get_current_user, get_db, workspace_member
from app.meta import MetaProviderError, build_meta_client
from app.models import (
    AuditEvent,
    CaptureSession,
    CaptureStatus,
    Device,
    DeviceAssignment,
    DeviceStatus,
    JobStatus,
    MediaAsset,
    MediaAssetChunk,
    MediaKind,
    ObjectAlias,
    ObjectFact,
    ObjectObservation,
    ObjectTrack,
    ObjectTrackFrame,
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
    DeviceAssignmentCreate,
    DeviceAssignmentResponse,
    DeviceCreate,
    DeviceEnrollmentResponse,
    DeviceResponse,
    DeviceSessionCreate,
    InventoryAnalyticsResponse,
    JobResponse,
    LoginRequest,
    ObjectAliasCreate,
    ObjectAliasResponse,
    ObjectFactResponse,
    ObjectFactUpdate,
    ObjectResponse,
    ObservationResponse,
    ObservationUpdate,
    ProcessingRequest,
    QueryRequest,
    QueryResponse,
    RefreshRequest,
    SessionCreate,
    SessionResponse,
    TokenResponse,
    TrackFrameResponse,
    TrackResponse,
    UserResponse,
    WorkspaceCreate,
    WorkspaceResponse,
    ZoneCreate,
    ZoneResponse,
)
from app.security import (
    create_access_token,
    create_device_credential,
    create_refresh_token,
    decode_token,
    hash_device_credential,
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
    device_id: uuid.UUID | None = None,
) -> None:
    db.add(
        AuditEvent(
            workspace_id=workspace_id,
            actor_id=actor_id,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            device_id=device_id,
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


def _device_response(item: Device) -> DeviceResponse:
    return DeviceResponse(
        id=item.id,
        workspace_id=item.workspace_id,
        device_identifier=item.device_identifier,
        label=item.label,
        status=item.status.value,
        last_seen_at=item.last_seen_at,
        revoked_at=item.revoked_at,
        metadata=item.metadata_json,
    )


def _assignment_response(item: DeviceAssignment) -> DeviceAssignmentResponse:
    return DeviceAssignmentResponse(
        id=item.id,
        device_id=item.device_id,
        operator_label=item.operator_label,
        external_reference=item.external_reference,
        effective_from=item.effective_from,
        effective_to=item.effective_to,
        notice_version=item.notice_version,
    )


def _fact_response(item: ObjectFact) -> ObjectFactResponse:
    return ObjectFactResponse(
        id=item.id,
        object_id=item.object_id,
        observation_id=item.observation_id,
        fact_type=item.fact_type,
        value_text=item.value_text,
        normalized_value=item.normalized_value,
        numeric_value=item.numeric_value,
        unit=item.unit,
        confidence=item.confidence,
        provenance=item.provenance.value,
        evidence_geometry=item.evidence_geometry,
        model_name=item.model_name,
        verification_status=item.verification_status.value,
    )


def _track_response(item: ObjectTrack) -> TrackResponse:
    return TrackResponse(
        id=item.id,
        object_id=item.object_id,
        source_media_asset_id=item.source_media_asset_id,
        model_name=item.model_name,
        status=item.status,
        last_seen_at=item.last_seen_at,
        last_seen_pts_seconds=item.last_seen_pts_seconds,
        metadata=item.metadata_json,
    )


def _track_frame_response(item: ObjectTrackFrame) -> TrackFrameResponse:
    return TrackFrameResponse(
        id=item.id,
        track_id=item.track_id,
        source_frame_index=item.source_frame_index,
        pts_seconds=item.pts_seconds,
        visible=item.visible,
        bounding_box=item.bounding_box,
        confidence=item.confidence,
        simulated=item.simulated,
    )


def _active_assignment(db: Session, device: Device) -> DeviceAssignment | None:
    now = datetime.now(UTC)
    return db.scalar(
        select(DeviceAssignment)
        .where(
            DeviceAssignment.device_id == device.id,
            DeviceAssignment.effective_from <= now,
            (DeviceAssignment.effective_to.is_(None)) | (DeviceAssignment.effective_to > now),
        )
        .order_by(desc(DeviceAssignment.effective_from))
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


@router.get("/admin/devices", response_model=list[DeviceResponse])
async def list_devices(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DeviceResponse]:
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    return [
        _device_response(item)
        for item in db.scalars(
            select(Device)
            .where(Device.workspace_id == workspace_id)
            .order_by(Device.label, Device.device_identifier)
        )
    ]


@router.post(
    "/admin/devices", response_model=DeviceEnrollmentResponse, status_code=status.HTTP_201_CREATED
)
async def enroll_device(
    payload: DeviceCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeviceEnrollmentResponse:
    workspace_member(payload.workspace_id, user, db, {Role.ADMIN})
    identifier = payload.device_identifier.strip()
    if db.scalar(select(Device.id).where(Device.device_identifier == identifier)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device ID already exists.")
    device_key = create_device_credential()
    device = Device(
        workspace_id=payload.workspace_id,
        device_identifier=identifier,
        label=payload.label.strip(),
        credential_hash=hash_device_credential(device_key, request.app.state.settings),
        created_by_id=user.id,
        metadata_json=payload.metadata,
    )
    db.add(device)
    db.flush()
    _audit(db, "device.enrolled", "device", user.id, device.id, device.workspace_id, device.id)
    result = _device_response(device)
    return DeviceEnrollmentResponse(**result.model_dump(), device_key=device_key)


@router.post("/admin/devices/{device_id}/rotate", response_model=DeviceEnrollmentResponse)
async def rotate_device_credential(
    device_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeviceEnrollmentResponse:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")
    workspace_member(device.workspace_id, user, db, {Role.ADMIN})
    if device.status != DeviceStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device is revoked.")
    device_key = create_device_credential()
    device.credential_hash = hash_device_credential(device_key, request.app.state.settings)
    _audit(db, "device.credential_rotated", "device", user.id, device.id, device.workspace_id, device.id)
    result = _device_response(device)
    return DeviceEnrollmentResponse(**result.model_dump(), device_key=device_key)


@router.post("/admin/devices/{device_id}/revoke", response_model=DeviceResponse)
async def revoke_device(
    device_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeviceResponse:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")
    workspace_member(device.workspace_id, user, db, {Role.ADMIN})
    device.status = DeviceStatus.REVOKED
    device.revoked_at = datetime.now(UTC)
    _audit(db, "device.revoked", "device", user.id, device.id, device.workspace_id, device.id)
    return _device_response(device)


@router.get("/admin/devices/{device_id}/assignments", response_model=list[DeviceAssignmentResponse])
async def list_device_assignments(
    device_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DeviceAssignmentResponse]:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")
    workspace_member(device.workspace_id, user, db, {Role.ADMIN})
    return [
        _assignment_response(item)
        for item in db.scalars(
            select(DeviceAssignment)
            .where(DeviceAssignment.device_id == device.id)
            .order_by(desc(DeviceAssignment.effective_from))
        )
    ]


@router.post(
    "/admin/devices/{device_id}/assignments",
    response_model=DeviceAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assign_device(
    device_id: uuid.UUID,
    payload: DeviceAssignmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeviceAssignmentResponse:
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")
    workspace_member(device.workspace_id, user, db, {Role.ADMIN})
    now = datetime.now(UTC)
    for current in db.scalars(
        select(DeviceAssignment).where(
            DeviceAssignment.device_id == device.id, DeviceAssignment.effective_to.is_(None)
        )
    ):
        current.effective_to = now
    assignment = DeviceAssignment(
        device_id=device.id,
        operator_label=payload.operator_label.strip(),
        external_reference=payload.external_reference.strip() if payload.external_reference else None,
        attested_by_id=user.id,
        notice_version=payload.notice_version.strip(),
        effective_from=now,
    )
    db.add(assignment)
    db.flush()
    _audit(
        db,
        "device.assigned",
        "device_assignment",
        user.id,
        assignment.id,
        device.workspace_id,
        device.id,
    )
    return _assignment_response(assignment)


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


@router.post("/device/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_device_session(
    payload: DeviceSessionCreate,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> SessionResponse:
    if payload.zone_id:
        zone = db.get(Zone, payload.zone_id)
        if zone is None or zone.workspace_id != device.workspace_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zone not found.")
    assignment = _active_assignment(db, device)
    session = CaptureSession(
        workspace_id=device.workspace_id,
        zone_id=payload.zone_id,
        created_by_id=None,
        device_id=device.id,
        device_assignment_id=assignment.id if assignment else None,
        origin="device",
        consent_confirmed=True,
    )
    db.add(session)
    db.flush()
    _audit(
        db,
        "device.capture_session.opened",
        "capture_session",
        None,
        session.id,
        session.workspace_id,
        device.id,
    )
    return _session_response(session)


@router.post("/device/sessions/{session_id}/close", response_model=SessionResponse)
async def close_device_session(
    session_id: uuid.UUID,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> SessionResponse:
    session = db.get(CaptureSession, session_id)
    if session is None or session.device_id != device.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capture session not found.")
    if session.status == CaptureStatus.OPEN:
        session.status = CaptureStatus.CLOSED
        session.closed_at = datetime.now(UTC)
        _audit(
            db,
            "device.capture_session.closed",
            "capture_session",
            None,
            session.id,
            session.workspace_id,
            device.id,
        )
    return _session_response(session)


async def _store_capture(
    request: Request,
    session: CaptureSession,
    captured_at: datetime | None = Form(default=None),
    file: UploadFile = File(...),
    *,
    db: Session,
    actor_id: uuid.UUID | None,
    device_id: uuid.UUID | None = None,
) -> CaptureResponse:
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
    _audit(
        db,
        "capture.created",
        "media_asset",
        actor_id,
        asset.id,
        session.workspace_id,
        device_id,
    )
    return _capture_response(asset)


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
    return await _store_capture(
        request,
        session,
        captured_at,
        file,
        db=db,
        actor_id=user.id,
    )


@router.post("/device/captures", response_model=CaptureResponse, status_code=status.HTTP_201_CREATED)
async def create_device_capture(
    request: Request,
    session_id: uuid.UUID = Form(...),
    captured_at: datetime | None = Form(default=None),
    file: UploadFile = File(...),
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> CaptureResponse:
    session = db.get(CaptureSession, session_id)
    if session is None or session.device_id != device.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capture session not found.")
    return await _store_capture(
        request,
        session,
        captured_at,
        file,
        db=db,
        actor_id=None,
        device_id=device.id,
    )


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
    payload: ProcessingRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = db.get(MediaAsset, capture_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capture not found.")
    workspace_member(asset.workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    profile = payload or ProcessingRequest()
    job = create_processing_job(
        db,
        asset,
        provider=request.app.state.settings.meta_mode,
        profile=profile.profile,
        priority_terms=profile.priority_terms,
    )
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


@router.post("/device/captures/{capture_id}/process", response_model=JobResponse)
async def process_device_capture(
    capture_id: uuid.UUID,
    request: Request,
    payload: ProcessingRequest | None = None,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> JobResponse:
    asset = db.get(MediaAsset, capture_id)
    if asset is None or asset.workspace_id != device.workspace_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Capture not found.")
    session = db.get(CaptureSession, asset.capture_session_id) if asset.capture_session_id else None
    if session is None or session.device_id != device.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Capture belongs to another device.")
    profile = payload or ProcessingRequest()
    job = create_processing_job(
        db,
        asset,
        provider=request.app.state.settings.meta_mode,
        profile=profile.profile,
        priority_terms=profile.priority_terms,
    )
    _audit(
        db,
        "device.capture.processing_requested",
        "processing_job",
        None,
        job.id,
        asset.workspace_id,
        device.id,
    )
    db.commit()
    if request.app.state.settings.enqueue_processing:
        try:
            from app.tasks import process_media

            process_media.delay(str(job.id))
        except Exception:
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


@router.get("/objects/{object_id}/facts", response_model=list[ObjectFactResponse])
async def object_facts(
    object_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[ObjectFactResponse]:
    tracked = db.get(TrackedObject, object_id)
    if tracked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found.")
    workspace_member(tracked.workspace_id, user, db, {Role.ADMIN})
    return [
        _fact_response(item)
        for item in db.scalars(
            select(ObjectFact)
            .where(ObjectFact.object_id == object_id)
            .order_by(desc(ObjectFact.created_at))
        )
    ]


@router.patch("/facts/{fact_id}", response_model=ObjectFactResponse)
async def verify_fact(
    fact_id: uuid.UUID,
    payload: ObjectFactUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ObjectFactResponse:
    fact = db.get(ObjectFact, fact_id)
    if fact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fact not found.")
    workspace_member(fact.workspace_id, user, db, {Role.ADMIN})
    fact.verification_status = VerificationStatus(payload.verification_status)
    fact.verified_by_id = user.id
    fact.verified_at = datetime.now(UTC)
    if payload.value_text is not None:
        fact.value_text = payload.value_text.strip() or None
    if payload.normalized_value is not None:
        fact.normalized_value = normalize(payload.normalized_value) or None
    tracked = db.get(TrackedObject, fact.object_id)
    if tracked and fact.verification_status == VerificationStatus.VERIFIED:
        values = dict(tracked.attributes or {})
        if fact.fact_type == "visible_count" and fact.numeric_value is not None:
            values["visible_count"] = fact.numeric_value
        elif fact.value_text:
            values[fact.fact_type] = fact.value_text
        tracked.attributes = values
    _audit(db, "object_fact.verified", "object_fact", user.id, fact.id, fact.workspace_id)
    return _fact_response(fact)


@router.get("/objects/{object_id}/tracks", response_model=list[TrackResponse])
async def object_tracks(
    object_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> list[TrackResponse]:
    tracked = db.get(TrackedObject, object_id)
    if tracked is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found.")
    workspace_member(tracked.workspace_id, user, db, {Role.ADMIN})
    return [
        _track_response(item)
        for item in db.scalars(
            select(ObjectTrack)
            .where(ObjectTrack.object_id == tracked.id)
            .order_by(desc(ObjectTrack.created_at))
        )
    ]


@router.get("/tracks/{track_id}/frames", response_model=list[TrackFrameResponse])
async def track_frames(
    track_id: uuid.UUID,
    offset: int = 0,
    limit: int = 240,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TrackFrameResponse]:
    if offset < 0 or limit < 1 or limit > 1000:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid page.")
    track = db.get(ObjectTrack, track_id)
    if track is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Track not found.")
    workspace_member(track.workspace_id, user, db, {Role.ADMIN})
    return [
        _track_frame_response(item)
        for item in db.scalars(
            select(ObjectTrackFrame)
            .where(ObjectTrackFrame.track_id == track.id)
            .order_by(ObjectTrackFrame.source_frame_index)
            .offset(offset)
            .limit(limit)
        )
    ]


def _fact_rollup(db: Session, workspace_id: uuid.UUID, fact_type: str) -> list[dict]:
    rows = db.execute(
        select(
            ObjectFact.normalized_value,
            ObjectFact.value_text,
            func.count(func.distinct(ObjectFact.object_id)),
        )
        .where(
            ObjectFact.workspace_id == workspace_id,
            ObjectFact.fact_type == fact_type,
            ObjectFact.verification_status == VerificationStatus.VERIFIED,
        )
        .group_by(ObjectFact.normalized_value, ObjectFact.value_text)
        .order_by(desc(func.count(func.distinct(ObjectFact.object_id))))
    ).all()
    return [
        {"value": normalized or display or "unknown", "count": int(count)}
        for normalized, display, count in rows
    ]


@router.get("/admin/analytics/inventory", response_model=InventoryAnalyticsResponse)
async def inventory_analytics(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InventoryAnalyticsResponse:
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    verified_object_count = db.scalar(
        select(func.count(func.distinct(ObjectFact.object_id))).where(
            ObjectFact.workspace_id == workspace_id,
            ObjectFact.verification_status == VerificationStatus.VERIFIED,
        )
    ) or 0
    provisional_fact_count = db.scalar(
        select(func.count(ObjectFact.id)).where(
            ObjectFact.workspace_id == workspace_id,
            ObjectFact.verification_status == VerificationStatus.PENDING,
        )
    ) or 0
    category_rows = db.execute(
        select(TrackedObject.category, func.count(TrackedObject.id))
        .where(TrackedObject.workspace_id == workspace_id)
        .group_by(TrackedObject.category)
        .order_by(desc(func.count(TrackedObject.id)))
    ).all()
    device_rows = db.execute(
        select(Device.label, Device.device_identifier, func.count(CaptureSession.id))
        .outerjoin(CaptureSession, CaptureSession.device_id == Device.id)
        .where(Device.workspace_id == workspace_id)
        .group_by(Device.id, Device.label, Device.device_identifier)
        .order_by(Device.label)
    ).all()
    return InventoryAnalyticsResponse(
        workspace_id=workspace_id,
        verified_object_count=int(verified_object_count),
        provisional_fact_count=int(provisional_fact_count),
        brands=_fact_rollup(db, workspace_id, "brand"),
        categories=[{"value": value or "uncategorized", "count": int(count)} for value, count in category_rows],
        conditions=_fact_rollup(db, workspace_id, "condition"),
        usage_states=_fact_rollup(db, workspace_id, "usage_state"),
        devices=[
            {"label": label, "device_id": identifier, "capture_sessions": int(count)}
            for label, identifier, count in device_rows
        ],
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
    user: User | None,
    db: Session,
    client=None,
    *,
    authorized_workspace_id: uuid.UUID | None = None,
    device_view: bool = False,
) -> QueryResponse:
    if user is None:
        if authorized_workspace_id != payload.workspace_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace access denied.")
        can_refine = False
    else:
        member = workspace_member(payload.workspace_id, user, db, {Role.ADMIN, Role.QUERY})
        can_refine = member.role in {Role.ADMIN, Role.REGISTER}
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
            (
                f"/v1/device/observations/{observation.id}/highlighted"
                if device_view
                else f"/v1/observations/{observation.id}/highlighted"
            )
            if highlight_quality != "none"
            else None
        ),
        highlight_quality=highlight_quality,
        segmentation_status=segmentation_status,
        segmentation_job_id=segmentation_job.id if segmentation_job else None,
        can_refine=can_refine
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


@router.post("/device/queries", response_model=QueryResponse)
async def device_query(
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
    )


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


@router.get("/device/observations/{observation_id}/highlighted")
async def device_highlighted_observation(
    observation_id: uuid.UUID,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> Response:
    observation = db.get(ObjectObservation, observation_id)
    if (
        observation is None
        or observation.workspace_id != device.workspace_id
        or observation.verification_status != VerificationStatus.VERIFIED
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Observation not found.")
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
