"""Bounded, request-only ElevenLabs synthesis."""

import threading

from app.config import Settings
from app.providers import elevenlabs
from app.tts_contracts import SpeechRequest


class SpeechUnavailable(Exception):
    pass


_generation_slots = threading.BoundedSemaphore(2)


async def synthesize(payload: SpeechRequest, settings: Settings, transport=None) -> bytes:
    if settings.meta_mode != "live":
        raise SpeechUnavailable("Speech synthesis is unavailable in simulated mode.")
    if not _generation_slots.acquire(blocking=False):
        raise SpeechUnavailable("Speech generation is busy.")
    try:
        return await elevenlabs.synthesize(payload, settings, transport)
    except elevenlabs.ElevenLabsUnavailable as error:
        raise SpeechUnavailable(str(error)) from error
    finally:
        _generation_slots.release()
