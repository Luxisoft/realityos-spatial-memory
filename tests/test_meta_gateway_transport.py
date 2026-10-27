from __future__ import annotations

import httpx
import pytest
from app.config import Settings
from app.meta import (
    LiveMetaModelClient,
    MetaProviderError,
    MetaProviderUncertainError,
    SegmentationResult,
    VideoTrackFrame,
    VideoTrackingResult,
    VideoTrackPrompt,
)


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


def test_live_video_uses_temporary_file_once_and_sam_file_id(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    client = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_gateway_base_url="https://meta.luxisoft.com/v1",
            meta_gateway_token="gateway-token-long-enough-for-tests",
        )
    )
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"video")
    calls: list[tuple[str, str, object]] = []
    captured: dict[str, object] = {}

    def file_request(method: str, path: str, **kwargs: object) -> httpx.Response:
        calls.append((method, path, kwargs))
        request = httpx.Request(method, f"https://gateway.test/{path}")
        if method == "POST":
            return httpx.Response(200, json={"id": "file-123"}, request=request)
        return httpx.Response(200, json={"id": "file-123", "deleted": True}, request=request)

    def stream(body: dict[str, object]) -> list[dict[str, object]]:
        captured["body"] = body
        return []

    monkeypatch.setattr(client, "_file_request_once", file_request)
    monkeypatch.setattr(client, "_stream_events_once", stream)
    monkeypatch.setattr(
        client,
        "_video_result_from_events",
        lambda events, width, height, file_id: VideoTrackingResult(
            "sam-3.1",
            False,
            file_id,
            [VideoTrackFrame("0", 0, None, None, None, None, None)],
        ),
    )

    result = client.track_video(
        clip,
        width=100,
        height=80,
        frame_count=10,
        prompts=[
            VideoTrackPrompt(
                object_id="track-1",
                frame_index=2,
                bounding_box={"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4},
            )
        ],
    )

    assert result.provider_file_id == "file-123"
    assert result.frames[0].object_id == "track-1"
    assert [call[:2] for call in calls] == [("POST", "files"), ("DELETE", "files/file-123")]
    assert calls[0][2]["data"] == {
        "purpose": "user_data",
        "expires_after[anchor]": "created_at",
        "expires_after[seconds]": "3600",
    }
    body = captured["body"]
    assert isinstance(body, dict)
    assert body["stream"] is True
    assert "file-123" in str(body)
    assert "propagation_direction" in str(body)


def test_live_video_marks_stream_failure_uncertain_without_a_second_submission(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    client = LiveMetaModelClient(
        Settings(
            meta_mode="live",
            meta_gateway_base_url="https://meta.luxisoft.com/v1",
            meta_gateway_token="gateway-token-long-enough-for-tests",
        )
    )
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"video")
    calls: list[tuple[str, str]] = []

    def file_request(method: str, path: str, **kwargs: object) -> httpx.Response:
        calls.append((method, path))
        return httpx.Response(200, json={"id": "file-123"})

    monkeypatch.setattr(client, "_file_request_once", file_request)
    monkeypatch.setattr(
        client,
        "_stream_events_once",
        lambda body: (_ for _ in ()).throw(MetaProviderUncertainError("gateway interrupted")),
    )
    with pytest.raises(MetaProviderUncertainError, match="gateway interrupted"):
        client.track_video(
            clip,
            width=100,
            height=80,
            frame_count=10,
            prompts=[
                VideoTrackPrompt(
                    "track-1", 0, {"x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4}
                )
            ],
        )
    assert calls == [("POST", "files"), ("DELETE", "files/file-123")]
