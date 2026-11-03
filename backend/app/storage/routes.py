import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import Response
from fastapi.routing import APIRoute
from PIL import Image, ImageOps
from sqlalchemy import select
from starlette.datastructures import Headers

from app.dependencies import get_current_user, get_db
from app.storage.client import BucketClient, encrypt, endpoint_address
from app.storage.models import StorageConnection, StorageImport, StorageSync
from app.storage.schemas import ConnectionInput, ImportInput, KeyInput, SyncInput
from app.storage.service import (
    create_import,
    destination,
    dispatch,
    import_json,
    now,
    owned,
    process_import,
    sync_page,
)


class StorageRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def validated(request):
            try:
                return await handler(request)
            except RequestValidationError as exc:
                # Model errors can include the whole credential-bearing body.
                errors = [
                    {key: error[key] for key in ("loc", "msg", "type")} for error in exc.errors()
                ]
                raise HTTPException(422, errors) from None

        return validated


router = APIRouter(
    prefix="/me/storage-connections", tags=["storage-connections"], route_class=StorageRoute
)


def connection_json(row):
    return {
        k: getattr(row, k)
        for k in (
            "id",
            "name",
            "provider",
            "endpoint",
            "bucket",
            "region",
            "prefix",
            "active",
            "workspace_id",
            "revision",
        )
    }


def configure(row, payload, settings):
    endpoint_address(payload.endpoint)
    if payload.provider == "r2" and not payload.endpoint.rstrip("/").endswith(
        ".r2.cloudflarestorage.com"
    ):
        raise HTTPException(422, "Use the R2 S3 API endpoint.")
    if payload.access_key:
        row.secret = encrypt(
            settings, payload.access_key.get_secret_value(), payload.secret_key.get_secret_value()
        )
    elif not row.secret:
        raise HTTPException(422, "Provide storage credentials.")
    for key in ("name", "provider", "endpoint", "bucket", "region", "prefix"):
        setattr(row, key, getattr(payload, key))


@router.get("")
def connections(user=Depends(get_current_user), db=Depends(get_db)):
    return [
        connection_json(r)
        for r in db.scalars(
            select(StorageConnection).where(
                StorageConnection.owner_id == user.id, StorageConnection.active.is_(True)
            )
        )
    ]


def selected_workspace(db, user, requested, previous=None):
    from app.models import Workspace, WorkspaceMember
    from app.social_features.uploads import check_destination

    target = requested or previous
    if target is None:
        options = list(
            db.scalars(
                select(Workspace.id)
                .join(WorkspaceMember)
                .where(WorkspaceMember.user_id == user.id, ~Workspace.name.startswith("home:"))
            )
        )
        if len(options) == 1:
            target = options[0]
    check_destination(db, user, "work", target)
    return target


def enable_default_sync(db, row):
    rule = StorageSync(
        connection_id=row.id,
        prefix=row.prefix,
        audience="work",
        workspace_id=row.workspace_id,
        interval_minutes=15,
        enabled=True,
        next_run=now(),
        seen_keys=[],
    )
    db.add(rule)
    db.flush()
    return rule


@router.post("", status_code=201)
def create(
    payload: ConnectionInput, request: Request, user=Depends(get_current_user), db=Depends(get_db)
):
    if user.is_guest:
        raise HTTPException(403, "Sign in to connect storage.")
    target = selected_workspace(db, user, payload.workspace_id)
    row = StorageConnection(owner_id=user.id, workspace_id=target, revision=1)
    configure(row, payload, request.app.state.settings)
    BucketClient(row, request.app.state.settings).objects()
    db.add(row)
    db.flush()
    enable_default_sync(db, row)
    return connection_json(row)


