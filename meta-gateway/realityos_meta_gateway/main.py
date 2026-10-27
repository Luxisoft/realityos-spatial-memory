from __future__ import annotations

import hmac
import logging
from typing import Final

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from realityos_meta_gateway.config import GatewaySettings

logger = logging.getLogger("realityos.meta_gateway")

_UPSTREAM_PATHS: Final = {
    ("GET", "models"),
    ("POST", "responses"),
    ("POST", "asr/transcribe"),
    ("POST", "files"),
}
_REQUEST_HEADERS: Final = ("content-type", "accept")
_RESPONSE_HEADERS: Final = ("content-type", "x-request-id", "retry-after", "cache-control")


def _gateway_error(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"error": {"message": message}})


def _forward_headers(request: Request, settings: GatewaySettings) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {settings.model_api_key}"}
    for header in _REQUEST_HEADERS:
        value = request.headers.get(header)
        if value:
            headers[header] = value
    return headers


def _response_headers(response: httpx.Response) -> dict[str, str]:
    return {
        header: response.headers[header]
        for header in _RESPONSE_HEADERS
        if header in response.headers
    }


def create_app(
    settings: GatewaySettings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> FastAPI:
    settings = settings or GatewaySettings()
    app = FastAPI(title="RealityOS Meta Gateway", version="0.1.0", docs_url=None, redoc_url=None)
    app.state.settings = settings
    app.state.transport = transport

    async def forward(request: Request, path: str) -> Response:
        supplied_token = request.headers.get("X-RealityOS-Gateway-Token", "")
        if not hmac.compare_digest(supplied_token, settings.meta_gateway_token):
            return _gateway_error(401, "Invalid gateway token.")

        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit() and int(content_length) > settings.gateway_max_request_bytes:
            return _gateway_error(413, "Gateway request exceeds the configured size limit.")

        forwarded_bytes = 0

        async def limited_body():
            nonlocal forwarded_bytes
            async for chunk in request.stream():
                forwarded_bytes += len(chunk)
                if forwarded_bytes > settings.gateway_max_request_bytes:
                    raise ValueError("Gateway request exceeds the configured size limit.")
                yield chunk

        upstream_url = f"{str(settings.meta_api_base_url).rstrip('/')}/{path}"
        try:
            async with httpx.AsyncClient(
                timeout=settings.gateway_timeout_seconds,
                follow_redirects=False,
                transport=app.state.transport,
            ) as client:
                upstream_request = client.build_request(
                    request.method,
                    upstream_url,
                    headers=_forward_headers(request, settings),
                    content=limited_body(),
                )
                upstream = await client.send(upstream_request, stream=True)
                await upstream.aread()
        except ValueError:
            return _gateway_error(413, "Gateway request exceeds the configured size limit.")
        except httpx.HTTPError:
            logger.warning("Meta upstream unavailable path=%s method=%s", path, request.method)
            return _gateway_error(502, "Meta upstream is unavailable.")

        logger.info(
            "Meta request complete path=%s method=%s status=%s bytes=%s request_id=%s",
            path,
            request.method,
            upstream.status_code,
            forwarded_bytes,
            upstream.headers.get("x-request-id", ""),
        )
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=_response_headers(upstream),
        )

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/models", include_in_schema=False)
    async def models(request: Request) -> Response:
        return await forward(request, "models")

    @app.post("/v1/responses", include_in_schema=False)
    async def responses(request: Request) -> Response:
        return await forward(request, "responses")

    @app.post("/v1/asr/transcribe", include_in_schema=False)
    async def transcribe(request: Request) -> Response:
        return await forward(request, "asr/transcribe")

    @app.post("/v1/files", include_in_schema=False)
    async def files(request: Request) -> Response:
        return await forward(request, "files")

    @app.delete("/v1/files/{file_id}", include_in_schema=False)
    async def delete_file(file_id: str, request: Request) -> Response:
        return await forward(request, f"files/{file_id}")

    return app


def app_factory() -> FastAPI:
    """Uvicorn factory so imports do not require production secrets."""

    return create_app()
