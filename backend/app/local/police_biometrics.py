"""Enroll the sixteen fictional Police portraits as record biometric references."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select

from app.local.state import receipt, require_local
from app.local_models import LocalEvaluationState
from app.models import MediaAsset, User, Workspace
from app.workspaces.models import Record, RecordMedia

RECEIPT = "police-biometrics-v1"
WORKSPACE = uuid.UUID("09f6bc06-8d36-5e69-a050-6f690fe1168b")
AUTHORIZED_BY = uuid.UUID("6b70a3aa-0e7b-5234-8245-a923d31bd2ec")
BASIS = (
    "Owner-ordered fictional-case enrollment 2026-11-04 "
    "(AGENTS.md Police biometric enrollment correction)."
)
EXPECTED_RECORDS = 16


def seed_police_biometrics(db, settings, *, engine=None):
    """Enroll each linked Police portrait once, preserving later edits.

    The owner confirmed the portraits depict fictional characters and removed
    the no-enrollment restriction, so each active person record gets one
    traceable record enrollment. Search-time consent gates are untouched:
    this seeds references, never consent.
    """

    require_local(db, settings)
    if db.get(LocalEvaluationState, RECEIPT):
        return {"initialized": False}
    if db.get(LocalEvaluationState, "evaluation-v1") is None:
        raise ValueError("Initialize the local scenarios first.")
    workspace = db.get(Workspace, WORKSPACE)
    if workspace is None:
        return {"initialized": False, "reason": "workspace-removed"}
    if workspace.name != "Pacific Ridge Police Department":
        raise ValueError("Unexpected police workspace; initialization aborted.")
    if db.get(User, AUTHORIZED_BY) is None:
        raise ValueError("Police authorizer account is missing.")
    from app.faces import FaceRecordEnrollment, build_face_engine

    engine = engine or build_face_engine(settings)
    records = list(
        db.scalars(
            select(Record)
            .where(
                Record.workspace_id == WORKSPACE,
                Record.status == "active",
                Record.kind == "person",
            )
            .order_by(Record.title)
        )
    )
    if len(records) != EXPECTED_RECORDS:
        raise ValueError(
            f"Expected {EXPECTED_RECORDS} police person records, found {len(records)}."
        )
    enrolled = 0
    for record in records:
        link = db.scalar(
            select(RecordMedia)
            .where(
                RecordMedia.record_id == record.id,
                RecordMedia.publication_id.is_not(None),
            )
            .order_by(RecordMedia.id)
            .limit(1)
        )
        if link is None:
            raise ValueError(f"Record {record.title} has no linked portrait.")
        asset = db.get(MediaAsset, link.media_id)
        existing = db.scalar(
            select(FaceRecordEnrollment).where(
                FaceRecordEnrollment.record_id == record.id,
                FaceRecordEnrollment.media_asset_id == asset.id,
                FaceRecordEnrollment.face_index == 0,
            )
        )
        if existing is not None and existing.embedding_model == engine.name:
            enrolled += 1
        else:
            if existing is not None:
                db.delete(existing)
                db.flush()
            faces = engine.detect_faces(asset.original_bytes)
            if len(faces) != 1:
                raise ValueError(f"Record {record.title} portrait must show exactly one face.")
            face = faces[0]
            db.add(
                FaceRecordEnrollment(
                    record_id=record.id,
                    workspace_id=WORKSPACE,
                    media_asset_id=asset.id,
                    record_media_id=link.id,
                    face_index=0,
                    embedding_model=engine.name,
                    embedding=face.embedding,
                    bounding_box=face.bounding_box,
                    quality=face.quality,
                    source="record-portrait",
                    authorized_by=AUTHORIZED_BY,
                )
            )
            db.flush()
            enrolled += 1
        if not record.biometric_authorized:
            record.biometric_authorized = True
            record.biometric_basis = BASIS
            record.biometric_authorized_by = AUTHORIZED_BY
            record.biometric_authorized_at = datetime.now(UTC)
            db.flush()
    receipt(db, RECEIPT, "police-biometrics", {"records": len(records), "enrollments": enrolled})
    return {"initialized": True, "records": len(records), "enrollments": enrolled}
