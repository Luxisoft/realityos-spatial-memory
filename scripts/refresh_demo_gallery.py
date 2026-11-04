"""Replace only identified demo publications with licensed, varied recordings.

Dry run by default. Existing accounts, groups, records, record media and biometric
portraits are preserved. A JSON visibility journal supports non-destructive rollback.
Run with the deployed backend environment and --root pointing at the fixture tree.
"""

import argparse
import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.accounts.models import PasswordAccount
from app.config import get_settings
from app.db import Database
from app.models import MediaAsset, MediaKind, User, Workspace, WorkspaceMember
from app.social_features.models import Publication
from app.workspaces.models import Record, RecordMedia
from sqlalchemy import select

SCENARIOS = {
    "security": (
        "Pacific Ridge Police Department",
        ("alex-rivera", "maya-johnson", "daniel-kim"),
    ),
    "nursing": (
        "California Valley Medical Center",
        ("elena-marquez", "mateo-rios", "sarah-chen"),
    ),
    "memory": (
        "Sonoran Neurological Institute",
        ("noah-brooks", "lucia-vega", "owen-patel"),
    ),
}
SOURCE = "simulator-licensed"


def attach_bucket_source(db, workspace, owner, item, raw, post):
    """Link verified fixture bytes to their author source before scheduled scans."""
    from app.social_features.evidence_models import PublicationUpload
    from app.storage.models import StorageConnection
    from app.storage.provenance_models import StorageObject
    from app.storage.service import upload_request_key

    folder = "police" if item["group"] == "security" else item["group"]
    username = db.scalar(
        select(PasswordAccount.username).where(PasswordAccount.user_id == owner.id)
    )
    prefix = f"demo/v2/{folder}/{username}/"
    connection = db.scalar(
        select(StorageConnection).where(
            StorageConnection.owner_id == owner.id,
            StorageConnection.workspace_id == workspace.id,
            StorageConnection.prefix == prefix,
            StorageConnection.active.is_(True),
        )
    )
    if connection is None:
        return
    filename = Path(item["path"]).name
    key = prefix + filename
    identity = json.dumps(
        [str(connection.id), key, item["sha256"], "work", str(workspace.id)]
    )
    request_key = upload_request_key(db, owner.id, identity, item["sha256"])
    upload = db.scalar(
        select(PublicationUpload).where(
            PublicationUpload.owner_id == owner.id,
            PublicationUpload.request_key == request_key,
        )
    )
    if upload is None:
        upload = PublicationUpload(
            owner_id=owner.id,
            request_key=request_key,

            workspace_id=workspace.id,
            original_bytes=raw,
            mime_type="video/mp4" if item["kind"] == "video" else "image/jpeg",
            caption=filename,
            note_text="",
            note_source="",
            status="published",
            result_id=post.id,
        )
        db.add(upload)
        db.flush()
    if not db.scalar(
        select(StorageObject.id).where(StorageObject.upload_id == upload.id)
    ):
        db.add(
            StorageObject(
                connection_id=connection.id,
                revision=connection.revision,
                key=key,
                workspace_id=workspace.id,
                sha256=item["sha256"],
                upload_id=upload.id,
            )
        )
        db.flush()


