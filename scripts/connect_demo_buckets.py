"""Prepare private bucket connections for the existing scenario and QA accounts.

Run on the backend host with DATABASE_URL and STORAGE_ENCRYPTION_KEY configured.
Default is a read-only account check; --apply also requires read-only S3 credentials.
Accounts, memberships and biometric data are preserved. Changing an existing demo
source retires its imported copies through the standard connection lifecycle.
"""

import argparse
import json
from pathlib import Path

from sqlalchemy import or_, select

WORKSPACES = {
    "police": "Pacific Ridge Police Department",
    "nursing": "California Valley Medical Center",
    "memory": "Sonoran Neurological Institute",
}

PRINCIPALS = {
    "police": ("alex-rivera", "maya-johnson", "daniel-kim"),
    "nursing": ("elena-marquez", "mateo-rios", "sarah-chen"),
    "memory": ("noah-brooks", "lucia-vega", "owen-patel"),
    "qa": (
        "qa-hackathon-admin",
        "qa-hackathon-member",
        "qa-hackathon-reader",
        "qa-hackathon-outsider",
    ),
}


def prepare(db, settings, credentials=None):
    from app.accounts.models import PasswordAccount
    from app.models import User, Workspace, WorkspaceMember
    from app.storage.client import BucketClient
    from app.storage.lifecycle import retire_connection
    from app.storage.models import StorageConnection, StorageSync
    from app.storage.routes import configure, enable_default_sync
    from app.storage.schemas import ConnectionInput

    if credentials and db.scalar(
        select(StorageSync.id).where(
            StorageSync.enabled.is_(True),
            StorageSync.prefix.like("demo/v2/%/evaluation-%/"),
        )
    ):
        raise ValueError(
            "Versioned evaluation sources are active; use renew_evaluation_videos.py"
        )
    prepared = []
    # Validate every account before changing any connection.
    for group, usernames in PRINCIPALS.items():
        for username in usernames:
            user = db.scalar(
                select(User)
                .join(PasswordAccount, PasswordAccount.user_id == User.id)
                .where(
                    PasswordAccount.username == username,
                    User.is_active.is_(True),
                )
            )
            if not user or user.is_guest:
                raise ValueError(f"Prepare the existing demo account first: {username}")
            prepared.append((user, username, group))
    results = []
    for user, username, group in prepared:
        prefix = (
            f"demo/v1/{group}/" if group == "qa" else f"demo/v2/{group}/{username}/"
        )
        if credentials:
            payload = ConnectionInput(
                name={
                    "police": "Archivo policial",
                    "nursing": "Archivo de enfermería",
                    "memory": "Archivo de seguimiento",
                    "qa": "Archivo del equipo",
                }[group],
                provider="r2",
                prefix=prefix,
                endpoint=credentials["endpoint"],
                bucket=credentials["bucket"],
                region=credentials.get("region", "auto"),
                access_key=credentials["access_key"],
                secret_key=credentials["secret_key"],
            )
            workspace = (
                db.scalar(
                    select(Workspace)
                    .join(WorkspaceMember)
                    .where(
                        WorkspaceMember.user_id == user.id,
                        Workspace.name == WORKSPACES.get(group),
                    )
                )
                if group != "qa"
                else None
            )
            if group != "qa" and workspace is None:
                raise ValueError(f"Existing group membership required: {username}")
            trial = StorageConnection(owner_id=user.id)
            configure(trial, payload, settings)
            page = BucketClient(trial, settings).objects()
            if not page["items"]:
                raise ValueError(f"Upload and verify the demo prefix first: {prefix}")
            row = db.scalar(
                select(StorageConnection)
                .where(
                    StorageConnection.owner_id == user.id,
                    StorageConnection.endpoint == payload.endpoint,
                    StorageConnection.bucket == payload.bucket,
                    or_(
                        StorageConnection.prefix == prefix,
                        StorageConnection.prefix == f"demo/v1/{group}/",
                    ),
                    StorageConnection.active.is_(True),
                )
                .with_for_update()
            )
            if row is None:
                row = StorageConnection(owner_id=user.id)
                db.add(row)
            elif row.prefix != prefix:
                retire_connection(db, row)
            configure(row, payload, settings)
            if workspace:
                row.workspace_id = workspace.id
            db.flush()
            if workspace:
                enable_default_sync(db, row)
            if group == "qa":
                for legacy in db.scalars(
                    select(StorageConnection).where(
                        StorageConnection.owner_id == user.id,
                        StorageConnection.endpoint == payload.endpoint,
                        StorageConnection.bucket == payload.bucket,
                        StorageConnection.prefix == "demo/v1/social-directory/",
                        StorageConnection.active.is_(True),
                    )
                ):
                    retire_connection(db, legacy)
                    legacy.active, legacy.secret = False, ""
        results.append(
            {"username": username, "prefix": prefix, "connected": bool(credentials)}
        )
    return results


def main():
    from app.config import get_settings
    from app.db import Database

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--read-credentials-file", type=Path)
    args = parser.parse_args()
    if args.apply and not args.read_credentials_file:
        parser.error(
            "--apply requires --read-credentials-file with list/read permission"
        )
    credentials = (
        json.loads(args.read_credentials_file.read_text()) if args.apply else None
    )
    settings = get_settings()
    with Database(settings.database_url).session_factory() as db:
        results = prepare(db, settings, credentials)
        if args.apply:
            db.commit()
        print(json.dumps({"applied": args.apply, "accounts": results}, indent=2))


if __name__ == "__main__":
    main()
