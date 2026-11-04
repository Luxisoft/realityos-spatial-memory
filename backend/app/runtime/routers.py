"""Application capabilities, registered before requests can reach a handler."""

from fastapi import FastAPI

from app.config import Settings


def register_routes(application: FastAPI, settings: Settings) -> None:
    from app.accounts import avatar  # noqa: F401
    from app.accounts import routes as accounts
    from app.face_setup import router as setup_router
    from app.faces import router as faces_router
    from app.routes import build_router as core_router
    from app.social import build_router as social_router
    from app.workspaces import media, provisioning, search  # noqa: F401
    from app.workspaces import routes as records

    local = settings.environment == "local"
    prefix = settings.api_prefix
    application.include_router(core_router(local=local), prefix=prefix)
    if not local:
        from app.storage.routes import router as storage_router
        from app.workspaces import sync  # noqa: F401

        application.include_router(storage_router, prefix=prefix)
        application.include_router(records.server_router, prefix=prefix)
    application.include_router(records.router, prefix=prefix)
    if not local:
        application.include_router(accounts.server_router, prefix=prefix)
    application.include_router(accounts.router, prefix=prefix)
    if local and settings.local_login_enabled:
        from app.http.local_access import router as local_router

        application.include_router(local_router, prefix=prefix)
    application.include_router(social_router(local=local), prefix=prefix)
    application.include_router(faces_router, prefix=prefix)
    application.include_router(setup_router, prefix=prefix)
