from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

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
from sqlalchemy.orm import Session

from app.dependencies import get_current_device, get_current_user, get_db, workspace_member
from app.http.common import (
    _active_assignment,
    _audit,
    _capture_response,
    _job_response,
    _session_response,
    _store_capture,
)
from app.models import (
    CaptureSession,
    CaptureStatus,
    Device,
    MediaAsset,
    ProcessingJob,
    Role,
    User,
    Zone,
)
from app.schemas import (
    CaptureResponse,
    DeviceSessionCreate,
    JobResponse,
    ProcessingRequest,
    SessionCreate,
    SessionResponse,
)
from app.services import (
    create_processing_job,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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


@router.post(
    "/device/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED
)
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
        created_by_id=device.created_by_id if device.metadata_json.get("facebook_owner") else None,
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Capture session not found."
        )
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


@router.post(
    "/device/captures", response_model=CaptureResponse, status_code=status.HTTP_201_CREATED
)
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Capture session not found."
        )
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
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Capture belongs to another device."
        )
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


@router.get("/device/jobs/{job_id}", response_model=JobResponse)
async def get_device_job(
    job_id: uuid.UUID,
    device: Device = Depends(get_current_device),
    db: Session = Depends(get_db),
) -> JobResponse:
    """Return only jobs created from a capture session owned by this device.

    Device credentials are deliberately narrower than a workspace membership:
    a device may observe its own upload's processing state, but never another
    device's capture history, even when both are assigned to the same workspace.
    """

    job = db.get(ProcessingJob, job_id)
    session = db.get(CaptureSession, job.capture_session_id) if job else None
    if (
        job is None
        or job.workspace_id != device.workspace_id
        or session is None
        or session.workspace_id != device.workspace_id
        or session.device_id != device.id
    ):
        # Keep the response indistinguishable from an unknown job so a device
        # cannot enumerate another device's capture activity.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Processing job not found."
        )
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
