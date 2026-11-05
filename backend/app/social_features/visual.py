"""Gallery-only image normalization, duplicate candidates and grounded boxes."""

from __future__ import annotations

import hashlib
import io
import math
import os

from PIL import Image, ImageOps

from app.geometry import overlap as overlap
from app.geometry import valid_box as valid_box
from app.providers.contracts import GALLERY_MIN_CONFIDENCE as MIN_CONFIDENCE

INDEX_VERSION = 2

# Background grounding may describe complex scenes; it gets a longer ceiling
# than interactive chat requests. Read per call so tests can override it.
DEFAULT_GROUNDING_TIMEOUT_SECONDS = 300.0


def clean_label(label: str) -> str:
    """Labels travel as comma-joined query values; commas would corrupt them."""

    return " ".join(str(label).replace(",", " ").split())


def grounding_timeout_seconds() -> float:
    raw = (os.environ.get("META_GROUNDING_TIMEOUT_SECONDS") or "").strip()
    try:
        return float(raw) if raw else DEFAULT_GROUNDING_TIMEOUT_SECONDS
    except ValueError:
        return DEFAULT_GROUNDING_TIMEOUT_SECONDS


def normalize(raw: bytes) -> tuple[bytes, int, int, str, str]:
    with Image.open(io.BytesIO(raw)) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")
        width, height = image.size
        small = image.resize((32, 32), Image.Resampling.LANCZOS)
        digest = hashlib.sha256(small.tobytes()).hexdigest()
        gray = image.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())
        bits = sum(
            (pixels[y * 9 + x] > pixels[y * 9 + x + 1]) << (y * 8 + x)
            for y in range(8)
            for x in range(8)
        )
        output = io.BytesIO()
        image.save(output, "JPEG", quality=95)
        return output.getvalue(), width, height, digest, f"{bits:016x}"


def similar(a: str, b: str) -> bool:
    return (int(a, 16) ^ int(b, 16)).bit_count() <= 10


def ground(client, raw: bytes) -> tuple[bytes, str, str, list[dict]]:
    image, width, height, digest, phash = normalize(raw)
    analysis = client.analyze_image(
        image,
        "image/jpeg",
        "Identify visible physical objects. Locate each instance precisely; ignore captions and do not guess hidden objects. Include object attributes in its label.",
        timeout=grounding_timeout_seconds(),
    )
    detections = []
    eligible = []
    for item in analysis.detections:
        box = valid_box(item.bounding_box)
        if box is not None and item.confidence >= MIN_CONFIDENCE:
            eligible.append(
                item.model_copy(update={"label": clean_label(item.label), "bounding_box": box})
            )
    localized = client.segment_gallery(image, width, height, eligible) if eligible else []
    if len(localized) != len(eligible):
        from app.providers.contracts import MetaProviderError

        raise MetaProviderError("Incomplete SAM object groups.", phase="sam_localization")
    for item, result in zip(eligible, localized):
        if result is None or (
            result.confidence is not None
            and (not math.isfinite(result.confidence) or result.confidence < MIN_CONFIDENCE)
        ):
            continue
        box = valid_box(result.bounding_box)
        if box is None or not any(result.mask):
            continue
        if any(d["label"] == item.label and overlap(d["box"], box) > 0.7 for d in detections):
            continue
        detections.append(
            dict(
                label=item.label,
                box=box,
                confidence=item.confidence,
                localization_confidence=result.confidence,
                model=result.model,
                simulated=result.simulated,
            )
        )
    return image, digest, phash, detections
