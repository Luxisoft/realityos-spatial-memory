import asyncio

import httpx
import pytest
from realityos_meta_gateway.config import GatewaySettings
from realityos_meta_gateway.main import create_app


def request(
    handler, *, token="gateway-secret-for-tests", path="/v1/tts/synthesize", **kwargs
):
    settings = GatewaySettings(
        model_api_key="meta-model-key-for-tests",
        meta_gateway_token="gateway-secret-for-tests",
        tts_service_url="http://seamless-tts:8091/synthesize",
        tts_service_token="private-tts-service-test-token",
    )

    async def send():
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(
                app=create_app(settings, httpx.MockTransport(handler))
            ),
            base_url="http://gateway.test",
        ) as client:
            return await client.post(
                path, headers={"X-RealityOS-Gateway-Token": token}, **kwargs
            )

    return asyncio.run(send())


def test_speech_has_fixed_destination_and_separate_secret():
    import io
    import wave

    out = io.BytesIO()
    with wave.open(out, "wb") as audio:
        audio.setparams((1, 2, 16000, 10, "NONE", "none"))
        audio.writeframes(b"\0\0" * 10)
    captured = []
    result = request(
        lambda req: captured.append(req) or httpx.Response(200, content=out.getvalue()),
        json={"text": "Hola", "language": "es"},
    )
    assert result.status_code == 200
    assert result.content == out.getvalue()
    assert result.headers["cache-control"] == "no-store"
    assert str(captured[0].url) == "http://seamless-tts:8091/synthesize"
    assert (
        captured[0].headers["authorization"] == "Bearer private-tts-service-test-token"
    )
    assert "x-realityos-gateway-token" not in captured[0].headers
    assert b"meta-model-key" not in captured[0].content


@pytest.mark.parametrize(
    "kwargs,token,status",
    [
        ({"json": {"text": "Hello", "language": "en"}}, "wrong", 401),
        (
            {"json": {"text": "Hello", "language": "en", "url": "http://elsewhere"}},
            "gateway-secret-for-tests",
            422,
        ),
        ({"content": b"x" * 32769}, "gateway-secret-for-tests", 413),
    ],
)
def test_rejected_speech_never_contacts_upstream(kwargs, token, status):
    calls = []
    result = request(
        lambda req: calls.append(req) or httpx.Response(200), token=token, **kwargs
    )
    assert result.status_code == status
    assert not calls


def test_gateway_rejects_arbitrary_routes_and_invalid_audio():
    assert (
        request(lambda _: httpx.Response(200), path="/v1/tts/other").status_code == 404
    )
    result = request(
        lambda _: httpx.Response(200, content=b"not-wav"),
        json={"text": "Hello", "language": "en"},
    )
    assert result.status_code == 502


@pytest.mark.parametrize("status", [401, 403, 422])
def test_service_auth_and_validation_failures_remain_permanent(status):
    result = request(
        lambda _: httpx.Response(status), json={"text": "Hello", "language": "en"}
    )
    assert result.status_code == status
