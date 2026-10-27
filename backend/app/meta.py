from __future__ import annotations

import asyncio
import base64
import json
import math
import time
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from meta_sam_parser import (
    FramePrompt,
    PromptBox,
    PromptObject,
    SegmentationBoxRecord,
    SegmentationMaskRecord,
    build_object_prompt,
    decode_mask_to_raster,
    image_segmentation_format,
    parse_responses_stream,
    video_segmentation_format,
)

from app.config import Settings
from app.schemas import ImageAnalysis, MetaDetection, MetaFact, QueryInterpretation


class MetaProviderError(RuntimeError):
    """Safe error raised when Meta cannot provide an inference."""


class MetaProviderUncertainError(MetaProviderError):
    """A provider request may have run, but the final result cannot be trusted."""


@dataclass(frozen=True)
class Transcription:
    text: str
    simulated: bool


@dataclass(frozen=True)
class SegmentationResult:
    """One exact SAM geometry and its decoded binary raster."""

    model: str
    simulated: bool
    bounding_box: dict[str, float]
    confidence: float | None
    mask: bytes
    mask_width: int
    mask_height: int


@dataclass(frozen=True)
class VideoTrackPrompt:
    object_id: str
    frame_index: int
    bounding_box: dict[str, float]


@dataclass(frozen=True)
class VideoTrackFrame:
    object_id: str
    frame_index: int
    bounding_box: dict[str, float] | None
    mask_rle: bytes | None
    mask_width: int | None
    mask_height: int | None
    confidence: float | None


@dataclass(frozen=True)
class VideoTrackingResult:
    model: str
    simulated: bool
    provider_file_id: str | None
    frames: list[VideoTrackFrame]


class MetaModelClient(ABC):
    @abstractmethod
    def analyze_image(self, image: bytes, mime_type: str, context: str = "") -> ImageAnalysis: ...

    @abstractmethod
    def segment(
        self,
        image: bytes,
        mime_type: str,
        prompt: str,
        *,
        width: int,
        height: int,
        bounding_box: dict[str, float],
    ) -> SegmentationResult | None: ...

    @abstractmethod
    def track_video(
        self,
        video_path: Path,
        *,
        width: int,
        height: int,
        frame_count: int,
        prompts: list[VideoTrackPrompt],
    ) -> VideoTrackingResult: ...

    @abstractmethod
    def transcribe_wav(self, audio: bytes) -> Transcription: ...

    @abstractmethod
    def interpret_query(self, question: str, known_terms: list[str]) -> QueryInterpretation: ...


