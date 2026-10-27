from __future__ import annotations

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    """Gateway-only runtime settings. Meta credentials never reach RealityOS."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    model_api_key: str = Field(min_length=12)
    meta_gateway_token: str = Field(min_length=24)
    meta_api_base_url: AnyHttpUrl = "https://api.meta.ai/v1"
    gateway_max_request_bytes: int = Field(default=1024 * 1024 * 1024, ge=1024, le=1024 * 1024 * 1024)
    gateway_timeout_seconds: float = Field(default=300, gt=0, le=900)
