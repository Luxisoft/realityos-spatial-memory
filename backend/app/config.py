from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets are read from the environment only."""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.facebook"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
    facebook_app_id: str | None = None
    facebook_app_secret: str | None = None
    social_moderator_facebook_ids: str = ""
    api_prefix: str = "/v1"
    database_url: str = "postgresql+psycopg://realityos:realityos@localhost:5432/realityos"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = Field(
        default="development-only-secret-must-change-before-production",
        min_length=24,
    )
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = Field(default=30, ge=5, le=120)
    refresh_token_days: int = Field(default=14, ge=1, le=90)
    # Display content is fetched by the glasses renderer, which cannot attach the
    # device headers used by the native client. Keep those bearer URLs short-lived
    # and scoped to exactly one observation and one enrolled device.
    display_evidence_token_minutes: int = Field(default=5, ge=1, le=30)
    # A dedicated value is preferred. When omitted, the already-required JWT
    # signing secret is used as a server-side fallback so a deployment cannot
    # accidentally authenticate every device with a public development value.
    device_credential_pepper: str | None = Field(default=None, min_length=24)
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    max_image_bytes: int = Field(default=10 * 1024 * 1024, ge=1)
    # Zero disables the application-level intake cap. PostgreSQL still has its
    # physical BYTEA limit and operators remain responsible for disk capacity.
    max_video_bytes: int = Field(default=0, ge=0)
    max_video_seconds: int = Field(default=0, ge=0)
    # Storage strategy, not an upload limit: large videos are split into
    # PostgreSQL BYTEA chunks to avoid single-value allocation limits.
    video_inline_bytes: int = Field(default=32 * 1024 * 1024, ge=1)
    video_bytea_chunk_bytes: int = Field(default=8 * 1024 * 1024, ge=1024 * 1024)
    video_segment_seconds: int = Field(default=120, ge=5, le=3600)
    video_frames_per_segment: int = Field(default=8, ge=1, le=24)
    meta_mode: str = "mock"
    model_api_key: str | None = None
    meta_api_base_url: AnyHttpUrl = "https://api.meta.ai/v1"
    meta_gateway_base_url: AnyHttpUrl | None = None
    meta_gateway_token: str | None = None
    meta_timeout_seconds: float = Field(default=30, gt=0, le=120)
    meta_video_timeout_seconds: float = Field(default=600, gt=0, le=900)
    meta_max_retries: int = Field(default=2, ge=0, le=5)
    tts_timeout_seconds: float = Field(default=30, gt=0, le=30)
    enqueue_processing: bool = True
    # Hackathon-only virtual glasses enrollment. This deliberately creates a
    # revocable device identity instead of embedding a reusable credential in
    # an Android APK. It must only be enabled on the public demo deployment.
    virtual_device_bootstrap_enabled: bool = False
    virtual_device_workspace_name: str = "Taller de electrónica"
    virtual_device_base_url: AnyHttpUrl = "https://realityos.luxisoft.com/v1"
    virtual_device_ttl_minutes: int = Field(default=1440, ge=30, le=10080)
    # Isolated biometric face-search arm. "mock" is deterministic and makes no
    # external call; "insightface" needs the backend faces extra (unverified live).
    face_engine: str = "mock"
    face_match_threshold: float = Field(default=0.5, ge=-1.0, le=1.0)
    face_search_limit: int = Field(default=20, ge=1, le=100)
    biometric_notice_version: str = "2026-10-28.1"
    facebook_photo_sync_limit: int = Field(default=25, ge=1, le=25)
    facebook_video_sync_limit: int = Field(default=5, ge=1, le=5)
    facebook_post_sync_limit: int = Field(default=50, ge=1, le=200)
    facebook_import_max_video_bytes: int = Field(default=100 * 1024 * 1024, ge=1024 * 1024)
    face_identity_threshold: float = Field(default=0.5, ge=-1.0, le=1.0)
    face_min_quality: float = Field(default=0.3, ge=0.0, le=1.0)
    face_min_box_area: float = Field(default=0.005, ge=0.0, le=1.0)
    face_probe_max_faces: int = Field(default=8, ge=1, le=64)
    face_video_probe_frames: int = Field(default=8, ge=1, le=24)
    face_spoof_max_risk: float = Field(default=0.85, ge=0.0, le=1.0)
    face_max_attempts: int = Field(default=5, ge=1)
    face_lockout_minutes: int = Field(default=30, ge=1)

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
