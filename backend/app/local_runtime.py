"""Local installation constraints; the processing providers remain real."""

from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.engine import make_url

from app.models import Role, User, Workspace, WorkspaceMember, Zone
from app.security import hash_password, verify_password


def validate_local_settings(settings):
    if settings.environment != "local":
        return
    if settings.meta_mode != "live" or settings.face_engine != "insightface":
        raise ValueError("Local installations require META_MODE=live and FACE_ENGINE=insightface.")
    if settings.meta_connection_mode != "direct" or settings.meta_gateway_fallback_enabled:
        raise ValueError("Local installations connect directly to Meta; gateways are disabled.")
    if urlsplit(str(settings.meta_api_base_url)).hostname != "api.meta.ai":
        raise ValueError("Local installations require the official Meta API endpoint.")
    if make_url(settings.database_url).host not in {
        None,
        "postgres",
        "localhost",
        "127.0.0.1",
        "::1",
    }:
        raise ValueError("Local installations require their own local database.")
    if urlsplit(settings.redis_url).hostname not in {"redis", "localhost", "127.0.0.1", "::1"}:
        raise ValueError("Local installations require a local task queue.")
    from app.providers.connections import provider_routes

    provider_routes(settings)


def create_local_account(db, settings, email, password, display_name):
    if settings.environment != "local" or not settings.local_login_enabled:
        raise ValueError("Account provisioning is restricted to the enabled local installation.")
    if not email or "@" not in email or not display_name.strip():
        raise ValueError("Provide a local account email and display name.")
    email = email.strip().casefold()
    user = db.scalar(select(User).where(User.email == email))
    created = user is None
    if created:
        user = User(
            email=email, display_name=display_name.strip(), password_hash=hash_password(password)
        )
        db.add(user)
        db.flush()
        name = "Local workspace"
        suffix = 1
        while db.scalar(select(Workspace.id).where(Workspace.name == name)) is not None:
            suffix += 1
            name = f"Local workspace ({suffix})"
        workspace = Workspace(name=name, created_by_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN))
        db.add(Zone(workspace_id=workspace.id, name="Principal", kind="zone"))
    elif not user.is_active or not verify_password(password, user.password_hash):
        raise ValueError("Existing local account credentials differ; no account was changed.")
    return {"account_created": created, "email": email}
