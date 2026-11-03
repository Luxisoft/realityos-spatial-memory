"""Explicitly provision the public Postman account and its empty query-only workspace.

No email, media, provider requests, existing user changes or schema creation.
"""

import argparse
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.accounts.models import PasswordAccount
from app.models import Role, User, Workspace, WorkspaceMember
from app.security import hash_password, verify_password
from sqlalchemy import or_, select


def provision(db, settings, realm, fixture):
    if realm not in {"server", "localhost"}:
        raise ValueError("Unknown Postman realm.")
    is_local = settings.environment == "local"
    if (realm == "localhost") != is_local or (
        is_local and not settings.local_login_enabled
    ):
        raise ValueError("The Postman realm must match the backend installation.")
    data = fixture[realm]
    user_id = uuid.UUID(data["user_id"])
    workspace_id = uuid.UUID(data["workspace_id"])
    user = db.scalar(
        select(User).where(or_(User.id == user_id, User.email == data["email"]))
    )
    workspace = db.scalar(
        select(Workspace).where(
            or_(Workspace.id == workspace_id, Workspace.name == data["workspace_name"])
        )
    )
    account = db.scalar(
        select(PasswordAccount).where(
            or_(
                PasswordAccount.user_id == user_id,
                PasswordAccount.username == data["username"],
            )
        )
    )
    if any((user, workspace, account)):
        memberships = list(
            db.scalars(
                select(WorkspaceMember).where(WorkspaceMember.user_id == user_id)
            )
        )
        if not (
            user
            and user.id == user_id
            and user.email == data["email"]
            and user.is_active
            and not user.is_guest
            and verify_password(data["password"], user.password_hash)
            and workspace
            and workspace.id == workspace_id
            and workspace.name == data["workspace_name"]
            and workspace.created_by_id == user_id
            and account
            and account.user_id == user_id
            and account.username == data["username"]
            and account.provisioned_by == user_id
            and account.verified_at
            and len(memberships) == 1
            and memberships[0].workspace_id == workspace_id
            and memberships[0].role == Role.QUERY
            and not memberships[0].can_invite
        ):
            raise ValueError(
                "Existing data differs from the isolated demo; nothing was changed."
            )
        return {
            "created": False,
            "realm": realm,
            "user_id": str(user_id),
            "workspace_id": str(workspace_id),
        }
    db.add(
        User(
            id=user_id,
            email=data["email"],
            display_name=data["display_name"],
            password_hash=hash_password(data["password"]),
            is_active=True,
        )
    )
    db.flush()
    db.add(
        PasswordAccount(
            user_id=user_id,
            username=data["username"],
            provisioned_by=user_id,
            verified_at=datetime.now(UTC),
        )
    )
    db.add(
        Workspace(
            id=workspace_id,
            name=data["workspace_name"],
            description="Espacio de trabajo de Postman.",
            created_by_id=user_id,
        )
    )
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace_id, user_id=user_id, role=Role.QUERY))
    db.flush()
    return {
        "created": True,
        "realm": realm,
        "user_id": str(user_id),
        "workspace_id": str(workspace_id),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--realm", choices=["server", "localhost"], required=True)
    parser.add_argument("--apply", action="store_true", required=True)
    args = parser.parse_args()
    # Import app only for the explicit operator command, never during docs generation.
    from app.main import app

    with app.state.database.session_factory() as db:
        result = provision(
            db,
            app.state.settings,
            args.realm,
            json.loads(Path(__file__).with_name("demo.json").read_text()),
        )
        db.commit()
    print(json.dumps(result))
