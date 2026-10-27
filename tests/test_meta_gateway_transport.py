from __future__ import annotations

import httpx
import pytest
from app.config import Settings
from app.meta import LiveMetaModelClient, MetaProviderError, SegmentationResult


def test_live_client_uses_gateway_without_model_key(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs: object) -> httpx.Response:
        captured["method"] = method
        captured["url"] = url
        captured["headers"] = kwargs["headers"]
        request = httpx.Request(method, url)
        return httpx.Response(200, json={"output_text": '{"detections": []}'}, request=request)

    monkeypatch.setattr(httpx, "request", fake_request)
    client = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_gateway_base_url="https://meta.luxisoft.com/v1",
            meta_gateway_token="gateway-token-long-enough-for-tests",
        )
    )

    response = client._request("POST", "responses", json={"model": "muse-spark-1.3"})

    assert response.status_code == 200
    assert captured["url"] == "https://meta.luxisoft.com/v1/responses"
    assert captured["headers"] == {"X-RealityOS-Gateway-Token": "gateway-token-long-enough-for-tests"}


def test_live_analysis_requests_english_human_readable_detections(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs: object) -> httpx.Response:
        captured["json"] = kwargs["json"]
        request = httpx.Request(method, url)
        return httpx.Response(
            200,
            json={"output_text": '{"detections": []}'},
            request=request,
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    client = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_gateway_base_url="https://meta.luxisoft.com/v1",
            meta_gateway_token="gateway-token-long-enough-for-tests",
        )
    )

    client.analyze_image(b"fixture", "image/png")

    payload = captured["json"]
    assert isinstance(payload, dict)
    assert "must use English" in str(payload["instructions"])


def test_live_query_interpretation_only_accepts_known_terms(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_request(method: str, url: str, **kwargs: object) -> httpx.Response:
        captured["json"] = kwargs["json"]
        request = httpx.Request(method, url)
        return httpx.Response(
            200,
            json={"output_text": '{"terms":["yellow drill","invented object"]}'},
            request=request,
        )

    monkeypatch.setattr(httpx, "request", fake_request)
    client = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_gateway_base_url="https://meta.luxisoft.com/v1",
            meta_gateway_token="gateway-token-long-enough-for-tests",
        )
    )

    interpretation = client.interpret_query(
        "¿Dónde está el taladro amarillo?", ["yellow drill", "hammer"]
    )

    assert interpretation.terms == ["yellow drill"]
    assert interpretation.simulated is False
    assert "multilingual object-query interpreter" in str(captured["json"])


def test_live_gateway_requires_its_own_token() -> None:
    with pytest.raises(MetaProviderError, match="META_GATEWAY_TOKEN"):
        LiveMetaModelClient(
            Settings(meta_mode="live", meta_gateway_base_url="https://meta.luxisoft.com/v1")
        )


def test_live_sam_uses_a_box_prompt_and_compact_mask_stream(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}
    client = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_gateway_base_url="https://meta.luxisoft.com/v1",
            meta_gateway_token="gateway-token-long-enough-for-tests",
        )
    )

    def stream(body: dict[str, object]) -> list[dict[str, object]]:
        captured["body"] = body
        return []

    monkeypatch.setattr(client, "_stream_events", stream)
    monkeypatch.setattr(
        client,
        "_sam_result_from_events",
        lambda events, width, height: SegmentationResult(
            model="sam-3.1",
            simulated=False,
            bounding_box={"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
            confidence=0.9,
            mask=b"\x01" * (width * height),
            mask_width=width,
            mask_height=height,
        ),
    )

    result = client.segment(
        b"fixture",
        "image/png",
        "yellow drill",
        width=100,
        height=80,
        bounding_box={"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
    )

    assert result is not None
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["stream"] is True
    assert body["metadata"] == {"mask_encoding": "one_bit", "include_confidence": "true"}
    assert "<0f>1<|box;x1=10;y1=16;x2=39;y2=48;w=100;h=80|>" in str(body)
