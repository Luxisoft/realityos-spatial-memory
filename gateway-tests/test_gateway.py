from __future__ import annotations

import asyncio

import httpx
from realityos_meta_gateway.config import GatewaySettings
from realityos_meta_gateway.main import create_app


def _client(app: object) -> httpx.Response:
    async def request() -> httpx.Response:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
        ) as client:
            return await client.get(
                "/v1/models", headers={"X-RealityOS-Gateway-Token": "gateway-secret-for-tests"}
            )

    return asyncio.run(request())


def _settings(**overrides: object) -> GatewaySettings:
    values: dict[str, object] = {
        "model_api_key": "meta-model-key-for-tests",
        "meta_gateway_token": "gateway-secret-for-tests",
        "meta_api_base_url": "https://api.meta.ai/v1",
    }
    values.update(overrides)
    return GatewaySettings(**values)


def test_gateway_injects_meta_key_and_hides_gateway_token() -> None:
    captured: dict[str, object] = {}

    def upstream(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        return httpx.Response(
            200,
            json={"object": "list", "data": [{"id": "muse-spark-1.3"}]},
            headers={"x-request-id": "meta-request-id"},
        )

    response = _client(create_app(_settings(), httpx.MockTransport(upstream)))

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "muse-spark-1.3"
    assert response.headers["x-request-id"] == "meta-request-id"
    assert captured["url"] == "https://api.meta.ai/v1/models"
    headers = captured["headers"]
    assert isinstance(headers, dict)
    assert headers["authorization"] == "Bearer meta-model-key-for-tests"
    assert "x-realityos-gateway-token" not in headers


def test_gateway_rejects_invalid_token_before_contacting_meta() -> None:
    called = False

    def upstream(_: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(200)

    async def request() -> httpx.Response:
        app = create_app(_settings(), httpx.MockTransport(upstream))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
        ) as client:
            return await client.get("/v1/models", headers={"X-RealityOS-Gateway-Token": "wrong"})

    response = asyncio.run(request())
    assert response.status_code == 401
    assert response.json()["error"]["message"] == "Invalid gateway token."
    assert called is False


def test_gateway_forwards_multipart_without_persisting_media() -> None:
    captured: dict[str, object] = {}
    body = b"--boundary\r\ncontent-disposition: form-data; name=audio\r\n\r\nbytes\r\n--boundary--\r\n"

    def upstream(request: httpx.Request) -> httpx.Response:
        captured["body"] = request.content
        captured["content_type"] = request.headers["content-type"]
        captured["authorization"] = request.headers["authorization"]
        return httpx.Response(200, json={"text": "taladro amarillo"})

    async def request() -> httpx.Response:
        app = create_app(_settings(), httpx.MockTransport(upstream))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
        ) as client:
            return await client.post(
                "/v1/asr/transcribe",
                content=body,
                headers={
                    "Content-Type": "multipart/form-data; boundary=boundary",
                    "X-RealityOS-Gateway-Token": "gateway-secret-for-tests",
                },
            )

    response = asyncio.run(request())
    assert response.status_code == 200
    assert captured["body"] == body
    assert captured["content_type"] == "multipart/form-data; boundary=boundary"
    assert captured["authorization"] == "Bearer meta-model-key-for-tests"


def test_gateway_exposes_only_the_required_file_routes() -> None:
    async def request() -> httpx.Response:
        app = create_app(_settings(), httpx.MockTransport(lambda _: httpx.Response(200)))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
        ) as client:
            allowed = await client.post(
                "/v1/files",
                headers={"X-RealityOS-Gateway-Token": "gateway-secret-for-tests"},
            )
            denied = await client.get(
                "/v1/files",
                headers={"X-RealityOS-Gateway-Token": "gateway-secret-for-tests"},
            )
            return allowed, denied

    allowed, denied = asyncio.run(request())
    assert allowed.status_code == 200
    assert denied.status_code == 405


def test_gateway_forwards_file_deletion_without_gateway_token_leakage() -> None:
    captured: dict[str, object] = {}

    def upstream(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        return httpx.Response(200, json={"id": "file-123", "deleted": True})

    async def request() -> httpx.Response:
        app = create_app(_settings(), httpx.MockTransport(upstream))
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
        ) as client:
            return await client.delete(
                "/v1/files/file-123",
                headers={"X-RealityOS-Gateway-Token": "gateway-secret-for-tests"},
            )

    response = asyncio.run(request())
    assert response.status_code == 200
    assert captured["url"] == "https://api.meta.ai/v1/files/file-123"
    assert "x-realityos-gateway-token" not in captured["headers"]


def test_gateway_propagates_meta_error_without_changing_it() -> None:
    def upstream(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            429,
            json={"error": {"message": "Rate limit"}},
            headers={"retry-after": "3", "x-request-id": "rate-limit-request"},
        )

    response = _client(create_app(_settings(), httpx.MockTransport(upstream)))
    assert response.status_code == 429
    assert response.json()["error"]["message"] == "Rate limit"
    assert response.headers["retry-after"] == "3"
    assert response.headers["x-request-id"] == "rate-limit-request"
