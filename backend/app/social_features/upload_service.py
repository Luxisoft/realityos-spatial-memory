"""Idempotent automatic review. Candidates never appear in publication feeds."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select, text

from app.meta import MetaProviderError
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
from app.social_features.evidence_models import (
    GalleryEvidence,
    PublicationRevision,
    PublicationUpload,
)
from app.social_features.models import Publication
from app.social_features.publication_visibility import publication_content
from app.social_features.visual import ground, normalize, similar


def scope_lock(db, owner, workspace, wait=True):
    if db.get_bind().dialect.name == "postgresql":
        function = "pg_advisory_xact_lock" if wait else "pg_try_advisory_xact_lock"
        result = db.execute(
            text(f"SELECT {function}(hashtextextended(:key,0))"),
            {"key": f"publication:{owner}:{workspace}"},
        )
        if not wait and not result.scalar():
            raise HTTPException(
                423, "review_busy: Another image is being processed. Retry confirmation later."
            )


def same_scope(db, owner, workspace):
    return (
        select(Publication)
        .where(
            Publication.owner_id == owner,
            Publication.workspace_id == workspace,
            Publication.hidden.is_(False),
            publication_content(),
        )
        .order_by(Publication.published_at, Publication.id)
    )


def duplicate(db, client, raw, owner, workspace, older_than=None):
    image, _, _, pixel, phash = normalize(raw)
    candidates = []
    statement = (
        same_scope(db, owner, workspace)
        if workspace is not None
        else select(Publication)
        .where(Publication.owner_id == owner, Publication.hidden.is_(False), publication_content())
        .order_by(Publication.published_at, Publication.id)
    )
    for post in db.scalars(statement):
        if older_than is not None and (post.published_at, str(post.id)) >= (
            older_than.published_at,
            str(older_than.id),
        ):
            continue
        asset = db.get(MediaAsset, post.media_id)
        if not asset or not asset.mime_type.startswith("image/"):
            continue
        meta = asset.extra_metadata or {}
        candidate_image = None
        if not meta.get("visual_hash"):
            candidate_image, _, _, p, h = normalize(asset.original_bytes)
            meta = {**meta, "pixel_hash": p, "visual_hash": h}
            asset.extra_metadata = meta
        if meta.get("pixel_hash") == pixel or similar(phash, meta["visual_hash"]):
            if candidate_image is None:
                candidate_image = normalize(asset.original_bytes)[0]
            candidates.append((str(post.id), candidate_image))
    # Meta checks EVERY new upload, even when there are no local candidates.
    for start in range(0, max(1, len(candidates)), 12):
        found = client.compare_gallery_images(image, candidates[start : start + 12])
        if found:
            return db.get(Publication, uuid.UUID(found))
    return None


def home_space(db, owner):
    workspace = db.scalar(select(Workspace).where(Workspace.name == f"home:{owner}"))
    if not workspace:
        workspace = Workspace(name=f"home:{owner}", created_by_id=owner)
        db.add(workspace)
        db.flush()
        db.add(WorkspaceMember(workspace_id=workspace.id, user_id=owner, role=Role.ADMIN))
        db.flush()
    return workspace.id


def save_publication(db, upload, replace=None):
    from app.social_features.localizations import LANGUAGES, persist, text_hash

    translations = (upload.analysis or {}).get("localizations", {})
    required = {
        text_hash(t)
        for t in (
            upload.caption or "",
            upload.note_text or "",
            *[d["label"] for d in (upload.analysis or {}).get("detections", [])],
        )
        if t.strip()
    }
    if any(not required.issubset(translations.get(language, {})) for language in LANGUAGES):
        raise HTTPException(
            409, "Publication languages are not ready. Retry analysis before publishing."
        )
    member = db.scalar(
        select(WorkspaceMember)
        .where(
            WorkspaceMember.workspace_id == upload.workspace_id,
            WorkspaceMember.user_id == upload.owner_id,
        )
        .with_for_update()
    )
    if member is None:
        raise HTTPException(403, "Workspace membership changed during analysis.")
    from app.social_features.uploads import check_destination

    check_destination(db, db.get(User, upload.owner_id), upload.workspace_id)
    from app.storage.lifecycle import check_upload_source

    check_upload_source(db, upload)
    from app.social_features.classification import (
        classification_json,
        set_classification,
        validate_classification,
    )

    validate_classification(db, upload.workspace_id, upload.category_id, upload.tag_ids)
    target = upload.workspace_id
    now = datetime.now(UTC)
    session = CaptureSession(
        workspace_id=target,
        created_by_id=upload.owner_id,
        origin="group-upload",
        status=CaptureStatus.CLOSED,
        consent_confirmed=True,
        closed_at=now,
    )
    db.add(session)
    db.flush()
    asset = MediaAsset(
        workspace_id=target,
        capture_session_id=session.id,
        kind=MediaKind.VIDEO if upload.mime_type == "video/mp4" else MediaKind.IMAGE,
        mime_type=upload.mime_type,
        original_bytes=upload.original_bytes,
        sha256=hashlib.sha256(upload.original_bytes).hexdigest(),
        byte_size=len(upload.original_bytes),
        extra_metadata={**upload.analysis.get("fingerprint", {}), "gallery_index_version": 2},
    )
    db.add(asset)
    db.flush()
    if replace:
        db.add(
            PublicationRevision(
                post_id=replace.id,
                previous={
                    "classification": classification_json(db, replace),
                    **{
                        key: str(getattr(replace, key))
                        if key == "media_id"
                        else getattr(replace, key)
                        for key in (
                            "media_id",
                            "caption",
                            "note_text",
                            "note_source",
                            "ai_labels",
                            "ai_detections",
                            "ai_caption",
                            "search_text",
                        )
                    },
                },
            )
        )
        post = replace
    else:
        post = Publication(
            owner_id=upload.owner_id,
            workspace_id=upload.workspace_id,
            source="local",
        )
        db.add(post)
    post.active_index_run_id = None
    post.media_id = asset.id
    set_classification(db, post, upload.category_id, upload.tag_ids)
    post.caption = upload.caption
    post.note_text = upload.note_text
    post.note_source = upload.note_source
    detections = upload.analysis["detections"]
    post.ai_detections = (
        [
            {**d, "frame_timestamp_ms": frame["timestamp"]}
            for frame in upload.analysis["frames"]
            for d in frame["detections"]
        ]
        if "frames" in upload.analysis
        else [{**d, "frame_timestamp_ms": None} for d in detections]
    )
    post.evidence_version = 2
    post.ai_labels = list(dict.fromkeys(d["label"] for d in detections))
    post.search_text = " ".join([post.caption, *post.ai_labels])[:8000]
    post.ai_caption = "; ".join(post.ai_labels)[:1000]
    post.indexed_at = now
    post.index_error = None
    db.flush()
    if upload.mime_type == "video/mp4":
        from app.social_features.video_uploads import analyzed_frames

        evidence_frames = analyzed_frames(db, upload)
    else:
        normalized, _, _, digest, _ = normalize(upload.original_bytes)
        evidence_frames = [(normalized, digest, None, detections)]
    for image, digest, timestamp, frame_detections in evidence_frames:
        if frame_detections:
            db.add(
                GalleryEvidence(
                    post_id=post.id,
                    media_id=asset.id,
                    image_bytes=image,
                    content_hash=digest,
                    frame_timestamp_ms=timestamp,
                    detections=frame_detections,
                    version=2,
                )
            )
    persist(db, post.id, translations, upload.analysis.get("simulated", False))
    upload.status = "published"
    upload.result_id = post.id
    return post


def process_upload(db, upload_id, client):
    upload = db.get(PublicationUpload, upload_id)
    if upload is None or upload.status not in ("pending", "failed"):
        return upload
    scope_lock(db, upload.owner_id, upload.workspace_id)
    db.refresh(upload)
    if upload.status not in ("pending", "failed"):
        return upload
    if not upload.category_id or not upload.tag_ids:
        upload.status = "awaiting_classification"
        return upload
    try:
        from app.dependencies import workspace_member
        from app.models import User

        if upload.workspace_id:
            workspace_member(upload.workspace_id, db.get(User, upload.owner_id), db)
        if upload.mime_type == "video/mp4":
            from app.social_features.video_uploads import analyze_video

            match, analysis = analyze_video(db, upload, client)
            db.refresh(upload)
            if upload.status == "cancelled":
                return upload
            upload.analysis = analysis
        else:
            match = duplicate(
                db,
                client,
                upload.original_bytes,
                upload.owner_id,
                upload.workspace_id,
            )
            image, pixel, phash, detections = ground(client, upload.original_bytes)
            db.refresh(upload)
            if upload.status == "cancelled":
                return upload
            identity_match = match or duplicate(
                db, client, upload.original_bytes, upload.owner_id, None
            )
            identity_asset = db.get(MediaAsset, identity_match.media_id) if identity_match else None
            identity = (
                (identity_asset.extra_metadata or {}).get("visual_identity", identity_asset.sha256)
                if identity_asset
                else __import__("hashlib").sha256(upload.original_bytes).hexdigest()
            )
            from app.social_features.localizations import prepare_languages

            translations = prepare_languages(
                client,
                [upload.caption or "", upload.note_text or "", *[d["label"] for d in detections]],
            )
            db.refresh(upload)
            if upload.status == "cancelled":
                return upload
            upload.analysis = {
                "localizations": translations,
                "simulated": client.__class__.__name__.startswith("Mock"),
                "fingerprint": {
                    "pixel_hash": pixel,
                    "visual_hash": phash,
                    "visual_identity": identity,
                },
                "detections": detections,
            }
        upload.error = None
        if match:
            upload.status = "duplicate"
            upload.duplicate_id = match.id
            upload.expected_media_id = match.media_id
        else:
            with db.begin_nested():
                save_publication(db, upload)
    except (MetaProviderError, ValueError, OSError, HTTPException) as exc:
        upload.status = "failed"
        upload.error = str(exc)[:1000]
    return upload


def confirm_replace(db, upload, user):
    from app.dependencies import workspace_member
    from app.social_features.gallery import get_post

    scope_lock(db, upload.owner_id, upload.workspace_id, wait=False)
    db.refresh(upload)
    if upload.status == "published":
        return upload
    if upload.status != "duplicate":
        raise HTTPException(409, "This upload is not awaiting replacement.")
    post = get_post(upload.duplicate_id, user, db)
    if post.owner_id != user.id or post.workspace_id != upload.workspace_id:
        raise HTTPException(409, "Publication destination changed. Upload again.")
    if upload.workspace_id:
        workspace_member(upload.workspace_id, user, db)
    if post.media_id != upload.expected_media_id:
        raise HTTPException(409, "The publication changed. Analyze this upload again.")
    with db.begin_nested():
        save_publication(db, upload, replace=post)
    return upload
