import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.models import MediaAsset, Role, User
from app.security import hash_device_credential
from app.workspaces.models import (
    Connection,
    ImportRun,
    Record,
    RecordMedia,
    RecordNote,
    RecordRevision,
)
from app.workspaces.schemas import ConnectionCreate, ImportBatch, NoteCreate
from app.workspaces.service import import_batch, record_json

router = APIRouter(tags=["workspace-data"])


def connection_json(row):
    return {
        "id": str(row.id),
        "workspace_id": str(row.workspace_id),
        "name": row.name,
        "active": row.active,
        "source_url": row.source_url,
        "has_source_token": bool(row.secret_encrypted),
    }


async def integration(request: Request, db: Session = Depends(get_db)):
    key = request.headers.get("X-RealityOS-Integration-Key", "")
    row = (
        db.scalar(
            select(Connection).where(
                Connection.token_hash == hash_device_credential(key, request.app.state.settings),
                Connection.active.is_(True),
            )
        )
        if key
        else None
    )
    if row is None:
        raise HTTPException(401, "Invalid integration credential.")
    # Revocation of the administrator's membership also revokes ingestion.
    workspace_member(row.workspace_id, db.get(User, row.created_by_id), db, {Role.ADMIN})
    return row


@router.post("/workspaces/{workspace_id}/connections", status_code=201)
async def create_connection(
    workspace_id: uuid.UUID,
    payload: ConnectionCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    from app.workspaces.sync import encrypt_secret, validate_source

    if payload.source_url:
        validate_source(payload.source_url, request.app.state.settings)
    secret = secrets.token_urlsafe(32)
    row = Connection(
        workspace_id=workspace_id,
        created_by_id=user.id,
        name=payload.name,
        token_hash=hash_device_credential(secret, request.app.state.settings),
        source_url=payload.source_url,
        secret_encrypted=encrypt_secret(payload.source_token, request.app.state.settings)
        if payload.source_token
        else None,
    )
    db.add(row)
    db.flush()
    return {**connection_json(row), "integration_key": secret}


@router.get("/workspaces/{workspace_id}/connections")
async def connections(
    workspace_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    return [
        connection_json(row)
        for row in db.scalars(select(Connection).where(Connection.workspace_id == workspace_id))
    ]


@router.delete("/workspaces/{workspace_id}/connections/{connection_id}")
async def revoke_connection(
    workspace_id: uuid.UUID,
    connection_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    row = db.get(Connection, connection_id)
    if row is None or row.workspace_id != workspace_id:
        raise HTTPException(404)
    row.active = False
    row.secret_encrypted = None
    return {"status": "revoked"}


@router.post("/integrations/imports")
async def ingest(
    payload: ImportBatch, source: Connection = Depends(integration), db: Session = Depends(get_db)
):
    # Serialize writes per source, including concurrent idempotent retries.
    db.refresh(source, with_for_update=True)
    return import_batch(db, source, payload)


@router.get("/integrations/imports/{run_id}")
async def import_status(
    run_id: uuid.UUID, source: Connection = Depends(integration), db: Session = Depends(get_db)
):
    row = db.get(ImportRun, run_id)
    if row is None or row.connection_id != source.id:
        raise HTTPException(404)
    return row.result


def scoped_record(db, workspace_id, record_id):
    row = db.get(Record, record_id)
    if row is None or row.workspace_id != workspace_id or row.status != "active":
        raise HTTPException(404, "Record not available.")
    return row


@router.get("/workspaces/{workspace_id}/records")
async def records(
    workspace_id: uuid.UUID,
    q: str = Query(default="", max_length=200),
    kind: str | None = None,
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db)
    query = select(Record).where(Record.workspace_id == workspace_id, Record.status == "active")
    if kind:
        query = query.where(Record.kind == kind)
    if q:
        query = query.where(
            Record.title.ilike(f"%{q}%", escape="\\")
            | Record.external_id.ilike(f"%{q}%", escape="\\")
        )
    return [
        record_json(row)
        for row in db.scalars(
            query.order_by(Record.occurred_at.desc(), Record.id).offset(offset).limit(50)
        )
    ]


@router.get("/workspaces/{workspace_id}/records/{record_id}")
async def record_detail(
    workspace_id: uuid.UUID,
    record_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db)
    row = scoped_record(db, workspace_id, record_id)
    related = list(
        db.scalars(
            select(Record).where(
                Record.connection_id == row.connection_id, Record.status == "active"
            )
        )
    )
    related = [
        r for r in related if r.external_id in row.related_ids or row.external_id in r.related_ids
    ]
    notes = list(
        db.scalars(
            select(RecordNote)
            .where(RecordNote.record_id == row.id)
            .order_by(RecordNote.occurred_at)
        )
    )
    media = db.execute(
        select(RecordMedia, MediaAsset.mime_type, MediaAsset.byte_size)
        .join(MediaAsset, RecordMedia.media_id == MediaAsset.id)
        .where(RecordMedia.record_id == row.id)
    ).all()
    return {
        **record_json(row),
        "related": [record_json(r) for r in related],
        "notes": [
            {
                "id": str(n.id),
                "text": n.text,
                "actor_id": str(n.actor_id),
                "occurred_at": n.occurred_at.isoformat(),
            }
            for n in notes
        ],
        "media": [
            {
                "id": str(m.id),
                "url": f"/v1/workspaces/{workspace_id}/record-media/{m.id}",
                "mime_type": mime,
                "byte_size": size,
                "external_id": m.external_id,
            }
            for m, mime, size in media
        ],
    }


@router.post("/workspaces/{workspace_id}/records/{record_id}/notes", status_code=201)
async def add_note(
    workspace_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: NoteCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    scoped_record(db, workspace_id, record_id)
    note = RecordNote(
        record_id=record_id, actor_id=user.id, text=payload.text, occurred_at=payload.occurred_at
    )
    db.add(note)
    db.flush()
    return {"id": str(note.id), "status": "recorded"}


@router.get("/workspaces/{workspace_id}/records/{record_id}/revisions")
async def revisions(
    workspace_id: uuid.UUID,
    record_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db, {Role.ADMIN})
    row = db.get(Record, record_id)
    if row is None or row.workspace_id != workspace_id:
        raise HTTPException(404)
    return [
        r.snapshot
        for r in db.scalars(
            select(RecordRevision)
            .where(RecordRevision.record_id == record_id)
            .order_by(RecordRevision.version)
        )
    ]


class PublicationLink(__import__("pydantic").BaseModel):
    publication_id: uuid.UUID


@router.post("/workspaces/{workspace_id}/records/{record_id}/publications", status_code=201)
async def link_publication(
    workspace_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: PublicationLink,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db, {Role.ADMIN, Role.REGISTER})
    scoped_record(db, workspace_id, record_id)
    from app.social_features.models import Publication

    post = db.get(Publication, payload.publication_id)
    if post is None or post.workspace_id != workspace_id or post.audience != "work" or post.hidden:
        raise HTTPException(404, "Publication unavailable in this workspace.")
    external_id = f"local-publication:{post.id}"
    existing = db.scalar(
        select(RecordMedia).where(
            RecordMedia.record_id == record_id, RecordMedia.external_id == external_id
        )
    )
    if not existing:
        existing = RecordMedia(
            record_id=record_id,
            external_id=external_id,
            media_id=post.media_id,
            publication_id=post.id,
        )
        db.add(existing)
        db.flush()
    return {"id": str(existing.id)}
