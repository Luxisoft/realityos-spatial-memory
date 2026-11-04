from __future__ import annotations

from app.models import (
    CaptureSession,
    Device,
    DeviceAssignment,
    MediaAsset,
    ObjectFact,
    ObjectObservation,
    ObjectTrack,
    ObjectTrackFrame,
    ProcessingJob,
    TrackedObject,
)
from app.schemas import (
    CaptureResponse,
    DeviceAssignmentResponse,
    DeviceResponse,
    JobResponse,
    ObjectFactResponse,
    ObjectResponse,
    ObservationResponse,
    SessionResponse,
    TrackFrameResponse,
    TrackResponse,
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
        started_at=item.started_at,
        completed_at=item.completed_at,
    )


def _object_response(item: TrackedObject) -> ObjectResponse:
    return ObjectResponse(
        id=item.id,
        canonical_name=item.canonical_name,
        category=item.category,
        attributes=item.attributes,
    )
