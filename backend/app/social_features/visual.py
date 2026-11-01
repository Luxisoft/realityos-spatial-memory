"""Gallery-only image normalization, duplicate candidates and grounded boxes."""

from __future__ import annotations

import hashlib
import io
import math
import os

from PIL import Image, ImageOps

MIN_CONFIDENCE = float(os.environ.get("GALLERY_MIN_CONFIDENCE", "0.65"))
INDEX_VERSION = 2


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


def valid_box(box) -> dict | None:
    try:
        x, y, w, h = (float(box[k]) for k in ("x", "y", "width", "height"))
        if not all(math.isfinite(v) for v in (x, y, w, h)) or w <= 0 or h <= 0:
            return None
        left, top, right, bottom = max(0.0, x), max(0.0, y), min(1.0, x + w), min(1.0, y + h)
        if right <= left or bottom <= top:
            return None
        return dict(x=left, y=top, width=right - left, height=bottom - top)
    except (KeyError, TypeError, ValueError):
        return None


def ground(client, raw: bytes) -> tuple[bytes, str, str, list[dict]]:
    image, width, height, digest, phash = normalize(raw)
    analysis = client.analyze_image(
        image,
        "image/jpeg",
        "Identify visible physical objects. Locate each instance precisely; ignore captions and do not guess hidden objects. Include object attributes in its label.",
    )
    detections = []
    eligible = []
    for item in analysis.detections:
        box = valid_box(item.bounding_box)
        if box is not None and item.confidence >= MIN_CONFIDENCE:
            eligible.append(item.model_copy(update={"bounding_box": box}))
    localized = client.segment_gallery(image, width, height, eligible) if eligible else []
    if len(localized) != len(eligible):
        from app.meta import MetaProviderError

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


def overlap(a, b):
    area = max(0, min(a["x"] + a["width"], b["x"] + b["width"]) - max(a["x"], b["x"])) * max(
        0, min(a["y"] + a["height"], b["y"] + b["height"]) - max(a["y"], b["y"])
    )
    return area / (a["width"] * a["height"] + b["width"] * b["height"] - area) if area else 0.0