class MockMetaModelClient(MetaModelClient):
    """Deterministic local fixtures; deliberately makes no network request."""

    def analyze_image(self, image: bytes, mime_type: str, context: str = "") -> ImageAnalysis:
        hint = context.casefold()
        catalog = [
            ("yellow drill", "power tool", 0.96),
            ("hammer", "hand tool", 0.91),
            ("adjustable wrench", "hand tool", 0.89),
            ("screwdriver", "hand tool", 0.88),
            ("toolbox", "container", 0.84),
            ("battery charger", "equipment", 0.82),
        ]
        label, category, confidence = next(
            (row for row in catalog if row[0].split()[0] in hint),
            catalog[0],
        )
        return ImageAnalysis(
            model="mock-muse-spark-1.3",
            simulated=True,
            detections=[
                MetaDetection(
                    label=label,
                    category=category,
                    confidence=confidence,
                    bounding_box={"x": 0.18, "y": 0.22, "width": 0.57, "height": 0.49},
                    spatial_description=f"Simulated: {label}, on a black box.",
                    relationships=[{"relation": "on", "object": "black box"}],
                    facts=[
                        MetaFact(
                            fact_type="brand",
                            value_text="RealityOS Workshop",
                            normalized_value="realityos workshop",
                            confidence=0.93,
                            provenance="visible_text",
                        ),
                        MetaFact(
                            fact_type="condition",
                            value_text="used",
                            normalized_value="used",
                            confidence=0.78,
                        ),
                        MetaFact(
                            fact_type="usage_state",
                            value_text="stored",
                            normalized_value="stored",
                            confidence=0.82,
                        ),
                        MetaFact(
                            fact_type="visible_count",
                            numeric_value=1,
                            unit="item",
                            confidence=0.96,
                        ),
                    ],
                )
            ],
        )

    def segment(
        self,
        image: bytes,
        mime_type: str,
        prompt: str,
        *,
        width: int,
        height: int,
        bounding_box: dict[str, float],
    ) -> SegmentationResult | None:
        """Deterministic local mask; it is visibly marked simulated downstream."""

        x = max(0, min(width - 1, int(float(bounding_box["x"]) * width)))
        y = max(0, min(height - 1, int(float(bounding_box["y"]) * height)))
        right = max(x + 1, min(width, math.ceil((float(bounding_box["x"]) + float(bounding_box["width"])) * width)))
        bottom = max(y + 1, min(height, math.ceil((float(bounding_box["y"]) + float(bounding_box["height"])) * height)))
        pixels = bytearray(width * height)
        for row in range(y, bottom):
            pixels[row * width + x : row * width + right] = b"\x01" * (right - x)
        return SegmentationResult(
            model="mock-sam-3.1",
            simulated=True,
            bounding_box={
                "x": x / width,
                "y": y / height,
                "width": (right - x) / width,
                "height": (bottom - y) / height,
            },
            confidence=0.94,
            mask=bytes(pixels),
            mask_width=width,
            mask_height=height,
        )

    def track_video(
        self,
        video_path: Path,
        *,
        width: int,
        height: int,
        frame_count: int,
        prompts: list[VideoTrackPrompt],
    ) -> VideoTrackingResult:
        """Deterministic local propagation for detailed-mode tests; makes no network calls."""

        frames: list[VideoTrackFrame] = []
        for prompt in prompts:
            for frame_index in range(max(0, frame_count)):
                frames.append(
                    VideoTrackFrame(
                        object_id=prompt.object_id,
                        frame_index=frame_index,
                        bounding_box=prompt.bounding_box,
                        mask_rle=_rectangle_rle(width, height, prompt.bounding_box),
                        mask_width=width,
                        mask_height=height,
                        confidence=0.94,
                    )
                )
        return VideoTrackingResult(
            model="mock-sam-3.1",
            simulated=True,
            provider_file_id=None,
            frames=frames,
        )

    def transcribe_wav(self, audio: bytes) -> Transcription:
        return Transcription(text="Where is the yellow drill?", simulated=True)

    def interpret_query(self, question: str, known_terms: list[str]) -> QueryInterpretation:
        """Deterministic multilingual fixture; it never calls a model or network."""

        normalized = question.casefold()
        known = {term.casefold(): term for term in known_terms}
        for key, original in known.items():
            if key in normalized:
                return QueryInterpretation(terms=[original], simulated=True)
        fixture_terms = {
            "yellow drill": [
                "yellow drill",
                "taladro amarillo",
                "perceuse jaune",
                "gelber bohrer",
                "黄色电钻",
            ],
            "hammer": ["hammer", "martillo", "marteau", "hammer"],
            "adjustable wrench": ["adjustable wrench", "llave inglesa", "clé à molette"],
            "screwdriver": ["screwdriver", "destornillador", "tournevis"],
        }
        for canonical, variants in fixture_terms.items():
            if canonical in known and any(variant in normalized for variant in variants):
                return QueryInterpretation(terms=[known[canonical]], simulated=True)
        return QueryInterpretation(simulated=True)


