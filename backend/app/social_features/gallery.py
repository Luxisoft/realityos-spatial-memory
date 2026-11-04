from __future__ import annotations

import io
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from PIL import Image, ImageOps
from pydantic import BaseModel, Field
from sqlalchemy import (
    select,
)
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.faces import delete_selfie_enrollments
from app.models import (
    CaptureSession,
    MediaAsset,
    User,
)
from app.processing.media_ranges import _chunked_slice as _chunked_slice
from app.processing.media_ranges import _parse_range as _parse_range
from app.social_features.classification_schemas import ClassificationInput
from app.social_features.classification_service import (
    set_classification,
)
from app.social_features.gallery_filters import GalleryFilters, gallery_scope
from app.social_features.gallery_queries import _decode_gallery_cursor as _decode_gallery_cursor
from app.social_features.gallery_queries import _encode_gallery_cursor as _encode_gallery_cursor
from app.social_features.gallery_queries import _gallery_page as _gallery_page
from app.social_features.gallery_queries import _publication_payload as _publication_payload
from app.social_features.models import Comment, Publication, Reaction, Report
from app.social_features.notes import merge_transcript_chunks as merge_transcript_chunks
from app.social_features.publication_access import get_post as get_post
from app.social_features.publication_access import visible as visible
from app.social_features.publication_visibility import (
    require_ordinary_media,
)
from app.social_features.schemas import Interaction, Publish, Share

router = APIRouter()


