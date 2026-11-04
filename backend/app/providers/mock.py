from __future__ import annotations

import math
from pathlib import Path

from app.providers.contracts import (
    MetaModelClient,
    ProfileAnswer,
    ProfileContext,
    SegmentationResult,
    Transcription,
    VideoTrackFrame,
    VideoTrackingResult,
    VideoTrackPrompt,
    _rectangle_rle,
)
from app.schemas import (
    ImageAnalysis,
    MetaDetection,
    MetaFact,
    PersonFilter,
    QueryInterpretation,
    SearchIntent,
)


class MockMetaModelClient(MetaModelClient):
    """Deterministic local fixtures; deliberately makes no network request."""

    def translate_gallery_texts(self, texts: dict[str, str], language: str) -> dict[str, str]:
        pairs = {
            "crimping tool": "crimpadora",
            "wire strippers": "pelacables",
            "pliers": "alicates",
            "clamp": "prensa",
            "yellow drill": "taladro amarillo",
            "hammer": "martillo",
            "Workshop": "Taller",
            "Keep on shelf 2": "Guardar en el estante 2",
        }
        mapping = pairs if language == "es" else {v: k for k, v in pairs.items()}
        return {key: mapping.get(value, value) for key, value in texts.items()}

    def review_gallery_objects(self, image: bytes, candidates: list[dict]) -> list[dict]:
        return [
            {"id": c["id"], "verdict": "confirmed", "confidence": 0.95, "box": c["box"]}
            for c in candidates
        ]

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

    def compare_gallery_images(
        self, image: bytes, candidates: list[tuple[str, bytes]]
    ) -> str | None:
        import io

        from PIL import Image, ImageChops, ImageStat

        with Image.open(io.BytesIO(image)) as source:
            new = source.convert("RGB").resize((64, 64))
        for key, raw in candidates:
            with Image.open(io.BytesIO(raw)) as source:
                old = source.convert("RGB").resize((64, 64))
            if max(ImageStat.Stat(ImageChops.difference(new, old)).mean) < 4:
                return key
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
        """Deterministic local mask; it is visibly marked simulated downstream."""

        x = max(0, min(width - 1, int(float(bounding_box["x"]) * width)))
        y = max(0, min(height - 1, int(float(bounding_box["y"]) * height)))
        right = max(
            x + 1,
            min(
                width, math.ceil((float(bounding_box["x"]) + float(bounding_box["width"])) * width)
            ),
        )
        bottom = max(
            y + 1,
            min(
                height,
                math.ceil((float(bounding_box["y"]) + float(bounding_box["height"])) * height),
            ),
        )
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

    def interpret_gallery_terms(self, question: str, known_terms: list[str]) -> QueryInterpretation:
        """Deterministic near-match fixture for gallery candidates only."""

        strict = self.interpret_query(question, known_terms)
        if strict.terms:
            return strict
        normalized = question.casefold()
        known = {term.casefold(): term for term in known_terms}
        near_terms = {
            "alicate": ["crimping tool", "clamp", "hand tool"],
            "alicates": ["crimping tool", "clamp", "hand tool"],
            "pliers": ["crimping tool", "clamp", "hand tool"],
            "pinza": ["clamp", "crimping tool"],
            "pinzas": ["clamp", "crimping tool"],
            "taladro": ["power tool"],
            "drill": ["power tool"],
        }
        matched: list[str] = []
        for variant, candidates in near_terms.items():
            if variant in normalized:
                for candidate in candidates:
                    if candidate in known and known[candidate] not in matched:
                        matched.append(known[candidate])
        return QueryInterpretation(terms=matched[:8], simulated=True)

    def classify_intent(self, question: str) -> SearchIntent:
        """Deterministic multilingual fixture; it never calls a model or network."""

        tokens = {
            word.casefold().strip(".,:?¿¡!\"'()")
            for word in question.split()
            if word.strip(".,:?¿¡!\"'()")
        }
        person_markers = {
            "quién",
            "quiénes",
            "quien",
            "quienes",
            "persona",
            "personas",
            "who",
            "whom",
            "whose",
            "person",
            "persons",
            "people",
            "somebody",
            "someone",
            "quem",
            "pessoa",
            "pessoas",
            "alguém",
            "algúem",
            "qui",
            "personne",
            "personnes",
            "quelqu'un",
            "quelqu’un",
            "wer",
            "wen",
            "wem",
            "wessen",
            "jemand",
            "mensch",
            "menschen",
            "chi",
            "cercare",
            "trova",
        }
        ask_markers = {
            "búscalo",
            "buscalo",
            "búscala",
            "buscala",
            "búscalos",
            "encuéntralo",
            "encuentralo",
            "encuéntrala",
            "encuéntralos",
            "findit",
            "findhim",
            "findher",
            "trouve-le",
            "trouve-la",
        }
        greeting_markers = {
            "hola",
            "hello",
            "hey",
            "hi",
            "oi",
            "olá",
            "ola",
            "bonjour",
            "salut",
            "hallo",
            "ciao",
            "buenos",
            "buenas",
            "días",
            "dias",
            "tardes",
            "noches",
            "gracias",
            "gràcies",
            "thanks",
            "thank",
            "obrigado",
            "obrigada",
            "merci",
            "danke",
            "grazie",
        }
        search_verbs = {
            "busca",
            "buscas",
            "busco",
            "buscar",
            "buscando",
            "busque",
            "busquen",
            "encuentra",
            "encuentras",
            "encuentro",
            "encontrar",
            "encontré",
            "dónde",
            "donde",
            "where",
            "find",
            "finds",
            "search",
            "searching",
            "looking",
            "encontre",
            "encontrar",
            "trova",
            "trouver",
            "trouve",
            "finden",
            "finde",
            "suche",
            "where's",
            "wheres",
        }
        if tokens & person_markers:
            return SearchIntent(target="person", simulated=True)
        if tokens & ask_markers:
            return SearchIntent(target="ask", simulated=True)
        if tokens & greeting_markers and not (tokens & search_verbs):
            return SearchIntent(target="chat", simulated=True)
        return SearchIntent(target="object", simulated=True)

    def interpret_person_filter(self, question: str) -> PersonFilter:
        """Deterministic offline filter; it never calls a model or network."""

        from app.providers.person_filters import interpret

        return PersonFilter(filter=interpret(question), simulated=True)

    def extract_profile_context(self, cv_text: str) -> ProfileContext:
        normalized = " ".join(cv_text.split())[:12_000]
        return ProfileContext(text=normalized, simulated=True)

    def answer_profile_question(
        self, question: str, candidates: list[dict[str, str]], language: str | None = None
    ) -> ProfileAnswer:
        terms = {word.casefold().strip(".,:?¿¡!") for word in question.split() if len(word) > 3}
        ranked = sorted(
            candidates,
            key=lambda item: sum(
                term in f"{item.get('public_profile', '')} {item.get('context', '')}".casefold()
                for term in terms
            ),
            reverse=True,
        )
        matched = [item for item in ranked if item.get("public_profile") or item.get("context")][:3]
        if not matched:
            return ProfileAnswer(
                text="There is not enough professional information to answer."
                if language == "en"
                else "No hay información profesional suficiente para responder.",
                matched_user_ids=[],
                simulated=True,
            )
        names = ", ".join(item["name"] for item in matched)
        return ProfileAnswer(
            text=(
                f"Simulated result based on the available professional profile: {names}."
                if language == "en"
                else f"Resultado simulado basado en el perfil profesional disponible: {names}."
            ),
            matched_user_ids=[item["user_id"] for item in matched],
            simulated=True,
        )
