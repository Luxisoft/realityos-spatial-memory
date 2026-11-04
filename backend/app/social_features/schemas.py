from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas import LocalizedGalleryInformation
from app.social_features.classification_schemas import ClassificationInput

"""Facebook identities and explicitly shared audiovisual publications."""


class InvitePermission(BaseModel):
    allowed: bool = False


class GroupAction(BaseModel):
    name: str = Field(default="", max_length=160)
    code: str = Field(default="", max_length=128)
    categories: list[str] = Field(default_factory=list, max_length=100)
    tags: list[str] = Field(default_factory=list, max_length=200)


class PinJoin(BaseModel):
    pin: str = Field(min_length=9, max_length=16)


class ChatGalleryItem(BaseModel):
    localized_information: dict[str, LocalizedGalleryInformation] = Field(default_factory=dict)
    thumbnail_url: str = Field(min_length=1, max_length=1024)
    media_url: str = Field(default="", max_length=1024)
    caption: str = Field(default="", max_length=400)
    boxed_url: str = Field(default="", max_length=2048)
    evidence_id: uuid.UUID | None = None
    media_id: uuid.UUID | None = None
    image_url: str = Field(default="", max_length=2048)
    mime_type: str = "image/jpeg"
    frame_timestamp_ms: int | None = Field(default=None, ge=0)
    note_text: str = Field(default="", max_length=4000)
    note_source: str = ""
    matched_labels: list[str] = Field(default_factory=list, max_length=32)
    confidence: float | None = Field(default=None, ge=0, le=1)
    published_at: str = ""
    simulated: bool = False
    match_kind: Literal["exact", "family", "similar"] | None = None
    localization_quality: Literal["sam", "approximate_box"] | None = None


class ChatQuickReplyItem(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    label: str = Field(min_length=1, max_length=64)


class ChatAppend(BaseModel):
    response_language: str | None = Field(default=None, max_length=16)
    role: Literal["user", "ai"] = "user"
    kind: str = "text"
    text: str = Field(min_length=1, max_length=4000)
    evidence_url: str | None = Field(default=None, max_length=1024)
    gallery: list[ChatGalleryItem] = Field(default_factory=list, max_length=6)
    simulated: bool = False
    quick_replies: list[ChatQuickReplyItem] = Field(default_factory=list, max_length=4)
    face_action: bool = False


class MergeTexts(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=12)


class Share(ClassificationInput):
    model_config = ConfigDict(extra="forbid")
    workspace_id: uuid.UUID


class AssistantCommand(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: str | None = Field(default=None, max_length=16)
    text: str = Field(min_length=2, max_length=500)
    workspace_id: uuid.UUID | None = None
    post_id: uuid.UUID | None = None


class FacebookLogin(BaseModel):
    access_token: str = Field(min_length=1, max_length=4096)
    device_id: str | None = Field(default=None, min_length=1, max_length=128)


class GuestLogin(BaseModel):
    device_id: str = Field(min_length=1, max_length=128)


class ProfileLinkInput(BaseModel):
    label: str = Field(min_length=1, max_length=40)
    url: str = Field(min_length=8, max_length=1024)


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    birthday: date | None = None
    gender: str | None = Field(default=None, max_length=32)
    hometown: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=160)
    headline: str = Field(default="", max_length=240)
    biography: str = Field(default="", max_length=4000)
    phone: str = Field(default="", max_length=64)
    website: str = Field(default="", max_length=1024)
    social_links: list[ProfileLinkInput] = Field(default_factory=list, max_length=12)

    @field_validator("display_name")
    @classmethod
    def valid_display_name(cls, value):
        if value is None or not value.strip():
            raise ValueError("A display name is required.")
        return value.strip()

    @field_validator("birthday", mode="before")
    @classmethod
    def valid_birthday(cls, value):
        if value is None:
            return None
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("Use YYYY-MM-DD for the birthday.")
        parsed = date.fromisoformat(value)
        if (
            parsed.isoformat() != value
            or not date(1900, 1, 1) <= parsed <= datetime.now(UTC).date()
        ):
            raise ValueError("Birthday must be a past or current date from 1900 onwards.")
        return parsed


class ProfileSearchRequest(BaseModel):
    language: str | None = Field(default=None, max_length=16)
    question: str = Field(min_length=2, max_length=500)
    user_id: uuid.UUID | None = None


class Publish(ClassificationInput):
    model_config = ConfigDict(extra="forbid")
    media_id: uuid.UUID
    caption: str = Field(default="", max_length=4000)
    workspace_id: uuid.UUID


class Interaction(BaseModel):
    action: Literal["like", "unlike", "comment", "report"]
    text: str = Field(default="", max_length=2000)
    parent_id: uuid.UUID | None = None
