from __future__ import annotations

from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Secrets are read from the environment only."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "development"
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
    meta_max_retries: int = Field(default=2, ge=0, le=5)
    sam_min_confidence: float = Field(default=0.65, ge=0, le=1)
    enqueue_processing: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [value.strip() for value in self.cors_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
