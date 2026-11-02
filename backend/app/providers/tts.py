"""Bounded, stateless TTS with direct execution and optional gateway fallback."""

import asyncio
import logging
import threading

import httpx

from app.config import Settings
from app.providers import elevenlabs
from app.providers.connections import fallback_log, fallback_status, provider_routes
from app.providers.contracts import MetaProviderError
from app.tts_contracts import MAX_AUDIO_BYTES, SpeechRequest, validate_wav

logger = logging.getLogger("realityos.providers")


class SpeechUnavailable(Exception):
    pass


_generation_slots = threading.BoundedSemaphore(2)


async def synthesize(payload: SpeechRequest, settings: Settings, transport=None) -> bytes:
    if settings.meta_mode != "live":
        raise SpeechUnavailable("Speech synthesis is unavailable in simulated mode.")
    if not _generation_slots.acquire(blocking=False):
        raise SpeechUnavailable("Speech generation is busy.")
    try:
        if settings.tts_provider == "elevenlabs":
            try:
                return await elevenlabs.synthesize(payload, settings, transport)
            except elevenlabs.ElevenLabsUnavailable as error:
                raise SpeechUnavailable(str(error)) from error
        return await _seamless_synthesize(payload, settings, transport)
    finally:
        _generation_slots.release()


async def _seamless_synthesize(payload: SpeechRequest, settings: Settings, transport=None) -> bytes:
    if settings.meta_mode != "live":
        raise SpeechUnavailable("Speech synthesis is unavailable in simulated mode.")
    try:
        routes = provider_routes(settings, speech=True)
    except MetaProviderError as error:
        raise SpeechUnavailable("Speech connection is unavailable.") from error
    route_index = 0
    try:
        async with asyncio.timeout(settings.tts_timeout_seconds):
            async with httpx.AsyncClient(
                transport=transport,
                follow_redirects=False,
                timeout=httpx.Timeout(settings.tts_timeout_seconds / 2),
            ) as client:
                for attempt in range(2):
                    route = routes[route_index]
                    fallback = route_index + 1 < len(routes)
                    url = (
                        f"{route.base_url}/tts/synthesize"
                        if route.name == "gateway"
                        else route.base_url
                    )
                    logger.info("Speech request route=%s", route.name)
                    try:
                        async with client.stream(
                            "POST",
                            url,
                            json=payload.model_dump(),
                            headers=route.headers,
                        ) as response:
                            if response.status_code != 200:
                                if fallback and fallback_status(response.status_code):
                                    fallback_log(route, response.status_code)
                                    route_index += 1
                                    continue
                                if response.status_code in {408, 429, 500, 502, 503, 504}:
                                    raise httpx.ConnectError("Speech temporarily unavailable.")
                                raise SpeechUnavailable("Speech synthesis is unavailable.")
                            raw = bytearray()
                            async for chunk in response.aiter_bytes():
                                raw.extend(chunk)
                                if len(raw) > MAX_AUDIO_BYTES:
                                    raise SpeechUnavailable("Invalid speech response.")
                            try:
                                return validate_wav(bytes(raw))
                            except ValueError as error:
                                raise SpeechUnavailable("Invalid speech response.") from error
                    except (httpx.TimeoutException, httpx.NetworkError, httpx.RemoteProtocolError):
                        if attempt:
                            raise SpeechUnavailable("Speech service did not respond.") from None
                        if fallback:
                            fallback_log(route, "connection")
                            route_index += 1
                        else:
                            await asyncio.sleep(0.5)
    except TimeoutError as error:
        raise SpeechUnavailable("Speech generation timed out.") from error
    except httpx.HTTPError as error:
        raise SpeechUnavailable("Speech service is unavailable.") from error
    raise SpeechUnavailable("Speech synthesis is unavailable.")
