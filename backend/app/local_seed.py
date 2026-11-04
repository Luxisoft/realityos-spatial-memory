"""Initialize the public local fixtures once; never refresh or overwrite user data."""

import hashlib
import json
import mimetypes
import secrets
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import select, text

from app.accounts.models import PasswordAccount
from app.local_catalog import FIXTURES, catalog, local_id
from app.local_display import install_display_text
from app.local_models import LocalEvaluationState
from app.local_runtime import validate_local_settings
from app.models import MediaAsset, MediaKind, Role, User, Workspace, WorkspaceMember, Zone
from app.security import hash_password
from app.social_features.classification import add_term, set_classification
from app.social_features.models import Publication, UserProfile
from app.workspaces.models import Connection, Record, RecordMedia, RecordRevision
from app.workspaces.schemas import ImportBatch
from app.workspaces.service import record_json

RECEIPT = "evaluation-v1"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def fixture_file(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Fixture must remain inside simulator.")
    return path


def preflight(root):
    data = catalog(root)
    scenes = read_json(root / "real-scenes/manifest.json")["items"]
    classifications = read_json(root / "real-scenes/publication-classification.json")["items"]
    profiles = read_json(root / "profiles/accounts.json")["accounts"]
    for entry in scenes:
        path = fixture_file(root, entry["path"].removeprefix("simulator/"))
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"Fixture integrity failed: {path.name}")
    for group in data["groups"]:
        if not group["records"] and not group["publications"]:
            for user in group["users"]:
                raw = fixture_file(root, user["avatar"]).read_bytes()
                if hashlib.sha256(raw).hexdigest() != user["avatar_sha256"]:
                    raise ValueError("Avatar fixture integrity failed.")
            continue
        group["fixture"] = read_json(root / f"workspaces/{group['slug']}.json")
        batch = ImportBatch.model_validate(group["fixture"]["batch"])
        ids = {r.external_id for r in batch.records}
        if any(set(r.related_ids) - ids for r in batch.records):
            raise ValueError("Unresolved fixture record relationships.")
        for attachment in group["fixture"]["attachments"]:
            raw = fixture_file(root, "workspaces/" + attachment["path"]).read_bytes()
            if attachment.get("sha256") and hashlib.sha256(raw).hexdigest() != attachment["sha256"]:
                raise ValueError("Attachment fixture integrity failed.")
            if attachment["record"] not in ids:
                raise ValueError("Unresolved fixture attachment.")
        for user in group["users"]:
            raw = fixture_file(root, user["avatar"]).read_bytes()
            if hashlib.sha256(raw).hexdigest() != user["avatar_sha256"]:
                raise ValueError("Avatar fixture integrity failed.")
    return data, scenes, classifications, profiles


def add_media(db, workspace_id, path, key, metadata):
    raw = path.read_bytes()
    kind = MediaKind.VIDEO if path.suffix == ".mp4" else MediaKind.IMAGE
    asset = MediaAsset(
        id=local_id("media", key),
        workspace_id=workspace_id,
        kind=kind,
        mime_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        original_bytes=raw,
        byte_size=len(raw),
        sha256=hashlib.sha256(raw).hexdigest(),
        extra_metadata=metadata,
    )
    db.add(asset)
    db.flush()
    return asset


def seed_records(db, root, group, workspace_id, owner_id, counts):
    """Install one group's reviewed records and original attachment bytes."""
    previous_counts = dict(counts)
    # Required provenance FK in the existing record schema, never an external connection.
    connection = Connection(
        id=local_id("provenance", group["slug"]),
        workspace_id=workspace_id,
        created_by_id=owner_id,
        name="Local fixture provenance",
        active=False,
        token_hash=hashlib.sha256(secrets.token_bytes(32)).hexdigest(),
    )
    db.add(connection)
    db.flush()
    for entry in ImportBatch.model_validate(group["fixture"]["batch"]).records:
        record = Record(
            id=uuid.UUID(group["records"][entry.external_id]),
            workspace_id=workspace_id,
            connection_id=connection.id,
            updated_at=entry.occurred_at,
            **entry.model_dump(exclude={"authorized", "biometric_authorized", "biometric_basis"}),
        )
        db.add(record)
        db.flush()
        db.add(
            RecordRevision(
                record_id=record.id, version=record.version, snapshot=record_json(record)
            )
        )
        counts["records"] += 1
    for index, entry in enumerate(group["fixture"]["attachments"]):
        asset = add_media(
            db,
            workspace_id,
            fixture_file(root, "workspaces/" + entry["path"]),
            f"attachment:{group['slug']}:{index}",
            {"origin": "local-evaluation", "simulated": True},
        )
        db.add(
            RecordMedia(
                record_id=uuid.UUID(group["records"][entry["record"]]),
                external_id=entry["external_id"],
                media_id=asset.id,
            )
        )
        counts["attachments"] += 1
    if group.get("content_revision"):
        db.add(
            LocalEvaluationState(
                name=group["content_revision"],
                manifest_hash=hashlib.sha256(
                    json.dumps(group["fixture"], sort_keys=True).encode()
                ).hexdigest(),
                counts={
                    key: counts[key] - previous_counts[key] for key in ("records", "attachments")
                },
            )
        )
        db.flush()


