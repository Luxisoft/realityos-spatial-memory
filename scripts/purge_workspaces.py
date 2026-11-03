"""Exact-scope workspace purge. Dry run by default, transactional, protects identity data.

Use only after a reversible technical snapshot and successful replacement import.
"""

import argparse
import json
import uuid
from datetime import UTC, datetime

from app.config import Settings
from app.db import Database
from app.models import CaptureSession, MediaAsset, Workspace
from app.social_features.models import Publication
from app.social_features.upload_service import home_space
from sqlalchemy import MetaData, delete, or_, select, tuple_, update

PROTECTED = {
    "users",
    "password_accounts",
    "facebook_identities",
    "facebook_profiles",
    "user_profiles",
    "face_enrollments",
    "biometric_consents",
    "refresh_tokens",
    "account_challenges",
}


def condition(table, keys):
    columns = list(table.primary_key.columns)
    if not columns:
        raise RuntimeError(f"Table without primary key: {table.name}")
    if len(columns) == 1:
        return columns[0].in_([key[0] for key in keys])
    return tuple_(*columns).in_(list(keys))


def purge(db, workspace_ids, apply=False):
    targets = {uuid.UUID(str(value)) for value in workspace_ids}
    spaces = list(db.scalars(select(Workspace).where(Workspace.id.in_(targets))))
    if len(spaces) != len(targets) or any(s.name.startswith("home:") for s in spaces):
        raise RuntimeError("All targets must be existing non-personal workspaces.")
    # A personal publication sharing an old asset keeps its bytes and ancestry.
    shared = list(
        db.execute(
            select(MediaAsset.id, Publication.owner_id)
            .join(Publication, Publication.media_id == MediaAsset.id)
            .where(
                MediaAsset.workspace_id.in_(targets),
                or_(
                    Publication.workspace_id.is_(None),
                    Publication.workspace_id.not_in(targets),
                ),
            )
        )
    )
    preserved = set()
    for media_id, owner in shared:
        destination = home_space(db, owner)
        cursor = media_id
        while cursor and cursor not in preserved:
            asset = db.get(MediaAsset, cursor)
            if asset is None:
                break
            preserved.add(asset.id)
            asset.workspace_id = destination
            if asset.capture_session_id:
                session = db.get(CaptureSession, asset.capture_session_id)
                session.workspace_id = destination
                session.zone_id = None
                session.device_id = None
                session.device_assignment_id = None
            cursor = asset.parent_asset_id
    db.flush()
    metadata = MetaData()
    metadata.reflect(bind=db.get_bind())
    selected = {"workspaces": {(value,) for value in targets}}
    changed = True
    while changed:
        changed = False
        for table in metadata.tables.values():
            clauses = []
            for fk in table.foreign_keys:
                parent = fk.column.table
                keys = selected.get(parent.name)
                if not keys:
                    continue
                values = select(fk.column).where(condition(parent, keys))
                clauses.append(fk.parent.in_(values))
            if not clauses:
                continue
            keys = set(
                db.execute(
                    select(*table.primary_key.columns).where(or_(*clauses))
                ).all()
            )
            if keys and table.name in PROTECTED:
                raise RuntimeError(
                    f"Purge would affect protected identity table {table.name}; aborting."
                )
            new = keys - selected.get(table.name, set())
            if new:
                selected.setdefault(table.name, set()).update(new)
                changed = True
    report = {
        "workspaces": [{"id": str(s.id), "name": s.name} for s in spaces],
        "preserved_media": [str(i) for i in preserved],
        "rows": {name: len(keys) for name, keys in sorted(selected.items())},
        "applied": apply,
        "at": datetime.now(UTC).isoformat(),
    }
    # Determine the complete deletion order before mutating any selected rows.
    pending = set(selected)
    order = []
    while pending:
        sinks = []
        for name in pending:
            dependent = False
            for other in pending:
                for fk in metadata.tables[other].foreign_keys:
                    if (
                        fk.column.table.name == name
                        and not fk.parent.nullable
                        and other != name
                    ):
                        dependent = True
            if not dependent:
                sinks.append(name)
        if not sinks:
            raise RuntimeError("Non-null dependency cycle; explicit handling required.")
        order.extend(sorted(sinks))
        pending.difference_update(sinks)
    if apply:
        # Break nullable cycles only within rows already selected for deletion.
        for name, keys in selected.items():
            table = metadata.tables[name]
            columns = {
                fk.parent.name: None
                for fk in table.foreign_keys
                if fk.parent.nullable and fk.column.table.name in selected
            }
            if columns:
                db.execute(
                    update(table).where(condition(table, keys)).values(**columns)
                )
        for name in order:
            table = metadata.tables[name]
            db.execute(delete(table).where(condition(table, selected[name])))
        db.commit()
    else:
        db.rollback()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace_ids", nargs="+")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    database = Database(Settings().database_url)
    with database.session_factory() as db:
        print(json.dumps(purge(db, args.workspace_ids, args.apply), indent=2))


if __name__ == "__main__":
    main()
