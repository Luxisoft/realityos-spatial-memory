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
    status: str
    provider: str
    attempts: int
    error_message: str | None
    created_at: datetime


class ObjectResponse(FromAttributes):
    id: uuid.UUID
    canonical_name: str
    category: str | None
    attributes: dict


class ObservationUpdate(BaseModel):
    verification_status: Literal["verified", "rejected"]
    spatial_description: str | None = Field(default=None, max_length=3000)


class ObservationResponse(FromAttributes):
    id: uuid.UUID
    object_id: uuid.UUID
    zone_id: uuid.UUID | None
    media_asset_id: uuid.UUID
    bounding_box: dict | None
    spatial_description: str | None
    seen_at: datetime
    visual_confidence: float
    model_name: str
    verification_status: str


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
    retrieval_confidence: float | None = None
    tts_text: str
    simulated: bool = False


class MetaDetection(BaseModel):
    label: str
    confidence: float = Field(ge=0, le=1)
    bounding_box: dict[str, float] | None = None
    spatial_description: str | None = None


class ImageAnalysis(BaseModel):
    model: str
    simulated: bool
    detections: list[MetaDetection]
