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


def now():
    return datetime.now(UTC)


def owned(db, connection_id, user):
    row = db.get(StorageConnection, connection_id, populate_existing=True)
    if row is None or row.owner_id != user.id or not row.active or not user.is_active:
        raise HTTPException(404, "Storage connection unavailable.")
    return row


def destination(db, row, audience, workspace_id):
    user = db.get(User, row.owner_id, populate_existing=True)
    if user is None or not user.is_active or not row.active:
        raise HTTPException(403, "Connection or account is inactive.")
    check_destination(db, user, audience, workspace_id)
    return user


def create_import(db, row, payload):
    destination(db, row, payload.audience, payload.workspace_id)
    for key in payload.keys:
        check_key(row, key)
        if mime_for(key) not in MEDIA:
            raise HTTPException(415, "Publication imports support JPEG, PNG, WebP and MP4.")
    digest = hashlib.sha256(payload.model_dump_json().encode()).hexdigest()
    previous = db.scalar(
        select(StorageImport).where(
            StorageImport.connection_id == row.id, StorageImport.request_key == payload.request_key
        )
    )
    if previous:
        if previous.payload_hash != digest:
            raise HTTPException(409, "Import request key already used for different content.")
        return previous
    run = StorageImport(
        connection_id=row.id,
        request_key=payload.request_key,
        payload_hash=digest,
        audience=payload.audience,
        workspace_id=payload.workspace_id,
        items=[{"key": key, "status": "pending"} for key in dict.fromkeys(payload.keys)],
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
                )
        items.append(item)
    status = run.status
    if status in {"completed", "attention"}:
        status = "completed" if all(i["status"] == "published" for i in items) else "attention"
    return {
        "id": str(run.id),
        "status": status,
        "items": items,
        "audience": run.audience,
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
                        Publication.audience == previous.audience,
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
        if source["status"] not in {"pending", "downloading"}:
            continue
        item = dict(source)
        row = db.get(StorageConnection, run.connection_id, populate_existing=True)
        try:
            destination(db, row, run.audience, run.workspace_id)
            item["status"] = "downloading"
            run.items = [dict(v) if i != index else item for i, v in enumerate(run.items)]
            db.commit()
            raw, mime, provenance = BucketClient(row, settings).download(item["key"])
            # Serialize publication with disconnect/credential rotation and membership validation.
            db.refresh(row, with_for_update=True)
            user = destination(db, row, run.audience, run.workspace_id)
            request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(settings=settings)))
            identity = json.dumps(
                [
                    str(row.id),
                    item["key"],
                    provenance["sha256"],
                    run.audience,
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
                    run.audience,
                    run.workspace_id,
                    request_key,
                )
            )
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
            destination(db, row, run.audience, run.workspace_id)
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
    destination(db, connection, rule.audience, rule.workspace_id)
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
                audience=rule.audience,
                workspace_id=rule.workspace_id,
            ),
        )
        db.flush()
        run_id = run.id
    else:
        run_id = None
    rule.cursor = page["next_cursor"]
    rule.next_run = now() + timedelta(minutes=1 if rule.cursor else rule.interval_minutes)
    rule.error = None
    db.commit()
    if run_id:
        dispatch(db.get(StorageImport, run_id), settings)
        if not settings.enqueue_processing:
            process_import(db, run_id, settings)
    return run_id
