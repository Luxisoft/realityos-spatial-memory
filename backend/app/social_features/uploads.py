"""Private automatic upload review and explicit duplicate replacement."""

from __future__ import annotations

import asyncio
import io
import json
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from PIL import Image
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.meta import build_meta_client
from app.models import User
from app.social_features.classification_schemas import ClassificationInput
from app.social_features.classification_service import validate_classification
from app.social_features.evidence_models import PublicationUpload
from app.social_features.publication_access import check_destination as check_destination
from app.social_features.upload_service import confirm_replace, process_upload, upload_preview
from app.social_features.upload_service import owned as owned

router = APIRouter()


def payload(upload):
    return dict(
        id=str(upload.id),
        workspace_id=str(upload.workspace_id) if upload.workspace_id else None,
        category_id=str(upload.category_id) if upload.category_id else None,
        tag_ids=upload.tag_ids,
        status=upload.status,
        error=upload.error,
        result_id=str(upload.result_id) if upload.result_id else None,
        duplicate_id=str(upload.duplicate_id) if upload.duplicate_id else None,
        preview_url=f"/v1/me/publication-uploads/{upload.id}/preview",
        duplicate_preview_url=f"/v1/gallery/{upload.duplicate_id}/thumbnail"
        if upload.duplicate_id
        else None,
    )


async def candidate(
    request,
    file,
    caption,
    note_text,
    note_source,
    user,
    db,
    workspace_id,
    request_key,
    category_id=None,
    tag_ids=None,
    allow_unclassified=False,
):
    from app.social_features.notes import _checked_note

    check_destination(db, user, workspace_id)
    if not allow_unclassified or category_id is not None or tag_ids:
        category_id, tag_ids = validate_classification(db, workspace_id, category_id, tag_ids)
    tags = sorted(str(key) for key in (tag_ids or []))
    note, source = _checked_note(note_text, note_source)
    is_video = file.content_type == "video/mp4"
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "video/mp4"}:
        raise HTTPException(415, "Only JPEG, PNG, WebP and MP4 are accepted.")
    settings = request.app.state.settings
    maximum = settings.max_video_bytes if is_video else settings.max_image_bytes
    raw = await file.read(maximum + 1 if maximum else -1)
    if not raw or (maximum and len(raw) > maximum):
        raise HTTPException(413, "Media exceeds permitted size.")
    if is_video:
        from app.social_features.video_uploads import validate_video

        await asyncio.to_thread(validate_video, raw, settings)
    else:
        try:
            with Image.open(io.BytesIO(raw)) as image:
                image.verify()
        except (ValueError, OSError) as exc:
            raise HTTPException(422, "Invalid image.") from exc
    old = db.scalar(
        select(PublicationUpload).where(
            PublicationUpload.owner_id == user.id, PublicationUpload.request_key == request_key
        )
    )
    if old:
        if (
            old.original_bytes != raw
            or old.mime_type != file.content_type
            or old.workspace_id != workspace_id
            or old.caption != caption
            or old.note_text != note
            or old.note_source != source
            or (
                (not allow_unclassified or category_id is not None)
                and (old.category_id != category_id or sorted(old.tag_ids) != tags)
            )
        ):
            raise HTTPException(409, "Upload key already used.")
        return old
    upload = PublicationUpload(
        owner_id=user.id,
        request_key=request_key,
        workspace_id=workspace_id,
        original_bytes=raw,
        mime_type=file.content_type,
        caption=caption,
        note_text=note,
        note_source=source,
        category_id=category_id,
        tag_ids=tags,
        status="pending" if category_id else "awaiting_classification",
    )
    db.add(upload)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(PublicationUpload).where(
                PublicationUpload.owner_id == user.id, PublicationUpload.request_key == request_key
            )
        )
        if existing is None:
            raise HTTPException(409, "Upload destination changed. Retry the upload.")
        await file.seek(0)
        return await candidate(
            request,
            file,
            caption,
            note_text,
            note_source,
            user,
            db,
            workspace_id,
            request_key,
            category_id,
            tag_ids,
            allow_unclassified,
        )
    return upload


