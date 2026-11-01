"""Bounded, stateless TTS egress. Only the backend retries synthesis."""

import asyncio

import httpx

from app.config import Settings
from app.tts_contracts import MAX_AUDIO_BYTES, SpeechRequest, validate_wav


class SpeechUnavailable(Exception):
    pass


async def synthesize(payload: SpeechRequest, settings: Settings, transport=None) -> bytes:
    if settings.meta_mode != "live":
        raise SpeechUnavailable("Speech synthesis is unavailable in simulated mode.")
    if not settings.meta_gateway_base_url or not settings.meta_gateway_token:
        raise SpeechUnavailable("Speech gateway is unavailable.")
    url = f"{str(settings.meta_gateway_base_url).rstrip('/')}/tts/synthesize"
    try:
        async with asyncio.timeout(settings.tts_timeout_seconds):
            async with httpx.AsyncClient(
                transport=transport,
                follow_redirects=False,
                timeout=httpx.Timeout(settings.tts_timeout_seconds / 2),
            ) as client:
                for attempt in range(2):
                    try:
                        async with client.stream(
                            "POST",
                            url,
                            json=payload.model_dump(),
                            headers={"X-RealityOS-Gateway-Token": settings.meta_gateway_token},
                        ) as response:
                            if response.status_code in {429, 502, 503, 504}:
                                raise httpx.ConnectError("Speech temporarily unavailable.")
                            if response.status_code != 200:
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
                    except (httpx.TimeoutException, httpx.NetworkError):
                        if attempt:
                            raise SpeechUnavailable("Speech gateway did not respond.") from None
                        await asyncio.sleep(0.5)
    except TimeoutError as error:
        raise SpeechUnavailable("Speech generation timed out.") from error
    except httpx.HTTPError as error:
        raise SpeechUnavailable("Speech gateway is unavailable.") from error
    raise SpeechUnavailable("Speech synthesis is unavailable.")
