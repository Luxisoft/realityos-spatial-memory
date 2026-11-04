"""Populate the nine existing scenario profiles; never create accounts or groups.

Dry run by default. Apply saves a private, field-level rollback journal before
committing. Public profile validation is shared with the authenticated API.
"""

import argparse
import json
import os
from datetime import date
from pathlib import Path

from app.accounts.models import PasswordAccount
from app.config import get_settings
from app.db import Database
from app.models import User, Workspace, WorkspaceMember
from app.social_features.models import FacebookIdentity, UserProfile
from app.social_features.profiles import update_profile
from app.social_features.schemas import ProfileUpdate
from sqlalchemy import select

GROUPS = {
    "Pacific Ridge Police Department": ("alex-rivera", "maya-johnson", "daniel-kim"),
    "California Valley Medical Center": ("elena-marquez", "mateo-rios", "sarah-chen"),
    "Sonoran Neurological Institute": ("noah-brooks", "lucia-vega", "owen-patel"),
}
ACCOUNTS = {name: group for group, names in GROUPS.items() for name in names}
FIELDS = {
    "headline",
    "biography",
    "phone",
    "website",
    "social_links",
    "birthday",
    "gender",
    "hometown",
    "location",
}


def read_fixture(path):
    document = json.loads(Path(path).read_text())
    accounts = document["accounts"]
    if document.get("synthetic") is not True or len(accounts) != len(ACCOUNTS):
        raise ValueError("Expected the nine authorized fictional profiles.")
    if {item["username"] for item in accounts} != set(ACCOUNTS):
        raise ValueError("Only the existing nine scenario accounts are allowed.")
    for item in accounts:
        if (
            item["workspace"] != ACCOUNTS[item["username"]]
            or set(item["fields"]) != FIELDS
        ):
            raise ValueError("Unexpected workspace or profile fields.")
        ProfileUpdate.model_validate(item["fields"])
    return accounts


def snapshot(profile):
    return {
        field: value.isoformat()
        if isinstance(value := getattr(profile, field), date)
        else value
        for field in sorted(FIELDS)
    }


def target(db, username):
    user = db.scalar(
        select(User)
        .join(PasswordAccount, PasswordAccount.user_id == User.id)
        .where(PasswordAccount.username == username)
    )
    if (
        user is None
        or user.email != f"{username}@jury.example.test"
        or not user.is_active
        or user.is_guest
    ):
        raise ValueError(f"Existing scenario account required: {username}")
    member = db.scalar(
        select(WorkspaceMember)
        .join(Workspace)
        .where(WorkspaceMember.user_id == user.id, Workspace.name == ACCOUNTS[username])
    )
    if member is None or db.scalar(
        select(FacebookIdentity).where(FacebookIdentity.user_id == user.id)
    ):
        raise ValueError(f"Expected email account and work group: {username}")
    profile = db.scalar(
        select(UserProfile).where(UserProfile.user_id == user.id).with_for_update()
    )
    if profile is None:
        raise ValueError(f"Existing profile required: {username}")
    return user, profile


def plan(db, accounts):
    changes = []
    for item in accounts:
        user, profile = target(db, item["username"])
        before = snapshot(profile)
        after = item["fields"]
        if before != after:
            changes.append(
                {
                    "username": item["username"],
                    "user_id": str(user.id),
                    "before": before,
                    "after": after,
                }
            )
    return changes


def apply_changes(db, changes, rollback=False):
    targets = []
    for change in changes:
        if change["username"] not in ACCOUNTS:
            raise ValueError("Account is outside the authorized set.")
        if any(set(change[key]) != FIELDS for key in ("before", "after")):
            raise ValueError("Unexpected profile fields in journal.")
        user, profile = target(db, change["username"])
        expected, replacement = (
            (change["after"], change["before"])
            if rollback
            else (change["before"], change["after"])
        )
        if str(user.id) != change["user_id"] or snapshot(profile) != expected:
            raise ValueError(f"Profile changed since planning: {change['username']}")
        targets.append((user, ProfileUpdate.model_validate(replacement)))
    for user, payload in targets:
        update_profile(payload, user=user, db=db)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixture",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "simulator/profiles/accounts.json",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--rollback", type=Path)
    parser.add_argument("--journal", type=Path)
    args = parser.parse_args()
    if args.apply and args.journal is None:
        parser.error("--apply requires a private --journal path")
    database = Database(get_settings().database_url)
    with database.session_factory() as db:
        if args.rollback:
            changes = json.loads(args.rollback.read_text())["changes"]
            apply_changes(db, changes, rollback=True)
            db.commit()
        else:
            changes = plan(db, read_fixture(args.fixture))
            if args.apply:
                args.journal.parent.mkdir(parents=True, exist_ok=True)
                descriptor = os.open(
                    args.journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
                )
                with os.fdopen(descriptor, "w") as output:
                    json.dump(
                        {"operation": "scenario-profiles", "changes": changes},
                        output,
                        ensure_ascii=False,
                        indent=2,
                    )
                    output.write("\n")
                apply_changes(db, changes)
                db.commit()
        print(
            json.dumps(
                {
                    "mode": "rollback"
                    if args.rollback
                    else "apply"
                    if args.apply
                    else "preview",
                    "profiles": len(changes),
                    "accounts": [item["username"] for item in changes],
                }
            )
        )


if __name__ == "__main__":
    main()
