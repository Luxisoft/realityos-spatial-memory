from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import Settings, get_settings
from app.db import Database
from app.routes import router


def create_app(settings: Settings | None = None) -> FastAPI:
    runtime_settings = settings or get_settings()
    from app.local_runtime import validate_local_settings

    validate_local_settings(runtime_settings)
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
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type"],
    )
    app.include_router(router, prefix=runtime_settings.api_prefix)
    from app.storage.routes import router as storage_router

    app.include_router(storage_router, prefix=runtime_settings.api_prefix)
    from app.workspaces import clinical, media, provisioning, search, sync  # noqa: F401
    from app.workspaces.routes import router as workspace_data_router

    app.include_router(workspace_data_router, prefix=runtime_settings.api_prefix)
    from app.accounts import avatar  # noqa: F401
    from app.accounts.routes import router as accounts_router

    app.include_router(accounts_router, prefix=runtime_settings.api_prefix)
    if runtime_settings.environment == "local" and runtime_settings.local_login_enabled:
        from app.http.local_access import router as local_router

        app.include_router(local_router, prefix=runtime_settings.api_prefix)
    from app.social import router as social_router

    app.include_router(social_router, prefix=runtime_settings.api_prefix)
    from app.faces import router as faces_router

    app.include_router(faces_router, prefix=runtime_settings.api_prefix)
    from app.face_setup import router as face_setup_router

    app.include_router(face_setup_router, prefix=runtime_settings.api_prefix)

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
