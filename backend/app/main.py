from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import Settings, get_settings
from app.db import Database
from app.routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    app = FastAPI(
        title="RealityOS API",
        version="0.1.0",
        description="Evidence-first spatial memory. Query routes never create captures.",
        openapi_url=f"{runtime_settings.api_prefix}/openapi.json",
        docs_url="/docs",
    )
    app.state.settings = runtime_settings
    app.state.database = Database(runtime_settings.database_url)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=runtime_settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(router, prefix=runtime_settings.api_prefix)

    @app.get("/health/live", tags=["system"])
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["system"])
    async def ready() -> dict[str, str]:
        with app.state.database.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ready"}

    return app


app = create_app()
