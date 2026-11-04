import asyncio
import hashlib
import io
import json
import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from fastapi import HTTPException, UploadFile
from sqlalchemy import select
from starlette.datastructures import Headers

from app.meta import build_meta_client
from app.models import MediaAsset, User
from app.social_features.evidence_models import PublicationUpload
from app.social_features.models import Publication
from app.social_features.upload_service import process_upload
from app.social_features.uploads import candidate, check_destination
from app.storage.client import MEDIA, BucketClient, check_key, mime_for
from app.storage.models import StorageConnection, StorageImport
from app.storage.provenance_models import StorageObject


def now():
    return datetime.now(UTC)


def owned(db, connection_id, user):
    row = db.get(StorageConnection, connection_id, populate_existing=True)
    if row is None or row.owner_id != user.id or not row.active or not user.is_active:
        raise HTTPException(404, "Storage connection unavailable.")
    return row


def destination(db, row, workspace_id):
    user = db.get(User, row.owner_id, populate_existing=True)
    if user is None or not user.is_active or not row.active:
        raise HTTPException(403, "Connection or account is inactive.")
    check_destination(db, user, workspace_id)
    return user


def create_import(db, row, payload):
    destination(db, row, payload.workspace_id)
    for key in payload.keys:
        check_key(row, key)
        if mime_for(key) not in MEDIA:
            raise HTTPException(415, "Publication imports support JPEG, PNG, WebP and MP4.")
    from app.social_features.classification import validate_classification

    if set(payload.classifications) - set(payload.keys):
        raise HTTPException(422, "Classification keys must belong to this import.")
    for selection in payload.classifications.values():
        validate_classification(db, payload.workspace_id, selection.category_id, selection.tag_ids)
    # Empty new metadata must preserve request hashes of existing scheduled scans.
    digest = hashlib.sha256(
        payload.model_dump_json(
            exclude={"classifications"} if not payload.classifications else set()
        ).encode()
    ).hexdigest()
    previous = db.scalar(
        select(StorageImport).where(
            StorageImport.connection_id == row.id, StorageImport.request_key == payload.request_key
        )
    )
    if previous:
        if previous.revision != row.revision:
            raise HTTPException(409, "Use a new request key for the new connection source.")
        if previous.payload_hash != digest:
            raise HTTPException(409, "Import request key already used for different content.")
        return previous
    run = StorageImport(
        connection_id=row.id,
        request_key=payload.request_key,
        payload_hash=digest,
        revision=row.revision,

        workspace_id=payload.workspace_id,
        items=[
            {
                "key": key,
                "status": "pending",
                **(
                    {"classification": payload.classifications[key].model_dump(mode="json")}
                    if key in payload.classifications
                    else {}
                ),
            }
            for key in dict.fromkeys(payload.keys)
        ],
    )
    db.add(run)
    db.flush()
    return run


def import_json(db, run):
    items = []
    for source in run.items:
        item = dict(source)
        if item.get("upload_id"):
            upload = db.get(PublicationUpload, uuid.UUID(item["upload_id"]))
            if upload:
                item.update(
                    status=upload.status,
                    publication_id=str(upload.result_id) if upload.result_id else None,
                    preview_url=f"/v1/me/publication-uploads/{upload.id}/preview",
                    mime_type=upload.mime_type,
                    workspace_id=str(upload.workspace_id) if upload.workspace_id else None,
                )
        items.append(item)
    status = run.status
    if status in {"completed", "attention"}:
        status = "completed" if all(i["status"] == "published" for i in items) else "attention"
    return {
        "id": str(run.id),
        "status": status,
        "items": items,

        "workspace_id": str(run.workspace_id) if run.workspace_id else None,
    }


