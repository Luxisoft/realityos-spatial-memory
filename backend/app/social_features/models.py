from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models import (
    TimestampMixin,
)

"""Facebook identities and explicitly shared audiovisual publications."""


class FacebookIdentity(Base):
    __tablename__ = "facebook_identities"
    subject: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), unique=True)


class ChatMessage(TimestampMixin, Base):
    """Persisted AI chat turn. Text only; capture bytes and audio stay ephemeral."""

    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(8))
    kind: Mapped[str] = mapped_column(String(8), default="text")
    text: Mapped[str] = mapped_column(Text)
    evidence_url: Mapped[str | None] = mapped_column(String(1024))
    audio_duration_ms: Mapped[int] = mapped_column(default=0)
    gallery: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    quick_replies: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    response_language: Mapped[str | None] = mapped_column(String(16))
    template_data: Mapped[dict | None] = mapped_column(JSON)
    face_action: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ChatAudio(TimestampMixin, Base):
    """Voice note segment attached to one chat turn. Owner-only playback."""

    __tablename__ = "chat_audio"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    audio: Mapped[bytes] = mapped_column(LargeBinary)
    mime_type: Mapped[str] = mapped_column(String(32))
    duration_ms: Mapped[int] = mapped_column(default=0)


class PublicationTerm(TimestampMixin, Base):
    __tablename__ = "publication_terms"
    __table_args__ = (
        UniqueConstraint("workspace_id", "kind", "name_key", name="uq_publication_term_name"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(16))
    name: Mapped[str] = mapped_column(String(80))
    name_key: Mapped[str] = mapped_column(String(160))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PublicationTag(Base):
    __tablename__ = "publication_tags"
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publications.id", ondelete="CASCADE"), primary_key=True
    )
    term_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("publication_terms.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class Publication(TimestampMixin, Base):
    __tablename__ = "publications"
    __table_args__ = (
        UniqueConstraint("owner_id", "source", "source_ref", name="uq_publication_source"),
        UniqueConstraint("shared_from_id", "workspace_id", name="uq_publication_group_copy"),
        Index("ix_publication_feed", "workspace_id", "published_at", "id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    shared_from_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("publications.id"), index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("publication_terms.id", ondelete="SET NULL"), index=True
    )
    media_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("media_assets.id"))
    caption: Mapped[str] = mapped_column(Text, default="")
    note_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    note_source: Mapped[str] = mapped_column(String(16), default="", nullable=False)
    search_text: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ai_labels: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    ai_detections: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    active_index_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("gallery_index_runs.id", use_alter=True, name="fk_publication_active_index_run")
    )
    evidence_version: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )
    ai_caption: Mapped[str] = mapped_column(Text, default="", nullable=False)
    face_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    index_error: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), default="local", nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(160))
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    hidden: Mapped[bool] = mapped_column(default=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"), nullable=False)


class Reaction(Base):
    __tablename__ = "publication_likes"
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)


class Comment(TimestampMixin, Base):
    __tablename__ = "publication_comments"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.id"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("publication_comments.id"))
    text: Mapped[str] = mapped_column(Text)


