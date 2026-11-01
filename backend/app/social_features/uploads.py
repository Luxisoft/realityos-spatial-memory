"""Private automatic upload review and explicit duplicate replacement."""

from __future__ import annotations

import asyncio
import io
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from PIL import Image
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.meta import build_meta_client
from app.models import User, Workspace
from app.social_features.evidence_models import PublicationUpload
from app.social_features.upload_service import confirm_replace, process_upload

router = APIRouter()


def owned(db, key, user):
    upload = db.get(PublicationUpload, key)
    if not upload or upload.owner_id != user.id:
        raise HTTPException(404, "Upload unavailable.")
    return upload


def payload(upload):
    return dict(
        id=str(upload.id),
        status=upload.status,
        error=upload.error,
        result_id=str(upload.result_id) if upload.result_id else None,
        duplicate_id=str(upload.duplicate_id) if upload.duplicate_id else None,
        preview_url=f"/v1/me/publication-uploads/{upload.id}/preview",
        duplicate_preview_url=f"/v1/gallery/{upload.duplicate_id}/thumbnail"
        if upload.duplicate_id
        else None,
    )


def check_destination(db, user, audience, workspace_id):
    if audience == "work":
        if not workspace_id:
            raise HTTPException(422, "Choose a work group.")
        workspace_member(workspace_id, user, db)
        space = db.get(Workspace, workspace_id)
        if not space or space.name.startswith("home:"):
            raise HTTPException(422, "Choose a work group.")
    elif workspace_id:
        raise HTTPException(422, "Only work publications accept a group.")


async def candidate(
    request, file, caption, note_text, note_source, user, db, audience, workspace_id, request_key
):
    from app.social_features.profiles import _checked_note

    check_destination(db, user, audience, workspace_id)
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
            or old.audience != audience
            or old.workspace_id != workspace_id
            or old.caption != caption
            or old.note_text != note
            or old.note_source != source
        ):
            raise HTTPException(409, "Upload key already used.")
        return old
    upload = PublicationUpload(
        owner_id=user.id,
        request_key=request_key,
        audience=audience,
        workspace_id=workspace_id,
        original_bytes=raw,
        mime_type=file.content_type,
        caption=caption,
        note_text=note,
        note_source=source,
        status="pending",
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
            audience,
            workspace_id,
            request_key,
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
    audience: Literal["home", "work", "public"] = Form("home"),
    workspace_id: uuid.UUID | None = Form(None),
    caption: str = Form("", max_length=4000),
    note_text: str = Form("", max_length=4000),
    note_source: str = Form(""),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    upload = await candidate(
        request,
        file,
        caption,
        note_text,
        note_source,
        user,
        db,
        audience,
        workspace_id,
        request_key,
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
    upload = owned(db, upload_id, user)
    if upload.workspace_id:
        workspace_member(upload.workspace_id, user, db)
    from app.social_features.video_uploads import preview_bytes

    with Image.open(io.BytesIO(preview_bytes(upload))) as source:
        from PIL import ImageOps

        image = ImageOps.exif_transpose(source).convert("RGB")
        image.thumbnail((360, 480))
        output = io.BytesIO()
        image.save(output, "JPEG")
    return Response(
        output.getvalue(), media_type="image/jpeg", headers={"Cache-Control": "private, no-store"}
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
    check_destination(db, user, upload.audience, upload.workspace_id)
    upload.status = "pending"
    upload.error = None
    upload.duplicate_id = None
    upload.expected_media_id = None
    await enqueue(db, upload, request)
    return payload(upload)


async def legacy_upload(
    request, file, caption, note_text, note_source, user, db, audience="home", workspace_id=None
):
    from app.social_features.gallery import _publication_payload

    upload = await candidate(
        request,
        file,
        caption,
        note_text,
        note_source,
        user,
        db,
        audience,
        workspace_id,
        str(uuid.uuid4()),
    )
    await asyncio.to_thread(
        process_upload, db, upload.id, build_meta_client(request.app.state.settings)
    )
    db.commit()
    if upload.status == "duplicate":
        return JSONResponse(
            status_code=409,
            content={
                "detail": "This photo already exists. Update the app to confirm replacement.",
                "upload": payload(upload),
            },
        )
    if upload.status != "published":
        raise HTTPException(503, upload.error or "Analysis unavailable.")
    from app.social_features.models import Publication

    return _publication_payload(db.get(Publication, upload.result_id), user, db)
