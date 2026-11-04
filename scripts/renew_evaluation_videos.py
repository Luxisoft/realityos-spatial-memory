"""Stage, index and activate annotated evaluation videos in existing groups.

Run inside the backend runtime with --root pointing at this checkout's fixtures.
The default inventory is read-only. The durable journal is required for every
mutation. Neither reference answers nor fixture labels enter model detections.
"""

import argparse
import hashlib
import json
import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

from app.accounts.models import PasswordAccount
from app.config import get_settings
from app.db import Database
from app.models import MediaAsset, MediaKind, User, Workspace, WorkspaceMember
from app.social_features.evidence_models import GalleryIndexRun, PublicationUpload
from app.social_features.models import Publication
from app.storage.models import StorageConnection, StorageImport, StorageSync
from app.storage.provenance_models import StorageObject
from sqlalchemy import func, select

RELEASE = "evaluation-v3"
PREVIOUS = "evaluation-v2-rollback"
SOURCE = "simulator-licensed"
GROUPS = {
    "security": (
        "Pacific Ridge Police Department",
        "police",
        ("alex-rivera", "maya-johnson", "daniel-kim"),
    ),
    "nursing": (
        "California Valley Medical Center",
        "nursing",
        ("elena-marquez", "mateo-rios", "sarah-chen"),
    ),
    "memory": (
        "Sonoran Neurological Institute",
        "memory",
        ("noah-brooks", "lucia-vega", "owen-patel"),
    ),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, data):
    """Persist rollback identifiers before the corresponding database commit."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with temp.open("w") as stream:
        os.chmod(temp, 0o600)
        json.dump(data, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temp.replace(path)


def load_inputs(root):
    base = root / "simulator/real-scenes"
    manifest = json.loads((base / "video-candidate-manifest.json").read_text())
    cases = json.loads((base / "video-evaluation.json").read_text())
    previous = json.loads((base / "video-previous-manifest.json").read_text())
    if manifest.get("errors") or previous.get("errors"):
        raise ValueError("Resolve all source preparation errors")
    if cases["release"] != RELEASE or len(manifest["items"]) != 12:
        raise ValueError("Exactly twelve reviewed candidate videos are required")
    by_id = {c["id"]: c for c in cases["videos"]}
    for group in GROUPS:
        rows = [i for i in manifest["items"] if i["group"] == group]
        if len(rows) != 4:
            raise ValueError("Exactly four videos per existing group are required")
        counts = {owner: 0 for owner in GROUPS[group][2]}
        for item in rows:
            case = by_id[item["id"]]
            if case["group"] != group or not case.get("footage_reviewed"):
                raise ValueError("Review the actual footage before staging")
            if case["sha256"] != item["sha256"] or len(case["queries"]) != 2:
                raise ValueError("Ground truth must bind to the reviewed video bytes")
            for query in case["queries"]:
                start, end = query["visible_ms"]
                if not (0 <= start < end <= round(item["duration"] * 1000)):
                    raise ValueError("Invalid expected evidence interval")
                if not all(query.get(language) for language in ("es", "en")):
                    raise ValueError("Both query languages are required")
            counts[case["owner"]] += 1
            if item["kind"] != "video" or not item.get("complete_recording"):
                raise ValueError("Use complete recorded actions")
            if digest((root / item["path"]).read_bytes()) != item["sha256"]:
                raise ValueError("Candidate bytes changed after review")
        if list(counts.values()) != [2, 1, 1]:
            raise ValueError("Use two jury videos and one per companion account")
    return manifest, cases, previous


def inventory(db, root):
    manifest, cases, previous = load_inputs(root)
    case_by_id = {c["id"]: c for c in cases["videos"]}
    journal = {
        "release": RELEASE,
        "phase": "prepared",
        "created": [],
        "previous": [],
        "connections": [],
    }
    for group, (name, folder, usernames) in GROUPS.items():
        workspace = db.scalar(select(Workspace).where(Workspace.name == name))
        if workspace is None:
            raise ValueError(f"Existing group required: {name}")
        owners = {}
        for username in usernames:
            user = db.scalar(
                select(User)
                .join(PasswordAccount, PasswordAccount.user_id == User.id)
                .where(PasswordAccount.username == username)
            )
            if user is None or not db.scalar(
                select(WorkspaceMember).where(
                    WorkspaceMember.user_id == user.id,
                    WorkspaceMember.workspace_id == workspace.id,
                )
            ):
                raise ValueError(f"Existing membership required: {username}")
            owners[username] = user
            connection = db.scalar(
                select(StorageConnection).where(
                    StorageConnection.owner_id == user.id,
                    StorageConnection.workspace_id == workspace.id,
                    StorageConnection.prefix == f"demo/v2/{folder}/{username}/",
                    StorageConnection.active.is_(True),
                )
            )
            if connection is None:
                raise ValueError(f"Existing bucket connection required: {username}")
            rules = list(
                db.scalars(
                    select(StorageSync).where(
                        StorageSync.connection_id == connection.id
                    )
                )
            )
            journal["connections"].append(
                {
                    "id": str(connection.id),
                    "owner": username,
                    "workspace_id": str(workspace.id),
                    "revision": connection.revision,
                    "prefix": connection.prefix,
                    "rules": [
                        {
                            "id": str(r.id),
                            "prefix": r.prefix,
                            "enabled": r.enabled,
                            "interval_minutes": r.interval_minutes,
                        }
                        for r in rules
                    ],
                }
            )
        for item in (i for i in previous["items"] if i["group"] == group):
            post = db.scalar(
                select(Publication).where(
                    Publication.workspace_id == workspace.id,
                    Publication.source == SOURCE,
                    Publication.source_ref == f"licensed-v2:{group}:{item['id']}",
                )
            )
            if (
                post is None
                or db.get(MediaAsset, post.media_id).sha256 != item["sha256"]
            ):
                raise ValueError(f"Previous publication changed: {group}/{item['id']}")
            owner = db.scalar(
                select(PasswordAccount.username).where(
                    PasswordAccount.user_id == post.owner_id
                )
            )
            if owner not in owners:
                raise ValueError("Previous fixture has an unexpected owner")
            journal["previous"].append(
                {
                    "id": str(post.id),
                    "media_id": str(post.media_id),
                    "hidden": post.hidden,
                    "owner": owner,
                    "item": item,
                }
            )
        for item in (i for i in manifest["items"] if i["group"] == group):
            owner = owners[case_by_id[item["id"]]["owner"]]
            reference = f"{RELEASE}:{group}:{item['id']}:{item['sha256'][:16]}"
            post_id = uuid.uuid5(
                uuid.NAMESPACE_URL, f"realityos:{owner.id}:{reference}"
            )
            journal["created"].append(
                {
                    "id": str(post_id),
                    "media_id": str(uuid.uuid5(post_id, "original")),
                    "owner_id": str(owner.id),
                    "owner": case_by_id[item["id"]]["owner"],
                    "workspace_id": str(workspace.id),
                    "reference": reference,
                    "item": item,
                }
            )
    return journal


def stage(db, root, journal):
    for row in journal["created"]:
        identifier = uuid.UUID(row["id"])
        item = row["item"]
        post = db.get(Publication, identifier)
        if post:
            if db.get(MediaAsset, post.media_id).sha256 != item["sha256"]:
                raise ValueError("Staged source changed")
            continue
        raw = (root / item["path"]).read_bytes()
        if digest(raw) != item["sha256"]:
            raise ValueError("Candidate bytes changed")
        asset = MediaAsset(
            id=uuid.UUID(row["media_id"]),
            workspace_id=uuid.UUID(row["workspace_id"]),
            kind=MediaKind.VIDEO,
            mime_type="video/mp4",
            original_bytes=raw,
            byte_size=len(raw),
            sha256=item["sha256"],
            width=item["width"],
            height=item["height"],
            extra_metadata={
                "origin": "licensed-evaluation",
                "simulated": True,
                "release": RELEASE,
                "license": item["license"],
                "source_url": item["source"],
                "author": item["author"],
                "complete_recording": True,
            },
        )
        db.add(asset)
        db.flush()
        db.add(
            Publication(
                id=identifier,
                owner_id=uuid.UUID(row["owner_id"]),
                media_id=asset.id,
                workspace_id=asset.workspace_id,
                audience="work",
                source=SOURCE,
                source_ref=row["reference"],
                caption=item["label"],
                published_at=datetime.now(UTC),
            )
        )
    db.flush()


def index(db, journal, settings, group=None, report_path=None, repair_previous=False):
    from app.meta import build_meta_client
    from app.social_features.index_runs import process_run

    if settings.meta_mode != "live":
        raise ValueError("Evaluation requires the live provider")
    client = build_meta_client(settings)
    rows = journal["previous"] if repair_previous else journal["created"]
    for row in rows:
        if group and row["item"]["group"] != group:
            continue
        post = db.get(Publication, uuid.UUID(row["id"]))
        run = (
            db.get(GalleryIndexRun, post.active_index_run_id)
            if post.active_index_run_id
            else None
        )
        if run and run.status == "ready" and not post.index_error:
            continue
        for attempt in range(3):
            result = process_run(db, post, client, checkpoint=True)
            db.commit()
            record = json.dumps(
                {
                    "id": row["item"]["id"],
                    "attempt": attempt + 1,
                    "indexed": bool(post.indexed_at),
                    "error": post.index_error,
                    "at": datetime.now(UTC).isoformat(),
                }
            )
            print(record, flush=True)
            if report_path:
                with report_path.open("a") as stream:
                    stream.write(record + "\n")
            if result is None or (post.indexed_at and not post.index_error):
                break


def checked_connection(db, row):
    connection = db.get(StorageConnection, uuid.UUID(row["id"]))
    if (
        not connection.active
        or connection.revision != row["revision"]
        or connection.prefix != row["prefix"]
    ):
        raise ValueError("Bucket configuration changed during evaluation")
    return connection


def bind_source(db, connection, row, generation):
    post = db.get(Publication, uuid.UUID(row["id"]))
    asset = db.get(MediaAsset, post.media_id)
    key = connection.prefix + generation + "/" + Path(row["item"]["path"]).name
    request_key = digest(
        json.dumps(
            [str(connection.id), key, asset.sha256, "work", str(post.workspace_id)]
        ).encode()
    )
    upload = db.scalar(
        select(PublicationUpload).where(
            PublicationUpload.owner_id == post.owner_id,
            PublicationUpload.request_key == request_key,
        )
    )
    if upload is None:
        upload = PublicationUpload(
            owner_id=post.owner_id,
            request_key=request_key,
            audience="work",
            workspace_id=post.workspace_id,
            original_bytes=asset.original_bytes,
            mime_type=asset.mime_type,
            caption=Path(row["item"]["path"]).name,
            status="published",
            result_id=post.id,
        )
        db.add(upload)
        db.flush()
        db.add(
            StorageObject(
                connection_id=connection.id,
                revision=connection.revision,
                key=key,
                sha256=asset.sha256,
                workspace_id=post.workspace_id,
                upload_id=upload.id,
            )
        )
    elif upload.result_id != post.id or upload.status != "published":
        raise ValueError("Source generation already has a different import result")


def upload_sources(db, journal, credentials):
    import boto3
    from botocore.config import Config

    client = boto3.client(
        "s3",
        endpoint_url=credentials["endpoint"],
        region_name=credentials.get("region", "auto"),
        aws_access_key_id=credentials["access_key"],
        aws_secret_access_key=credentials["secret_key"],
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )
    for connection_row in journal["connections"]:
        connection = checked_connection(db, connection_row)
        if connection.bucket != credentials["bucket"] or connection.endpoint.rstrip(
            "/"
        ) != credentials["endpoint"].rstrip("/"):
            raise ValueError("Upload credentials do not address the configured source")
        previous = [
            r for r in journal["previous"] if r["owner"] == connection_row["owner"]
        ]
        current = [r for r in previous if r["item"]["kind"] == "image"] + [
            r for r in journal["created"] if r["owner"] == connection_row["owner"]
        ]
        for generation, rows in ((PREVIOUS, previous), (RELEASE, current)):
            for row in rows:
                asset = db.get(MediaAsset, uuid.UUID(row["media_id"]))
                raw = asset.original_bytes
                if digest(raw) != row["item"]["sha256"]:
                    raise ValueError("Original BYTEA differs from reviewed manifest")
                key = (
                    connection.prefix
                    + generation
                    + "/"
                    + Path(row["item"]["path"]).name
                )
                client.put_object(
                    Bucket=connection.bucket,
                    Key=key,
                    Body=raw,
                    ContentType=asset.mime_type,
                    Metadata={"sha256": asset.sha256, "evaluation-fixture": "true"},
                )
                with client.get_object(Bucket=connection.bucket, Key=key)[
                    "Body"
                ] as body:
                    if digest(body.read()) != asset.sha256:
                        raise ValueError("Bucket read-back failed")
                bind_source(db, connection, row, generation)
        db.flush()
        print(f"Verified source generations: {connection_row['owner']}", flush=True)


def pause_sources(db, journal):
    for row in journal["connections"]:
        connection = checked_connection(db, row)
        for rule in db.scalars(
            select(StorageSync).where(StorageSync.connection_id == connection.id)
        ):
            rule.enabled = False
        # Drain pre-existing work instead of cancelling historical imports.
        if db.scalar(
            select(StorageImport.id).where(
                StorageImport.connection_id == connection.id,
                StorageImport.status.in_(["pending", "running"]),
            )
        ):
            raise ValueError("An existing source import must finish before activation")


def select_generation(db, journal, generation):
    for row in journal["connections"]:
        connection = checked_connection(db, row)
        for rule in db.scalars(
            select(StorageSync).where(StorageSync.connection_id == connection.id)
        ):
            rule.enabled = False
        prefix = connection.prefix + generation + "/"
        rule = db.scalar(
            select(StorageSync).where(
                StorageSync.connection_id == connection.id, StorageSync.prefix == prefix
            )
        )
        if rule is None:
            rule = StorageSync(
                connection_id=connection.id,
                prefix=prefix,
                audience="work",
                workspace_id=connection.workspace_id,
            )
            db.add(rule)
        rule.enabled, rule.interval_minutes, rule.cursor, rule.seen_keys = (
            True,
            15,
            None,
            [],
        )
        rule.next_run = datetime.now(UTC)


def require_acceptance(db, journal, receipt):
    if journal.get("retired_media_deleted"):
        raise ValueError("Retired media was deleted; this release is already final")
    expected = {r["id"]: r["item"]["sha256"] for r in journal["created"]}
    if receipt.get("release") != RELEASE or receipt.get("sources") != expected:
        raise ValueError("Acceptance receipt does not match the staged videos")
    if (
        not receipt.get("passed")
        or not receipt.get("visual_review_passed")
        or len(receipt.get("positive", [])) != 48
    ):
        raise ValueError("Complete live and visual acceptance is required")
    if not all(
        r.get("passed")
        for r in receipt["positive"]
        + receipt.get("negative", [])
        + receipt.get("isolation", [])
    ):
        raise ValueError("Acceptance contains failures")
    keys = {
        f"{row['item']['id']}:{number}:{language}": row["id"]
        for row in journal["created"]
        for number in (0, 1)
        for language in ("es", "en")
    }
    if {row.get("key"): row.get("post_id") for row in receipt["positive"]} != keys:
        raise ValueError("Acceptance must cover every distinct video query")
    if len(receipt.get("negative", [])) != 6 or len(receipt.get("isolation", [])) < 6:
        raise ValueError("Negative and cross-group checks are required")
    originals = receipt.get("originals", [])
    if len(originals) != 12 or not all(row.get("passed") for row in originals):
        raise ValueError("Original downloads must match all twelve reviewed hashes")
    for row in journal["created"]:
        post = db.get(Publication, uuid.UUID(row["id"]))
        run = (
            db.get(GalleryIndexRun, post.active_index_run_id)
            if post.active_index_run_id
            else None
        )
        if (
            not run
            or run.status != "ready"
            or post.index_error
            or run.source_hash != row["item"]["sha256"]
        ):
            raise ValueError("Every candidate must have complete current evidence")
        if any(d.get("simulated") for d in post.ai_detections):
            raise ValueError("Simulated inference cannot pass live acceptance")


def activate(db, journal):
    select_generation(db, journal, RELEASE)
    for row in journal["previous"]:
        if row["item"]["kind"] == "video":
            db.get(Publication, uuid.UUID(row["id"])).hidden = True
    for row in journal["created"]:
        db.get(Publication, uuid.UUID(row["id"])).hidden = False


def rollback(db, journal):
    if journal.get("retired_media_deleted"):
        raise ValueError("Retired media was deleted; media rollback is unavailable")
    for row in journal["previous"]:
        db.get(Publication, uuid.UUID(row["id"])).hidden = row["hidden"]
    for row in journal["created"]:
        post = db.get(Publication, uuid.UUID(row["id"]))
        if post:
            post.hidden = True
    if journal.get("sources_verified"):
        # A recursive root scan would import the new generation again. Restore
        # the previous content through its verified, separate source folder.
        select_generation(db, journal, PREVIOUS)
    elif journal.get("phase") == "sources_paused":
        raise ValueError("Finish verifying both source generations before rollback")


def verify_sync(db, journal, settings):
    """Exercise the actual bucket scanner twice without creating new publications."""
    from app.storage.service import sync_page

    if journal.get("phase") != "active":
        raise ValueError("Activate the verified source generation first")
    synchronous = settings.model_copy(update={"enqueue_processing": False})
    total = db.scalar(select(func.count()).select_from(Publication))
    cycles = []
    for cycle in (1, 2):
        for connection_row in journal["connections"]:
            connection = checked_connection(db, connection_row)
            rules = list(
                db.scalars(
                    select(StorageSync).where(
                        StorageSync.connection_id == connection.id,
                        StorageSync.enabled.is_(True),
                    )
                )
            )
            if len(rules) != 1 or rules[0].prefix != connection.prefix + RELEASE + "/":
                raise ValueError("Only the accepted generation may synchronize")
            rule = rules[0]
            pages = 0
            while True:
                run_id = sync_page(db, rule, synchronous)
                pages += 1
                if run_id:
                    run = db.get(StorageImport, run_id, populate_existing=True)
                    if run.status != "completed":
                        raise ValueError(f"Source scan did not complete: {run.id}")
                if rule.cursor is None:
                    break
            cycles.append(
                {
                    "cycle": cycle,
                    "owner": connection_row["owner"],
                    "pages": pages,
                    "passed": True,
                }
            )
        if db.scalar(select(func.count()).select_from(Publication)) != total:
            raise ValueError("Synchronization changed the publication count")
        for row in journal["previous"] + journal["created"]:
            post = db.get(Publication, uuid.UUID(row["id"]), populate_existing=True)
            if row["id"] in journal.get("deleted_publication_ids", []):
                if post is not None:
                    raise ValueError("Deleted evaluation media reappeared")
                continue
            if post is None:
                raise ValueError("An accepted publication is missing")
            asset = db.get(MediaAsset, post.media_id)
            should_hide = (
                row["item"]["kind"] == "video" or row["hidden"]
                if row in journal["previous"]
                else False
            )
            if post.hidden != should_hide or str(post.media_id) != row["media_id"]:
                raise ValueError(
                    "Synchronization changed accepted visibility or identity"
                )
            if digest(asset.original_bytes) != row["item"]["sha256"]:
                raise ValueError("Synchronization changed preserved original bytes")
    return {
        "cycles": cycles,
        "publication_count": total,
        "passed": True,
        "at": datetime.now(UTC).isoformat(),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument(
        "--phase",
        choices=("inventory", "stage", "index", "activate", "rollback", "verify-sync"),
        default="inventory",
    )
    parser.add_argument("--journal", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--credentials-file", type=Path)
    parser.add_argument("--group", choices=tuple(GROUPS))
    parser.add_argument(
        "--repair-previous",
        action="store_true",
        help="Retry incomplete existing indexes without changing original media",
    )
    args = parser.parse_args()
    settings = get_settings()
    with Database(settings.database_url).session_factory() as db:
        if args.phase == "inventory":
            plan = inventory(db, args.root)
            print(
                json.dumps(
                    {
                        "new_videos": len(plan["created"]),
                        "existing_publications": len(plan["previous"]),
                        "connections": len(plan["connections"]),
                    }
                )
            )
            return
        if args.journal.exists():
            journal = json.loads(args.journal.read_text())
            if journal["release"] != RELEASE:
                raise ValueError("Wrong release journal")
        elif args.phase == "stage":
            journal = inventory(db, args.root)
            save(args.journal, journal)
        else:
            raise ValueError("Stage and persist the rollback journal first")
        if args.phase == "stage":
            stage(db, args.root, journal)
            db.commit()
            journal["phase"] = "staged"
        elif args.phase == "index":
            index(
                db,
                journal,
                settings,
                args.group,
                args.journal.parent / "index-attempts.jsonl",
                args.repair_previous,
            )
        elif args.phase == "activate":
            if not args.receipt or not args.credentials_file:
                parser.error("activate requires --receipt and --credentials-file")
            require_acceptance(db, journal, json.loads(args.receipt.read_text()))
            pause_sources(db, journal)
            journal["phase"] = "sources_paused"
            save(args.journal, journal)
            db.commit()
            upload_sources(db, journal, json.loads(args.credentials_file.read_text()))
            db.commit()
            journal["sources_verified"] = True
            save(args.journal, journal)
            activate(db, journal)
            db.commit()
            journal["phase"] = "active"
        elif args.phase == "verify-sync":
            result = verify_sync(db, journal, settings)
            save(args.journal.parent / "synchronization.json", result)
        elif args.phase == "rollback":
            rollback(db, journal)
            db.commit()
            journal["phase"] = "rolled_back"
        save(args.journal, journal)
        print(json.dumps({"phase": journal["phase"], "journal": str(args.journal)}))


if __name__ == "__main__":
    main()
