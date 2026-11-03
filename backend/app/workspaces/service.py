import hashlib
import json
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select

from app.social_features.models import Publication
from app.workspaces.models import ImportRun, Record, RecordMedia, RecordRevision


def record_json(row):
    return {
        "id": str(row.id),
        "workspace_id": str(row.workspace_id),
        "connection_id": str(row.connection_id),
        "external_id": row.external_id,
        "kind": row.kind,
        "title": row.title,
        "version": row.version,
        "status": row.status,
        "data": row.data,
        "related_ids": row.related_ids,
        "occurred_at": row.occurred_at.isoformat(),
        "updated_at": row.updated_at.isoformat(),
        "simulated": row.simulated,
    }


def import_batch(db, connection, payload):
    serialized = json.dumps(payload.model_dump(mode="json"), sort_keys=True)
    if len(serialized.encode()) > 2 * 1024 * 1024:
        raise HTTPException(413, "Batch exceeds 2 MiB.")
    digest = hashlib.sha256(serialized.encode()).hexdigest()
    previous = db.scalar(
        select(ImportRun).where(
            ImportRun.connection_id == connection.id, ImportRun.request_key == payload.request_key
        )
    )
    if previous:
        if previous.payload_hash != digest:
            raise HTTPException(409, "Request key already used for different content.")
        return previous.result
    external_ids = [r.external_id for r in payload.records]
    if len(set(external_ids)) != len(external_ids):
        raise HTTPException(422, "Duplicate external IDs in batch.")
    existing = {
        r.external_id: r
        for r in db.scalars(select(Record).where(Record.connection_id == connection.id))
    }
    available = set(existing) | set(external_ids)
    targets = {**existing, **{r.external_id: r for r in payload.records}}
    # Atomic validation: incomplete graphs do not become searchable.
    for entry in payload.records:
        if set(entry.related_ids) - available:
            raise HTTPException(422, f"Unresolved relationships for {entry.external_id}.")
        previous_row = existing.get(entry.external_id)
        if previous_row and (
            entry.kind != previous_row.kind or entry.version <= previous_row.version
        ):
            raise HTTPException(
                409, f"Version must increase and kind must stay unchanged: {entry.external_id}."
            )
    # Validate the resulting graph, including unchanged clinical history. A
    # person withdrawal must not leave active prescriptions or allergies orphaned.
    for entry in targets.values():
        if entry.status == "active" and entry.kind in {"prescription", "allergy", "administration"}:
            patients = [targets[key] for key in entry.related_ids if targets[key].kind == "person"]
            if len(patients) != 1 or patients[0].status != "active":
                raise HTTPException(
                    422, f"Clinical record requires one active person: {entry.external_id}."
                )
    rows = []
    now = datetime.now(UTC)
    for entry in payload.records:
        row = existing.get(entry.external_id)
        if row is None:
            row = Record(
                workspace_id=connection.workspace_id,
                connection_id=connection.id,
                external_id=entry.external_id,
            )
            db.add(row)
        for field in (
            "kind",
            "title",
            "version",
            "status",
            "data",
            "related_ids",
            "occurred_at",
            "simulated",
        ):
            setattr(row, field, getattr(entry, field))
        row.updated_at = now
        db.flush()
        snapshot = record_json(row)
        db.add(RecordRevision(record_id=row.id, version=row.version, snapshot=snapshot))
        if row.status != "active":
            for link in db.scalars(select(RecordMedia).where(RecordMedia.record_id == row.id)):
                if link.publication_id:
                    post = db.get(Publication, link.publication_id)
                    if post.source == "workspace-import":
                        post.hidden = True
        rows.append(
            {
                "id": str(row.id),
                "external_id": row.external_id,
                "version": row.version,
                "status": row.status,
            }
        )
    run = ImportRun(
        connection_id=connection.id, request_key=payload.request_key, payload_hash=digest
    )
    db.add(run)
    db.flush()
    run.result = {"id": str(run.id), "status": "completed", "records": rows}
    return run.result
