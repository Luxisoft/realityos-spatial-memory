from __future__ import annotations

import base64
import io
import json
import uuid
from datetime import UTC, datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from PIL import Image
from sqlalchemy import (
    and_,
    func,
    or_,
    select,
)
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db, workspace_member
from app.faces import delete_selfie_enrollments
from app.models import (
    CaptureSession,
    MediaAsset,
    MediaKind,
    User,
    WorkspaceMember,
)
from app.social_features.models import Comment, Publication, Reaction, Report
from app.social_features.publication_visibility import (
    publication_content,
    require_ordinary_media,
    require_publication_content,
)
from app.social_features.schemas import Interaction, Publish, Share

"""Facebook identities and explicitly shared audiovisual publications."""


router = APIRouter()


def merge_transcript_chunks(chunks: list[str]) -> str:
    """Join consecutive voice chunks, dropping words repeated at boundaries."""

    def tokens(text: str) -> list[str]:
        return [word for word in text.split() if word]

    def key(word: str) -> str:
        return word.casefold().strip(".,:?¿¡!\"'()")

    words: list[str] = []
    for chunk in chunks:
        parts = tokens(chunk)
        if not parts:
            continue
        if not words:
            words = parts
            continue
        overlap = 0
        for size in range(min(6, len(words), len(parts)), 0, -1):
            if [key(word) for word in words[-size:]] == [key(word) for word in parts[:size]]:
                overlap = size
                break
        words += parts[overlap:]
    return " ".join(words)


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

    post = get_post(post_id, user, db)
    if post.owner_id != user.id:
        raise HTTPException(403, "Only the owner can share this publication.")
    if payload.audience == "work":
        if payload.workspace_id is None:
            raise HTTPException(422, "Choose a group.")
        workspace_member(payload.workspace_id, user, db)
    post.audience = payload.audience
    post.workspace_id = payload.workspace_id if payload.audience == "work" else None
    return {"ok": True}


def visible(post: Publication, user: User, db: Session) -> Publication:

    require_publication_content(post)
    if post.hidden:
        raise HTTPException(404, "Publication unavailable.")
    if user.is_guest and post.owner_id != user.id:
        owner = db.get(User, post.owner_id)
        if owner is None or not owner.is_guest:
            raise HTTPException(404, "Publication unavailable.")
    if post.owner_id == user.id or post.audience == "public":
        return post
    if post.audience == "work":
        workspace_member(post.workspace_id, user, db)
        return post
    raise HTTPException(404, "Publication unavailable.")


def get_post(post_id: uuid.UUID, user: User, db: Session):

    from app.social_features.evidence_models import PublicationDuplicate

    original = db.get(Publication, post_id)
    if original is not None:
        require_publication_content(original)
    alias = db.get(PublicationDuplicate, post_id)
    if alias is not None:
        post_id = alias.canonical_id
    post = db.get(Publication, post_id)
    if post is None:
        raise HTTPException(404, "Publication unavailable.")
    return visible(post, user, db)


