from __future__ import annotations

import asyncio
from collections.abc import Generator

import httpx
import pytest
from app.config import Settings
from app.db import Base
from app.main import create_app
from app.models import User
from app.security import hash_password

pytest_plugins = ["postgres_support"]


class APIClient:
    """Synchronous test wrapper around HTTPX's in-process ASGI transport."""

    def __init__(self, app) -> None:
        self.app = app

    def request(self, method: str, path: str, **kwargs):
        async def send():
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(
                transport=transport, base_url="http://testserver"
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())

    def get(self, path: str, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs):
        return self.request("POST", path, **kwargs)


@pytest.fixture(autouse=True)
def isolate_provider_credentials(monkeypatch):
    # A production checkout must never lend its real credentials to unit tests.
    for key, value in {
        "META_CONNECTION_MODE": "direct",
        "META_GATEWAY_FALLBACK_ENABLED": "false",
        "MODEL_API_KEY": "unit-test-placeholder-key",
        "META_GATEWAY_TOKEN": "",
        "ELEVENLABS_API_KEY": "unit-test-placeholder-key",
    }.items():
        monkeypatch.setenv(key, value)


@pytest.fixture
def client(tmp_path, monkeypatch) -> Generator[APIClient, None, None]:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'realityos-test.db'}",
        jwt_secret="test-secret-that-is-long-enough-for-local-validation",
        meta_mode="mock",
        enqueue_processing=False,
        cors_origins="http://localhost:5173",
    )
    # Indexing is tested directly; API fixtures must not contact a live broker.
    monkeypatch.setattr(
        "app.tasks.index_gallery_media.delay", lambda *args, **kwargs: None
    )
    app = create_app(settings)
    Base.metadata.create_all(app.state.database.engine)
    with app.state.database.session_factory() as db:
        db.add(
            User(
                email="admin@example.test",
                display_name="Admin Demo",
                password_hash=hash_password("VerySecurePass123!"),
            )
        )
        db.commit()
    yield APIClient(app)
    Base.metadata.drop_all(app.state.database.engine)


@pytest.fixture
def auth_headers(client: APIClient) -> dict[str, str]:
    response = client.post(
        "/v1/auth/login",
        json={"email": "admin@example.test", "password": "VerySecurePass123!"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def evaluation(tmp_path, request, monkeypatch):
    from app.local import bootstrap
    from test_local_access import local_settings

    app = create_app(
        local_settings(tmp_path, local_evaluation_enabled=True, elevenlabs_api_key=None)
    )
    try:
        Base.metadata.create_all(app.state.database.engine)
        baseline = getattr(request, "param", "current") == "baseline"
        with monkeypatch.context() as configuration:
            if baseline:
                configuration.setattr(bootstrap, "DATA_UPDATES", ())
            with app.state.database.session_factory() as db:
                result = bootstrap.seed_evaluation(db, app.state.settings)
                assert result == {
                    "initialized": True,
                    "groups": 3,
                    "users": 9,
                    "records": 28 if baseline else 34,
                    "attachments": 20 if baseline else 26,
                    "publications": 29 if baseline else 41,
                    "updates": {}
                    if baseline
                    else {
                        "group-videos-v1": {"publications": 6},
                        "police-records-v2": {"publications": 6},
                    },
                }
                db.commit()
        yield APIClient(app)
    finally:
        app.state.database.engine.dispose()
        (tmp_path / "local.db").unlink(missing_ok=True)
