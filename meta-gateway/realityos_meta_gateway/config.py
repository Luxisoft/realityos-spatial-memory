from __future__ import annotations

import os
from pathlib import Path

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    """Gateway-only runtime settings. Gateway credentials stay in server-side runtime files."""

    model_config = SettingsConfigDict(env_file=None, env_file_encoding="utf-8", extra="ignore")

    model_api_key: str = Field(min_length=12)
    meta_gateway_token: str = Field(min_length=24)
    meta_api_base_url: AnyHttpUrl = "https://api.meta.ai/v1"
    gateway_max_request_bytes: int = Field(
        default=1024 * 1024 * 1024, ge=1024, le=1024 * 1024 * 1024
    )
    gateway_timeout_seconds: float = Field(default=300, gt=0, le=900)


def get_settings() -> GatewaySettings:
    """Use injected variables or an explicitly selected gateway file only."""
    selected_file = os.getenv("META_GATEWAY_ENV_FILE") or None
    if selected_file is not None and not Path(selected_file).is_file():
        raise FileNotFoundError("The explicitly selected META_GATEWAY_ENV_FILE does not exist.")
    return GatewaySettings(_env_file=selected_file)