def _encode_gallery_cursor(post: Publication) -> str:

    payload = json.dumps(
        [post.published_at.isoformat(), str(post.id)], separators=(",", ":")
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def _decode_gallery_cursor(value: str) -> tuple[datetime, uuid.UUID]:
    try:
        padded = value + "=" * (-len(value) % 4)
        timestamp, post_id = json.loads(base64.urlsafe_b64decode(padded).decode())
        parsed = datetime.fromisoformat(timestamp)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed, uuid.UUID(post_id)
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(422, "Invalid gallery cursor.") from exc


def _publication_payload(post: Publication, viewer: User, db: Session) -> dict:
    from app.social_features.profiles import _public_profile_payload

    asset = db.get(MediaAsset, post.media_id)
    owner = db.get(User, post.owner_id)
    owner_profile = _public_profile_payload(owner, db) if owner else {}
    return {
        "id": str(post.id),
        "caption": post.caption,
        "note_text": post.note_text,
        "note_source": post.note_source,
        "audience": post.audience,
        "workspace_id": str(post.workspace_id) if post.workspace_id else None,
        "mime_type": asset.mime_type if asset else "application/octet-stream",
        "media_url": f"gallery/{post.id}/media",
        "thumbnail_url": f"gallery/{post.id}/thumbnail",
        "owned": post.owner_id == viewer.id,
        "liked": db.get(Reaction, (post.id, viewer.id)) is not None,
        "likes": db.scalar(
            select(func.count()).select_from(Reaction).where(Reaction.post_id == post.id)
        ),
        "published_at": post.published_at.isoformat(),
        "source": post.source,
        "owner": {
            "user_id": str(post.owner_id),
            "display_name": owner.display_name if owner else "",
            "picture_url": owner_profile.get("picture_url"),
            "headline": owner_profile.get("headline", ""),
        },
    }


def _gallery_page(query, limit: int, cursor: str | None, viewer: User, db: Session) -> dict:

    page_size = min(max(limit, 1), 30)
    if cursor:
        published_at, post_id = _decode_gallery_cursor(cursor)
        query = query.where(
            or_(
                Publication.published_at < published_at,
                and_(Publication.published_at == published_at, Publication.id < post_id),
            )
        )
    rows = list(
        db.scalars(
            query.order_by(Publication.published_at.desc(), Publication.id.desc()).limit(
                page_size + 1
            )
        )
    )
    has_more = len(rows) > page_size
    rows = rows[:page_size]
    return {
        "items": [_publication_payload(post, viewer, db) for post in rows],
        "next_cursor": _encode_gallery_cursor(rows[-1]) if has_more and rows else None,
    }


@router.get("/profiles/{user_id}/media")
def profile_media_page(
    user_id: uuid.UUID,
    limit: int = 12,
    cursor: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    from app.social_features.profiles import _guest_may_view_profile

    target = db.get(User, user_id)
    if target is None or not target.is_active:
        raise HTTPException(404, "Profile unavailable.")
    if not _guest_may_view_profile(user, target):
        raise HTTPException(404, "Profile unavailable.")
    query = select(Publication).where(
        Publication.owner_id == user_id,
        Publication.hidden.is_(False),
        publication_content(),
    )
    if user.id != user_id:
        query = query.where(Publication.audience == "public")
    return _gallery_page(query, limit, cursor, user, db)


@router.get("/gallery/page")
def gallery_page(
    audience: Literal["home", "work"] = "home",
    workspace_id: uuid.UUID | None = None,
    limit: int = 12,
    cursor: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    query = select(Publication).where(
        Publication.audience == audience,
        Publication.hidden.is_(False),
        publication_content(),
    )
    if audience == "home":
        query = query.where(Publication.owner_id == user.id)
    else:
        if workspace_id is not None:
            workspace_member(workspace_id, user, db)
            query = query.where(Publication.workspace_id == workspace_id)
        query = query.where(
            Publication.workspace_id.in_(
                select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user.id)
            )
        )
    if user.is_guest:
        query = query.where(
            Publication.owner_id.in_(
                select(User.id).where(or_(User.id == user.id, User.is_guest.is_(True)))
            )
        )
    return _gallery_page(query, limit, cursor, user, db)


@router.get("/gallery")
def gallery(
    audience: Literal["home", "public", "work"] = "home",
    offset: int = 0,
    workspace_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    query = (
        select(Publication)
        .join(MediaAsset, Publication.media_id == MediaAsset.id)
        .where(
            Publication.audience == audience, Publication.hidden.is_(False), publication_content()
        )
    )
    if audience == "home":
        query = query.where(Publication.owner_id == user.id)
    elif audience == "work":
        if workspace_id is not None:
            workspace_member(workspace_id, user, db)
            query = query.where(Publication.workspace_id == workspace_id)
        query = query.where(
            Publication.workspace_id.in_(
                select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user.id)
            )
        )
    if user.is_guest:
        query = query.where(
            Publication.owner_id.in_(
                select(User.id).where(or_(User.id == user.id, User.is_guest.is_(True)))
            )
        )
    posts = db.scalars(
        query.order_by(Publication.created_at.desc(), Publication.id)
        .offset(max(0, offset))
        .limit(30)
    )
    return [_publication_payload(post, user, db) for post in posts]


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
    if payload.audience == "work":
        if payload.workspace_id is None:
            raise HTTPException(422, "Choose a work group.")
        workspace_member(payload.workspace_id, user, db)
    from app.meta import build_meta_client
    from app.social_features.upload_service import duplicate, scope_lock

    scope_lock(db, user.id, payload.audience, payload.workspace_id)
    if asset.mime_type.startswith("image/"):
        old = duplicate(
            db,
            build_meta_client(request.app.state.settings),
            asset.original_bytes,
            user.id,
            payload.audience,
            payload.workspace_id,
        )
        if old:
            if old.media_id == asset.id:
                return {"id": str(old.id)}
            raise HTTPException(
                409,
                "This photo already exists in this destination. Use image upload to confirm replacement.",
            )
    post = Publication(owner_id=user.id, **payload.model_dump())
    db.add(post)
    db.flush()
    from app.social_features.localizations import prepare_posts

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


def _parse_range(value: str, total: int) -> tuple[int, int] | None:
    """Parse a single ``bytes=`` range into inclusive (start, end) offsets."""

    if total <= 0 or not value.startswith("bytes="):
        return None
    spec = value.removeprefix("bytes=").strip()
    if "," in spec:
        return None
    start_text, dash, end_text = spec.partition("-")
    if not dash:
        return None
    try:
        if not start_text:
            suffix = int(end_text)
            if suffix <= 0:
                return None
            start = max(0, total - suffix)
            return (start, total - 1)
        start = int(start_text)
        end = int(end_text) if end_text else total - 1
    except ValueError:
        return None
    if start < 0 or end < start or start >= total:
        return None
    return (start, min(end, total - 1))


def _chunked_slice(db: Session, asset_id: uuid.UUID, start: int, end: int) -> bytes:
    from app.models import MediaAssetChunk

    sizes = list(
        db.execute(
            select(MediaAssetChunk.chunk_index, MediaAssetChunk.byte_size)
            .where(MediaAssetChunk.asset_id == asset_id)
            .order_by(MediaAssetChunk.chunk_index)
        )
    )
    first_index = last_index = -1
    first_start = 0
    offset = 0
    for chunk_index, byte_size in sizes:
        chunk_start, chunk_end = offset, offset + byte_size - 1
        if chunk_end >= start and chunk_start <= end:
            if first_index < 0:
                first_index = chunk_index
                first_start = chunk_start
            last_index = chunk_index
        offset += byte_size
    if first_index < 0:
        return b""
    parts = db.scalars(
        select(MediaAssetChunk.content)
        .where(
            MediaAssetChunk.asset_id == asset_id,
            MediaAssetChunk.chunk_index >= first_index,
            MediaAssetChunk.chunk_index <= last_index,
        )
        .order_by(MediaAssetChunk.chunk_index)
    )
    joined = b"".join(parts)
    return joined[start - first_start : end - first_start + 1]


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
    import subprocess
    import tempfile
    from pathlib import Path

    from fastapi.responses import Response

    from app.models import MediaAssetChunk
    from app.services import media_is_chunked

    post = get_post(post_id, user, db)
    asset = db.get(MediaAsset, post.media_id)
    if asset.mime_type.startswith("image/"):
        raw = asset.original_bytes
    else:
        frame = db.scalar(
            select(MediaAsset).where(
                MediaAsset.parent_asset_id == asset.id, MediaAsset.kind == MediaKind.FRAME
            )
        )
        if frame is not None:
            raw = frame.original_bytes
        else:
            with tempfile.TemporaryDirectory(prefix="realityos-thumbnail-") as directory:
                source = Path(directory) / "source.mp4"
                with source.open("wb") as output:
                    if media_is_chunked(asset):
                        for chunk in db.scalars(
                            select(MediaAssetChunk.content)
                            .where(MediaAssetChunk.asset_id == asset.id)
                            .order_by(MediaAssetChunk.chunk_index)
                        ):
                            output.write(chunk)
                    else:
                        output.write(asset.original_bytes)
                try:
                    result = subprocess.run(
                        [
                            "ffmpeg",
                            "-v",
                            "error",
                            "-i",
                            str(source),
                            "-frames:v",
                            "1",
                            "-vf",
                            "scale=360:480:force_original_aspect_ratio=decrease",
                            "-f",
                            "image2pipe",
                            "-vcodec",
                            "mjpeg",
                            "pipe:1",
                        ],
                        capture_output=True,
                        timeout=15,
                        check=True,
                    )
                    raw = result.stdout
                except (subprocess.SubprocessError, OSError) as error:
                    raise HTTPException(422, "Video thumbnail unavailable.") from error
    try:
        with Image.open(io.BytesIO(raw)) as image:
            image.thumbnail((360, 480))
            output = io.BytesIO()
            image.convert("RGB").save(output, format="JPEG", quality=85)
    except (ValueError, OSError) as error:
        raise HTTPException(422, "Thumbnail unavailable.") from error
    return Response(
        output.getvalue(),
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
            picture = image.convert("RGB")
            draw = ImageDraw.Draw(picture)
            width_px, height_px = picture.size
            outline = max(2, min(width_px, height_px) // 150)
            for x, y, width, height in boxes:
                left = min(max(x, 0.0), 1.0) * width_px
                top = min(max(y, 0.0), 1.0) * height_px
                right = min(max(x + width, 0.0), 1.0) * width_px
                bottom = min(max(y + height, 0.0), 1.0) * height_px
                draw.rectangle([left, top, right, bottom], outline=(255, 196, 0), width=outline)
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