def prepare(db, root, apply=False):
    manifest = json.loads((root / "simulator/real-scenes/manifest.json").read_text())
    if manifest.get("video_release"):
        raise ValueError(
            "Use renew_evaluation_videos.py for the versioned video release"
        )
    if manifest.get("errors"):
        raise ValueError("Resolve media validation errors before publishing")
    targets, previous, created = [], [], []
    for scenario, (name, owners) in SCENARIOS.items():
        workspace = db.scalar(select(Workspace).where(Workspace.name == name))
        if workspace is None:
            raise ValueError(f"Existing workspace is required: {name}")
        rows = [i for i in manifest["items"] if i["group"] == scenario]
        assert len(rows) == 16
        assert sum(i["kind"] == "video" for i in rows) == 4
        users = []
        for username in owners:
            user = db.scalar(
                select(User)
                .join(PasswordAccount, PasswordAccount.user_id == User.id)
                .where(PasswordAccount.username == username)
            )
            if user is None or not db.scalar(
                select(WorkspaceMember).where(
                    WorkspaceMember.workspace_id == workspace.id,
                    WorkspaceMember.user_id == user.id,
                )
            ):
                raise ValueError(f"Existing member required: {username} / {name}")
            users.append(user)
        for index, item in enumerate(rows):
            path = root / item["path"]
            raw = path.read_bytes()
            if hashlib.sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError(f"Changed fixture: {path.name}")
            targets.append((workspace, users[index % len(users)], item, raw))
        # Only fixture provenance or explicitly simulated record media qualifies.
        record_posts = (
            select(RecordMedia.publication_id)
            .join(Record)
            .where(Record.workspace_id == workspace.id, Record.simulated.is_(True))
        )
        old = db.execute(
            select(Publication.id, Publication.hidden).where(
                Publication.workspace_id == workspace.id,
                Publication.hidden.is_(False),
                (Publication.source.in_(["workshop", "simulator-work"]))
                | (
                    (Publication.source == "workspace-import")
                    & Publication.id.in_(record_posts)
                ),
            )
        )
        previous.extend({"id": str(p.id), "hidden": p.hidden} for p in old)
    if apply:
        for workspace, owner, item, raw in targets:
            reference = f"licensed-v2:{item['group']}:{item['id']}"
            post = db.scalar(
                select(Publication).where(
                    Publication.source == SOURCE, Publication.source_ref == reference
                )
            )
            if post is None:
                asset = MediaAsset(
                    workspace_id=workspace.id,
                    kind=MediaKind.VIDEO
                    if item["kind"] == "video"
                    else MediaKind.IMAGE,
                    mime_type="video/mp4" if item["kind"] == "video" else "image/jpeg",
                    original_bytes=raw,
                    byte_size=len(raw),
                    sha256=item["sha256"],
                    width=item["width"],
                    height=item["height"],
                    extra_metadata={
                        "origin": "licensed-demo",
                        "simulated": True,
                        "license": item["license"],
                        "source_url": item["source"],
                    },
                )
                db.add(asset)
                db.flush()
                post = Publication(
                    owner_id=owner.id,
                    media_id=asset.id,
                    workspace_id=workspace.id,

                    source=SOURCE,
                    source_ref=reference,
                    caption=item["label"],
                    published_at=datetime.now(UTC),
                )
                db.add(post)
                db.flush()
                created.append(str(post.id))
            attach_bucket_source(db, workspace, owner, item, raw, post)
        for item in previous:
            db.get(Publication, uuid.UUID(item["id"])).hidden = True
    return {"prepared": len(targets), "hidden": previous, "created": created}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--read-credentials-file", type=Path)
    args = parser.parse_args()
    settings = get_settings()
    with Database(settings.database_url).session_factory() as db:
        if args.rollback:
            import uuid

            journal = json.loads(args.journal.read_text())
            for item in journal["hidden"]:
                db.get(Publication, uuid.UUID(item["id"])).hidden = item["hidden"]
            for identifier in journal["created"]:
                db.get(Publication, uuid.UUID(identifier)).hidden = True
            db.commit()
            print("Demo visibility restored")
            return
        if args.read_credentials_file:
            if not args.apply:
                parser.error("--read-credentials-file requires --apply")
            from connect_demo_buckets import prepare as prepare_connections

            prepare_connections(
                db, settings, json.loads(args.read_credentials_file.read_text())
            )
        result = prepare(db, args.root, args.apply)
        if args.apply:
            # Journal must be durable before changing visibility in the database.
            args.journal.parent.mkdir(parents=True, exist_ok=True)
            journal = result.copy()
            if args.journal.exists():
                previous = json.loads(args.journal.read_text())
                journal["created"] = list(
                    dict.fromkeys(previous["created"] + result["created"])
                )
                hidden = {item["id"]: item for item in result["hidden"]}
                hidden.update({item["id"]: item for item in previous["hidden"]})
                journal["hidden"] = list(hidden.values())
            args.journal.write_text(json.dumps(journal, indent=2) + "\n")
            args.journal.chmod(0o600)
            db.commit()
            from app.tasks import index_gallery_media

            for identifier in result["created"]:
                index_gallery_media.delay(identifier)
        print(
            json.dumps(
                {
                    "applied": args.apply,
                    "prepared": result["prepared"],
                    "retired_demo_posts": len(result["hidden"]),
                    "new_posts": len(result["created"]),
                }
            )
        )


if __name__ == "__main__":
    main()
