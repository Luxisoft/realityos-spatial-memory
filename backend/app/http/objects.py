from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.http.common import (
    _audit,
    _fact_response,
    _fact_rollup,
    _job_response,
    _object_response,
    _observation_response,
    _track_frame_response,
    _track_response,
)
from app.models import (
    CaptureSession,
    Device,
    JobStatus,
    ObjectAlias,
    ObjectFact,
    ObjectObservation,
    ObjectTrack,
    ObjectTrackFrame,
    Role,
    TrackedObject,
    User,
    VerificationStatus,
    Zone,
)
from app.schemas import (
    InventoryAnalyticsResponse,
    JobResponse,
    ObjectAliasCreate,
    ObjectAliasResponse,
    ObjectFactResponse,
    ObjectFactUpdate,
    ObjectResponse,
    ObservationResponse,
    ObservationUpdate,
    TrackFrameResponse,
    TrackResponse,
)
from app.services import (
    create_segmentation_job,
    normalize,
    object_candidates,
)

logger = logging.getLogger(__name__)

router = APIRouter()


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
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Object alias already exists."
        )
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
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid page."
        )
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


@router.get("/admin/analytics/inventory", response_model=InventoryAnalyticsResponse)
async def inventory_analytics(
    workspace_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> InventoryAnalyticsResponse:
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    verified_object_count = (
        db.scalar(
            select(func.count(func.distinct(ObjectFact.object_id))).where(
                ObjectFact.workspace_id == workspace_id,
                ObjectFact.verification_status == VerificationStatus.VERIFIED,
            )
        )
        or 0
    )
    provisional_fact_count = (
        db.scalar(
            select(func.count(ObjectFact.id)).where(
                ObjectFact.workspace_id == workspace_id,
                ObjectFact.verification_status == VerificationStatus.PENDING,
            )
        )
        or 0
    )
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
        categories=[
            {"value": value or "uncategorized", "count": int(count)}
            for value, count in category_rows
        ],
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
