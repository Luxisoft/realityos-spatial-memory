from __future__ import annotations

import json
import math
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from app.schemas import (
    GalleryInterpretation,
    ImageAnalysis,
    QueryInterpretation,
    SearchIntent,
)


class MetaProviderError(RuntimeError):
    """Safe, structured failure without request payloads or credentials."""

    def __init__(self, message, *, phase=None, status_code=None, retryable=False):
        super().__init__(message)
        self.phase = phase
        self.status_code = status_code
        self.retryable = retryable


class MetaProviderUncertainError(MetaProviderError):
    """A provider request may have run, but the final result cannot be trusted."""


@dataclass(frozen=True)
class Transcription:
    text: str
    simulated: bool


@dataclass(frozen=True)
class ProfileContext:
    text: str
    simulated: bool


@dataclass(frozen=True)
class ProfileAnswer:
    text: str
    matched_user_ids: list[str]
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

    def prepare_gallery_languages(self, texts: dict[str, str]) -> dict[str, dict[str, str]]:
        return {
            language: self.translate_gallery_texts(texts, language) for language in ("en", "es")
        }

    def translate_gallery_texts(self, texts: dict[str, str], language: str) -> dict[str, str]:
        raise MetaProviderError("Information translation is unavailable.")

    def interpret_gallery_matches(
        self, question: str, known_terms: list[str]
    ) -> GalleryInterpretation:
        # Existing providers keep their exact interpreter; gallery-only local
        # relations are applied by the caller and cannot affect object Query.
        result = self.interpret_query(question, known_terms)
        return GalleryInterpretation(exact=result.terms)

    def interpret_gallery_terms(self, question: str, known_terms: list[str]) -> QueryInterpretation:
        """Near-match variant for gallery candidates; never verified evidence."""

        return self.interpret_query(question, known_terms)

    @abstractmethod
    def classify_intent(self, question: str) -> SearchIntent: ...

    def segment_gallery(self, image: bytes, width: int, height: int, detections: list) -> list:
        return [
            self.segment(
                image,
                "image/jpeg",
                d.label,
                width=width,
                height=height,
                bounding_box=d.bounding_box,
            )
            for d in detections
        ]

    def segment_gallery_concept(self, image, width, height, label, expected_box):
        """Optional second localization of a visually confirmed instance."""
        return None

    def review_gallery_objects(self, image: bytes, candidates: list[dict]) -> list[dict]:
        raise MetaProviderError("Object review is unavailable.", phase="review")

    def compare_gallery_images(
        self, image: bytes, candidates: list[tuple[str, bytes]]
    ) -> str | None:
        """Return an exact-photo duplicate id, or None; uncertainty must raise."""
        raise MetaProviderError("Image comparison is unavailable.")

    def extract_profile_context(self, cv_text: str) -> ProfileContext:
        raise MetaProviderError("Profile extraction is unavailable.")

    def answer_profile_question(
        self, question: str, candidates: list[dict[str, str]], language: str | None = None
    ) -> ProfileAnswer:
        raise MetaProviderError("Profile questions are unavailable.")


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
