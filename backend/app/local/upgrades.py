"""One-time transitions for earlier local databases, using the same relational seed."""

import uuid

from sqlalchemy import MetaData, inspect, select

from app.local.sql_data import FIXTURES, seed_digest, seed_tables
from app.local.state import receipt, require_local
from app.local_models import LocalAccessAccount, LocalEvaluationState
from app.models import Device, MediaAsset, Workspace, WorkspaceMember
from app.social_features.models import Publication, PublicationTag, PublicationTerm, UserProfile
from app.workspaces.models import Connection, Record, RecordMedia, RecordRevision
from app.workspaces.purge import purge

OLD_HOSPITAL = uuid.UUID("749f3aad-1543-55d1-9633-03f0cf443a1a")
POLICE = uuid.UUID("09f6bc06-8d36-5e69-a050-6f690fe1168b")
SOCIAL = uuid.UUID("3ea760d8-8394-5ddd-b1d7-ad27bd996b17")
REVISIONS = (
    "replace-hospital-meta-social-v1",
    "police-people-v1",
    "local-group-publications-v1",
    "bilingual-copy-v1",
)


def source(db, model):
    table = model.__table__.to_metadata(MetaData(), name="bootstrap_" + model.__tablename__)
    return list(db.execute(select(table)).mappings())


def instance(model, row):
    return model(**{attr.key: row[attr.columns[0].name] for attr in inspect(model).column_attrs})


def expected_members(db, workspace):
    return {
        row["user_id"] for row in source(db, WorkspaceMember) if row["workspace_id"] == workspace
    }


def replace_hospital(db):
    old = db.get(Workspace, OLD_HOSPITAL)
    if old is None:
        return {}
    if old.name != "California Valley Medical Center":
        raise ValueError("Unexpected old workspace; replacement aborted.")
    members = list(
        db.scalars(select(WorkspaceMember).where(WorkspaceMember.workspace_id == old.id))
    )
    if {m.user_id for m in members} != expected_members(db, SOCIAL):
        raise ValueError("Unexpected membership; replacement aborted.")
    if db.get(Workspace, SOCIAL):
        raise ValueError("Replacement workspace already exists; refusing to overwrite it.")
    destination = next(row for row in source(db, Workspace) if row["id"] == SOCIAL)
    db.add(instance(Workspace, destination))
    db.flush()
    for member in members:
        member.workspace_id = SOCIAL
        profile = db.get(UserProfile, member.user_id)
        avatar = (
            db.get(MediaAsset, profile.avatar_media_id)
            if profile and profile.avatar_media_id
            else None
        )
        if avatar and avatar.workspace_id == OLD_HOSPITAL:
            avatar.workspace_id = SOCIAL
        access = db.get(LocalAccessAccount, member.user_id)
        if access and access.workspace_id == OLD_HOSPITAL:
            access.workspace_id = SOCIAL
    db.flush()
    return purge(db, [OLD_HOSPITAL], apply=True, commit=False, strict_scope=True)["rows"]


def replace_police(db):
    workspace = db.get(Workspace, POLICE)
    if workspace is None:
        return {}
    if workspace.name != "Pacific Ridge Police Department":
        raise ValueError("Unexpected workspace; police replacement aborted.")
    members = list(
        db.scalars(select(WorkspaceMember).where(WorkspaceMember.workspace_id == POLICE))
    )
    if {m.user_id for m in members} != expected_members(db, POLICE):
        raise ValueError("Unexpected membership; police replacement aborted.")
    avatars = set()
    for member in members:
        profile = db.get(UserProfile, member.user_id)
        avatar = (
            db.get(MediaAsset, profile.avatar_media_id)
            if profile and profile.avatar_media_id
            else None
        )
        if avatar and avatar.workspace_id == POLICE:
            avatars.add((avatar.id,))
    report = purge(
        db,
        [POLICE],
        apply=True,
        commit=False,
        strict_scope=True,
        preserve_workspace=True,
        preserve_rows={
            "workspace_members": {(m.id,) for m in members},
            "local_access_accounts": {(m.user_id,) for m in members},
            "media_assets": avatars,
            "devices": {
                (identifier,)
                for identifier in db.scalars(select(Device.id).where(Device.workspace_id == POLICE))
            },
        },
    )
    db.expire_all()
    record_ids = {row["id"] for row in source(db, Record) if row["workspace_id"] == POLICE}
    for model in (Connection, Record, RecordRevision, MediaAsset, RecordMedia):
        for row in source(db, model):
            belongs = row.get("workspace_id") == POLICE or row.get("record_id") in record_ids
            if belongs and db.get(model, row["id"]) is None:
                # Publications are restored by the common publication step
                # after their records and media exist (PostgreSQL FK order).
                values = {**row, "publication_id": None} if model is RecordMedia else row
                db.add(instance(model, values))
        db.flush()
    prepared = next(row for row in source(db, Workspace) if row["id"] == POLICE)
    workspace = db.get(Workspace, POLICE)
    workspace.description, workspace.display_text = (
        prepared["description"],
        prepared["display_text"],
    )
    return {"removed": report["rows"], "created": {"records": 10, "attachments": 10}}


