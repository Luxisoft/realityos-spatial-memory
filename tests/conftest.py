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


@pytest.fixture
def client(tmp_path) -> Generator[APIClient, None, None]:
    settings = Settings(
        database_url=f"sqlite:///{tmp_path / 'realityos-test.db'}",
        jwt_secret="test-secret-that-is-long-enough-for-local-validation",
        meta_mode="mock",
        enqueue_processing=False,
        cors_origins="http://localhost:5173",
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
