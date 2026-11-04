"""Database-backed selector access. No fixture files or implicit eligibility."""

from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import PasswordAccount
from app.local_models import LocalAccessAccount
from app.models import User, Workspace, WorkspaceMember
from app.social_features.models import UserProfile


def selected_account(db: Session, user_id: UUID, *, require_membership: bool = False):
    query = (
        select(User, Workspace)
        .join(LocalAccessAccount, LocalAccessAccount.user_id == User.id)
        .join(Workspace, Workspace.id == LocalAccessAccount.workspace_id)
        .where(User.id == user_id, User.is_active.is_(True), LocalAccessAccount.enabled.is_(True))
    )
    if require_membership:
        query = query.join(
            WorkspaceMember,
            (WorkspaceMember.workspace_id == Workspace.id) & (WorkspaceMember.user_id == User.id),
        )
    row = db.execute(query).first()
    if row is None:
        raise HTTPException(404, "Local account unavailable.")
    return row


def list_accounts(db: Session) -> list[dict]:
    rows = db.execute(
        select(User, Workspace, PasswordAccount.username, UserProfile.avatar_media_id)
        .join(LocalAccessAccount, LocalAccessAccount.user_id == User.id)
        .join(Workspace, Workspace.id == LocalAccessAccount.workspace_id)
        .join(PasswordAccount, PasswordAccount.user_id == User.id)
        .join(
            WorkspaceMember,
            (WorkspaceMember.workspace_id == Workspace.id) & (WorkspaceMember.user_id == User.id),
        )
        .outerjoin(UserProfile, UserProfile.user_id == User.id)
        .where(User.is_active.is_(True), LocalAccessAccount.enabled.is_(True))
        .order_by(LocalAccessAccount.position, User.id)
    )
    return [
        {
            "id": str(user.id),
            "display_name": user.display_name,
            "username": username,
            "workspace_id": str(workspace.id),
            "workspace_name": workspace.name,
            "picture_url": f"/v1/auth/local-accounts/{user.id}/avatar" if avatar else None,
        }
        for user, workspace, username, avatar in rows
    ]