def add_group_publications(db):
    prepared_terms = {row["id"]: row for row in source(db, PublicationTerm)}
    prepared_media = {row["id"]: row for row in source(db, MediaAsset)}
    tags = source(db, PublicationTag)
    count = 0
    for row in source(db, Publication):
        workspace_id = row["workspace_id"]
        if workspace_id not in {POLICE, SOCIAL} or db.get(Publication, row["id"]):
            continue
        member = db.scalar(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == workspace_id,
                WorkspaceMember.user_id == row["owner_id"],
            )
        )
        if member is None or db.get(Workspace, workspace_id) is None:
            continue
        asset = db.scalar(
            select(MediaAsset).where(
                MediaAsset.workspace_id == workspace_id,
                MediaAsset.sha256 == prepared_media[row["media_id"]]["sha256"],
                MediaAsset.extra_metadata["origin"]
                .as_string()
                .in_(["local-evaluation", "account-avatar"]),
            )
        )
        if asset is None:
            continue
        term_ids = [
            row["category_id"],
            *(tag["term_id"] for tag in tags if tag["post_id"] == row["id"]),
        ]
        actual = {}
        for identifier in term_ids:
            value = prepared_terms[identifier]
            # A locally renamed term retains its identity; never recreate its
            # original name or collide with its primary key during an upgrade.
            term = db.get(PublicationTerm, identifier)
            if term is not None and (
                term.workspace_id != workspace_id or term.kind != value["kind"]
            ):
                raise ValueError("Prepared publication term has an unexpected scope.")
            if term is None:
                term = db.scalar(
                    select(PublicationTerm).where(
                        PublicationTerm.workspace_id == workspace_id,
                        PublicationTerm.kind == value["kind"],
                        PublicationTerm.name_key == value["name_key"],
                    )
                )
            if term is None:
                term = instance(PublicationTerm, value)
                db.add(term)
                db.flush()
            actual[identifier] = term.id
        post = instance(
            Publication, {**row, "media_id": asset.id, "category_id": actual[row["category_id"]]}
        )
        db.add(post)
        db.flush()
        for tag in tags:
            if tag["post_id"] == post.id:
                db.add(PublicationTag(post_id=post.id, term_id=actual[tag["term_id"]]))
        for attachment in db.scalars(
            select(RecordMedia)
            .join(Record)
            .where(Record.workspace_id == workspace_id, RecordMedia.media_id == asset.id)
        ):
            if attachment.publication_id is None:
                attachment.publication_id = post.id
        count += 1
    return {"publications": count}


def install_copy(db):
    count = 0
    for model in (Workspace, PublicationTerm, Record, Publication, UserProfile):
        for value in source(db, model):
            if model is PublicationTerm:
                row = db.scalar(
                    select(model).where(
                        model.workspace_id == value["workspace_id"],
                        model.kind == value["kind"],
                        model.name_key == value["name_key"],
                    )
                )
            else:
                row = db.get(model, value["user_id"] if model is UserProfile else value["id"])
            if row is None:
                continue
            if model is Workspace and row.description == "Local evaluation · fictional scenario":
                row.description = value["description"]
            display = dict(row.display_text or {})
            for field, pair in value["display_text"].items():
                if getattr(row, field) == pair["source"]:
                    display[field] = pair
                    count += 1
            row.display_text = display
    return {"fields": count}


def upgrade_local_data(db, settings, root=FIXTURES):
    require_local(db, settings)
    pending = [name for name in REVISIONS if db.get(LocalEvaluationState, name) is None]
    if not pending:
        return {}
    filename = "001-scenarios.sql"
    actions = dict(
        zip(
            REVISIONS,
            (replace_hospital, replace_police, add_group_publications, install_copy),
            strict=True,
        )
    )
    results = {}
    with seed_tables(db, settings, filename, root, staged=True):
        for name in pending:
            results[name] = actions[name](db)
            # Police replacement also resets its obsolete publications; the same
            # shared loader links the new cases even on an intermediate release.
            if name == "police-people-v1" and "local-group-publications-v1" not in pending:
                add_group_publications(db)
            receipt(db, name, seed_digest(root, filename), results[name])
    return results
