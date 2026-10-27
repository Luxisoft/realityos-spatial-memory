from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class FromAttributes(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=512)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class UserResponse(FromAttributes):
    id: uuid.UUID
    email: str
    display_name: str


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    description: str | None = Field(default=None, max_length=5000)


class WorkspaceResponse(FromAttributes):
    id: uuid.UUID
    name: str
    description: str | None
    created_at: datetime
    role: str | None = None


class ZoneCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    parent_id: uuid.UUID | None = None
    kind: str = Field(default="zone", min_length=1, max_length=32)
    sort_order: int = Field(default=0, ge=0, le=9999)


class ZoneResponse(FromAttributes):
    id: uuid.UUID
    workspace_id: uuid.UUID
    parent_id: uuid.UUID | None
    name: str
    kind: str
    sort_order: int


class SessionCreate(BaseModel):
    workspace_id: uuid.UUID
    zone_id: uuid.UUID | None = None
    consent_confirmed: bool


class DeviceCreate(BaseModel):
    workspace_id: uuid.UUID
    device_identifier: str = Field(min_length=3, max_length=96, pattern=r"^[A-Za-z0-9._:-]+$")
    label: str = Field(min_length=2, max_length=160)
    metadata: dict = Field(default_factory=dict)


class DeviceAssignmentCreate(BaseModel):
    operator_label: str = Field(min_length=1, max_length=160)
    external_reference: str | None = Field(default=None, max_length=160)
    notice_version: str = Field(min_length=1, max_length=80)


class DeviceResponse(FromAttributes):
    id: uuid.UUID
    workspace_id: uuid.UUID
    device_identifier: str
    label: str
    status: str
    last_seen_at: datetime | None
    revoked_at: datetime | None
    metadata: dict = Field(default_factory=dict)


class DeviceEnrollmentResponse(DeviceResponse):
    device_key: str


class VirtualDeviceBootstrapResponse(BaseModel):
    """One real, temporary device credential for Meta's virtual glasses."""

    api_base_url: str
    workspace_id: uuid.UUID
    workspace_name: str
    device_id: str
    device_key: str
    expires_at: datetime
    processing_mode: Literal["live"]


class DeviceAssignmentResponse(FromAttributes):
    id: uuid.UUID
    device_id: uuid.UUID
    operator_label: str
    external_reference: str | None
    effective_from: datetime
    effective_to: datetime | None
    notice_version: str


class DeviceSessionCreate(BaseModel):
    zone_id: uuid.UUID | None = None


class ProcessingRequest(BaseModel):
    profile: Literal["basic", "detailed"] = "basic"
    priority_terms: list[str] = Field(default_factory=list, max_length=16)


class SessionResponse(FromAttributes):
    id: uuid.UUID
    workspace_id: uuid.UUID
    zone_id: uuid.UUID | None
    status: str
    started_at: datetime
    closed_at: datetime | None
    consent_confirmed: bool


class CaptureResponse(FromAttributes):
    id: uuid.UUID
    workspace_id: uuid.UUID
    capture_session_id: uuid.UUID | None
    kind: str
    mime_type: str
    sha256: str
    byte_size: int
    width: int | None
    height: int | None
    created_at: datetime


class JobResponse(FromAttributes):
    id: uuid.UUID
    media_asset_id: uuid.UUID
    observation_id: uuid.UUID | None = None
    operation: str
    status: str
    provider: str
    attempts: int
    error_message: str | None
    result_metadata: dict = Field(default_factory=dict)
    created_at: datetime


class ObjectResponse(FromAttributes):
    id: uuid.UUID
    canonical_name: str
    category: str | None
    attributes: dict


class ObjectAliasCreate(BaseModel):
    alias: str = Field(min_length=2, max_length=240)


class ObjectAliasResponse(FromAttributes):
    id: uuid.UUID
    object_id: uuid.UUID
    alias: str


class ObservationUpdate(BaseModel):
    verification_status: Literal["verified", "rejected"]
    spatial_description: str | None = Field(default=None, max_length=3000)


