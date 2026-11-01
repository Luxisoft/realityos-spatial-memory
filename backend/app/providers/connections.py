"""Explicit per-request routes; credentials never cross destination boundaries."""

import logging
from dataclasses import dataclass

from app.providers.contracts import MetaProviderError

logger = logging.getLogger("realityos.providers")


@dataclass(frozen=True)
class ProviderRoute:
    name: str
    base_url: str
    headers: dict[str, str]

    def request_headers(self, extra=None):
        # Callers may supply Accept/Content-Type, never replace route credentials.
        safe = {
            key: value
            for key, value in (extra or {}).items()
            if key.lower() not in {"authorization", "x-realityos-gateway-token"}
        }
        return safe | self.headers


def gateway_route(settings):
    if not settings.meta_gateway_base_url or not settings.meta_gateway_token:
        raise MetaProviderError("META_GATEWAY_BASE_URL and META_GATEWAY_TOKEN are required.")
    return ProviderRoute(
        "gateway",
        str(settings.meta_gateway_base_url).rstrip("/"),
        {"X-RealityOS-Gateway-Token": settings.meta_gateway_token},
    )


def provider_routes(settings, *, speech=False):
    if settings.meta_connection_mode == "gateway":
        return (gateway_route(settings),)
    if speech:
        if not settings.tts_service_url or not settings.tts_service_token:
            raise MetaProviderError("TTS_SERVICE_URL and TTS_SERVICE_TOKEN are required.")
        direct = ProviderRoute(
            "direct",
            str(settings.tts_service_url),
            {"Authorization": f"Bearer {settings.tts_service_token}"},
        )
    else:
        if not settings.model_api_key:
            raise MetaProviderError("MODEL_API_KEY is required for a direct Meta connection.")
        direct = ProviderRoute(
            "direct",
            str(settings.meta_api_base_url).rstrip("/"),
            {"Authorization": f"Bearer {settings.model_api_key}"},
        )
    if settings.meta_gateway_fallback_enabled:
        return (direct, gateway_route(settings))
    return (direct,)


def fallback_status(status):
    return status in {401, 403, 404, 408, 429} or 500 <= status < 600


def fallback_log(route, reason):
    logger.warning("Provider fallback route=%s reason=%s", route.name, reason)


def upload_positions(kwargs):
    """Remember file offsets without buffering captured videos into memory."""
    files = kwargs.get("files") or {}
    entries = files.values() if isinstance(files, dict) else (value for _, value in files)
    positions = []
    for entry in entries:
        content = entry[1] if isinstance(entry, tuple) else entry
        if hasattr(content, "read"):
            try:
                positions.append((content, content.tell()))
            except (AttributeError, OSError):
                positions.append((content, None))
    return positions


def rewind_uploads(positions):
    for handle, offset in positions:
        if offset is None:
            raise MetaProviderError("Cannot safely replay a non-seekable upload.")
        try:
            handle.seek(offset)
        except (AttributeError, OSError) as error:
            raise MetaProviderError("Cannot safely replay an upload.") from error
