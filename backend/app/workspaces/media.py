import hashlib
import io
import uuid

from fastapi import Depends, File, Form, HTTPException, Request, UploadFile
from PIL import Image, UnidentifiedImageError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.models import MediaAsset, MediaKind, User
from app.social_features.models import Publication
from app.workspaces.models import Connection, Record, RecordMedia
from app.workspaces.routes import authorize_connection, integration, router, scoped_record


@router.post("/integrations/records/{record_id}/media", status_code=201)
async def upload(
    record_id: uuid.UUID,
    request: Request,
    external_id: str = Form(max_length=160),
    publish: bool = Form(default=False),
    author_id: uuid.UUID | None = Form(default=None),
    file: UploadFile = File(),
    source: Connection = Depends(integration),
    db: Session = Depends(get_db),
):
    db.refresh(source, with_for_update=True)
    authorize_connection(db, source)
    record = db.get(Record, record_id)
    if record is None or record.connection_id != source.id or record.status == "deleted":
        raise HTTPException(404)
    if publish and record.status != "active":
        raise HTTPException(409, "Only active records may be published.")
    author = db.get(User, author_id or source.created_by_id)
    if author is None or not author.is_active:
        raise HTTPException(422, "Invalid publication author.")
    workspace_member(source.workspace_id, author, db)
    raw = await file.read(64 * 1024 * 1024 + 1)
    if not raw or len(raw) > 64 * 1024 * 1024:
        raise HTTPException(413, "Each integration attachment must be between 1 byte and 64 MiB.")
    mime = file.content_type
    width = height = None
    if mime in {"image/jpeg", "image/png", "image/webp"}:
        try:
            with Image.open(io.BytesIO(raw)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise HTTPException(422, "Use JPEG, PNG or WebP image content.")
                if image.width * image.height > 40_000_000:
                    raise HTTPException(413, "Image exceeds 40 megapixels.")
                image.verify()
                mime = Image.MIME[image.format]
                width, height = image.size
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise HTTPException(422, "Invalid image.") from exc
    elif mime == "video/mp4":
        from app.social_features.video_uploads import validate_video

        validate_video(raw, request.app.state.settings)
    else:
        raise HTTPException(415, "Use JPEG, PNG, WebP or MP4.")
    digest = hashlib.sha256(raw).hexdigest()
    link = db.scalar(
        select(RecordMedia).where(
            RecordMedia.record_id == record_id, RecordMedia.external_id == external_id
        )
    )
    if link:
        if (
            db.get(MediaAsset, link.media_id).sha256 != digest
            or bool(link.publication_id) != publish
            or (
                link.publication_id
                and db.get(Publication, link.publication_id).owner_id != author.id
            )
        ):
            raise HTTPException(409, "Attachment ID already used. Use a new ID for a new revision.")
        return {
            "id": str(link.id),
            "media_id": str(link.media_id),
            "publication_id": str(link.publication_id) if link.publication_id else None,
        }
    asset = MediaAsset(
        workspace_id=source.workspace_id,
        kind=MediaKind.VIDEO if mime == "video/mp4" else MediaKind.IMAGE,
        mime_type=mime,
        original_bytes=raw,
        sha256=digest,
        byte_size=len(raw),
        width=width,
        height=height,
        captured_at=record.occurred_at,
        extra_metadata={
            "source": "workspace_import",
            "record_id": str(record.id),
            "simulated": record.simulated,
        },
    )
    db.add(asset)
    db.flush()
    post = None
    if publish:
        post = Publication(
            owner_id=author.id,
            media_id=asset.id,

            workspace_id=source.workspace_id,
            caption=record.title,
            source="workspace-import",
            source_ref=str(uuid.uuid4()),
            published_at=record.occurred_at,
        )
        db.add(post)
        db.flush()
    link = RecordMedia(
        record_id=record_id,
        external_id=external_id,
        media_id=asset.id,
        publication_id=post.id if post else None,
    )
    db.add(link)
    db.commit()
    if post:
        from app.tasks import index_gallery_media

        try:
            index_gallery_media.delay(str(post.id))
        except Exception:
            post.index_error = "Index dispatch pending; retry using the index endpoint."
            db.commit()
    return {
        "id": str(link.id),
        "media_id": str(asset.id),
        "publication_id": str(post.id) if post else None,
    }


@router.post("/integrations/records/{record_id}/index")
async def retry_index(
    record_id: uuid.UUID, source: Connection = Depends(integration), db: Session = Depends(get_db)
):
    row = scoped_record(db, source.workspace_id, record_id)
    if row.connection_id != source.id:
        raise HTTPException(404)
    from app.tasks import index_gallery_media

    count = 0
    for link in db.scalars(select(RecordMedia).where(RecordMedia.record_id == row.id)):
        if link.publication_id:
            index_gallery_media.delay(str(link.publication_id))
            count += 1
    return {"queued": count}


@router.get("/workspaces/{workspace_id}/record-media/{link_id}")
async def media(
    workspace_id: uuid.UUID,
    link_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    workspace_member(workspace_id, user, db)
    link = db.get(RecordMedia, link_id)
    if not link:
        raise HTTPException(404)
    scoped_record(db, workspace_id, link.record_id)
    asset = db.get(MediaAsset, link.media_id)
    from app.workspaces.media_response import media_response

    return media_response(db, asset, request.headers.get("range"))
