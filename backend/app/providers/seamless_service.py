"""Private Seamless runtime. Heavy model dependencies belong only in its image."""

import hmac
import io
import os
import re
import threading
import time
import wave
from contextlib import asynccontextmanager

import anyio
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.tts_contracts import SpeechRequest, validate_wav

MODEL_ID = "facebook/seamless-m4t-v2-large"
MODEL_REVISION = "5f8cc790b19fc3f67a61c105133b20b34e3dcb76"
LANGUAGES = {"en": "eng", "es": "spa"}


def speech_chunks(text: str) -> list[str]:
    """Keep phrase boundaries and bound each input without dropping any words."""
    chunks: list[str] = []
    for phrase in re.split(r"(?<=[.!?;\n])\s+", text.strip()):
        current = ""
        for word in phrase.split():
            if len(word) > 240:
                raise ValueError("Speech contains an oversized word.")
            if current and len(current) + len(word) + 1 > 240:
                chunks.append(current)
                current = ""
            current = f"{current} {word}".strip()
        if current:
            chunks.append(current)
    return chunks


class SeamlessEngine:
    def __init__(self):
        import torch
        from transformers import AutoProcessor, SeamlessM4Tv2ForTextToSpeech

        self.torch = torch
        torch.set_num_threads(int(os.environ.get("TTS_CPU_THREADS", "2")))
        self.processor = AutoProcessor.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
        self.model = SeamlessM4Tv2ForTextToSpeech.from_pretrained(
            MODEL_ID,
            revision=MODEL_REVISION,
            use_safetensors=True,
            low_cpu_mem_usage=True,
        ).eval()
        self.rate = self.model.config.sampling_rate

    def synthesize(self, payload: SpeechRequest) -> bytes:
        import numpy as np

        deadline = time.monotonic() + 13
        samples = []
        language = LANGUAGES[payload.language]
        with self.torch.inference_mode():
            for chunk in speech_chunks(payload.text):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Speech generation timed out.")
                inputs = self.processor(text=chunk, src_lang=language, return_tensors="pt")
                output = self.model.generate(
                    **inputs,
                    tgt_lang=language,
                    speaker_id=0,
                    text_do_sample=False,
                    speech_do_sample=False,
                    text_max_new_tokens=256,
                    text_max_time=remaining,
                )
                if time.monotonic() > deadline:
                    raise TimeoutError("Speech generation timed out.")
                waveform = output[0].detach().cpu().float().numpy().reshape(-1)
                if not waveform.size or not np.isfinite(waveform).all():
                    raise ValueError("Invalid generated audio.")
                samples.append(waveform)
                samples.append(np.zeros(int(self.rate * 0.12), dtype=np.float32))
        pcm = (np.clip(np.concatenate(samples), -1, 1) * 32767).astype("<i2")
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as audio:
            audio.setnchannels(1)
            audio.setsampwidth(2)
            audio.setframerate(self.rate)
            audio.writeframes(pcm.tobytes())
        return validate_wav(buffer.getvalue())


def create_app(engine_factory=SeamlessEngine, token: str | None = None) -> FastAPI:
    secret = token or os.environ.get("TTS_SERVICE_TOKEN", "")
    if len(secret) < 24:
        raise ValueError("Set a private TTS_SERVICE_TOKEN of at least 24 characters.")
    lock = threading.Lock()

    @asynccontextmanager
    async def lifespan(app):
        app.state.engine = await anyio.to_thread.run_sync(engine_factory)
        yield
        app.state.engine = None

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.engine = None
    bearer = HTTPBearer(auto_error=False)

    def authorize(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
        if credentials is None or not hmac.compare_digest(credentials.credentials, secret):
            raise HTTPException(401, "Invalid speech service token.")

    @app.get("/health/ready")
    def ready():
        if app.state.engine is None:
            raise HTTPException(503, "Speech model is not loaded.")
        return {"status": "ready", "model": MODEL_ID, "revision": MODEL_REVISION}

    @app.post("/synthesize", dependencies=[Depends(authorize)])
    def synthesize(payload: SpeechRequest):
        if app.state.engine is None:
            raise HTTPException(503, "Speech model is not loaded.")
        if not lock.acquire(blocking=False):
            raise HTTPException(429, "Speech generation is busy.")
        try:
            raw = validate_wav(app.state.engine.synthesize(payload))
        except TimeoutError as error:
            raise HTTPException(504, "Speech generation timed out.") from error
        except ValueError as error:
            raise HTTPException(422, "Speech could not be generated.") from error
        except Exception as error:
            raise HTTPException(503, "Speech model is unavailable.") from error
        finally:
            lock.release()
        return Response(raw, media_type="audio/wav", headers={"Cache-Control": "no-store"})

    return app


def app_factory():
    return create_app()
