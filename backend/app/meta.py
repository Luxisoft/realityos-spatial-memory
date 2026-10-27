from __future__ import annotations

import base64
import json
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings
from app.schemas import ImageAnalysis, MetaDetection, QueryInterpretation


class MetaProviderError(RuntimeError):
    """Safe error raised when Meta cannot provide an inference."""


@dataclass(frozen=True)
class Transcription:
    text: str
    simulated: bool


class MetaModelClient(ABC):
    @abstractmethod
    def analyze_image(self, image: bytes, mime_type: str, context: str = "") -> ImageAnalysis: ...

    @abstractmethod
    def segment(self, image: bytes, mime_type: str, prompt: str) -> list[MetaDetection]: ...

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
                )
            ],
        )

    def segment(self, image: bytes, mime_type: str, prompt: str) -> list[MetaDetection]:
        return [
            MetaDetection(
                label=prompt,
                category=None,
                confidence=0.94,
                bounding_box={"x": 0.18, "y": 0.22, "width": 0.57, "height": 0.49},
                spatial_description="Simulated geometry; it was not inferred by real SAM.",
            )
        ]

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
            "for a visible brand, model, or technical acronym. Each detection needs label, "
            "optional category, confidence from 0 to 1, bounding_box {x,y,width,height} "
            "normalized 0..1, spatial_description, and optional relationships as objects "
            "with relation and object keys. Do not claim locations that cannot be seen."
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

    def segment(self, image: bytes, mime_type: str, prompt: str) -> list[MetaDetection]:
        body = {
            "model": "sam-3.1",
            "store": False,
            "input": [
                {
                    "type": "message",
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": prompt},
                        {"type": "input_image", "image_url": self._data_url(image, mime_type)},
                    ],
                }
            ],
        }
        text = self._output_text(self._request("POST", "responses", json=body).json())
        boxes: list[MetaDetection] = []
        pattern = re.compile(
            r"<\|box;x1=(?P<x1>\d+);y1=(?P<y1>\d+);x2=(?P<x2>\d+);y2=(?P<y2>\d+);"
            r"w=(?P<w>\d+);h=(?P<h>\d+)\|>"
        )
        for match in pattern.finditer(text):
            values = {key: float(value) for key, value in match.groupdict().items()}
            boxes.append(
                MetaDetection(
                    label=prompt,
                    confidence=1.0,
                    bounding_box={
                        "x": values["x1"] / values["w"],
                        "y": values["y1"] / values["h"],
                        "width": (values["x2"] - values["x1"]) / values["w"],
                        "height": (values["y2"] - values["y1"]) / values["h"],
                    },
                    spatial_description="Box returned by SAM 3.1; the worker retains the mask geometry.",
                )
            )
        return boxes

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