class ObservationResponse(FromAttributes):
    id: uuid.UUID
    object_id: uuid.UUID
    zone_id: uuid.UUID | None
    media_asset_id: uuid.UUID
    muse_bounding_box: dict | None = None
    bounding_box: dict | None
    spatial_description: str | None
    seen_at: datetime
    visual_confidence: float
    model_name: str
    verification_status: str


class ObjectFactResponse(FromAttributes):
    id: uuid.UUID
    object_id: uuid.UUID
    observation_id: uuid.UUID | None
    fact_type: str
    value_text: str | None
    normalized_value: str | None
    numeric_value: float | None
    unit: str | None
    confidence: float
    provenance: str
    evidence_geometry: dict | None
    model_name: str
    verification_status: str


class ObjectFactUpdate(BaseModel):
    verification_status: Literal["verified", "rejected"]
    value_text: str | None = Field(default=None, max_length=500)
    normalized_value: str | None = Field(default=None, max_length=500)


class InventoryAnalyticsResponse(BaseModel):
    workspace_id: uuid.UUID
    verified_object_count: int
    provisional_fact_count: int
    brands: list[dict]
    categories: list[dict]
    conditions: list[dict]
    usage_states: list[dict]
    devices: list[dict]


class TrackResponse(FromAttributes):
    id: uuid.UUID
    object_id: uuid.UUID
    source_media_asset_id: uuid.UUID
    model_name: str
    status: str
    last_seen_at: datetime | None
    last_seen_pts_seconds: float | None
    metadata: dict = Field(default_factory=dict)


class TrackFrameResponse(FromAttributes):
    id: uuid.UUID
    track_id: uuid.UUID
    source_frame_index: int
    pts_seconds: float
    visible: bool
    bounding_box: dict | None
    confidence: float | None
    simulated: bool


class QueryRequest(BaseModel):
    workspace_id: uuid.UUID
    question: str = Field(min_length=2, max_length=500)


class QueryResponse(BaseModel):
    found: bool
    ambiguous: bool = False
    message: str
    object: ObjectResponse | None = None
    observation: ObservationResponse | None = None
    zone_path: list[str] = Field(default_factory=list)
    media_id: uuid.UUID | None = None
    highlighted_media_url: str | None = None
    # A short-lived URL for DAT Display image rendering. It is populated only
    # for device-authenticated queries and must never be reused as API auth.
    display_media_url: str | None = None
    highlight_quality: Literal["sam_mask", "approximate_box", "none"] = "none"
    segmentation_status: Literal[
        "not_requested", "queued", "processing", "ready", "no_match", "failed"
    ] = "not_requested"
    segmentation_job_id: uuid.UUID | None = None
    can_refine: bool = False
    retrieval_confidence: float | None = None
    tts_text: str
    simulated: bool = False


class MetaFact(BaseModel):
    """A bounded, evidence-linked visual claim returned by the analysis provider."""

    fact_type: Literal[
        "brand",
        "manufacturer",
        "model",
        "product_line",
        "visible_text",
        "color",
        "condition",
        "usage_state",
        "packaging",
        "visible_count",
    ]
    value_text: str | None = Field(default=None, max_length=500)
    normalized_value: str | None = Field(default=None, max_length=500)
    numeric_value: float | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=40)
    confidence: float = Field(ge=0, le=1)
    provenance: Literal["visible_text", "visual", "temporal"] = "visual"


class MetaDetection(BaseModel):
    label: str
    category: str | None = Field(default=None, max_length=120)
    confidence: float = Field(ge=0, le=1)
    bounding_box: dict[str, float] | None = None
    spatial_description: str | None = None
    relationships: list[dict[str, str]] = Field(default_factory=list)
    facts: list[MetaFact] = Field(default_factory=list, max_length=16)


class ImageAnalysis(BaseModel):
    model: str
    simulated: bool
    detections: list[MetaDetection]


class QueryInterpretation(BaseModel):
    """Only workspace-known terms may leave the query-understanding layer."""

    terms: list[str] = Field(default_factory=list, max_length=8)
    simulated: bool = False
