"""Bounded inference transport with explicit routing and safe fallback."""

import json
import logging
import time

import httpx

from app.providers.connections import (
    fallback_log,
    fallback_status,
    rewind_uploads,
    upload_positions,
)
from app.providers.contracts import MetaProviderError, MetaProviderUncertainError

TRANSIENT = {408, 429, 500, 502, 503, 504}
SAFE_REJECTION = {401, 403, 404, 429}
CONNECT_FAILURES = (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout)
logger = logging.getLogger("realityos.providers")


def failure(client, response, phase):
    return MetaProviderError(
        f"Meta Model API returned {response.status_code}: {client._safe_error(response)}",
        status_code=response.status_code,
        phase=phase,
        retryable=response.status_code in TRANSIENT,
    )


def request_json(client, method, path, **kwargs):
    extra = kwargs.pop("headers", {})
    phase = kwargs.pop("_phase", None) or kwargs.get("json", {}).get("model", "request")
    explicit_timeout = kwargs.pop("timeout", None)
    positions = upload_positions(kwargs)
    last = None
    submitted = False
    for index, route in enumerate(client.routes):
        fallback = index + 1 < len(client.routes)
        attempts = 1 if fallback else client.settings.meta_max_retries + 1
        for attempt in range(attempts):
            if submitted:
                rewind_uploads(positions)
            submitted = True
            logger.info("Meta request route=%s phase=%s", route.name, phase)
            try:
                response = httpx.request(
                    method,
                    f"{route.base_url}/{path.lstrip('/')}",
                    headers=route.request_headers(extra),
                    timeout=explicit_timeout or client.settings.meta_timeout_seconds,
                    **kwargs,
                )
                if response.status_code < 400:
                    return response
                last = failure(client, response, phase)
                if fallback and fallback_status(response.status_code):
                    fallback_log(route, response.status_code)
                    break
                if not last.retryable:
                    raise last
            except httpx.HTTPError as exc:
                last = MetaProviderError(
                    f"Meta connection failed ({type(exc).__name__}).",
                    phase=phase,
                    retryable=True,
                )
                last.__cause__ = exc
                if fallback:
                    fallback_log(route, type(exc).__name__)
                    break
            if attempt + 1 < attempts:
                time.sleep(0.35 * (2**attempt))
    raise last or MetaProviderError("Meta request failed.", phase=phase)


def request_file(client, method, path, **kwargs):
    """Switch only after a definite rejection or failure before submission."""
    extra = kwargs.pop("headers", {})
    positions = upload_positions(kwargs)
    for index, route in enumerate(client.routes):
        if index:
            rewind_uploads(positions)
        fallback = index + 1 < len(client.routes)
        logger.info("Meta file request route=%s method=%s", route.name, method)
        try:
            response = httpx.request(
                method,
                f"{route.base_url}/{path.lstrip('/')}",
                headers=route.request_headers(extra),
                timeout=client.settings.meta_video_timeout_seconds,
                **kwargs,
            )
        except CONNECT_FAILURES as exc:
            if fallback:
                fallback_log(route, type(exc).__name__)
                continue
            raise MetaProviderUncertainError("Meta video request connection failed.") from exc
        except httpx.HTTPError as exc:
            raise MetaProviderUncertainError("Meta video request connection failed.") from exc
        if fallback and response.status_code in SAFE_REJECTION:
            fallback_log(route, response.status_code)
            continue
        if response.status_code in TRANSIENT or response.status_code >= 500:
            raise MetaProviderUncertainError(
                f"Meta video request returned {response.status_code}; result state is uncertain."
            )
        if response.status_code >= 400:
            raise failure(client, response, "video_file")
        return response
    raise MetaProviderError("Meta file request failed.")


def read_events(response):
    events = []
    completed = False
    for line in response.iter_lines():
        if not line or not line.startswith("data: "):
            continue
        data = line.removeprefix("data: ")
        if data == "[DONE]":
            continue
        event = json.loads(data)
        if isinstance(event, dict):
            if event.get("type") in {"response.failed", "error"}:
                raise MetaProviderUncertainError("SAM stream reported a failure.")
            completed |= event.get("type") == "response.completed"
            events.append(event)
    if not completed:
        raise MetaProviderUncertainError("SAM stream did not complete.")
    return events


def request_events(client, body, *, once=False):
    last = None
    timeout = (
        client.settings.meta_video_timeout_seconds if once else client.settings.meta_timeout_seconds
    )
    for index, route in enumerate(client.routes):
        fallback = index + 1 < len(client.routes)
        attempts = 1 if fallback or once else client.settings.meta_max_retries + 1
        for attempt in range(attempts):
            accepted = False
            logger.info("Meta stream route=%s video=%s", route.name, once)
            try:
                with httpx.stream(
                    "POST",
                    f"{route.base_url}/responses",
                    headers=route.request_headers({"Accept": "text/event-stream"}),
                    timeout=timeout,
                    json=body,
                ) as response:
                    if response.status_code >= 400:
                        response.read()
                        can_switch = (
                            response.status_code in SAFE_REJECTION
                            if once
                            else fallback_status(response.status_code)
                        )
                        if fallback and can_switch:
                            fallback_log(route, response.status_code)
                            break
                        if once and (
                            response.status_code in TRANSIENT or response.status_code >= 500
                        ):
                            raise MetaProviderUncertainError(
                                f"Meta SAM Video returned {response.status_code}; result state is uncertain."
                            )
                        last = failure(client, response, "sam_localization")
                        if not last.retryable:
                            raise last
                    else:
                        accepted = True
                        return read_events(response)
            except (httpx.HTTPError, json.JSONDecodeError) as exc:
                if accepted or (once and not isinstance(exc, CONNECT_FAILURES)):
                    raise MetaProviderUncertainError(
                        "SAM connection or stream failed after submission."
                    ) from exc
                last = MetaProviderError(
                    "SAM connection or stream failed.", phase="sam_localization", retryable=True
                )
                last.__cause__ = exc
                if fallback:
                    fallback_log(route, type(exc).__name__)
                    break
            if attempt + 1 < attempts:
                time.sleep(0.35 * (2**attempt))
    raise last or MetaProviderError("SAM request failed.", phase="sam_localization")
