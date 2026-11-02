"""Routing decisions, credential isolation, replay safety and bounded fallback."""

from contextlib import contextmanager
from io import BytesIO

import httpx
import pytest
from app.config import Settings
from app.meta import LiveMetaModelClient, MetaProviderError, MetaProviderUncertainError
from pydantic import ValidationError


def settings(**changes):
    values = {
        "_env_file": None,
        "meta_mode": "live",
        "meta_connection_mode": "direct",
        "model_api_key": "direct-test-key",
        "meta_gateway_fallback_enabled": True,
        "meta_gateway_base_url": "https://gateway.test/v1",
        "meta_gateway_token": "gateway-test-token",
        "meta_api_base_url": "https://meta.test/v1",
        "meta_max_retries": 0,
    }
    return Settings(**(values | changes))


def response(url, status=200, **kwargs):
    return httpx.Response(status, request=httpx.Request("POST", url), **kwargs)


@pytest.mark.parametrize(
    "mode,host,auth",
    [
        ("direct", "meta.test", "authorization"),
        ("gateway", "gateway.test", "X-RealityOS-Gateway-Token"),
    ],
)
def test_explicit_mode_and_credentials(monkeypatch, mode, host, auth):
    calls = []

    def request(method, url, **kwargs):
        calls.append(httpx.Request(method, url, headers=kwargs["headers"]))
        return response(url)

    monkeypatch.setattr(httpx, "request", request)
    client = LiveMetaModelClient(settings(meta_connection_mode=mode))
    client._request(
        "GET",
        "models",
        headers={
            "Authorization": "wrong",
            "X-RealityOS-Gateway-Token": "wrong",
            "Accept": "application/json",
        },
    )
    assert len(calls) == 1 and calls[0].url.host == host
    assert calls[0].headers[auth] != "wrong"
    assert ("authorization" in calls[0].headers) == (mode == "direct")
    assert ("x-realityos-gateway-token" in calls[0].headers) == (mode == "gateway")


@pytest.mark.parametrize("status", [401, 403, 404, 408, 429, 500, 501, 502, 503, 504])
def test_http_failure_switches_once_then_next_request_starts_direct(
    monkeypatch, status
):
    calls = []

    def request(method, url, **kwargs):
        calls.append(url)
        return response(
            url,
            status if len(calls) == 1 else 200,
            json={"error": {"message": "fixture"}},
        )

    monkeypatch.setattr(httpx, "request", request)
    client = LiveMetaModelClient(settings())
    assert client._request("POST", "responses").status_code == 200
    assert calls == [
        "https://meta.test/v1/responses",
        "https://gateway.test/v1/responses",
    ]
    client._request("GET", "models")
    assert calls[-1] == "https://meta.test/v1/models"


@pytest.mark.parametrize("status", [400, 422])
def test_invalid_request_never_falls_back(monkeypatch, status):
    calls = []
    monkeypatch.setattr(
        httpx,
        "request",
        lambda method, url, **kw: calls.append(url) or response(url, status),
    )
    with pytest.raises(MetaProviderError) as caught:
        LiveMetaModelClient(settings())._request("POST", "responses")
    assert caught.value.status_code == status
    assert len(calls) == 1


def test_connection_failure_and_failed_gateway_are_bounded(monkeypatch):
    calls = []

    def request(method, url, **kwargs):
        calls.append(url)
        raise httpx.ConnectError("fixture")

    monkeypatch.setattr(httpx, "request", request)
    with pytest.raises(MetaProviderError):
        LiveMetaModelClient(settings())._request("GET", "models")
    assert len(calls) == 2
    calls.clear()
    with pytest.raises(MetaProviderError):
        LiveMetaModelClient(settings(meta_gateway_fallback_enabled=False))._request(
            "GET", "models"
        )
    assert len(calls) == 1


def test_configuration_requires_selected_credentials():
    with pytest.raises(ValidationError):
        settings(meta_connection_mode="automatic")
    with pytest.raises(MetaProviderError, match="MODEL_API_KEY"):
        LiveMetaModelClient(settings(model_api_key=None))
    with pytest.raises(MetaProviderError, match="META_GATEWAY_TOKEN"):
        LiveMetaModelClient(settings(meta_gateway_token=None))
    assert LiveMetaModelClient(
        settings(model_api_key=None, meta_connection_mode="gateway")
    )


def test_file_fallback_rewinds_upload_without_reuploading_success(monkeypatch):
    payloads = []
    handle = BytesIO(b"captured-video-fixture")

    def request(method, url, **kwargs):
        payloads.append(kwargs["files"]["file"][1].read())
        return response(
            url, 404 if len(payloads) == 1 else 200, json={"id": "file-fixture"}
        )

    monkeypatch.setattr(httpx, "request", request)
    result = LiveMetaModelClient(settings())._file_request_once(
        "POST", "files", files={"file": ("clip.mp4", handle, "video/mp4")}
    )
    assert result.json()["id"] == "file-fixture"
    assert payloads == [b"captured-video-fixture"] * 2


@pytest.mark.parametrize("error", [httpx.ReadTimeout, httpx.WriteError])
def test_submitted_file_failure_is_uncertain_and_not_replayed(monkeypatch, error):
    calls = []

    def request(method, url, **kwargs):
        calls.append(url)
        raise error("fixture")

    monkeypatch.setattr(httpx, "request", request)
    with pytest.raises(MetaProviderUncertainError):
        LiveMetaModelClient(settings())._file_request_once("POST", "files")
    assert len(calls) == 1


@pytest.mark.parametrize("once", [False, True])
def test_sam_404_falls_back_before_stream_acceptance(monkeypatch, once):
    calls = []

    @contextmanager
    def stream(method, url, **kwargs):
        calls.append(url)
        yield response(
            url,
            404 if len(calls) == 1 else 200,
            content=b'data: {"type":"response.completed"}\n\n',
        )

    monkeypatch.setattr(httpx, "stream", stream)
    client = LiveMetaModelClient(settings())
    events = client._stream_events_once({}) if once else client._stream_events({})
    assert events == [{"type": "response.completed"}]
    assert len(calls) == 2


@pytest.mark.parametrize("once", [False, True])
def test_incomplete_accepted_stream_never_switches_route(monkeypatch, once):
    calls = []

    @contextmanager
    def stream(method, url, **kwargs):
        calls.append(url)
        yield response(url, content=b'data: {"type":"response.created"}\n\n')

    monkeypatch.setattr(httpx, "stream", stream)
    client = LiveMetaModelClient(settings())
    with pytest.raises(MetaProviderUncertainError):
        client._stream_events_once({}) if once else client._stream_events({})
    assert len(calls) == 1
