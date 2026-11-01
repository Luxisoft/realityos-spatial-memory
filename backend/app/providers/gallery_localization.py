"""Concept fallback for an already visually confirmed instance, never a new claim."""

import asyncio

from meta_sam_parser import (
    SegmentationBoxRecord,
    SegmentationMaskRecord,
    decode_mask_to_raster,
    image_segmentation_format,
    parse_responses_stream,
)

from app.providers.contracts import MetaProviderError, SegmentationResult
from app.social_features.visual import MIN_CONFIDENCE, overlap, valid_box


def segment_confirmed_concept(client, image, width, height, label, expected_box):
    events = client._stream_events(
        {
            "model": "sam-3.1",
            "store": False,
            "stream": True,
            "metadata": {"mask_encoding": "one_bit", "include_confidence": "true"},
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": label},
                        {"type": "input_image", "image_url": client._data_url(image, "image/jpeg")},
                    ],
                }
            ],
        }
    )

    async def source():
        for event in events:
            yield event

    async def parse():
        return await parse_responses_stream(source(), image_segmentation_format()).final_result()

    try:
        result = asyncio.run(parse())
        boxes = {r.object_id: r for r in result.records if isinstance(r, SegmentationBoxRecord)}
        candidates = []
        for mask in (r for r in result.records if isinstance(r, SegmentationMaskRecord)):
            box = boxes.get(mask.object_id)
            if box is None:
                continue
            bounds = valid_box(
                {
                    "x": box.left / width,
                    "y": box.top / height,
                    "width": (box.right - box.left + 1) / width,
                    "height": (box.bottom - box.top + 1) / height,
                }
            )
            confidence = mask.confidence if mask.confidence is not None else box.confidence
            if bounds is None or confidence is None or not MIN_CONFIDENCE <= confidence <= 1:
                continue
            agreement = overlap(bounds, expected_box)
            if agreement < 0.5:
                continue
            raster = decode_mask_to_raster(mask.mask)
            if not any(raster):
                continue
            candidates.append(
                (
                    agreement,
                    confidence,
                    SegmentationResult(
                        model="sam-3.1",
                        simulated=False,
                        bounding_box=bounds,
                        confidence=confidence,
                        mask=raster,
                        mask_width=mask.mask.width,
                        mask_height=mask.mask.height,
                    ),
                )
            )
        return max(candidates, key=lambda row: row[:2])[2] if candidates else None
    except MetaProviderError:
        raise
    except Exception as error:
        raise MetaProviderError("Invalid confirmed-object segmentation.", phase="review") from error