def upload_request_key(db, owner_id, identity, sha256):
    # Follow cancelled or superseded attempts without changing their history.
    # Stable successor keys keep concurrent/repeated imports idempotent.
    key = hashlib.sha256(identity.encode()).hexdigest()
    while previous := db.scalar(
        select(PublicationUpload).where(
            PublicationUpload.owner_id == owner_id, PublicationUpload.request_key == key
        )
    ):
        reusable = previous.status != "cancelled"
        if previous.status == "published":
            # A published candidate is historical: its result may since have
            # been removed or replaced with different original bytes.
            reusable = (
                db.scalar(
                    select(Publication.id)
                    .join(MediaAsset, Publication.media_id == MediaAsset.id)
                    .where(
                        Publication.id == previous.result_id,
                        Publication.owner_id == owner_id,

                        Publication.workspace_id == previous.workspace_id,
                        Publication.hidden.is_(False),
                        MediaAsset.sha256 == sha256,
                    )
                )
                is not None
            )
        if reusable:
            break
        key = hashlib.sha256(f"{key}:{previous.id}".encode()).hexdigest()
    return key


def process_import(db, run_id, settings):
    run = db.scalar(
        select(StorageImport).where(StorageImport.id == run_id).with_for_update(skip_locked=True)
    )
    if not run or run.status not in {"pending", "running"}:
        return
    if run.status == "running" and run.lease_until and run.lease_until.replace(tzinfo=UTC) > now():
        return
    run.status = "running"
    run.lease_until = now() + timedelta(hours=1)
    db.commit()
    for index, source in enumerate(run.items):
        db.refresh(run)
        if run.status == "cancelled":
            return
        if source["status"] not in {"pending", "downloading"}:
            continue
        item = dict(source)
        row = db.get(StorageConnection, run.connection_id, populate_existing=True)
        try:
            destination(db, row, run.workspace_id)
            if run.revision != row.revision:
                raise HTTPException(409, "Connection source changed.")
            item["status"] = "downloading"
            run.items = [dict(v) if i != index else item for i, v in enumerate(run.items)]
            db.commit()
            raw, mime, provenance = BucketClient(row, settings).download(item["key"])
            # Serialize publication with disconnect/credential rotation and membership validation.
            db.refresh(row, with_for_update=True)
            user = destination(db, row, run.workspace_id)
            if run.revision != row.revision:
                raise HTTPException(409, "Connection source changed.")
            request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings)))
            identity = json.dumps(
                [
                    str(row.id),
                    item["key"],
                    provenance["sha256"],
                    "work",  # Stable digest namespace for previously stored upload attempts.
                    str(run.workspace_id),
                ]
            )
            request_key = upload_request_key(db, user.id, identity, provenance["sha256"])
            upload = asyncio.run(
                candidate(
                    request,
                    UploadFile(
                        io.BytesIO(raw),
                        filename=item["key"].rsplit("/", 1)[-1],
                        headers=Headers({"content-type": mime}),
                    ),
                    item["key"].rsplit("/", 1)[-1],
                    "",
                    "",
                    user,
                    db,

                    run.workspace_id,
                    request_key,
                    category_id=item.get("classification", {}).get("category_id"),
                    tag_ids=item.get("classification", {}).get("tag_ids"),
                    allow_unclassified=True,
                )
            )
            from app.storage.lifecycle import retire_object

            source_row = db.scalar(
                select(StorageObject).where(
                    StorageObject.connection_id == row.id,
                    StorageObject.revision == row.revision,
                    StorageObject.key == item["key"],
                    StorageObject.retired.is_(False),
                    StorageObject.workspace_id == run.workspace_id,
                )
            )
            if source_row is not None and source_row.upload_id != upload.id:
                retire_object(db, source_row)
                source_row = None
            if source_row is None:
                source_row = StorageObject(
                    connection_id=row.id,
                    revision=row.revision,
                    key=item["key"],
                    workspace_id=run.workspace_id,
                )
                db.add(source_row)
            source_row.sha256, source_row.upload_id, source_row.retired = (
                provenance["sha256"],
                upload.id,
                False,
            )
            db.flush()
            # Persist the candidate and release the connection lock before
            # provider calls. Other imports, rotation and disconnect must not
            # wait for the complete analysis. Recovery reuses this candidate.
            db.commit()
            item.update(provenance, upload_id=str(upload.id), status="analyzing")
            if upload.status == "pending":
                process_upload(db, upload.id, build_meta_client(settings))
            # Publication changes are still uncommitted. Recheck the source
            # after analysis so a concurrent disconnect rolls them back.
            db.refresh(row, with_for_update=True)
            destination(db, row, run.workspace_id)
            if run.revision != row.revision:
                raise HTTPException(409, "Connection source changed.")
            item["status"] = upload.status
            item["error"] = (
                "Analysis failed; retry this file." if upload.status == "failed" else None
            )
        except Exception as exc:
            db.rollback()
            if item.get("upload_id"):
                upload = db.get(
                    PublicationUpload,
                    uuid.UUID(item["upload_id"]),
                    populate_existing=True,
                    with_for_update=True,
                )
                if upload and upload.status == "pending":
                    upload.status = "failed"
                    upload.error = "Storage import failed; check access and retry."
            # Never persist provider responses, credentials, or signed URLs in a job error.
            item.update(
                status="failed",
                error="Storage import failed. Check connection, permissions and file limits.",
                error_code=exc.status_code if isinstance(exc, HTTPException) else 502,
            )
        run = db.get(StorageImport, run_id, populate_existing=True)
        if run.status == "cancelled" or run.revision != row.revision:
            db.rollback()
            return
        run.items = [dict(v) if i != index else item for i, v in enumerate(run.items)]
        run.lease_until = now() + timedelta(hours=1)
        db.commit()
    run.status = "completed" if all(i["status"] == "published" for i in run.items) else "attention"
    run.lease_until = None
    db.commit()


