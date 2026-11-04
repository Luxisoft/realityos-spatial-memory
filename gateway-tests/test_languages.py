"""Gateway-owned copy follows the caller language; Meta bytes remain original."""

import asyncio

import httpx
import pytest
from realityos_meta_gateway.main import create_app
from test_gateway import _settings


def request(path="/v1/models", *, header=None, token=None, transport=None, **kwargs):
    async def send():
        app = create_app(_settings(gateway_max_request_bytes=1024), transport)
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
        ) as client:
            headers = {}
            if header:
                headers["Accept-Language"] = header
            if token:
                headers["X-RealityOS-Gateway-Token"] = token
            return await client.get(path, headers=headers, **kwargs)

    return asyncio.run(send())


@pytest.mark.parametrize(
    "header,language",
    [
        (None, "en"),
        ("en-US", "en"),
        ("fr", "en"),
        ("es-CO,en;q=0.2", "es"),
        ("es;q=0,en;q=0.2", "en"),
        ("en;q=NaN,es_MX", "es"),
    ],
)
def test_gateway_token_errors_are_localized_before_upstream(header, language):
    def never(_):
        pytest.fail("Invalid token must not contact Meta")

    response = request(header=header, transport=httpx.MockTransport(never))
    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "message": "El token del gateway no es válido."
            if language == "es"
            else "Invalid gateway token."
        }
    }
    assert response.headers["content-language"] == language
    assert response.headers["vary"] == "Accept-Language"


def test_upstream_error_bytes_headers_and_allowlist_are_unchanged():
    raw = b'{"error":{"message":"Invalid gateway token.","code":"upstream_error"}}'

    def upstream(incoming):
        assert "accept-language" not in incoming.headers
        assert "x-realityos-gateway-token" not in incoming.headers
        return httpx.Response(
            429,
            content=raw,
            headers={
                "Content-Type": "application/json",
                "Retry-After": "30",
                "X-Request-Id": "upstream-id",
            },
        )

    response = request(
        header="es",
        token="gateway-secret-for-tests",
        transport=httpx.MockTransport(upstream),
    )
    assert response.status_code == 429 and response.content == raw
    assert response.headers["retry-after"] == "30"
    assert response.headers["x-request-id"] == "upstream-id"
    assert "content-language" not in response.headers
    denied = request("/v1/arbitrary-proxy", header="es")
    assert denied.status_code == 404 and denied.json() == {
        "detail": "No se encontró el recurso."
    }
    method = request("/v1/files", header="es")
    assert method.status_code == 405 and method.json() == {
        "detail": "Método no permitido."
    }
    english = request("/v1/arbitrary-proxy", header="en")
    assert english.headers["vary"] == "Accept-Language"
    assert english.headers["content-language"] == "en"


def test_gateway_unavailable_is_localized_without_external_details():
    def unavailable(incoming):
        raise httpx.ConnectError("technical transport failure", request=incoming)

    response = request(
        header="es",
        token="gateway-secret-for-tests",
        transport=httpx.MockTransport(unavailable),
    )
    assert response.status_code == 502
    assert response.json() == {
        "error": {"message": "El servicio de Meta no está disponible."}
    }


def test_gateway_size_limit_is_still_enforced_in_spanish():
    async def send():
        app = create_app(
            _settings(gateway_max_request_bytes=1024),
            httpx.MockTransport(
                lambda _: pytest.fail("Oversize body must not reach Meta")
            ),
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
        ) as client:
            return await client.post(
                "/v1/responses",
                content=b"x" * 1025,
                headers={
                    "Accept-Language": "es",
                    "X-RealityOS-Gateway-Token": "gateway-secret-for-tests",
                },
            )

    response = asyncio.run(send())
    assert response.status_code == 413
    assert response.json() == {
        "error": {"message": "La solicitud al gateway supera el tamaño configurado."}
    }
