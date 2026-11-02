"""Request-only speech synthesis; no local model or persistent audio cache."""

import asyncio
import io
import logging
import math
import time
import wave

import httpx

from app.tts_contracts import MAX_AUDIO_BYTES, SpeechRequest, validate_wav

logger = logging.getLogger("realityos.providers")
SAMPLE_RATE = 24000
MAX_PCM_BYTES = min(MAX_AUDIO_BYTES - 44, SAMPLE_RATE * 2 * 300)


class ElevenLabsUnavailable(Exception):
    pass


async def synthesize(payload: SpeechRequest, settings, transport=None) -> bytes:
    key = settings.elevenlabs_api_key
    if key is None or not key.get_secret_value().strip():
        raise ElevenLabsUnavailable("Speech provider is not configured.")
    started = time.monotonic()
    try:
        async with asyncio.timeout(settings.tts_timeout_seconds):
            async with httpx.AsyncClient(
                transport=transport,
                follow_redirects=False,
                timeout=settings.tts_timeout_seconds,
            ) as client:
                # Never replay a potentially accepted, billable generation.
                async with client.stream(
                    "POST",
                    "https://api.elevenlabs.io/v1/text-to-speech/" + settings.elevenlabs_voice_id,
                    params={"output_format": "pcm_24000"},
                    headers={"xi-api-key": key.get_secret_value()},
                    json={
                        "text": payload.text,
                        "language_code": payload.language,
                        "model_id": settings.elevenlabs_model_id,
                    },
                ) as response:
                    if response.status_code != 200:
                        logger.warning("Speech provider=elevenlabs status=%s", response.status_code)
                        raise ElevenLabsUnavailable("Speech provider is unavailable.")
                    content_type = response.headers.get("content-type", "").split(";", 1)[0]
                    if content_type not in {
                        "",
                        "audio/pcm",
                        "audio/x-pcm",
                        "application/octet-stream",
                    }:
                        raise ElevenLabsUnavailable("Invalid speech response.")
                    pcm = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(pcm) + len(chunk) > MAX_PCM_BYTES:
                            raise ElevenLabsUnavailable("Invalid speech response.")
                        pcm.extend(chunk)
                    if not pcm or len(pcm) % 2:
                        raise ElevenLabsUnavailable("Invalid speech response.")
                    output = io.BytesIO()
                    with wave.open(output, "wb") as audio:
                        audio.setparams((1, 2, SAMPLE_RATE, 0, "NONE", "not compressed"))
                        audio.writeframes(pcm)
                    raw = validate_wav(output.getvalue())
                    try:
                        cost = float(response.headers.get("character-cost", "nan"))
                    except ValueError:
                        cost = math.nan
                    logger.info(
                        "Speech provider=elevenlabs duration_ms=%d request_id=%s character_cost=%s",
                        (time.monotonic() - started) * 1000,
                        response.headers.get("request-id", "unknown")[:128],
                        cost if math.isfinite(cost) and cost >= 0 else "unknown",
                    )
                    return raw
    except (TimeoutError, httpx.HTTPError, ValueError) as error:
        raise ElevenLabsUnavailable("Speech generation is unavailable.") from error