class Report(TimestampMixin, Base):
    __tablename__ = "publication_reports"
    __table_args__ = (UniqueConstraint("post_id", "user_id"),)
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("publications.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)


class GroupInvite(Base):
    __tablename__ = "group_invites"
    code: Mapped[str] = mapped_column(String(128), primary_key=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id"))
    active: Mapped[bool] = mapped_column(default=True)


class FacebookProfile(TimestampMixin, Base):
    """Synced Facebook profile for one local user. Visible only to its owner."""

    __tablename__ = "facebook_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    email: Mapped[str | None] = mapped_column(String(320))
    birthday: Mapped[str | None] = mapped_column(String(32))
    age_min: Mapped[int | None] = mapped_column(Integer)
    age_max: Mapped[int | None] = mapped_column(Integer)
    gender: Mapped[str | None] = mapped_column(String(32))
    hometown: Mapped[str | None] = mapped_column(String(160))
    location: Mapped[str | None] = mapped_column(String(160))
    profile_link: Mapped[str | None] = mapped_column(String(512))
    picture_url: Mapped[str | None] = mapped_column(String(1024))
    friends_count: Mapped[int | None] = mapped_column(Integer)
    likes_count: Mapped[int | None] = mapped_column(Integer)
    photos_count: Mapped[int | None] = mapped_column(Integer)
    videos_count: Mapped[int | None] = mapped_column(Integer)
    granted_scopes: Mapped[list] = mapped_column(JSON, default=list)
    import_status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False)
    imported_photos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    imported_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sync_diagnostics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    skipped_media: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    picture_imported: Mapped[bool] = mapped_column(default=False, nullable=False)
    import_error: Mapped[str | None] = mapped_column(String(500))
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserProfile(TimestampMixin, Base):
    """Public profile fields plus the owner's single private, replaceable CV."""

    __tablename__ = "user_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    birthday: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String(32))
    hometown: Mapped[str | None] = mapped_column(String(160))
    location: Mapped[str | None] = mapped_column(String(160))
    headline: Mapped[str] = mapped_column(String(240), default="", nullable=False)
    biography: Mapped[str] = mapped_column(Text, default="", nullable=False)
    phone: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    website: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    social_links: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    avatar_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL")
    )
    cv_bytes: Mapped[bytes | None] = mapped_column(LargeBinary)
    cv_filename: Mapped[str | None] = mapped_column(String(255))
    cv_mime_type: Mapped[str | None] = mapped_column(String(128))
    cv_sha256: Mapped[str | None] = mapped_column(String(64))
    cv_text: Mapped[str | None] = mapped_column(Text)
    cv_context: Mapped[str | None] = mapped_column(Text)
    cv_status: Mapped[str] = mapped_column(String(16), default="empty", nullable=False)
    cv_error: Mapped[str | None] = mapped_column(String(500))
    cv_simulated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cv_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class FacebookFriend(Base):
    """A friend explicitly returned by Graph for this app-scoped login."""

    __tablename__ = "facebook_friends"
    __table_args__ = (Index("ix_facebook_friends_owner", "owner_user_id"),)

    owner_user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    facebook_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    picture_url: Mapped[str | None] = mapped_column(String(1024))
    profile_link: Mapped[str | None] = mapped_column(String(1024))


class FacebookMedia(Base):
    """Inventory of one Facebook photo/video. Bytes import separately on purpose."""

    __tablename__ = "facebook_media"
    __table_args__ = (Index("ix_facebook_media_user", "user_id"),)

    fb_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    kind: Mapped[str] = mapped_column(String(8), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2048))
    caption: Mapped[str | None] = mapped_column(Text)
    fb_created_time: Mapped[str | None] = mapped_column(String(64))
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    imported_media_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("media_assets.id", ondelete="SET NULL")
    )


class FacebookPost(TimestampMixin, Base):
    """Raw post material for future personality-profile analysis. Owner-only."""

    __tablename__ = "facebook_posts"
    __table_args__ = (Index("ix_facebook_post_user", "user_id"),)

    fb_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    message: Mapped[str | None] = mapped_column(Text)
    fb_created_time: Mapped[str | None] = mapped_column(String(64))
    permalink: Mapped[str | None] = mapped_column(String(1024))


class ChatMessageTranslation(Base):
    __tablename__ = "chat_message_translations"

    message_id: Mapped[int] = mapped_column(
        ForeignKey("chat_messages.id", ondelete="CASCADE"), primary_key=True
    )
    language: Mapped[str] = mapped_column(String(2), primary_key=True)
    source_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    text: Mapped[str] = mapped_column(Text, default="")
    quick_replies: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    simulated: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
