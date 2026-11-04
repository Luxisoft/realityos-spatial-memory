from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.dependencies import get_current_device, get_current_user, get_db, workspace_member
from app.http.common import _assignment_response, _audit, _device_response
from app.models import (
    Device,
    DeviceAssignment,
    DeviceStatus,
    Role,
    User,
    Workspace,
    WorkspaceMember,
    Zone,
)
from app.schemas import (
    DeviceAssignmentCreate,
    DeviceAssignmentResponse,
    DeviceCreate,
    DeviceEnrollmentResponse,
    DeviceResponse,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
    VirtualDeviceBootstrapResponse,
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
from app.stored_display import display_text

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/virtual-devices/bootstrap",
    response_model=VirtualDeviceBootstrapResponse,
    status_code=status.HTTP_201_CREATED,
)
async def bootstrap_virtual_device(
    request: Request,
    installation_id: str = Header(alias="X-RealityOS-Installation-ID"),
    db: Session = Depends(get_db),
) -> VirtualDeviceBootstrapResponse:
    """Issue a short-lived, real device identity for Meta's virtual glasses.

    The route exists so the APK can show usable live values without committing a
    permanent device key. The reverse proxy rate-limits this public bootstrap
    endpoint and all issued identities remain scoped to one configured workspace.
    """

    settings: Settings = request.app.state.settings
    if not settings.virtual_device_bootstrap_enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Virtual enrollment is disabled."
        )
    if settings.meta_mode.lower() != "live":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Virtual enrollment requires RealityOS Live processing.",
        )
    try:
        install_uuid = uuid.UUID(installation_id)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid virtual-glasses installation identifier is required.",
        ) from error

    workspace = db.scalar(
        select(Workspace).where(Workspace.name == settings.virtual_device_workspace_name)
    )
    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="The configured live virtual-glasses workspace is unavailable.",
        )

    identifier = f"virtual-display-{install_uuid.hex}"
    device = db.scalar(select(Device).where(Device.device_identifier == identifier))
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.virtual_device_ttl_minutes)
    device_key = create_device_credential()
    metadata = {
        "virtual_device": True,
        "installation_id": str(install_uuid),
        "virtual_device_expires_at": expires_at.isoformat(),
        "provisioning_source": "android_virtual_glasses",
    }
    if device is None:
        device = Device(
            workspace_id=workspace.id,
            device_identifier=identifier,
            label=f"Virtual Meta Ray-Ban Display {install_uuid.hex[:8]}",
            credential_hash=hash_device_credential(device_key, settings),
            created_by_id=workspace.created_by_id,
            metadata_json=metadata,
        )
        db.add(device)
        db.flush()
    else:
        if device.workspace_id != workspace.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Virtual device is bound to a different workspace.",
            )
        device.credential_hash = hash_device_credential(device_key, settings)
        device.status = DeviceStatus.ACTIVE
        device.revoked_at = None
        device.metadata_json = metadata

    _audit(
        db,
        "device.virtual_bootstrapped",
        "device",
        workspace.created_by_id,
        device.id,
        workspace.id,
        device.id,
    )
    return VirtualDeviceBootstrapResponse(
        api_base_url=str(settings.virtual_device_base_url).rstrip("/"),
        workspace_id=workspace.id,
        workspace_name=workspace.name,
        device_id=device.device_identifier,
        device_key=device_key,
        expires_at=expires_at,
        processing_mode="live",
    )


@router.get("/device/zones", response_model=list[ZoneResponse])
async def list_device_zones(
    device: Device = Depends(get_current_device), db: Session = Depends(get_db)
) -> list[Zone]:
    """Return the enrolled device's locations without exposing other workspaces."""

    return list(
        db.scalars(
            select(Zone)
            .where(Zone.workspace_id == device.workspace_id)
            .order_by(Zone.sort_order, Zone.name)
        )
    )


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest, request: Request, db: Session = Depends(get_db)
) -> TokenResponse:
    from app.accounts.models import PasswordAccount
    from app.accounts.service import throttle

    throttle(db, request, payload.email, "login")
    identifier = payload.email.strip().casefold()
    user = db.scalar(select(User).where(User.email == identifier))
    if user is None:
        account = db.scalar(select(PasswordAccount).where(PasswordAccount.username == identifier))
        user = db.get(User, account.user_id) if account else None
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
    if (
        token is None
        or token.revoked_at is not None
        or (token.expires_at if token.expires_at.tzinfo else token.expires_at.replace(tzinfo=UTC))
        < datetime.now(UTC)
    ):
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
        select(Workspace, WorkspaceMember.role, WorkspaceMember.can_invite)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.name)
    ).all()
    return [
        WorkspaceResponse(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            display_text=display_text(workspace),
            created_at=workspace.created_at,
            role=role.value,
            created_by_me=workspace.created_by_id == user.id,
            can_invite=role == Role.ADMIN or bool(member_can_invite),
        )
        for workspace, role, member_can_invite in rows
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
        display_text=display_text(workspace),
        created_at=workspace.created_at,
        role=Role.ADMIN.value,
        created_by_me=True,
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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Device ID already exists."
        )
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
    _audit(
        db,
        "device.credential_rotated",
        "device",
        user.id,
        device.id,
        device.workspace_id,
        device.id,
    )
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
        external_reference=payload.external_reference.strip()
        if payload.external_reference
        else None,
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
