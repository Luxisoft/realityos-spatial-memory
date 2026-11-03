from __future__ import annotations

import hashlib
import io
import uuid
from datetime import UTC, datetime
from typing import Callable

import httpx
from PIL import Image
from sqlalchemy import (
    delete,
    func,
    select,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.faces import build_face_engine, ingest_media_assets
from app.models import (
    CaptureSession,
    CaptureStatus,
    MediaAsset,
    MediaKind,
    Role,
    User,
    Workspace,
    WorkspaceMember,
)
from app.social_features.models import (
    FacebookFriend,
    FacebookMedia,
    FacebookPost,
    FacebookProfile,
    Publication,
)
from app.video import VideoProcessingError, extract_representative_frames, probe_video

_FB_PROFILE_FIELDS = (
    "id,name,email,birthday,age_range,gender,hometown{name},location{name},link,picture.type(large)"
)

"""Facebook identities and explicitly shared audiovisual publications."""


async def _graph_get(
    client: httpx.AsyncClient, path: str, token: str, params: dict | None = None
) -> dict | None:
    """One isolated Graph read. A denied scope returns None instead of failing sync."""

    try:
        response = await client.get(
            f"https://graph.facebook.com{path}",
            params={"access_token": token, **(params or {})},
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None
    return payload if isinstance(payload, dict) and "error" not in payload else None


def _graph_total(node: dict | None) -> int | None:
    if not node:
        return None
    summary = node.get("summary") or {}
    total = summary.get("total_count")
    return total if isinstance(total, int) else None


async def sync_facebook_profile(
    db: Session,
    settings,
    user: User,
    client: httpx.AsyncClient,
    user_token: str,
    granted_scopes: list,
) -> FacebookProfile:
    """Fetch profile fields and photo/video inventory. Missing scopes stay NULL."""

    profile_node = await _graph_get(client, "/me", user_token, {"fields": _FB_PROFILE_FIELDS})
    friends_node = await _graph_get(
        client,
        "/me/friends",
        user_token,
        {"fields": "id,name,picture.type(square),link", "limit": 100, "summary": True},
    )
    likes_node = await _graph_get(client, "/me/likes", user_token, {"limit": 0, "summary": True})
    photos_count_node = await _graph_get(
        client, "/me/photos", user_token, {"limit": 0, "summary": True}
    )
    videos_count_node = await _graph_get(
        client, "/me/videos", user_token, {"limit": 0, "summary": True}
    )
    photos_node = await _graph_get(
        client,
        "/me/photos",
        user_token,
        {
            "fields": "id,created_time,images,name",
            "type": "uploaded",
            "limit": settings.facebook_photo_sync_limit,
        },
    )
    videos_node = await _graph_get(
        client,
        "/me/videos",
        user_token,
        {
            "fields": "id,description,source,created_time",
            "limit": settings.facebook_video_sync_limit,
        },
    )
    posts_node = await _graph_get(
        client,
        "/me/posts",
        user_token,
        {
            "fields": "id,message,created_time,permalink_url",
            "limit": settings.facebook_post_sync_limit,
        },
    )
    node = profile_node or {}
    age_range = node.get("age_range") or {}
    picture = ((node.get("picture") or {}).get("data") or {}).get("url")
    row = db.get(FacebookProfile, user.id)
    if row is None:
        row = FacebookProfile(user_id=user.id)
        db.add(row)
    # Preserve the last successful profile on a transient failure while keeping
    # the independent photo/video inventory and import flow running as before.
    if profile_node is not None:
        row.email = node.get("email")
        row.birthday = node.get("birthday")
        row.age_min = age_range.get("min")
        row.age_max = age_range.get("max")
        row.gender = node.get("gender")
        row.hometown = (node.get("hometown") or {}).get("name")
        row.location = (node.get("location") or {}).get("name")
        row.profile_link = node.get("link")
        row.picture_url = picture
    row.friends_count = _graph_total(friends_node)
    row.likes_count = _graph_total(likes_node)
    row.photos_count = _graph_total(photos_count_node)
    row.videos_count = _graph_total(videos_count_node)
    row.granted_scopes = granted_scopes
    row.sync_diagnostics = {
        "profile": "ready" if profile_node is not None else "unavailable",
        "photos": (
            "unavailable"
            if photos_node is None
            else "ready"
            if (photos_node.get("data") or [])
            else "empty"
        ),
        "videos": (
            "unavailable"
            if videos_node is None
            else "ready"
            if (videos_node.get("data") or [])
            else "empty"
        ),
    }
    if profile_node is not None:
        row.synced_at = datetime.now(UTC)
    if friends_node is not None:
        db.execute(delete(FacebookFriend).where(FacebookFriend.owner_user_id == user.id))
        for friend in friends_node.get("data", []) or []:
            friend_id = str(friend.get("id") or "").strip()
            friend_name = str(friend.get("name") or "").strip()
            if not friend_id or not friend_name:
                continue
            friend_picture = ((friend.get("picture") or {}).get("data") or {}).get("url")
            db.add(
                FacebookFriend(
                    owner_user_id=user.id,
                    facebook_id=friend_id,
                    name=friend_name[:160],
                    picture_url=friend_picture,
                    profile_link=friend.get("link"),
                )
            )
    before = db.scalar(
        select(func.count())
        .select_from(FacebookMedia)
        .where(FacebookMedia.user_id == user.id, FacebookMedia.imported_media_id.is_(None))
    )
    for item in (photos_node or {}).get("data", []) or []:
        _upsert_facebook_media(db, user.id, item, "photo")
    for item in (videos_node or {}).get("data", []) or []:
        _upsert_facebook_media(db, user.id, item, "video")
    db.flush()
    after = db.scalar(
        select(func.count())
        .select_from(FacebookMedia)
        .where(FacebookMedia.user_id == user.id, FacebookMedia.imported_media_id.is_(None))
    )
    if after and after > (before or 0) and row.import_status in ("done", "partial"):
        row.import_status = "pending"
    for item in (posts_node or {}).get("data", []) or []:
        fb_id = str(item.get("id") or "")
        if fb_id and db.get(FacebookPost, fb_id) is None:
            db.add(
                FacebookPost(
                    fb_id=fb_id,
                    user_id=user.id,
                    message=item.get("message"),
                    fb_created_time=item.get("created_time"),
                    permalink=item.get("permalink_url"),
                )
            )
    db.flush()
    return row


def _upsert_facebook_media(db: Session, user_id: uuid.UUID, item: dict, kind: str) -> None:

    fb_id = str(item.get("id") or "")
    if not fb_id or db.get(FacebookMedia, fb_id) is not None:
        return
    if kind == "photo":
        images = item.get("images") or []
        first = images[0] if images else {}
        source_url = first.get("source")
        width, height = first.get("width"), first.get("height")
        caption = item.get("name")
    else:
        source_url = item.get("source")
        width, height, caption = None, None, item.get("description")
    db.add(
        FacebookMedia(
            fb_id=fb_id,
            user_id=user_id,
            kind=kind,
            source_url=source_url,
            caption=caption,
            fb_created_time=item.get("created_time"),
            width=width if isinstance(width, int) else None,
            height=height if isinstance(height, int) else None,
        )
    )


def _facebook_published_at(value: str | None) -> datetime:
    if not value:
        return datetime.now(UTC)
    normalized = value.strip().replace("Z", "+00:00")
    if normalized.endswith("+0000"):
        normalized = normalized[:-5] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(UTC)
    return parsed.replace(tzinfo=UTC) if parsed.tzinfo is None else parsed


def _ensure_import_publication(db: Session, item: FacebookMedia) -> Publication | None:
    """Expose imported account media through the normal private publication path."""

    if item.imported_media_id is None:
        return None
    existing = db.scalar(
        select(Publication).where(
            Publication.owner_id == item.user_id,
            Publication.source_ref == item.fb_id,
        )
    )
    if existing is not None:
        existing.media_id = item.imported_media_id
        existing.caption = item.caption or ""
        existing.search_text = item.caption or ""
        existing.published_at = _facebook_published_at(item.fb_created_time)
        return existing
    publication = Publication(
        owner_id=item.user_id,
        media_id=item.imported_media_id,
        audience="home",
        caption=item.caption or "",
        search_text=item.caption or "",
        source="facebook",
        source_ref=item.fb_id,
        published_at=_facebook_published_at(item.fb_created_time),
    )
    db.add(publication)
    return publication


def _store_chunked_bytes(db: Session, asset, raw: bytes, chunk_bytes: int) -> None:
    from app.models import MediaAssetChunk

    for index in range(0, len(raw), chunk_bytes):
        piece = raw[index : index + chunk_bytes]
        db.add(
            MediaAssetChunk(
                asset_id=asset.id,
                chunk_index=index // chunk_bytes,
                content=piece,
                byte_size=len(piece),
            )
        )


def _create_import_asset(db, workspace, session, item, raw: bytes, digest: str, settings):
    if item.kind == "photo":
        if len(raw) > settings.max_image_bytes:
            raise ValueError("Photo exceeds the image limit.")
        try:
            with Image.open(io.BytesIO(raw)) as picture:
                width, height = picture.size
                picture.verify()
        except Exception:
            raise ValueError("Invalid image data.")
        asset = MediaAsset(
            workspace_id=workspace.id,
            capture_session_id=session.id,
            kind=MediaKind.IMAGE,
            mime_type="image/jpeg",
            original_bytes=raw,
            sha256=digest,
            byte_size=len(raw),
            width=width,
            height=height,
            extra_metadata={"facebook_id": item.fb_id, "origin": "facebook-import"},
        )
        db.add(asset)
        db.flush()
        return asset
    if len(raw) > settings.facebook_import_max_video_bytes:
        raise ValueError("Video exceeds the import limit.")
    try:
        info = probe_video(raw)
    except VideoProcessingError as exc:
        raise ValueError(str(exc)) from exc
    chunked = len(raw) > settings.video_inline_bytes
    asset = MediaAsset(
        workspace_id=workspace.id,
        capture_session_id=session.id,
        kind=MediaKind.VIDEO,
        mime_type="video/mp4",
        original_bytes=b"" if chunked else raw,
        sha256=digest,
        byte_size=len(raw),
        width=info.width,
        height=info.height,
        extra_metadata={"facebook_id": item.fb_id, "origin": "facebook-import"},
    )
    db.add(asset)
    db.flush()
    if chunked:
        _store_chunked_bytes(db, asset, raw, settings.video_bytea_chunk_bytes)
    frames = extract_representative_frames(raw, info, segment_seconds=60, frames_per_segment=4)[:12]
    unique_frames: dict[str, object] = {}
    for frame in frames:
        unique_frames.setdefault(hashlib.sha256(frame.bytes).hexdigest(), frame)
    for frame_digest, frame in unique_frames.items():
        exists = db.scalar(
            select(MediaAsset).where(
                MediaAsset.capture_session_id == session.id,
                MediaAsset.sha256 == frame_digest,
            )
        )
        if exists is not None:
            continue
        db.add(
            MediaAsset(
                workspace_id=workspace.id,
                capture_session_id=session.id,
                parent_asset_id=asset.id,
                kind=MediaKind.FRAME,
                mime_type="image/jpeg",
                original_bytes=frame.bytes,
                sha256=frame_digest,
                byte_size=len(frame.bytes),
                width=info.width,
                height=info.height,
                extra_metadata={"facebook_id": item.fb_id, "origin": "facebook-import"},
            )
        )
    db.flush()
    return asset


def import_facebook_media(
    db: Session,
    settings,
    user_id: uuid.UUID,
    fetch_bytes: Callable[[str], bytes] | None = None,
) -> dict:
    """Download inventoried bytes into BYTEA and enroll faces. Bounded and resumable."""

    profile = db.get(FacebookProfile, user_id)
    user = db.get(User, user_id)
    if profile is None or user is None:
        return {"import_status": "pending", "imported_photos": 0, "imported_videos": 0}
    try:
        engine = build_face_engine(settings)
    except Exception as exc:
        profile.import_status = "partial"
        profile.import_error = str(exc)[:500]
        db.flush()
        return {"import_status": "partial", "imported_photos": 0, "imported_videos": 0}
    # Enforce the current window again during import. Older releases may have
    # inventoried more rows than the UI is now allowed to expose.
    photos = list(
        db.scalars(
            select(FacebookMedia)
            .where(
                FacebookMedia.user_id == user_id,
                FacebookMedia.kind == "photo",
            )
            .order_by(FacebookMedia.fb_created_time.desc(), FacebookMedia.fb_id.desc())
            .limit(settings.facebook_photo_sync_limit)
        )
    )
    videos = list(
        db.scalars(
            select(FacebookMedia)
            .where(
                FacebookMedia.user_id == user_id,
                FacebookMedia.kind == "video",
            )
            .order_by(FacebookMedia.fb_created_time.desc(), FacebookMedia.fb_id.desc())
            .limit(settings.facebook_video_sync_limit)
        )
    )
    inventory = sorted(
        [*photos, *videos],
        key=lambda item: (_facebook_published_at(item.fb_created_time), item.fb_id),
        reverse=True,
    )
    # Counts describe the active import window, not legacy rows or the separate
    # avatar asset.
    profile.imported_photos = sum(
        item.kind == "photo" and item.imported_media_id is not None for item in inventory
    )
    profile.imported_videos = sum(
        item.kind == "video" and item.imported_media_id is not None for item in inventory
    )
    # Failures are retry state for the active bounded window, not a lifetime
    # counter. A later successful retry must be able to return the profile to
    # done.
    profile.skipped_media = 0
    profile.import_error = None
    ensured_ids: list[str] = []
    for imported in inventory:
        ensured = _ensure_import_publication(db, imported)
        if ensured is not None and ensured.indexed_at is None:
            ensured_ids.append(str(ensured.id))
    pending = [item for item in inventory if item.imported_media_id is None]
    needs_picture = bool(profile.picture_url) and not profile.picture_imported
    if not pending and not needs_picture:
        profile.import_status = "done"
        db.flush()
        return {
            "import_status": profile.import_status,
            "imported_photos": profile.imported_photos,
            "imported_videos": profile.imported_videos,
            "publication_ids": ensured_ids,
        }
    profile.import_status = "running"
    name = f"home:{user.id}"
    workspace = db.scalar(select(Workspace).where(Workspace.name == name))
    if workspace is None:
        workspace = Workspace(name=name, created_by_id=user.id)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=user.id, role=Role.ADMIN))
        db.flush()
    session = CaptureSession(
        workspace_id=workspace.id,
        created_by_id=user.id,
        origin="facebook-import",
        status=CaptureStatus.OPEN,
        consent_confirmed=True,
    )
    db.add(session)
    db.flush()
    if needs_picture:
        with httpx.Client(timeout=60) as picture_client:
            try:
                assert profile.picture_url is not None
                if fetch_bytes is None:
                    picture_response = picture_client.get(profile.picture_url)
                    picture_response.raise_for_status()
                    picture_raw = picture_response.content
                else:
                    picture_raw = fetch_bytes(profile.picture_url)
                if picture_raw and len(picture_raw) <= settings.max_image_bytes:
                    with Image.open(io.BytesIO(picture_raw)) as picture_image:
                        picture_image.verify()
                    picture_digest = hashlib.sha256(picture_raw).hexdigest()
                    picture_asset = db.scalar(
                        select(MediaAsset).where(
                            MediaAsset.capture_session_id == session.id,
                            MediaAsset.sha256 == picture_digest,
                        )
                    )
                    if picture_asset is None:
                        picture_asset = MediaAsset(
                            workspace_id=workspace.id,
                            capture_session_id=session.id,
                            kind=MediaKind.IMAGE,
                            mime_type="image/jpeg",
                            original_bytes=picture_raw,
                            sha256=picture_digest,
                            byte_size=len(picture_raw),
                            extra_metadata={
                                "origin": "facebook-import",
                                "face_profile_picture": True,
                            },
                        )
                        db.add(picture_asset)
                        db.flush()
                    ingest_media_assets(db, user, [picture_asset], "facebook-photo", engine)
                    profile.picture_imported = True
            except Exception as exc:
                profile.import_error = f"picture: {exc}"[:500]
        db.flush()
    with httpx.Client(timeout=60) as client:
        for item in pending:
            try:
                if not item.source_url:
                    raise ValueError("No downloadable URL.")
                if fetch_bytes is None:
                    response = client.get(item.source_url)
                    response.raise_for_status()
                    raw = response.content
                else:
                    raw = fetch_bytes(item.source_url)
                if not raw:
                    raise ValueError("Empty download.")
                digest = hashlib.sha256(raw).hexdigest()
                try:
                    with db.begin_nested():
                        asset = db.scalar(
                            select(MediaAsset).where(
                                MediaAsset.capture_session_id == session.id,
                                MediaAsset.sha256 == digest,
                            )
                        )
                        if asset is None:
                            asset = _create_import_asset(
                                db, workspace, session, item, raw, digest, settings
                            )
                except IntegrityError:
                    asset = db.scalar(
                        select(MediaAsset).where(
                            MediaAsset.capture_session_id == session.id,
                            MediaAsset.sha256 == digest,
                        )
                    )
                    if asset is None:
                        raise
                if asset.kind == MediaKind.VIDEO:
                    children = list(
                        db.scalars(select(MediaAsset).where(MediaAsset.parent_asset_id == asset.id))
                    )
                    if not children:
                        raise ValueError("Video has no extracted frames.")
                    ingest_media_assets(db, user, children, "facebook-video", engine)
                    item.imported_media_id = asset.id
                    profile.imported_videos += 1
                else:
                    ingest_media_assets(db, user, [asset], "facebook-photo", engine)
                    item.imported_media_id = asset.id
                    profile.imported_photos += 1
                ensured = _ensure_import_publication(db, item)
                if ensured is not None and ensured.indexed_at is None:
                    ensured_ids.append(str(ensured.id))
            except Exception as exc:
                profile.skipped_media += 1
                profile.import_error = f"{item.fb_id}: {exc}"[:500]
            db.flush()
    session.status = CaptureStatus.CLOSED
    session.closed_at = datetime.now(UTC)
    profile.import_status = "done" if not profile.skipped_media else "partial"
    db.flush()
    return {
        "import_status": profile.import_status,
        "imported_photos": profile.imported_photos,
        "imported_videos": profile.imported_videos,
        "publication_ids": ensured_ids,
    }
