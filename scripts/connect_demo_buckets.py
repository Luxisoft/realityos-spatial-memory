"""Prepare private bucket connections for the existing scenario and QA accounts.

Run on the backend host with DATABASE_URL and STORAGE_ENCRYPTION_KEY configured.
Default is a read-only account check; --apply also requires read-only S3 credentials.
No account, publication, membership or biometric data is created or changed.
"""

import argparse
import json
from pathlib import Path

from sqlalchemy import select

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
    from app.models import User
    from app.storage.client import BucketClient
    from app.storage.models import StorageConnection
    from app.storage.routes import configure
    from app.storage.schemas import ConnectionInput

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
        prefix = f"demo/v1/{group}/"
        if credentials:
            payload = ConnectionInput(
                name=f"Demo {group}",
                provider="r2",
                prefix=prefix,
                endpoint=credentials["endpoint"],
                bucket=credentials["bucket"],
                region=credentials.get("region", "auto"),
                access_key=credentials["access_key"],
                secret_key=credentials["secret_key"],
            )
            row = db.scalar(
                select(StorageConnection)
                .where(
                    StorageConnection.owner_id == user.id,
                    StorageConnection.endpoint == payload.endpoint,
                    StorageConnection.bucket == payload.bucket,
                    StorageConnection.prefix == prefix,
                    StorageConnection.active.is_(True),
                )
                .with_for_update()
            )
            if row is None:
                row = StorageConnection(owner_id=user.id)
                db.add(row)
            configure(row, payload, settings)
            page = BucketClient(row, settings).objects()
            if not page["items"]:
                raise ValueError(f"Upload and verify the demo prefix first: {prefix}")
            db.flush()
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
