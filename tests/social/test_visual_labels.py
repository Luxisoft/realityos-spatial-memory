"""Grounding labels must survive the evidence-image endpoint.

The endpoint addresses annotations as comma-joined exact labels, so a stored
label containing a comma can never resolve and its gallery image 404s.
"""

from __future__ import annotations

import io

from app.providers.mock import MockMetaModelClient
from app.schemas import ImageAnalysis, MetaDetection
from app.social_features import visual
from PIL import Image


class CommaLabelClient(MockMetaModelClient):
    def analyze_image(self, image, mime_type, context="", **kwargs):
        return ImageAnalysis(
            model="mock-test",
            simulated=True,
            detections=[
                MetaDetection(
                    label="older man with receding gray hair, blue eyes and gray mustache",
                    category="person",
                    confidence=0.95,
                    bounding_box={"x": 0.1, "y": 0.1, "width": 0.8, "height": 0.8},
                )
            ],
        )


def test_ground_removes_commas_from_labels():
    out = io.BytesIO()
    Image.new("RGB", (64, 48), "green").save(out, "JPEG")
    _, _, _, detections = visual.ground(CommaLabelClient(), out.getvalue())
    assert detections, "expected the detection to survive grounding"
    assert all("," not in item["label"] for item in detections)
    assert all(item["label"].split() for item in detections)