@router.put("/{connection_id}")
def update(
    connection_id: uuid.UUID,
    payload: ConnectionInput,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    from app.storage.lifecycle import retire_connection

    row = owned(db, connection_id, user)
    db.refresh(row, with_for_update=True)
    target = selected_workspace(db, user, payload.workspace_id, row.workspace_id)
    identity = ("provider", "endpoint", "bucket", "region", "prefix")
    changed = any(getattr(payload, k).rstrip("/") != getattr(row, k).rstrip("/") for k in identity)
    changed |= target != row.workspace_id
    # Validate a temporary configuration before retiring anything.
    trial = StorageConnection(owner_id=user.id, secret=row.secret)
    configure(trial, payload, request.app.state.settings)
    BucketClient(trial, request.app.state.settings).objects()
    if changed:
        retire_connection(db, row)
    configure(row, payload, request.app.state.settings)
    row.workspace_id = target
    if changed:
        enable_default_sync(db, row)
    return connection_json(row)


@router.delete("/{connection_id}")
def disconnect(connection_id: uuid.UUID, user=Depends(get_current_user), db=Depends(get_db)):
    from app.storage.lifecycle import retire_connection

    row = owned(db, connection_id, user)
    db.refresh(row, with_for_update=True)
    retire_connection(db, row)
    row.active, row.secret = False, ""
    return {"status": "disconnected", "imported_copies_retained": False}


@router.post("/{connection_id}/test")
def test(
    connection_id: uuid.UUID, request: Request, user=Depends(get_current_user), db=Depends(get_db)
):
    row = owned(db, connection_id, user)
    BucketClient(row, request.app.state.settings).objects()
    return {"status": "connected"}


@router.get("/{connection_id}/objects")
def objects(
    connection_id: uuid.UUID,
    request: Request,
    prefix: str = "",
    cursor: str | None = Query(None, max_length=4096),
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    return BucketClient(owned(db, connection_id, user), request.app.state.settings).objects(
        prefix, cursor
    )


@router.get("/{connection_id}/content")
def content(
    connection_id: uuid.UUID,
    request: Request,
    key: str = Query(max_length=1024),
    preview: bool = False,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    raw, mime, _ = BucketClient(
        owned(db, connection_id, user), request.app.state.settings
    ).download(key)
    if preview:
        if mime == "video/mp4":
            from types import SimpleNamespace

            from app.social_features.video_uploads import preview_bytes

            raw = preview_bytes(SimpleNamespace(mime_type=mime, original_bytes=raw))
        elif not mime.startswith("image/"):
            raise HTTPException(415, "Preview supports images and MP4.")
        try:
            with Image.open(io.BytesIO(raw)) as picture:
                image = ImageOps.exif_transpose(picture).convert("RGB")
                image.thumbnail((480, 480))
                output = io.BytesIO()
                image.save(output, "JPEG")
                raw, mime = output.getvalue(), "image/jpeg"
        except (OSError, ValueError) as exc:
            raise HTTPException(422, "Invalid image.") from exc
    headers = {
        "Cache-Control": "private, no-store",
        "X-Content-Type-Options": "nosniff",
        "Accept-Ranges": "bytes",
    }
    if range_header := request.headers.get("range"):
        from app.social_features.gallery import _parse_range

        bounds = _parse_range(range_header.strip(), len(raw))
        if bounds is None:
            return Response(
                status_code=416, headers=headers | {"Content-Range": f"bytes */{len(raw)}"}
            )
        start, end = bounds
        return Response(
            raw[start : end + 1],
            status_code=206,
            media_type=mime,
            headers=headers | {"Content-Range": f"bytes {start}-{end}/{len(raw)}"},
        )
    return Response(raw, media_type=mime, headers=headers)


@router.post("/{connection_id}/cv")
async def cv(
    connection_id: uuid.UUID,
    payload: KeyInput,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    import asyncio

    from app.social_features.profiles import upload_cv

    row = owned(db, connection_id, user)
    revision = row.revision
    raw, mime, provenance = await asyncio.to_thread(
        BucketClient(row, request.app.state.settings).download, payload.key
    )
    db.refresh(row, with_for_update=True)
    owned(db, connection_id, user)
    if row.revision != revision:
        raise HTTPException(409, "The source connection has changed.")
    result = await upload_cv(
        request,
        UploadFile(
            io.BytesIO(raw),
            filename=payload.key.rsplit("/", 1)[-1],
            headers=Headers({"content-type": mime}),
        ),
        user,
        db,
    )
    from app.storage.provenance_models import StorageObject

    db.refresh(row, with_for_update=True)
    owned(db, connection_id, user)
    if row.revision != revision:
        raise HTTPException(409, "The source connection has changed.")
    source = db.scalar(
        select(StorageObject).where(
            StorageObject.connection_id == row.id,
            StorageObject.revision == row.revision,
            StorageObject.key == "cv:" + payload.key,
        )
    )
    if source is None:
        source = StorageObject(connection_id=row.id, revision=row.revision, key="cv:" + payload.key)
        db.add(source)
    source.sha256, source.retired = provenance["sha256"], False
    return result


@router.post("/{connection_id}/imports", status_code=202)
def start_import(
    connection_id: uuid.UUID,
    payload: ImportInput,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    row = owned(db, connection_id, user)
    db.refresh(row, with_for_update=True)
    payload = payload.model_copy(update={"workspace_id": payload.workspace_id or row.workspace_id})
    run = create_import(db, row, payload)
    db.commit()
    dispatch(run, request.app.state.settings)
    if not request.app.state.settings.enqueue_processing:
        process_import(db, run.id, request.app.state.settings)
    return import_json(db, run)


@router.get("/{connection_id}/imports")
def imports(connection_id: uuid.UUID, user=Depends(get_current_user), db=Depends(get_db)):
    owned(db, connection_id, user)
    return [
        import_json(db, r)
        for r in db.scalars(
            select(StorageImport)
            .where(StorageImport.connection_id == connection_id)
            .order_by(StorageImport.created_at.desc())
            .limit(30)
        )
    ]


@router.post("/{connection_id}/imports/{run_id}/retry")
def retry(
    connection_id: uuid.UUID,
    run_id: uuid.UUID,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    row = owned(db, connection_id, user)
    run = db.get(StorageImport, run_id)
    if not run or run.connection_id != row.id:
        raise HTTPException(404)
    db.refresh(run, with_for_update=True)
    destination(db, row, run.audience, run.workspace_id)
    if run.status not in {"attention", "completed"}:
        raise HTTPException(409, "Import is still running.")
    items = []
    for value in import_json(db, run)["items"]:
        item = dict(value)
        if item["status"] == "failed":
            if item.get("upload_id"):
                from app.social_features.evidence_models import PublicationUpload

                upload = db.get(PublicationUpload, uuid.UUID(item["upload_id"]))
                if upload and upload.status == "failed":
                    upload.status = "pending"
            item["status"] = "pending"
        items.append(item)
    run.items, run.status = items, "pending"
    db.commit()
    dispatch(run, request.app.state.settings)
    if not request.app.state.settings.enqueue_processing:
        process_import(db, run.id, request.app.state.settings)
    return import_json(db, run)


@router.get("/{connection_id}/syncs")
def syncs(connection_id: uuid.UUID, user=Depends(get_current_user), db=Depends(get_db)):
    owned(db, connection_id, user)
    return list(db.scalars(select(StorageSync).where(StorageSync.connection_id == connection_id)))


@router.post("/{connection_id}/syncs", status_code=201)
def create_sync(
    connection_id: uuid.UUID, payload: SyncInput, user=Depends(get_current_user), db=Depends(get_db)
):
    row = owned(db, connection_id, user)
    prefix = (payload.prefix.rstrip("/") + "/") if payload.prefix else row.prefix
    if not prefix.startswith(row.prefix):
        raise HTTPException(422, "Folder is outside the connection.")
    payload = payload.model_copy(update={"workspace_id": payload.workspace_id or row.workspace_id})
    destination(db, row, payload.audience, payload.workspace_id)
    existing = db.scalar(
        select(StorageSync).where(
            StorageSync.connection_id == row.id,
            StorageSync.prefix == prefix,
            StorageSync.workspace_id == payload.workspace_id,
        )
    )
    if existing:
        existing.interval_minutes, existing.enabled = payload.interval_minutes, payload.enabled
        existing.next_run = now()
        return {"id": str(existing.id), "enabled": existing.enabled}
    rule = StorageSync(
        connection_id=row.id,
        prefix=prefix,
        audience=payload.audience,
        workspace_id=payload.workspace_id,
        interval_minutes=payload.interval_minutes,
        enabled=payload.enabled,
        next_run=now(),
    )
    db.add(rule)
    db.flush()
    return {"id": str(rule.id), "enabled": rule.enabled}


@router.post("/{connection_id}/syncs/{rule_id}/run", status_code=202)
def run_sync(
    connection_id: uuid.UUID,
    rule_id: uuid.UUID,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    row = owned(db, connection_id, user)
    rule = db.scalar(
        select(StorageSync)
        .where(StorageSync.id == rule_id, StorageSync.connection_id == row.id)
        .with_for_update()
    )
    if not rule:
        raise HTTPException(404)
    run_id = sync_page(db, rule, request.app.state.settings)
    return {"import_id": str(run_id) if run_id else None, "has_more": bool(rule.cursor)}


@router.delete("/{connection_id}/syncs/{rule_id}")
def stop_sync(
    connection_id: uuid.UUID, rule_id: uuid.UUID, user=Depends(get_current_user), db=Depends(get_db)
):
    owned(db, connection_id, user)
    rule = db.get(StorageSync, rule_id)
    if not rule or rule.connection_id != connection_id:
        raise HTTPException(404)
    db.refresh(rule, with_for_update=True)
    rule.enabled = False
    return {"enabled": False}