def dispatch(run, settings):
    if settings.enqueue_processing:
        from app.storage.tasks import storage_import

        try:
            storage_import.delay(str(run.id))
        except Exception:
            pass  # Durable pending rows are recovered by the scheduler.


def sync_page(db, rule, settings):
    from app.storage.schemas import ImportInput

    connection = db.get(StorageConnection, rule.connection_id, populate_existing=True)
    destination(db, connection, rule.workspace_id)
    page = BucketClient(connection, settings).objects(rule.prefix, rule.cursor, recursive=True)
    objects = [o for o in page["items"] if mime_for(o["key"]) in MEDIA]
    if objects:
        signature = json.dumps(
            [str(rule.id), [(o["key"], o["etag"], o["size"], o["modified_at"]) for o in objects]]
        )
        run = create_import(
            db,
            connection,
            ImportInput(
                request_key=hashlib.sha256(signature.encode()).hexdigest(),
                keys=[o["key"] for o in objects],

                workspace_id=rule.workspace_id,
            ),
        )
        db.flush()
        run_id = run.id
    else:
        run_id = None
    rule.seen_keys = list(set(rule.seen_keys or []) | {item["key"] for item in page["items"]})
    if page["next_cursor"] is None:
        from app.storage.lifecycle import retire_object

        for source in db.scalars(
            select(StorageObject).where(
                StorageObject.connection_id == connection.id,
                StorageObject.revision == connection.revision,
                StorageObject.workspace_id == rule.workspace_id,
            )
        ):
            if source.key.startswith(rule.prefix) and source.key not in rule.seen_keys:
                retire_object(db, source)
        rule.seen_keys = []
    rule.cursor = page["next_cursor"]
    rule.next_run = now() + timedelta(minutes=1 if rule.cursor else rule.interval_minutes)
    rule.error = None
    db.commit()
    if run_id:
        dispatch(db.get(StorageImport, run_id), settings)
        if not settings.enqueue_processing:
            process_import(db, run_id, settings)
    return run_id