@router.post("/gallery/{post_id}/remove")
def remove_publication(
    post_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    post = get_post(post_id, user, db)
    if post.owner_id != user.id:
        raise HTTPException(403, "Only the owner can remove this publication.")
    post.hidden = True
    return {"ok": True}


@router.post("/gallery/{post_id}/share")
def share(
    post_id: uuid.UUID,
    payload: Share,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    from app.social_features.sharing import import_publications

    get_post(post_id, user, db)
    if not payload.workspace_id:
        raise HTTPException(422, "Choose a work group.")
    result = import_publications(db, user, payload.workspace_id, [post_id], {post_id: payload})
    return {"ok": True, **result}


@router.get("/gallery/page")
def gallery_page(
    workspace_id: uuid.UUID | None = None,
    limit: int = 12,
    cursor: str | None = None,
    filters: GalleryFilters = Depends(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = filters.apply(gallery_scope(db, user, workspace_id))
    return _gallery_page(query, limit, cursor, user, db)


@router.post("/gallery")
def publish(
    payload: Publish,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    asset = db.get(MediaAsset, payload.media_id)
    session = (
        db.get(CaptureSession, asset.capture_session_id)
        if asset and asset.capture_session_id
        else None
    )
    if session is None or session.created_by_id != user.id:
        raise HTTPException(403, "Only the capture owner can publish it.")
    workspace_member(asset.workspace_id, user, db)
    require_ordinary_media(asset, user, db)
    from app.social_features.publication_access import check_destination

    check_destination(db, user, payload.workspace_id)
    from app.meta import build_meta_client
    from app.social_features.upload_service import duplicate, scope_lock

    scope_lock(db, user.id, payload.workspace_id)
    if asset.mime_type.startswith("image/"):
        old = duplicate(
            db,
            build_meta_client(request.app.state.settings),
            asset.original_bytes,
            user.id,
            payload.workspace_id,
        )
        if old:
            if old.media_id == asset.id:
                return {"id": str(old.id)}
            raise HTTPException(
                409,
                "This photo already exists in this destination. Use image upload to confirm replacement.",
            )
    post = Publication(owner_id=user.id, **payload.model_dump(exclude={"tag_ids"}))
    db.add(post)
    db.flush()
    from app.social_features.localizations import prepare_posts

    set_classification(db, post, payload.category_id, payload.tag_ids)
    prepare_posts(db, [post], build_meta_client(request.app.state.settings))
    db.commit()
    from app.gallery_index import queue_publication_index

    queue_publication_index(post.id)
    return {"id": str(post.id)}


@router.post("/me/capture-profile")
def capture_profile(
    request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from app.device_profiles import issue_capture_profile

    profile = issue_capture_profile(db, request.app.state.settings, user)
    # Fresh logins always retake the face capture: drop the previous selfie so
    # verification below can only run against a new photo. Resumed sessions
    # never call this endpoint, so they keep silent re-verification.
    delete_selfie_enrollments(db, user.id)
    db.flush()
    return profile


@router.get("/gallery/{post_id}/media")
def media(
    post_id: uuid.UUID,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from fastapi.responses import Response, StreamingResponse

    from app.models import MediaAssetChunk
    from app.services import media_is_chunked

    post = get_post(post_id, user, db)
    asset = db.get(MediaAsset, post.media_id)
    total = asset.byte_size or 0
    base_headers = {"Cache-Control": "private, no-store", "Accept-Ranges": "bytes"}
    range_header = request.headers.get("range")
    if range_header:
        parsed = _parse_range(range_header.strip(), total)
        if parsed is None:
            return Response(
                b"",
                status_code=416,
                media_type=asset.mime_type,
                headers=base_headers | {"Content-Range": f"bytes */{total}"},
            )
        start, end = parsed
        if media_is_chunked(asset):
            body = _chunked_slice(db, asset.id, start, end)
        else:
            body = asset.original_bytes[start : end + 1]
        return Response(
            body,
            status_code=206,
            media_type=asset.mime_type,
            headers=base_headers
            | {
                "Content-Range": f"bytes {start}-{end}/{total}",
                "Content-Length": str(len(body)),
            },
        )
    if media_is_chunked(asset):

        def chunks():
            yield from db.scalars(
                select(MediaAssetChunk.content)
                .where(MediaAssetChunk.asset_id == asset.id)
                .order_by(MediaAssetChunk.chunk_index)
            )

        return StreamingResponse(
            chunks(),
            media_type=asset.mime_type,
            headers=base_headers | {"Content-Length": str(total)},
        )
    return Response(
        asset.original_bytes,
        media_type=asset.mime_type,
        headers=base_headers | {"Content-Length": str(total)},
    )


@router.get("/gallery/{post_id}/thumbnail")
def thumbnail(
    post_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    from fastapi.responses import Response

    from app.social_features.publication_media import publication_thumbnail

    return Response(
        publication_thumbnail(post_id, user, db),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.get("/gallery/{post_id}/boxed")
def boxed_thumbnail(
    post_id: uuid.UUID,
    labels: str = "",
    full_size: bool = False,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Ephemeral overlay: unfilled boxes around matched AI detections.

    full_size preserves the original image dimensions for the viewer.
    The original BYTEA is never modified. Videos fall back to the plain
    thumbnail because frame-indexed boxes have no single still to annotate.
    """

    from fastapi.responses import Response
    from PIL import ImageDraw

    post = get_post(post_id, user, db)
    asset = db.get(MediaAsset, post.media_id)
    if not asset.mime_type.startswith("image/"):
        return thumbnail(post_id, user, db)
    wanted = {bit.strip().casefold() for bit in labels.split(",") if bit.strip()}

    def _wanted(label: str) -> bool:
        folded = label.casefold()
        if not wanted:
            return True
        return any(term in folded or folded in term for term in wanted)

    boxes = []
    for detection in post.ai_detections or []:
        box = detection.get("box") or {}
        try:
            coords = tuple(float(box.get(key, 0.0)) for key in ("x", "y", "width", "height"))
        except (TypeError, ValueError):
            continue
        x, y, width, height = coords
        if width <= 0 or height <= 0:
            continue
        if _wanted(str(detection.get("label", ""))):
            boxes.append((x, y, width, height))
        if len(boxes) >= 20:
            break
    try:
        with Image.open(io.BytesIO(asset.original_bytes)) as image:
            # Current detections are measured on the normalized upright image.
            # Legacy boxes were drawn on encoded pixels: rotate that whole
            # annotated image afterwards so their existing alignment is kept.
            picture = (
                ImageOps.exif_transpose(image) if post.evidence_version >= 2 else image
            ).convert("RGB")
            draw = ImageDraw.Draw(picture)
            width_px, height_px = picture.size
            outline = max(2, min(width_px, height_px) // 150)
            for x, y, width, height in boxes:
                left = min(max(x, 0.0), 1.0) * width_px
                top = min(max(y, 0.0), 1.0) * height_px
                right = min(max(x + width, 0.0), 1.0) * width_px
                bottom = min(max(y + height, 0.0), 1.0) * height_px
                draw.rectangle([left, top, right, bottom], outline=(255, 196, 0), width=outline)
            if post.evidence_version < 2:
                picture = ImageOps.exif_transpose(picture)
            if not full_size:
                picture.thumbnail((360, 480))
            output = io.BytesIO()
            picture.save(output, format="JPEG", quality=95 if full_size else 85)
    except (ValueError, OSError) as error:
        raise HTTPException(422, "Boxed thumbnail unavailable.") from error
    return Response(
        output.getvalue(),
        media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=300"},
    )


@router.post("/gallery/{post_id}/interactions")
def interact(
    post_id: uuid.UUID,
    payload: Interaction,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    get_post(post_id, user, db)
    if payload.action in {"like", "unlike"}:
        existing = db.get(Reaction, (post_id, user.id))
        if payload.action == "like" and existing is None:
            db.add(Reaction(post_id=post_id, user_id=user.id))
        elif payload.action == "unlike" and existing:
            db.delete(existing)
    else:
        if not payload.text.strip():
            raise HTTPException(422, "Text is required.")
        if payload.action == "comment":
            parent = db.get(Comment, payload.parent_id) if payload.parent_id else None
            if payload.parent_id and (parent is None or parent.post_id != post_id):
                raise HTTPException(422, "Invalid reply target.")
            db.add(
                Comment(
                    post_id=post_id, user_id=user.id, text=payload.text, parent_id=payload.parent_id
                )
            )
        elif (
            db.scalar(select(Report).where(Report.post_id == post_id, Report.user_id == user.id))
            is None
        ):
            db.add(Report(post_id=post_id, user_id=user.id, reason=payload.text))
    return {"ok": True}


@router.get("/gallery/{post_id}/comments")
def comments(
    post_id: uuid.UUID, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):

    get_post(post_id, user, db)
    return [
        {"id": str(c.id), "text": c.text, "parent_id": str(c.parent_id) if c.parent_id else None}
        for c in db.scalars(
            select(Comment)
            .where(Comment.post_id == post_id)
            .order_by(Comment.created_at)
            .limit(100)
        )
    ]


class GroupPublicationImport(BaseModel):
    publication_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    classifications: dict[uuid.UUID, ClassificationInput] = Field(default_factory=dict)


@router.post("/groups/{workspace_id}/publications/import")
def import_group_publications(
    workspace_id: uuid.UUID,
    payload: GroupPublicationImport,
    user=Depends(get_current_user),
    db=Depends(get_db),
):
    from app.social_features.sharing import import_publications

    return import_publications(
        db, user, workspace_id, payload.publication_ids, payload.classifications
    )
