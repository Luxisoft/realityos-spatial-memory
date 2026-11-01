from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import (
    delete,
    select,
    update,
)
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.models import (
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from app.social_features.models import FacebookIdentity, GroupInvite, Publication, Report
from app.social_features.schemas import GroupAction, InvitePermission, PinJoin

"""Facebook identities and explicitly shared audiovisual publications."""


router = APIRouter()


def is_moderator(user: User, db: Session, request: Request) -> bool:

    subjects = {
        x.strip()
        for x in request.app.state.settings.social_moderator_facebook_ids.split(",")
        if x.strip()
    }
    identity = db.scalar(select(FacebookIdentity).where(FacebookIdentity.user_id == user.id))
    prefix = f"{request.app.state.settings.facebook_app_id}:"
    return (
        identity is not None
        and identity.subject.startswith(prefix)
        and identity.subject[len(prefix) :] in subjects
    )


@router.get("/me/social-capabilities")
def capabilities(
    request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return {"moderator": is_moderator(user, db, request)}


@router.get("/groups/{workspace_id}/members")
def members(
    workspace_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    _require_inviter(workspace_id, user, db)
    workspace = db.get(Workspace, workspace_id)
    rows = db.execute(
        select(User, WorkspaceMember)
        .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == workspace_id)
    ).all()
    return [
        {
            "id": str(u.id),
            "name": u.display_name,
            "role": m.role.value,
            "self": u.id == user.id,
            "can_invite": bool(m.can_invite),
            "creator": workspace is not None and u.id == workspace.created_by_id,
        }
        for u, m in rows
    ]


@router.post("/groups/{workspace_id}/members/{member_id}/invite-permission")
def set_invite_permission(
    workspace_id: uuid.UUID,
    member_id: uuid.UUID,
    payload: InvitePermission,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    workspace_member(workspace_id, user, db, {Role.ADMIN})
    target = db.get(User, member_id)
    member = workspace_member(workspace_id, target, db) if target is not None else None
    if member is None:
        raise HTTPException(404, "Member unavailable.")
    member.can_invite = bool(payload.allowed)
    return {"ok": True, "can_invite": member.can_invite}


@router.post("/groups/{workspace_id}/members/{member_id}/remove")
def remove_member(
    workspace_id: uuid.UUID,
    member_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    _require_inviter(workspace_id, user, db)
    member = (
        workspace_member(workspace_id, db.get(User, member_id), db)
        if db.get(User, member_id)
        else None
    )
    if member is None:
        raise HTTPException(404, "Member unavailable.")
    if member.role == Role.ADMIN:
        raise HTTPException(409, "Administrators cannot be removed here.")
    db.delete(member)
    return {"ok": True}


@router.get("/moderation/reports")
def moderation_reports(
    request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    if not is_moderator(user, db, request):
        raise HTTPException(403, "Moderator access required.")
    return [
        {"id": str(r.id), "post_id": str(r.post_id), "reason": r.reason}
        for r in db.scalars(select(Report).order_by(Report.created_at.desc()).limit(100))
    ]


@router.post("/moderation/{post_id}/hide")
def moderate_hide(
    post_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    if not is_moderator(user, db, request):
        raise HTTPException(403, "Moderator access required.")
    post = db.get(Publication, post_id)
    if post is None:
        raise HTTPException(404, "Publication unavailable.")
    post.hidden = True
    return {"ok": True}


def _require_inviter(workspace_id: uuid.UUID, user: User, db: Session) -> WorkspaceMember:

    member = workspace_member(workspace_id, user, db)
    if member.role != Role.ADMIN and not member.can_invite:
        raise HTTPException(403, "Invite permission required.")
    return member


def _new_join_pin(db: Session) -> str:

    for _ in range(50):
        pin = "".join(secrets.choice("0123456789") for _ in range(9))
        if db.scalar(select(Workspace.id).where(Workspace.join_pin == pin)) is None:
            return pin
    raise HTTPException(503, "Could not allocate a group PIN.")


@router.post("/groups")
def create_group(
    payload: GroupAction, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    if not payload.name.strip():
        raise HTTPException(422, "Group name required.")
    workspace = Workspace(
        name=f"{payload.name.strip()}:{uuid.uuid4().hex[:8]}",
        created_by_id=user.id,
        join_pin=_new_join_pin(db),
    )
    db.add(workspace)
    db.flush()
    db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN))
    return {"id": str(workspace.id), "name": workspace.name, "join_pin": workspace.join_pin}


@router.get("/groups/{workspace_id}/pin")
def group_pin(
    workspace_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    _require_inviter(workspace_id, user, db)
    workspace = db.get(Workspace, workspace_id)
    if workspace is None or not workspace.join_pin:
        raise HTTPException(404, "Group PIN unavailable.")
    return {"workspace_id": str(workspace.id), "join_pin": workspace.join_pin}


@router.post("/groups/{workspace_id}/pin/rotate")
def rotate_group_pin(
    workspace_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    _require_inviter(workspace_id, user, db)
    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(404, "Group unavailable.")
    workspace.join_pin = _new_join_pin(db)
    db.flush()
    return {"workspace_id": str(workspace.id), "join_pin": workspace.join_pin}


@router.delete("/groups/{workspace_id}")
def delete_group(
    workspace_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    workspace = db.get(Workspace, workspace_id)
    if workspace is None:
        raise HTTPException(404, "Group unavailable.")
    if workspace.name.startswith("home:"):
        raise HTTPException(409, "Personal spaces cannot be deleted.")
    if workspace.created_by_id != user.id:
        raise HTTPException(403, "Only the group creator can delete it.")
    # Core DML in dependency order: sessions run with autoflush=False, so ORM
    # deletes across tables cannot rely on flush ordering here.
    db.execute(delete(GroupInvite).where(GroupInvite.workspace_id == workspace_id))
    db.execute(delete(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace_id))
    db.execute(
        update(Publication)
        .where(Publication.workspace_id == workspace_id)
        .values(workspace_id=None)
    )
    from app.social_features.evidence_models import PublicationUpload

    db.execute(
        update(PublicationUpload)
        .where(
            PublicationUpload.workspace_id == workspace_id,
            PublicationUpload.status.in_(["pending", "failed", "duplicate"]),
        )
        .values(status="cancelled", error="Group deleted.")
    )
    db.execute(
        update(PublicationUpload)
        .where(PublicationUpload.workspace_id == workspace_id)
        .values(workspace_id=None)
    )
    db.delete(workspace)
    db.flush()
    return {"ok": True, "workspace_id": str(workspace_id)}


@router.post("/groups/join-by-pin")
def join_by_pin(
    payload: PinJoin, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    pin = "".join(character for character in payload.pin if character.isdigit())
    workspace = (
        db.scalar(select(Workspace).where(Workspace.join_pin == pin)) if len(pin) == 9 else None
    )
    if workspace is None or workspace.name.startswith("home:"):
        raise HTTPException(404, "Invitation unavailable.")
    existing = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id, WorkspaceMember.user_id == user.id
        )
    )
    if existing is None:
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.QUERY))
    return {"workspace_id": str(workspace.id)}


@router.post("/groups/{workspace_id}/invite")
def invite(
    workspace_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    _require_inviter(workspace_id, user, db)
    for old in db.scalars(select(GroupInvite).where(GroupInvite.workspace_id == workspace_id)):
        old.active = False
    item = GroupInvite(code=secrets.token_urlsafe(32), workspace_id=workspace_id)
    db.add(item)
    return {"code": item.code}


@router.post("/groups/join")
def join(
    payload: GroupAction, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    item = db.get(GroupInvite, payload.code)
    if item is None or not item.active:
        raise HTTPException(404, "Invitation unavailable.")
    existing = db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == item.workspace_id, WorkspaceMember.user_id == user.id
        )
    )
    if existing is None:
        db.add(WorkspaceMember(workspace_id=item.workspace_id, user_id=user.id, role=Role.QUERY))
    item.active = False
    return {"workspace_id": str(item.workspace_id)}


@router.get("/groups/{workspace_id}/reports")
def reports(
    workspace_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    workspace_member(workspace_id, user, db, {Role.ADMIN})
    return [
        {"id": str(r.id), "post_id": str(r.post_id), "reason": r.reason}
        for r in db.scalars(
            select(Report)
            .join(Publication, Report.post_id == Publication.id)
            .where(Publication.workspace_id == workspace_id)
            .limit(100)
        )
    ]


@router.post("/groups/{workspace_id}/hide/{post_id}")
def hide(
    workspace_id: uuid.UUID,
    post_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    workspace_member(workspace_id, user, db, {Role.ADMIN})
    post = db.get(Publication, post_id)
    if post is None or post.workspace_id != workspace_id:
        raise HTTPException(404, "Publication unavailable.")
    post.hidden = True
    return {"ok": True}
