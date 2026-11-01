"""Local setup uses real engines and its own empty account database."""

from sqlalchemy import select

from app.models import Role, User, Workspace, WorkspaceMember, Zone
from app.security import hash_password, verify_password


def validate_local_settings(settings):
    if settings.environment != "local":
        return
    if settings.meta_mode != "live" or settings.face_engine != "insightface":
        raise ValueError("Local installations require META_MODE=live and FACE_ENGINE=insightface.")
    if not settings.tts_service_url or not settings.tts_service_token:
        raise ValueError("Local installations require a real speech service and its token.")
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