async def enqueue(db, upload, request):
    db.commit()
    if request.app.state.settings.enqueue_processing:
        try:
            from app.tasks import process_publication_upload

            process_publication_upload.delay(str(upload.id))
        except Exception:
            upload.status = "failed"
            upload.error = "Processing unavailable. Retry."
            db.commit()
    else:
        await asyncio.to_thread(
            process_upload, db, upload.id, build_meta_client(request.app.state.settings)
        )
        db.commit()


@router.post("/me/publication-uploads", status_code=202)
async def prepare_publication_upload(
    request: Request,
    file: UploadFile = File(...),
    request_key: str = Form(..., max_length=64),
    category_id: uuid.UUID = Form(...),
    tag_ids: str = Form(..., description="JSON array of tag UUIDs from the destination group"),
    workspace_id: uuid.UUID = Form(...),
    caption: str = Form("", max_length=4000),
    note_text: str = Form("", max_length=4000),
    note_source: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    fields = await request.form()
    allowed = {
        "file",
        "request_key",
        "workspace_id",
        "category_id",
        "tag_ids",
        "caption",
        "note_text",
        "note_source",
    }
    if set(fields) - allowed:
        raise HTTPException(
            422, "Unsupported publication fields. Update the app before publishing."
        )
    upload = await candidate(
        request,
        file,
        caption,
        note_text,
        note_source,
        user,
        db,
        workspace_id,
        request_key,
        category_id,
        parse_tag_ids(tag_ids),
    )
    if upload.status == "pending":
        await enqueue(db, upload, request)
    return payload(upload)


@router.get("/me/publication-uploads/{upload_id}")
def publication_upload_status(
    upload_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return payload(owned(db, upload_id, user))


@router.get("/me/publication-uploads/{upload_id}/preview")
def publication_upload_preview(
    upload_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return Response(
        upload_preview(db, upload_id, user),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, no-store"},
    )


@router.post("/me/publication-uploads/{upload_id}/confirm")
def publication_upload_confirm(
    upload_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    upload = confirm_replace(db, owned(db, upload_id, user), user)
    db.commit()
    return payload(upload)


@router.post("/me/publication-uploads/{upload_id}/cancel")
def publication_upload_cancel(
    upload_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    upload = owned(db, upload_id, user)
    if upload.status == "published":
        raise HTTPException(409, "Already published.")
    upload.status = "cancelled"
    return payload(upload)


@router.post("/me/publication-uploads/{upload_id}/retry")
async def publication_upload_retry(
    upload_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    upload = owned(db, upload_id, user)
    if upload.status not in {"failed", "duplicate"}:
        raise HTTPException(409, "Upload cannot be analyzed again in this state.")
    check_destination(db, user, upload.workspace_id)
    upload.status = "pending"
    upload.error = None
    upload.duplicate_id = None
    upload.expected_media_id = None
    await enqueue(db, upload, request)
    return payload(upload)


def parse_tag_ids(value):
    try:
        tags = json.loads(value)
        if not isinstance(tags, list):
            raise ValueError()
        return [uuid.UUID(str(key)) for key in tags]
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, "tag_ids must be a JSON array of tag UUIDs.") from exc


@router.post("/me/publication-uploads/{upload_id}/classify")
async def classify_publication_upload(
    upload_id: uuid.UUID,
    selection: ClassificationInput,
    request: Request,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    from app.storage.lifecycle import check_upload_source

    upload = owned(db, upload_id, user)
    db.refresh(upload, with_for_update=True)
    if upload.status != "awaiting_classification":
        raise HTTPException(409, "This upload is not awaiting classification.")
    check_destination(db, user, upload.workspace_id)
    check_upload_source(db, upload)
    category, tags = validate_classification(
        db, upload.workspace_id, selection.category_id, selection.tag_ids
    )
    upload.category_id, upload.tag_ids = category, sorted(str(key) for key in tags)
    upload.status, upload.error = "pending", None
    await enqueue(db, upload, request)
    return payload(upload)
