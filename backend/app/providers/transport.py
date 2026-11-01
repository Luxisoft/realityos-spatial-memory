"""Bounded JSON/SSE inference transport; permanent requests are never repeated."""

import json
import time

import httpx

from app.providers.contracts import MetaProviderError

TRANSIENT = {408, 429, 500, 502, 503, 504}


def failure(client, response, phase):
    return MetaProviderError(
        f"Meta Model API returned {response.status_code}: {client._safe_error(response)}",
        status_code=response.status_code,
        phase=phase,
        retryable=response.status_code in TRANSIENT,
    )


def request_json(client, method, path, **kwargs):
    headers = client.headers | kwargs.pop("headers", {})
    phase = kwargs.pop("_phase", None) or kwargs.get("json", {}).get("model", "request")
    last = None
    for attempt in range(client.settings.meta_max_retries + 1):
        try:
            response = httpx.request(
                method,
                f"{client.base_url}/{path.lstrip('/')}",
                headers=headers,
                timeout=client.settings.meta_timeout_seconds,
                **kwargs,
            )
            if response.status_code < 400:
                return response
            last = failure(client, response, phase)
            if not last.retryable:
                raise last
        except httpx.HTTPError as exc:
            last = MetaProviderError("Meta connection failed.", phase=phase, retryable=True)
            last.__cause__ = exc
        if attempt < client.settings.meta_max_retries:
            time.sleep(0.35 * (2**attempt))
    raise last or MetaProviderError("Meta request failed.", phase=phase)


def request_events(client, body):
    last = None
    for attempt in range(client.settings.meta_max_retries + 1):
        accepted = False
        try:
            with httpx.stream(
                "POST",
                f"{client.base_url}/responses",
                headers=client.headers | {"Accept": "text/event-stream"},
                timeout=client.settings.meta_timeout_seconds,
                json=body,
            ) as response:
                if response.status_code >= 400:
                    response.read()
                    last = failure(client, response, "sam_localization")
                    if not last.retryable:
                        raise last
                else:
                    accepted = True
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
                                raise MetaProviderError(
                                    "SAM stream reported a failure.", phase="sam_localization"
                                )
                            completed |= event.get("type") == "response.completed"
                            events.append(event)
                    if not completed:
                        raise MetaProviderError(
                            "SAM stream did not complete.", phase="sam_localization", retryable=True
                        )
                    return events
        except (httpx.HTTPError, json.JSONDecodeError) as exc:
            last = MetaProviderError(
                "SAM connection or stream failed.", phase="sam_localization", retryable=True
            )
            last.__cause__ = exc
        # An accepted stream is uncertain: a later explicit attempt may resume it.
        if accepted:
            raise last or MetaProviderError(
                "SAM stream incomplete.", phase="sam_localization", retryable=True
            )
        if attempt < client.settings.meta_max_retries:
            time.sleep(0.35 * (2**attempt))
    raise last or MetaProviderError("SAM request failed.", phase="sam_localization")