def seed_evaluation(db, settings, root=FIXTURES):
    validate_local_settings(settings)
    if not (
        settings.environment == "local"
        and settings.local_login_enabled
        and settings.local_evaluation_enabled
    ):
        raise ValueError(
            "Fixture initialization is restricted to the local evaluation installation."
        )
    # Serialize concurrent starts. The receipt deliberately has no scenario foreign keys.
    if db.bind.dialect.name == "postgresql":
        db.execute(text("SELECT pg_advisory_xact_lock(7265616)"))
    previous = db.get(LocalEvaluationState, RECEIPT)
    if previous:
        install_display_text(db, settings, root)
        return {"initialized": False, **previous.counts}
    if db.scalar(select(User.id).limit(1)) is not None:
        raise ValueError(
            "Use an empty isolated local database; existing accounts were not changed."
        )
    data, scenes, classifications, profiles = preflight(root)
    profile_fields = {p["username"]: p["fields"] for p in profiles}
    classification = {p["post_id"]: p for p in classifications}
    counts = {"groups": 0, "users": 0, "records": 0, "attachments": 0, "publications": 0}
    for group in data["groups"]:
        workspace_id = uuid.UUID(group["id"])
        users = {}
        for entry in group["users"]:
            user = User(
                id=uuid.UUID(entry["id"]),
                email=entry["username"] + "@local.realityos.invalid",
                display_name=entry["display_name"],
                password_hash=hash_password(secrets.token_urlsafe(32)),
            )
            db.add(user)
            db.flush()
            db.add(
                PasswordAccount(
                    user_id=user.id, username=entry["username"], verified_at=datetime.now(UTC)
                )
            )
            users[entry["username"]] = user
            counts["users"] += 1
        owner = users[group["users"][0]["username"]]
        db.add(
            Workspace(
                id=workspace_id,
                name=group["name"],
                created_by_id=owner.id,
                description="Local evaluation · fictional scenario" if group["records"] else "",
            )
        )
        db.flush()
        counts["groups"] += 1
        db.add(Zone(workspace_id=workspace_id, name="Principal", kind="zone"))
        for entry in group["users"]:
            user = users[entry["username"]]
            db.add(
                WorkspaceMember(
                    workspace_id=workspace_id,
                    user_id=user.id,
                    role=Role.ADMIN if user.id == owner.id else Role.REGISTER,
                )
            )
            media = add_media(
                db,
                workspace_id,
                fixture_file(root, entry["avatar"]),
                "avatar:" + entry["username"],
                {"origin": "account-avatar"},
            )
            fields = dict(profile_fields[entry["username"]])
            if fields.get("birthday"):
                fields["birthday"] = date.fromisoformat(fields["birthday"])
            db.add(UserProfile(user_id=user.id, avatar_media_id=media.id, **fields))
        if not group["records"] and not group["publications"]:
            continue
        seed_records(db, root, group, workspace_id, owner.id, counts)
        terms = {}
        for entry in [s for s in scenes if s["group"] == group["media_group"]]:
            key = f"{entry['group']}:{entry['id']}"
            asset = add_media(
                db,
                workspace_id,
                fixture_file(root, entry["path"].removeprefix("simulator/")),
                key,
                {
                    "origin": "local-evaluation",
                    "source": entry["source"],
                    "license": entry["license"],
                    "staged_evaluation": True,
                },
            )
            post = Publication(
                id=uuid.UUID(group["publications"][str(entry["id"])]),
                workspace_id=workspace_id,
                owner_id=users[entry["owner"]].id,
                media_id=asset.id,
                caption=entry["label"],
                source="local-evaluation",
                source_ref=key,
            )
            db.add(post)
            db.flush()
            labels = classification[entry["post_id"]]
            if labels["media_sha256"] != asset.sha256:
                raise ValueError("Classification media mismatch.")
            for kind, names in (("category", [labels["category"]]), ("tag", labels["tags"])):
                for name in names:
                    if (kind, name) not in terms:
                        terms[kind, name] = add_term(db, workspace_id, kind, name).id
            set_classification(
                db,
                post,
                terms["category", labels["category"]],
                [terms["tag", tag] for tag in labels["tags"]],
            )
            counts["publications"] += 1
    digest = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
    db.add(LocalEvaluationState(name=RECEIPT, manifest_hash=digest, counts=counts))
    db.flush()
    install_display_text(db, settings, root)
    return {"initialized": True, **counts}


def enqueue_initial_media(db):
    """Persist dispatch receipts; normal index jobs are already idempotent per publication."""
    from app.tasks import index_gallery_media

    receipt = db.get(LocalEvaluationState, RECEIPT)
    if receipt is None:
        raise ValueError("Initialize the local dataset before indexing.")
    dispatched = set(receipt.counts.get("dispatched", []))
    for post in db.scalars(
        select(Publication).where(Publication.source == "local-evaluation")
    ).all():
        if str(post.id) in dispatched:
            continue
        if post.indexed_at is None:
            index_gallery_media.delay(str(post.id))
        dispatched.add(str(post.id))
        receipt.counts = {**receipt.counts, "dispatched": sorted(dispatched)}
        db.commit()
    return {"dispatched": len(dispatched)}
