import asyncio
import io
import wave

import httpx
import pytest
from app.config import Settings
from app.providers import elevenlabs
from app.providers.tts import SpeechUnavailable, synthesize
from app.tts_contracts import SpeechRequest
from pydantic import SecretStr


def settings(**changes):
    return Settings(
        _env_file=None,
        **(
            {"meta_mode": "live", "elevenlabs_api_key": "private-elevenlabs-test-key"}
            | changes
        ),
    )


def test_elevenlabs_is_request_only_and_independent_of_meta_gateway(
    client, auth_headers
):
    calls = []
    configured = client.app.state.settings
    configured.meta_mode = "live"
    configured.elevenlabs_api_key = SecretStr("private-elevenlabs-test-key")
    configured.meta_connection_mode = "gateway"
    configured.meta_gateway_base_url = None
    configured.meta_gateway_token = None

    def upstream(request):
        calls.append(request)
        return httpx.Response(
            200,
            content=b"\x01\x00" * 2400,
            headers={
                "content-type": "audio/pcm",
                "request-id": "test-request",
                "character-cost": "5",
            },
        )

    client.app.state.tts_transport = httpx.MockTransport(upstream)
    assert client.get("/health/live").status_code == 200
    assert calls == []
    for language in ("es", "en"):
        result = client.post(
            "/v1/tts",
            headers=auth_headers,
            json={"text": "Hello", "language": language},
        )
        assert result.status_code == 200
        assert result.headers["content-type"] == "audio/wav"
        assert result.headers["cache-control"] == "no-store"
        with wave.open(io.BytesIO(result.content)) as audio:
            assert audio.getparams()[:4] == (1, 2, 24000, 2400)
        request = calls[-1]
        assert request.url.host == "api.elevenlabs.io"
        assert request.url.params["output_format"] == "pcm_24000"
        assert request.headers["xi-api-key"] == "private-elevenlabs-test-key"
        assert "authorization" not in request.headers
        assert "x-realityos-gateway-token" not in request.headers
        assert f'"language_code":"{language}"'.encode() in request.content
    assert len(calls) == 2


@pytest.mark.parametrize("status", [401, 403, 404, 422, 429, 500, 502, 503, 504])
def test_elevenlabs_errors_are_not_replayed(status):
    calls = []
    transport = httpx.MockTransport(
        lambda request: calls.append(request) or httpx.Response(status)
    )
    with pytest.raises(SpeechUnavailable):
        asyncio.run(
            synthesize(
                SpeechRequest(text="Hello", language="en"), settings(), transport
            )
        )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "error", [httpx.ReadTimeout, httpx.WriteError, httpx.ConnectError]
)
def test_elevenlabs_uncertain_network_failures_are_not_replayed(error):
    calls = []

    def upstream(request):
        calls.append(request)
        raise error("private fixture message must not reach clients")

    with pytest.raises(SpeechUnavailable, match="Speech generation is unavailable"):
        asyncio.run(
            synthesize(
                SpeechRequest(text="Hello", language="en"),
                settings(),
                httpx.MockTransport(upstream),
            )
        )
    assert len(calls) == 1


@pytest.mark.parametrize(
    "pcm", [b"", b"\x00", b"\x00\x00" * (elevenlabs.MAX_PCM_BYTES // 2 + 1)]
)
def test_elevenlabs_rejects_empty_truncated_and_oversized_pcm(pcm):
    with pytest.raises(SpeechUnavailable, match="Invalid speech response"):
        asyncio.run(
            synthesize(
                SpeechRequest(text="Hello", language="en"),
                settings(),
                httpx.MockTransport(lambda _: httpx.Response(200, content=pcm)),
            )
        )


def test_elevenlabs_missing_key_and_mock_do_not_contact_provider():
    calls = []
    transport = httpx.MockTransport(
        lambda request: calls.append(request) or httpx.Response(200)
    )
    for configured in (settings(elevenlabs_api_key=None), settings(meta_mode="mock")):
        with pytest.raises(SpeechUnavailable):
            asyncio.run(
                synthesize(
                    SpeechRequest(text="Hello", language="en"), configured, transport
                )
            )
    assert calls == []
    assert "private-elevenlabs-test-key" not in repr(settings())


def test_elevenlabs_concurrency_and_cancelled_requests_release_slots():
    async def scenario():
        entered, release = asyncio.Event(), asyncio.Event()
        calls = []

        async def upstream(request):
            calls.append(request)
            if len(calls) == 2:
                entered.set()
            await release.wait()
            return httpx.Response(200, content=b"\x00\x00")

        payload = SpeechRequest(text="Hello", language="en")
        transport = httpx.MockTransport(upstream)
        tasks = [
            asyncio.create_task(synthesize(payload, settings(), transport))
            for _ in range(2)
        ]
        await asyncio.wait_for(entered.wait(), 1)
        with pytest.raises(SpeechUnavailable, match="busy"):
            await synthesize(payload, settings(), transport)
        assert len(calls) == 2
        tasks[0].cancel()
        with pytest.raises(asyncio.CancelledError):
            await tasks[0]
        release.set()
        await tasks[1]
        assert await synthesize(payload, settings(), transport)

    asyncio.run(scenario())


def test_elevenlabs_total_deadline_is_bounded():
    async def upstream(request):
        await asyncio.sleep(1)
        return httpx.Response(200, content=b"\x00\x00")

    with pytest.raises(SpeechUnavailable):
        asyncio.run(
            synthesize(
                SpeechRequest(text="Hello", language="en"),
                settings(tts_timeout_seconds=0.01),
                httpx.MockTransport(upstream),
            )
        )