class LiveMetaModelClient(MetaModelClient):
    """Meta Model API implementation based on Responses and Voice API contracts."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        if settings.meta_gateway_base_url:
            if not settings.meta_gateway_token:
                raise MetaProviderError(
                    "META_GATEWAY_TOKEN is required when META_GATEWAY_BASE_URL is configured."
                )
            self.base_url = str(settings.meta_gateway_base_url).rstrip("/")
            self.headers = {"X-RealityOS-Gateway-Token": settings.meta_gateway_token}
        else:
            if not settings.model_api_key:
                raise MetaProviderError("MODEL_API_KEY is required when META_MODE=live without a gateway.")
            self.base_url = str(settings.meta_api_base_url).rstrip("/")
            self.headers = {"Authorization": f"Bearer {settings.model_api_key}"}

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        url = f"{self.base_url}/{path.lstrip('/')}"
        last_error: Exception | None = None
        for attempt in range(self.settings.meta_max_retries + 1):
            try:
                response = httpx.request(
                    method,
                    url,
                    headers=self.headers | kwargs.pop("headers", {}),
                    timeout=self.settings.meta_timeout_seconds,
                    **kwargs,
                )
                if response.status_code not in {408, 429, 500, 502, 503, 504}:
                    response.raise_for_status()
                    return response
                last_error = MetaProviderError(
                    f"Meta Model API returned {response.status_code}: {self._safe_error(response)}"
                )
            except (httpx.HTTPError, MetaProviderError) as exc:
                last_error = exc
            if attempt < self.settings.meta_max_retries:
                time.sleep(0.35 * (2**attempt))
        raise MetaProviderError(f"Meta Model API unavailable: {last_error}") from last_error

    @staticmethod
    def _safe_error(response: httpx.Response) -> str:
        try:
            error = response.json().get("error", {})
            return str(error.get("message") or error.get("type") or "request failed")
        except ValueError:
            return "request failed"

    @staticmethod
    def _output_text(payload: dict[str, Any]) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str):
            return direct
        parts: list[str] = []
        for output in payload.get("output", []):
            for content in output.get("content", []):
                if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                    parts.append(content["text"])
        if not parts:
            raise MetaProviderError("Meta response did not include output_text.")
        return "".join(parts)

    @staticmethod
    def _data_url(image: bytes, mime_type: str) -> str:
        return f"data:{mime_type};base64,{base64.b64encode(image).decode('ascii')}"

    def analyze_image(self, image: bytes, mime_type: str, context: str = "") -> ImageAnalysis:
        instruction = (
            "Inspect this workspace image. Return only JSON with a detections array. "
            "Every human-readable detection field (label, category, spatial_description, "
            "relationship and related object) must use English, except "
            "for a visible brand, model, technical acronym, or exact visible text. Each detection needs label, "
            "optional category, confidence from 0 to 1, bounding_box {x,y,width,height} "
            "normalized 0..1, spatial_description, and optional relationships as objects "
            "with relation and object keys. Include optional facts only when supported by the image: "
            "brand, manufacturer, model, product_line, visible_text, color, condition, usage_state, "
            "packaging, or visible_count. A fact has fact_type, value_text or numeric_value, optional "
            "normalized_value and unit, confidence, and provenance (visible_text, visual, temporal). "
            "Use visible_text for brands/models/text only when text is legible; never guess a brand or model. "
            "Use usage_state only for directly observed state such as stored, charging, carried, or in_use; "
            "omit unknown facts. Do not claim locations or intended use that cannot be seen."
        )
        body = {
            "model": "muse-spark-1.3",
            "store": False,
            "instructions": instruction,
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": context or "Identify visible objects."},
                        {"type": "input_image", "image_url": self._data_url(image, mime_type)},
                    ],
                }
            ],
        }
        payload = self._request("POST", "responses", json=body).json()
        try:
            decoded = json.loads(self._output_text(payload))
            detections = [MetaDetection.model_validate(item) for item in decoded["detections"]]
        except (KeyError, ValueError, TypeError) as exc:
            raise MetaProviderError("Muse Spark returned an invalid structured analysis.") from exc
        return ImageAnalysis(model="muse-spark-1.3", simulated=False, detections=detections)

    def interpret_query(self, question: str, known_terms: list[str]) -> QueryInterpretation:
        """Map a question in any language to terms already authorized in its workspace."""

        if not known_terms:
            return QueryInterpretation()
        prompt = (
            "You are a multilingual object-query interpreter. The user may write in any "
            "language or transliteration. Match the requested physical object only against "
            "the known workspace terms below. Return only JSON shaped as {\"terms\":[...]} "
            "with zero, one, or several exact strings copied from known_terms. Return an "
            "empty list when there is no confident match or when the request is ambiguous. "
            "Never create terms, locations, evidence, or an answer.\n\n"
            f"known_terms={json.dumps(known_terms, ensure_ascii=False)}\n"
            f"user_question={question}"
        )
        payload = self._request(
            "POST",
            "responses",
            json={"model": "muse-spark-1.3", "store": False, "input": prompt},
        ).json()
        try:
            decoded = QueryInterpretation.model_validate(json.loads(self._output_text(payload)))
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MetaProviderError("Muse Spark returned an invalid query interpretation.") from exc
        allowed = {term.casefold(): term for term in known_terms}
        return QueryInterpretation(
            terms=list(
                dict.fromkeys(
                    allowed[term.casefold()]
                    for term in decoded.terms
                    if term.casefold() in allowed
                )
            )
        )

    def _stream_events(self, body: dict[str, Any]) -> list[dict[str, Any]]:
        """Read a Responses SSE stream with the same retry policy as JSON calls."""

        url = f"{self.base_url}/responses"
        last_error: Exception | None = None
        for attempt in range(self.settings.meta_max_retries + 1):
            try:
                with httpx.stream(
                    "POST",
                    url,
                    headers=self.headers | {"Accept": "text/event-stream"},
                    timeout=self.settings.meta_timeout_seconds,
                    json=body,
                ) as response:
                    if response.status_code in {408, 429, 500, 502, 503, 504}:
                        response.read()
                        last_error = MetaProviderError(
                            f"Meta Model API returned {response.status_code}: {self._safe_error(response)}"
                        )
                    else:
                        response.raise_for_status()
                        events: list[dict[str, Any]] = []
                        for line in response.iter_lines():
                            if not line or not line.startswith("data: "):
                                continue
                            data = line.removeprefix("data: ")
                            if data == "[DONE]":
                                continue
                            try:
                                event = json.loads(data)
                            except json.JSONDecodeError as exc:
                                raise MetaProviderError("Meta SAM stream contained invalid JSON.") from exc
                            if isinstance(event, dict):
                                events.append(event)
                        return events
            except (httpx.HTTPError, MetaProviderError) as exc:
                last_error = exc
            if attempt < self.settings.meta_max_retries:
                time.sleep(0.35 * (2**attempt))
        raise MetaProviderError(f"Meta Model API unavailable: {last_error}") from last_error

    @staticmethod
    def _sam_result_from_events(
        events: list[dict[str, Any]], width: int, height: int
    ) -> SegmentationResult | None:
        async def source():
            for event in events:
                yield event

        try:
            parsed = parse_responses_stream(source(), image_segmentation_format())
            result = asyncio.run(parsed.final_result())
        except Exception as exc:
            raise MetaProviderError("Meta SAM returned an invalid segmentation stream.") from exc
        boxes = {
            record.object_id: record
            for record in result.records
            if isinstance(record, SegmentationBoxRecord)
        }
        masks = [record for record in result.records if isinstance(record, SegmentationMaskRecord)]
        for mask_record in masks:
            box = boxes.get(mask_record.object_id)
            if box is None:
                continue
            try:
                raster = decode_mask_to_raster(mask_record.mask)
            except Exception as exc:
                raise MetaProviderError("Meta SAM returned an unreadable mask.") from exc
            return SegmentationResult(
                model="sam-3.1",
                simulated=False,
                bounding_box={
                    "x": max(0.0, min(1.0, box.left / width)),
                    "y": max(0.0, min(1.0, box.top / height)),
                    "width": max(0.0, min(1.0, (box.right - box.left) / width)),
                    "height": max(0.0, min(1.0, (box.bottom - box.top) / height)),
                },
                confidence=mask_record.confidence if mask_record.confidence is not None else box.confidence,
                mask=raster,
                mask_width=mask_record.mask.width,
                mask_height=mask_record.mask.height,
            )
        return None

    def segment(
        self,
        image: bytes,
        mime_type: str,
        prompt: str,
        *,
        width: int,
        height: int,
        bounding_box: dict[str, float],
    ) -> SegmentationResult | None:
        """Refine Muse's known instance box into a compact SAM one-bit mask."""

        left = max(0, min(width - 1, int(float(bounding_box["x"]) * width)))
        top = max(0, min(height - 1, int(float(bounding_box["y"]) * height)))
        right = max(left + 1, min(width, math.ceil((float(bounding_box["x"]) + float(bounding_box["width"])) * width)))
        bottom = max(top + 1, min(height, math.ceil((float(bounding_box["y"]) + float(bounding_box["height"])) * height)))
        object_prompt = build_object_prompt(
            size=(width, height),
            objects=[
                PromptObject(
                    id=1,
                    prompts=[FramePrompt(box=PromptBox(left=left, top=top, right=right, bottom=bottom))],
                )
            ],
        )
        body = {
            "model": "sam-3.1",
            "store": False,
            "stream": True,
            "metadata": {"mask_encoding": "one_bit", "include_confidence": "true"},
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": object_prompt},
                        {"type": "input_image", "image_url": self._data_url(image, mime_type)},
                    ],
                }
            ],
        }
        return self._sam_result_from_events(self._stream_events(body), width, height)

    def _file_request_once(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Never replay submitted video/file requests: a second call can be billable."""

        try:
            response = httpx.request(
                method,
                f"{self.base_url}/{path.lstrip('/')}",
                headers=self.headers | kwargs.pop("headers", {}),
                timeout=self.settings.meta_video_timeout_seconds,
                **kwargs,
            )
        except httpx.HTTPError as exc:
            raise MetaProviderUncertainError("Meta video request connection failed.") from exc
        if response.status_code in {408, 429, 500, 502, 503, 504}:
            raise MetaProviderUncertainError(
                f"Meta video request returned {response.status_code}; result state is uncertain."
            )
        try:
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise MetaProviderError(
                f"Meta Model API returned {response.status_code}: {self._safe_error(response)}"
            ) from exc
        return response

    def _stream_events_once(self, body: dict[str, Any]) -> list[dict[str, Any]]:
        """Read one SAM Video stream without retrying it after any accepted request."""

        try:
            with httpx.stream(
                "POST",
                f"{self.base_url}/responses",
                headers=self.headers | {"Accept": "text/event-stream"},
                timeout=self.settings.meta_video_timeout_seconds,
                json=body,
            ) as response:
                if response.status_code in {408, 429, 500, 502, 503, 504}:
                    response.read()
                    raise MetaProviderUncertainError(
                        f"Meta SAM Video returned {response.status_code}; result state is uncertain."
                    )
                if response.status_code >= 400:
                    response.read()
                    raise MetaProviderError(
                        f"Meta Model API returned {response.status_code}: {self._safe_error(response)}"
                    )
                events: list[dict[str, Any]] = []
                for line in response.iter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line.removeprefix("data: ")
                    if data != "[DONE]":
                        event = json.loads(data)
                        if isinstance(event, dict):
                            events.append(event)
                return events
        except MetaProviderError:
            raise
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            raise MetaProviderUncertainError("Meta SAM Video stream ended without a trusted result.") from exc

    @staticmethod
    def _video_result_from_events(
        events: list[dict[str, Any]], width: int, height: int, provider_file_id: str
    ) -> VideoTrackingResult:
        async def source():
            for event in events:
                yield event

        try:
            parsed = parse_responses_stream(source(), video_segmentation_format())
            result = asyncio.run(parsed.final_result())
        except Exception as exc:
            raise MetaProviderUncertainError("Meta SAM Video returned an invalid stream.") from exc
        boxes: dict[tuple[str, int], SegmentationBoxRecord] = {
            (record.object_id, record.frame.frame_index): record
            for record in result.records
            if isinstance(record, SegmentationBoxRecord) and record.frame is not None
        }
        frames: list[VideoTrackFrame] = []
        for record in result.records:
            if not isinstance(record, SegmentationMaskRecord):
                continue
            frame_index = record.frame.frame_index if record.frame else record.identity.frame_index
            if frame_index is None:
                continue
            box = boxes.get((record.object_id, frame_index))
            if box is None:
                continue
            try:
                raster = decode_mask_to_raster(record.mask)
            except Exception as exc:
                raise MetaProviderUncertainError("Meta SAM Video returned an unreadable mask.") from exc
            frames.append(
                VideoTrackFrame(
                    object_id=record.object_id,
                    frame_index=frame_index,
                    bounding_box={
                        "x": max(0.0, min(1.0, box.left / width)),
                        "y": max(0.0, min(1.0, box.top / height)),
                        "width": max(0.0, min(1.0, (box.right - box.left) / width)),
                        "height": max(0.0, min(1.0, (box.bottom - box.top) / height)),
                    },
                    mask_rle=_raster_rle(raster),
                    mask_width=record.mask.width,
                    mask_height=record.mask.height,
                    confidence=record.confidence if record.confidence is not None else box.confidence,
                )
            )
        return VideoTrackingResult("sam-3.1", False, provider_file_id, frames)

    def track_video(
        self,
        video_path: Path,
        *,
        width: int,
        height: int,
        frame_count: int,
        prompts: list[VideoTrackPrompt],
    ) -> VideoTrackingResult:
        if not prompts:
            return VideoTrackingResult("sam-3.1", False, None, [])
        file_id: str | None = None
        try:
            with video_path.open("rb") as handle:
                uploaded = self._file_request_once(
                    "POST",
                    "files",
                    data={
                        "purpose": "user_data",
                        "expires_after[anchor]": "created_at",
                        "expires_after[seconds]": "3600",
                    },
                    files={"file": (video_path.name, handle, "video/mp4")},
                ).json()
            file_id = uploaded.get("id")
            if not isinstance(file_id, str) or not file_id.startswith("file-"):
                raise MetaProviderUncertainError("Meta Files API returned no valid file ID.")
            # SAM's official prompt grammar accepts only a non-negative integer
            # object ID. Keep RealityOS' UUID/string track ID local and map the
            # small, per-request SAM ID back before the result leaves this client.
            sam_to_track_id: dict[str, str] = {}
            object_prompts: list[PromptObject] = []
            for sam_object_id, prompt in enumerate(prompts[:16]):
                sam_to_track_id[str(sam_object_id)] = prompt.object_id
                box = prompt.bounding_box
                left = max(0, min(width - 1, int(box["x"] * width)))
                top = max(0, min(height - 1, int(box["y"] * height)))
                right = max(left + 1, min(width, math.ceil((box["x"] + box["width"]) * width)))
                bottom = max(top + 1, min(height, math.ceil((box["y"] + box["height"]) * height)))
                object_prompts.append(
                    PromptObject(
                        id=sam_object_id,
                        prompts=[
                            FramePrompt(
                                frame=max(0, min(frame_count - 1, prompt.frame_index)),
                                box=PromptBox(left=left, top=top, right=right, bottom=bottom),
                            )
                        ],
                    )
                )
            body = {
                "model": "sam-3.1",
                "store": False,
                "stream": True,
                "metadata": {
                    "mask_encoding": "one_bit",
                    "include_confidence": "true",
                    "propagation_direction": "both",
                },
                "input": [
                    {
                        "type": "message",
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": build_object_prompt(
                                    size=(width, height), objects=object_prompts
                                ),
                            },
                            {"type": "input_video", "file_id": file_id},
                        ],
                    }
                ],
            }
            result = self._video_result_from_events(
                self._stream_events_once(body), width, height, file_id
            )
            return VideoTrackingResult(
                model=result.model,
                simulated=result.simulated,
                provider_file_id=result.provider_file_id,
                frames=[
                    VideoTrackFrame(
                        object_id=sam_to_track_id.get(str(frame.object_id), frame.object_id),
                        frame_index=frame.frame_index,
                        bounding_box=frame.bounding_box,
                        mask_rle=frame.mask_rle,
                        mask_width=frame.mask_width,
                        mask_height=frame.mask_height,
                        confidence=frame.confidence,
                    )
                    for frame in result.frames
                ],
            )
        finally:
            if file_id:
                try:
                    self._file_request_once("DELETE", f"files/{file_id}")
                except MetaProviderError:
                    pass

    def transcribe_wav(self, audio: bytes) -> Transcription:
        files = {
            "request": (
                None,
                json.dumps(
                    {
                        "model": "muse-voice-transcribe-1.0",
                        "audioEncoding": "WAV",
                        "mode": "PUSH_TO_TALK",
                    }
                ),
                "application/json",
            ),
            "audio": ("query.wav", audio, "audio/wav"),
        }
        payload = self._request(
            "POST",
            "asr/transcribe",
            files=files,
            headers={"Accept": "application/json"},
        ).json()
        text = payload.get("text") or payload.get("transcript")
        if not isinstance(text, str) or not text.strip():
            raise MetaProviderError("Muse Voice Transcribe returned no transcript.")
        return Transcription(text=text.strip(), simulated=False)


def build_meta_client(settings: Settings) -> MetaModelClient:
    if settings.meta_mode == "mock":
        return MockMetaModelClient()
    if settings.meta_mode == "live":
        return LiveMetaModelClient(settings)
    raise MetaProviderError("META_MODE must be either 'mock' or 'live'.")


def _raster_rle(raster: bytes) -> bytes:
    """Store a compact, self-identifying binary-mask run-length encoding."""

    if not raster:
        return b"RLE1\x00"
    runs: list[int] = []
    previous = raster[0]
    length = 1
    for value in raster[1:]:
        if value == previous:
            length += 1
        else:
            runs.append(length)
            previous = value
            length = 1
    runs.append(length)
    return b"RLE1" + zlib.compress(
        json.dumps({"first": int(raster[0] != 0), "runs": runs}, separators=(",", ":")).encode()
    )


def _rectangle_rle(width: int, height: int, box: dict[str, float]) -> bytes:
    pixels = bytearray(width * height)
    left = max(0, min(width - 1, int(float(box["x"]) * width)))
    top = max(0, min(height - 1, int(float(box["y"]) * height)))
    right = max(left + 1, min(width, math.ceil((float(box["x"]) + float(box["width"])) * width)))
    bottom = max(top + 1, min(height, math.ceil((float(box["y"]) + float(box["height"])) * height)))
    for row in range(top, bottom):
        pixels[row * width + left : row * width + right] = b"\x01" * (right - left)
    return _raster_rle(bytes(pixels))
