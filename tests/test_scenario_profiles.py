"""Profile preparation is confined to existing accounts and preserves private data."""

import importlib.util
from pathlib import Path

import pytest
from app.accounts.models import PasswordAccount
from app.models import MediaAsset, MediaKind, Role, User, Workspace, WorkspaceMember
from app.social_features.models import UserProfile
from sqlalchemy import func, select

ROOT = Path(__file__).resolve().parents[1]


def script():
    spec = importlib.util.spec_from_file_location(
        "scenario_profiles", ROOT / "scripts/complete_scenario_profiles.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepared(db, module):
    groups = {}
    profiles = []
    for username, name in module.ACCOUNTS.items():
        user = User(
            email=f"{username}@jury.example.test",
            display_name=username,
            password_hash="unchanged-password-hash",
        )
        db.add(user)
        db.flush()
        if name not in groups:
            groups[name] = Workspace(name=name, created_by_id=user.id)
            db.add(groups[name])
            db.flush()
        group = groups[name]
        db.add(PasswordAccount(user_id=user.id, username=username))
        db.add(
            WorkspaceMember(workspace_id=group.id, user_id=user.id, role=Role.REGISTER)
        )
        avatar = MediaAsset(
            workspace_id=group.id,
            kind=MediaKind.IMAGE,
            mime_type="image/png",
            original_bytes=b"avatar-original",
            sha256=username,
            byte_size=15,
        )
        db.add(avatar)
        db.flush()
        profile = UserProfile(
            user_id=user.id,
            avatar_media_id=avatar.id,
            cv_bytes=b"private-cv",
            cv_status="ready",
            cv_context="Existing private analysis",
        )
        db.add(profile)
        profiles.append(profile)
    db.commit()
    return profiles


def test_scope_preservation_idempotency_and_safe_rollback(client):
    module = script()
    fixture = module.read_fixture(ROOT / "simulator/profiles/accounts.json")
    with client.app.state.database.session_factory() as db:
        profiles = prepared(db, module)
        outsider = User(
            email="unrelated@example.test",
            display_name="Unrelated",
            password_hash="keep",
        )
        db.add(outsider)
        db.flush()
        untouched = UserProfile(user_id=outsider.id, biography="Owner's biography")
        db.add(untouched)
        db.commit()
        original = {
            p.user_id: (module.snapshot(p), p.avatar_media_id) for p in profiles
        }
        counts = [
            db.scalar(select(func.count()).select_from(model))
            for model in (User, Workspace, WorkspaceMember)
        ]
        changes = module.plan(db, fixture)
        module.apply_changes(db, changes)
        db.commit()
        assert module.plan(db, fixture) == []
        assert untouched.biography == "Owner's biography"
        for profile in profiles:
            assert profile.avatar_media_id == original[profile.user_id][1]
            assert profile.cv_bytes == b"private-cv" and profile.cv_status == "ready"
            assert profile.cv_context == "Existing private analysis"
            assert (
                db.get(User, profile.user_id).password_hash == "unchanged-password-hash"
            )
        assert counts == [
            db.scalar(select(func.count()).select_from(model))
            for model in (User, Workspace, WorkspaceMember)
        ]
        profiles[0].biography = "New owner edit"
        db.commit()
        with pytest.raises(ValueError, match="changed since planning"):
            module.apply_changes(db, changes, rollback=True)
        assert profiles[0].biography == "New owner edit"
        profiles[0].biography = changes[0]["after"]["biography"]
        db.commit()
        module.apply_changes(db, changes, rollback=True)
        db.commit()
        assert all(module.snapshot(p) == original[p.user_id][0] for p in profiles)


def test_missing_membership_never_creates_or_moves_accounts(client):
    module = script()
    fixture = module.read_fixture(ROOT / "simulator/profiles/accounts.json")
    with client.app.state.database.session_factory() as db:
        profiles = prepared(db, module)
        membership = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.user_id == profiles[-1].user_id
            )
        )
        db.delete(membership)
        db.commit()
        counts = [
            db.scalar(select(func.count()).select_from(model))
            for model in (User, Workspace, WorkspaceMember)
        ]
        with pytest.raises(ValueError, match="work group"):
            module.plan(db, fixture)
        assert all(not p.biography for p in profiles)
        assert counts == [
            db.scalar(select(func.count()).select_from(model))
            for model in (User, Workspace, WorkspaceMember)
        ]
