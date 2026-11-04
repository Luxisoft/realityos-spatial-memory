"""Retire the removed local scenario without cascading into another workspace."""

import uuid

from sqlalchemy import MetaData, delete, or_, select, update

from app.local.sql_data import FIXTURES, apply_seed, seed_digest
from app.local.state import receipt, require_local
from app.local_models import LocalEvaluationState
from app.workspaces.purge import condition

RECEIPT = "retire-memory-v1"
FILENAME = "007-retire-memory.sql"
WORKSPACE = uuid.UUID("8fd12f4c-0152-5300-874d-a162e05b0830")
USERS = {
    uuid.UUID("e2547625-1c50-5379-8e4c-f7d8221074ee"),
    uuid.UUID("6330f2dc-676c-5832-88dc-47d55549a5f3"),
    uuid.UUID("c5f99273-0b59-5322-a730-7587d63e2d87"),
}
PROTECTED = {
    "biometric_consents",
    "biometric_setups",
    "biometric_publication_quarantine",
    "face_enrollments",
    "face_record_enrollments",
    "face_verifications",
}
PRIVATE_IDENTITIES = {
    "user_profiles",
    "password_accounts",
    "facebook_profiles",
    "facebook_identities",
    "facebook_media",
    "facebook_posts",
    "facebook_friends",
    "refresh_tokens",
    "account_challenges",
    "chat_messages",
    "chat_audio",
}


def _candidates(db, metadata, workspace, users):
    selected = {}
    for name, identifiers in (("workspaces", {workspace}), ("users", users)):
        table = metadata.tables[name]
        keys = set(db.execute(select(table.c.id).where(table.c.id.in_(identifiers))).all())
        if keys:
            selected[name] = keys
    changed = True
    while changed:
        changed = False
        for table in metadata.tables.values():
            clauses = []
            for fk in table.foreign_keys:
                parent = fk.column.table
                if keys := selected.get(parent.name):
                    clauses.append(fk.parent.in_(select(fk.column).where(condition(parent, keys))))
            if not clauses:
                continue
            keys = set(db.execute(select(*table.primary_key.columns).where(or_(*clauses))).all())
            added = keys - selected.get(table.name, set())
            if added:
                selected.setdefault(table.name, set()).update(added)
                changed = True
    return selected


def _preserve_other_scopes(db, metadata, candidates, workspace, users):
    """Infer ownership through FK ancestors, reading keys only, never media bytes."""
    cached = {}

    def row(table, key):
        marker = (table.name, tuple(key))
        if marker not in cached:
            columns = set(table.primary_key.columns) | {fk.parent for fk in table.foreign_keys}
            cached[marker] = (
                db.execute(select(*columns).where(condition(table, {key}))).mappings().one()
            )
        return cached[marker]

    def scopes(table, key, visited=frozenset()):
        marker = (table.name, tuple(key))
        if marker in visited:
            return set()
        values = row(table, key)
        if table.name == "workspaces":
            return {values["id"]}
        if "workspace_id" in values and values["workspace_id"] is not None:
            return {values["workspace_id"]}
        if table.name in PRIVATE_IDENTITIES:
            owner = values.get("user_id", values.get("owner_user_id"))
            if owner is not None:
                return {workspace} if owner in users else {"another-account"}
        result = set()
        for fk in table.foreign_keys:
            parent = fk.column.table
            value = values[fk.parent.name]
            if value is None or parent.name == "users":
                continue
            keys = db.execute(select(*parent.primary_key.columns).where(fk.column == value))
            for parent_key in keys:
                result.update(scopes(parent, parent_key, visited | {marker}))
        return result

    return {
        name: {
            key
            for key in keys
            if name not in PROTECTED and not (scopes(metadata.tables[name], key) - {workspace})
        }
        for name, keys in candidates.items()
    }


def _preserve_referenced_ancestors(db, metadata, selected):
    """A surviving row keeps every required parent, including provenance links."""
    changed = True
    while changed:
        changed = False
        for table in metadata.tables.values():
            for fk in table.foreign_keys:
                parent = fk.column.table
                parent_keys = selected.get(parent.name)
                if not parent_keys:
                    continue
                referenced = {
                    values[-1]
                    for values in db.execute(
                        select(*table.primary_key.columns, fk.parent).where(
                            fk.parent.in_(select(fk.column).where(condition(parent, parent_keys)))
                        )
                    )
                    if tuple(values[:-1]) not in selected.get(table.name, set())
                }
                if referenced:
                    keep = set(
                        db.execute(
                            select(*parent.primary_key.columns).where(
                                condition(parent, parent_keys), fk.column.in_(referenced)
                            )
                        ).all()
                    )
                    if keep:
                        parent_keys.difference_update(keep)
                        changed = True
    return {name: keys for name, keys in selected.items() if keys}


def _delete_selected(db, metadata, selected):
    pending, order = set(selected), []
    while pending:
        sinks = [
            name
            for name in pending
            if not any(
                fk.column.table.name == name and not fk.parent.nullable
                for other in pending - {name}
                for fk in metadata.tables[other].foreign_keys
            )
        ]
        if not sinks:
            raise RuntimeError("Local retirement contains a non-null dependency cycle.")
        order.extend(sorted(sinks))
        pending.difference_update(sinks)
    for name, keys in selected.items():
        table = metadata.tables[name]
        nullable = {
            fk.parent.name: None
            for fk in table.foreign_keys
            if fk.parent.nullable and fk.column.table.name in selected
        }
        if nullable:
            db.execute(update(table).where(condition(table, keys)).values(**nullable))
    for name in order:
        table = metadata.tables[name]
        db.execute(delete(table).where(condition(table, selected[name])))


def retire_memory(db, settings, root=FIXTURES):
    """One atomic retirement; the receipt is independent of deletable group data."""
    require_local(db, settings)
    if db.get(LocalEvaluationState, RECEIPT):
        return None
    if db.get(LocalEvaluationState, "evaluation-v1") is None:
        raise ValueError("Initialize the local dataset before retiring historical scenarios.")
    with db.begin_nested():
        apply_seed(db, settings, FILENAME, root)
        metadata = MetaData()
        metadata.reflect(bind=db.connection())
        postgres = db.bind.dialect.name == "postgresql"
        workspace = WORKSPACE if postgres else WORKSPACE.hex
        users = USERS if postgres else {user.hex for user in USERS}
        candidates = _candidates(db, metadata, workspace, users)
        scoped = _preserve_other_scopes(db, metadata, candidates, workspace, users)
        selected = _preserve_referenced_ancestors(db, metadata, scoped)
        _delete_selected(db, metadata, selected)
        report = {
            "removed": {name: len(keys) for name, keys in sorted(selected.items())},
            "retained_dependencies": {
                name: len(keys - selected.get(name, set()))
                for name, keys in sorted(candidates.items())
                if keys - selected.get(name, set())
            },
        }
        receipt(db, RECEIPT, seed_digest(root, FILENAME), report)
    db.expire_all()
    return report
