"""Localize confirmed prior objects without relaxing confidence or losing pixels."""

import io
import math
from dataclasses import replace

from PIL import Image

from app.providers.contracts import MetaProviderError
from app.social_features.visual import MIN_CONFIDENCE, valid_box


def usable_mask(mask):
    return bool(
        mask is not None
        and valid_box(mask.bounding_box)
        and any(mask.mask)
        and (
            mask.confidence is None
            or math.isfinite(mask.confidence)
            and MIN_CONFIDENCE <= mask.confidence <= 1
        )
    )


def detail_crop(box, width, height):
    return [
        max(0, math.floor((box["x"] - box["width"] * 0.5) * width)),
        max(0, math.floor((box["y"] - box["height"] * 0.5) * height)),
        min(width, math.ceil((box["x"] + box["width"] * 1.5) * width)),
        min(height, math.ceil((box["y"] + box["height"] * 1.5) * height)),
    ]


def cropped(image, box, crop, width, height):
    if crop is None:
        return image, width, height, box
    left, top, right, bottom = crop
    cw, ch = right - left, bottom - top
    if cw <= 0 or ch <= 0:
        raise ValueError("Invalid confirmed-object crop.")
    with Image.open(io.BytesIO(image)) as picture:
        output = io.BytesIO()
        picture.crop(crop).save(output, "JPEG", quality=95)
    local = valid_box(
        {
            "x": (box["x"] * width - left) / cw,
            "y": (box["y"] * height - top) / ch,
            "width": box["width"] * width / cw,
            "height": box["height"] * height / ch,
        }
    )
    return output.getvalue(), cw, ch, local


def localize(client, image, width, height, item, crop=None):
    box = item.bounding_box
    if box["width"] * box["height"] < 0.04:
        crop = detail_crop(box, width, height)
    raw, cw, ch, local_box = cropped(image, box, crop, width, height)
    if local_box is None:
        return None, "box"
    results = client.segment_gallery(
        raw, cw, ch, [item.model_copy(update={"bounding_box": local_box})]
    )
    if len(results) != 1:
        raise MetaProviderError("Incomplete reviewed localization.", phase="review")
    value = results[0]
    method = "box"
    if not usable_mask(value):
        # A different prompt on source detail can resolve weak box segmentation.
        # The provider must return a confident mask overlapping this same instance.
        crop = crop or detail_crop(box, width, height)
        raw, cw, ch, local_box = cropped(image, box, crop, width, height)
        value = (
            client.segment_gallery_concept(raw, cw, ch, item.label, local_box)
            if local_box
            else None
        )
        method = "concept"
    if value is not None and crop is not None:
        left, top, right, bottom = crop
        b = value.bounding_box
        value = replace(
            value,
            bounding_box={
                "x": (left + b["x"] * (right - left)) / width,
                "y": (top + b["y"] * (bottom - top)) / height,
                "width": b["width"] * (right - left) / width,
                "height": b["height"] * (bottom - top) / height,
            },
        )
    return value, method
