import io
import wave

import httpx
import pytest
from app.providers.seamless_service import create_app, speech_chunks
from app.tts_contracts import validate_wav
from fastapi.testclient import TestClient


def wav():
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setparams((1, 2, 16000, 1600, "NONE", "not compressed"))
        audio.writeframes(b"\x01\x00" * 1600)
    return output.getvalue()


def configure(client, upstream):
    settings = client.app.state.settings
    settings.meta_mode = "live"
    settings.tts_provider = "seamless"
    settings.meta_connection_mode = "gateway"
    settings.meta_gateway_base_url = "https://gateway.test/v1"
    settings.meta_gateway_token = "private-gateway-token-for-tests"
    client.app.state.tts_transport = httpx.MockTransport(upstream)


def test_simulated_mode_never_contacts_speech_provider(client, auth_headers):
    requests = []
    configure(
        client, lambda req: requests.append(req) or httpx.Response(200, content=wav())
    )
    client.app.state.settings.meta_mode = "mock"
    assert (
        client.post(
            "/v1/tts",
            headers=auth_headers,
            json={"text": "Simulated answer", "language": "en"},
        ).status_code
        == 503
    )
    assert not requests


def test_tts_authenticated_stateless_audio(client, auth_headers):
    requests = []

    def upstream(request):
        requests.append(request)
        return httpx.Response(200, content=wav())

    configure(client, upstream)
    result = client.post(
        "/v1/tts", headers=auth_headers, json={"text": "Hola", "language": "es"}
    )
    assert result.status_code == 200
    assert result.content == wav()
    assert result.headers["cache-control"] == "no-store"
    assert str(requests[0].url) == "https://gateway.test/v1/tts/synthesize"
    assert "authorization" not in requests[0].headers
    assert b'"language":"es"' in requests[0].content
    # No chat/evidence identifiers may be used to synthesize another account's data.
    assert (
        client.post(
            "/v1/tts",
            headers=auth_headers,
            json={"text": "Hola", "language": "es", "workspace_id": "other-workspace"},
        ).status_code
        == 422
    )
    assert client.get("/v1/chat/history", headers=auth_headers).json()["messages"] == []


def test_tts_requires_valid_auth_before_egress(client, auth_headers):
    requests = []
    configure(
        client,
        lambda request: requests.append(request) or httpx.Response(200, content=wav()),
    )
    for headers in (
        {},
        {"Authorization": "Bearer invalid"},
        {"X-RealityOS-Device-ID": "unknown", "X-RealityOS-Device-Key": "invalid"},
    ):
        assert (
            client.post(
                "/v1/tts",
                headers=headers,
                json={"text": "Private answer", "language": "en"},
            ).status_code
            == 401
        )
    assert not requests


def test_device_tts_requires_active_assignment_and_cannot_select_another_workspace(
    client, auth_headers
):
    workspace = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Speech workspace"}
    ).json()
    device = client.post(
        "/v1/admin/devices",
        headers=auth_headers,
        json={
            "workspace_id": workspace["id"],
            "device_identifier": "speech-device",
            "label": "Speech device",
        },
    ).json()
    headers = {
        "X-RealityOS-Device-ID": "speech-device",
        "X-RealityOS-Device-Key": device["device_key"],
    }
    payload = {"text": "Hola", "language": "es"}
    requests = []
    configure(
        client, lambda req: requests.append(req) or httpx.Response(200, content=wav())
    )
    assert client.post("/v1/tts", headers=headers, json=payload).status_code == 403
    assert not requests
    assert (
        client.post(
            f"/v1/admin/devices/{device['id']}/assignments",
            headers=auth_headers,
            json={"operator_label": "Speech", "notice_version": "v1"},
        ).status_code
        == 201
    )
    assert client.post("/v1/tts", headers=headers, json=payload).status_code == 200
    assert (
        client.post(
            "/v1/tts", headers=headers, json={**payload, "workspace_id": "someone-else"}
        ).status_code
        == 422
    )
    assert len(requests) == 1
    assert (
        client.post(
            f"/v1/admin/devices/{device['id']}/revoke", headers=auth_headers
        ).status_code
        == 200
    )
    assert client.post("/v1/tts", headers=headers, json=payload).status_code == 401
    assert len(requests) == 1


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_tts_transient_failure_retried_once(client, auth_headers, status):
    attempts = []

    def upstream(request):
        attempts.append(request)
        return httpx.Response(status if len(attempts) == 1 else 200, content=wav())

    configure(client, upstream)
    response = client.post(
        "/v1/tts", headers=auth_headers, json={"text": "Hello", "language": "en"}
    )
    assert response.status_code == 200
    assert len(attempts) == 2


@pytest.mark.parametrize("status", [401, 403, 404, 422])
def test_tts_permanent_failures_not_retried(client, auth_headers, status):
    attempts = []
    configure(
        client, lambda request: attempts.append(request) or httpx.Response(status)
    )
    assert (
        client.post(
            "/v1/tts", headers=auth_headers, json={"text": "Hello", "language": "en"}
        ).status_code
        == 503
    )
    assert len(attempts) == 1


def test_tts_timeout_and_two_failures_are_bounded(client, auth_headers):
    attempts = []
    configure(client, lambda request: attempts.append(request) or httpx.Response(503))
    payload = {"text": "Hello", "language": "en"}
    assert client.post("/v1/tts", headers=auth_headers, json=payload).status_code == 503
    assert len(attempts) == 2
    attempts.clear()
    client.app.state.settings.tts_timeout_seconds = 0.01
    assert client.post("/v1/tts", headers=auth_headers, json=payload).status_code == 503
    assert len(attempts) == 1


@pytest.mark.parametrize(
    "payload",
    [
        {"text": " ", "language": "es"},
        {"text": "a" * 4001, "language": "es"},
        {"text": "Bonjour", "language": "fr"},
    ],
)
def test_tts_rejects_invalid_input(client, auth_headers, payload):
    assert client.post("/v1/tts", headers=auth_headers, json=payload).status_code == 422


def test_invalid_wav_never_reaches_clients(client, auth_headers):
    configure(client, lambda _: httpx.Response(200, content=b"<html>error</html>"))
    assert (
        client.post(
            "/v1/tts", headers=auth_headers, json={"text": "Hello", "language": "en"}
        ).status_code
        == 503
    )
    with pytest.raises(ValueError):
        validate_wav(wav()[:-2])


def test_service_loads_once_authenticates_and_preserves_all_phrases():
    loaded, calls = [], []

    class Engine:
        def __init__(self):
            loaded.append(True)

        def synthesize(self, payload):
            calls.append(payload)
            return wav()

    application = create_app(Engine, token="private-speech-token-for-tests")
    with TestClient(application) as client:
        assert client.get("/health/ready").status_code == 200
        for language in ("es", "en"):
            assert (
                client.post(
                    "/synthesize",
                    headers={"Authorization": "Bearer private-speech-token-for-tests"},
                    json={"text": "Hello", "language": language},
                ).content
                == wav()
            )
        assert (
            client.post(
                "/synthesize", json={"text": "Hello", "language": "en"}
            ).status_code
            == 401
        )
    assert len(loaded) == 1 and len(calls) == 2
    text = "Hola mundo. " + "respuesta " * 300
    chunks = speech_chunks(text)
    assert max(map(len, chunks)) <= 240
    assert " ".join(chunks).split() == text.split()
