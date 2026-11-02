import asyncio

import httpx
from realityos_meta_gateway.config import GatewaySettings
from realityos_meta_gateway.main import create_app


def test_gateway_has_no_synthesis_route_and_never_forwards_it():
    calls = []
    settings = GatewaySettings(
        _env_file=None,
        model_api_key="meta-model-test-key",
        meta_gateway_token="private-gateway-test-token",
    )

    async def send():
        app = create_app(
            settings,
            httpx.MockTransport(
                lambda request: calls.append(request) or httpx.Response(200)
            ),
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.test"
        ) as client:
            for path in ("/v1/tts/synthesize", "/v1/tts/other"):
                response = await client.post(
                    path,
                    headers={"X-RealityOS-Gateway-Token": settings.meta_gateway_token},
                    json={"text": "Hello", "language": "en"},
                )
                assert response.status_code == 404

    asyncio.run(send())
    assert not calls
