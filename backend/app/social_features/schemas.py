from __future__ import annotations

import uuid
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas import LocalizedGalleryInformation

"""Facebook identities and explicitly shared audiovisual publications."""


class InvitePermission(BaseModel):
    allowed: bool = False


class GroupAction(BaseModel):
    name: str = Field(default="", max_length=160)
    code: str = Field(default="", max_length=128)


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


class Share(BaseModel):
    audience: Literal["home", "public", "work"]
    workspace_id: uuid.UUID | None = None


class AssistantCommand(BaseModel):
    language: str | None = Field(default=None, max_length=16)
    text: str = Field(min_length=2, max_length=500)
    audience: Literal["home", "public", "work"] = "home"
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
    headline: str = Field(default="", max_length=240)
    biography: str = Field(default="", max_length=4000)
    phone: str = Field(default="", max_length=64)
    website: str = Field(default="", max_length=1024)
    social_links: list[ProfileLinkInput] = Field(default_factory=list, max_length=12)


class ProfileSearchRequest(BaseModel):
    language: str | None = Field(default=None, max_length=16)
    question: str = Field(min_length=2, max_length=500)
    user_id: uuid.UUID | None = None


class Publish(BaseModel):
    media_id: uuid.UUID
    audience: Literal["home", "public", "work"] = "home"
    caption: str = Field(default="", max_length=4000)
    workspace_id: uuid.UUID | None = None


class Interaction(BaseModel):
    action: Literal["like", "unlike", "comment", "report"]
    text: str = Field(default="", max_length=2000)
    parent_id: uuid.UUID | None = None
