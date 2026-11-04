import asyncio
import threading
from types import SimpleNamespace

import httpx
import pytest
from app.schemas import QueryResponse


@pytest.mark.parametrize("stage", ["analysis", "answer"])
def test_image_query_keeps_health_available(client, auth_headers, monkeypatch, stage):
    workspace = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Concurrent query"}
    ).json()["id"]
    started = threading.Event()
    released = threading.Event()
    health_available = []

    def provider_wait():
        started.set()
        health_available.append(released.wait(timeout=5))

    def analyze(*args, **kwargs):
        if stage == "analysis":
            provider_wait()
        return SimpleNamespace(
            simulated=True,
            detections=[SimpleNamespace(label="keys")] if stage == "answer" else [],
        )

    def answer(*args, **kwargs):
        provider_wait()
        return QueryResponse(found=False, message="No match", tts_text="No match")

    monkeypatch.setattr(
        "app.http.queries.build_meta_client",
        lambda settings: SimpleNamespace(analyze_image=analyze),
    )
    monkeypatch.setattr("app.http.queries._answer_query", answer)

    async def exercise():
        import io

        from PIL import Image

        image = io.BytesIO()
        Image.new("RGB", (16, 16), "red").save(image, "PNG")
        transport = httpx.ASGITransport(app=client.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as api:
            query = asyncio.create_task(
                api.post(
                    "/v1/queries/image",
                    headers=auth_headers,
                    data={"workspace_id": workspace},
                    files={"image": ("probe.png", image.getvalue(), "image/png")},
                )
            )
            assert await asyncio.to_thread(started.wait, 10)
            try:
                health = await api.get("/health/live")
                assert health.status_code == 200
            finally:
                released.set()
            response = await query
            assert response.status_code == 200, response.text

    asyncio.run(exercise())
    assert health_available == [True]


def test_text_query_keeps_health_available(client, auth_headers, monkeypatch):
    workspace = client.post(
        "/v1/workspaces", headers=auth_headers, json={"name": "Concurrent text query"}
    ).json()["id"]
    started, released = threading.Event(), threading.Event()
    completed = []

    def answer(*args, **kwargs):
        started.set()
        completed.append(released.wait(timeout=5))
        return QueryResponse(found=False, message="No match", tts_text="No match")

    monkeypatch.setattr("app.http.queries._answer_query", answer)

    async def exercise():
        transport = httpx.ASGITransport(app=client.app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as api:
            pending = asyncio.create_task(
                api.post(
                    "/v1/queries",
                    headers=auth_headers,
                    json={"workspace_id": workspace, "question": "Find the keys"},
                )
            )
            assert await asyncio.to_thread(started.wait, 10)
            try:
                assert (await api.get("/health/live")).status_code == 200
            finally:
                released.set()
            assert (await pending).status_code == 200

    asyncio.run(exercise())
    assert completed == [True]
