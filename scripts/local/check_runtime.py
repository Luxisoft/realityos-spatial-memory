"""Check real local providers without capturing or publishing sample evidence."""

import argparse
import asyncio
import json

from app.config import Settings
from app.local_runtime import validate_local_settings
from app.meta import LiveMetaModelClient
from app.providers.tts import synthesize
from app.tts_contracts import SpeechRequest, validate_wav


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--providers", action="store_true")
    parser.add_argument("--speech", action="store_true")
    args = parser.parse_args()
    settings = Settings()
    if settings.environment != "local":
        raise SystemExit("This diagnostic is restricted to ENVIRONMENT=local.")
    validate_local_settings(settings)
    models = LiveMetaModelClient(settings)._request("GET", "models").json()["data"]
    ids = {model["id"] for model in models}
    required = {"muse-spark-1.3", "sam-3.1", "muse-voice-transcribe-1.0"}
    if not required.issubset(ids):
        raise SystemExit(
            "The Meta key/network does not enable all required real models."
        )
    report = {"meta": "live", "models_available": sorted(required)}
    if args.providers:
        from app.faces import build_face_engine

        engine = build_face_engine(settings)
        if engine.simulated:
            raise SystemExit("A real face engine is required.")
        report["face_engine"] = engine.name
    report["speech_provider"] = "elevenlabs"
    if args.speech:
        for language, text in {
            "es": "La voz local está lista.",
            "en": "The local voice is ready.",
        }.items():
            raw = asyncio.run(
                synthesize(SpeechRequest(text=text, language=language), settings)
            )
            validate_wav(raw)
            report["speech_" + language] = "real WAV verified"
    print(json.dumps(report))


if __name__ == "__main__":
    main()
