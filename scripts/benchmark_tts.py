"""Measure the real private service before enabling gateway traffic (no customer text)."""

import argparse
import json
import os
import time
import urllib.request

from app.tts_contracts import validate_wav


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://seamless-tts:8091/synthesize")
    args = parser.parse_args()
    token = os.environ["TTS_SERVICE_TOKEN"]
    samples = {
        "es": "Vi el taladro por última vez en la estantería del taller.",
        "en": "The drill was last seen on the shelf in the workshop.",
    }
    results = []
    for language, text in samples.items():
        for trial in range(3):
            started = time.monotonic()
            request = urllib.request.Request(
                args.url,
                data=json.dumps({"text": text, "language": language}).encode(),
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=15) as response:
                    audio = validate_wav(response.read(16 * 1024 * 1024 + 1))
                elapsed = time.monotonic() - started
                results.append(
                    {
                        "language": language,
                        "trial": trial,
                        "seconds": round(elapsed, 3),
                        "wav_bytes": len(audio),
                        "passed": elapsed < 15,
                    }
                )
            except (OSError, ValueError):
                results.append({"language": language, "trial": trial, "passed": False})
    passed = all(result["passed"] for result in results)
    print(json.dumps({"passed": passed, "samples": results}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
