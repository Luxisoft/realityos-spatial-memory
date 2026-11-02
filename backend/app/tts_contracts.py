"""Speech request and WAV response contract for RealityOS clients."""

import io
import wave
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_AUDIO_BYTES = 16 * 1024 * 1024


class SpeechRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=4000)
    language: Literal["es", "en"]

    @field_validator("text")
    @classmethod
    def nonblank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Speech text must not be blank.")
        return value.strip()


def validate_wav(raw: bytes) -> bytes:
    if not raw or len(raw) > MAX_AUDIO_BYTES:
        raise ValueError("Invalid audio size.")
    try:
        with wave.open(io.BytesIO(raw), "rb") as audio:
            frames = audio.getnframes()
            if (
                audio.getnchannels() != 1
                or audio.getsampwidth() != 2
                or audio.getframerate() not in {16000, 22050, 24000, 48000}
                or frames <= 0
                or frames / audio.getframerate() > 300
                or len(audio.readframes(frames)) != frames * 2
            ):
                raise ValueError("Invalid PCM audio.")
    except (wave.Error, EOFError) as error:
        raise ValueError("Invalid WAV audio.") from error
    return raw
