"""Source ownership, retirement and late-worker rejection for bucket copies."""

import uuid

from fastapi import HTTPException
from sqlalchemy import delete, select

from app.models import MediaAsset, MediaAssetChunk
from app.social_features.evidence_models import GalleryEvidence, PublicationUpload
from app.social_features.models import Publication, UserProfile
from app.storage.models import StorageConnection, StorageImport, StorageSync
from app.storage.provenance_models import StorageObject


def check_upload_source(db, upload):
    source = db.scalar(select(StorageObject).where(StorageObject.upload_id == upload.id))
    if source is not None:
        db.refresh(source)
        connection = db.get(StorageConnection, source.connection_id, populate_existing=True)
        if source.retired or not connection.active or source.revision != connection.revision:
            raise HTTPException(409, "The source connection has changed.")


def retire_object(db, source):
    if source.retired:
        return
    source.retired = True
    if source.upload_id is None:
        owner = db.get(StorageConnection, source.connection_id).owner_id
        profile = db.get(UserProfile, owner)
        if profile and profile.cv_sha256 == source.sha256:
            for field in (
                "cv_bytes",
                "cv_filename",
                "cv_mime_type",
                "cv_sha256",
                "cv_text",
                "cv_context",
                "cv_error",
            ):
                setattr(profile, field, None)
            profile.cv_status = "empty"
        return
    upload = db.get(PublicationUpload, source.upload_id, populate_existing=True)
    if not upload:
        return
    upload.status, upload.original_bytes, upload.analysis = "cancelled", b"", {}
    if not upload.result_id:
        return
    post = db.get(Publication, upload.result_id)
    if not post:
        return
    family = list(
        db.scalars(
            select(Publication).where(
                (Publication.id == post.id) | (Publication.shared_from_id == post.id)
            )
        )
    )
    assets = {}
    for item in family:
        asset = db.get(MediaAsset, item.media_id)
        # Replaced publications survive; descendants retaining source bytes retire.
        if asset and asset.sha256 == source.sha256:
            item.hidden = True
            assets[asset.id] = asset
            db.execute(delete(GalleryEvidence).where(GalleryEvidence.post_id == item.id))
    db.flush()
    for asset in assets.values():
        erase_unreferenced_source(db, asset)


def erase_unreferenced_source(db, asset):
    from app.faces import FaceEnrollment, FaceRecordEnrollment
    from app.workspaces.models import RecordMedia

    remaining = db.scalar(
        select(Publication.id)
        .where(Publication.media_id == asset.id, Publication.hidden.is_(False))
        .limit(1)
    )
    referenced = any(
        db.scalar(select(model.id).where(column == asset.id).limit(1))
        for model, column in (
            (FaceEnrollment, FaceEnrollment.media_asset_id),
            (FaceRecordEnrollment, FaceRecordEnrollment.media_asset_id),
            (RecordMedia, RecordMedia.media_id),
        )
    )
    avatar = db.scalar(
        select(UserProfile.user_id).where(UserProfile.avatar_media_id == asset.id).limit(1)
    )
    if remaining is None and not referenced and avatar is None:
        asset.original_bytes = b""
        asset.byte_size = 0
        asset.extra_metadata = {**(asset.extra_metadata or {}), "retired": True}
        db.execute(delete(MediaAssetChunk).where(MediaAssetChunk.asset_id == asset.id))
        for child in db.scalars(select(MediaAsset).where(MediaAsset.parent_asset_id == asset.id)):
            erase_unreferenced_source(db, child)


def backfill_connection(db, connection):
    # Only proven upload IDs establish ownership; never guess from filenames.
    known = set(
        db.scalars(
            select(StorageObject.upload_id).where(StorageObject.connection_id == connection.id)
        )
    )
    for run in db.scalars(
        select(StorageImport).where(StorageImport.connection_id == connection.id)
    ):
        for item in run.items:
            if not item.get("upload_id"):
                continue
            upload_id = uuid.UUID(item["upload_id"])
            if upload_id in known:
                continue
            upload = db.get(PublicationUpload, upload_id)
            if not upload:
                continue
            import hashlib

            digest = item.get("sha256") or hashlib.sha256(upload.original_bytes).hexdigest()
            db.add(
                StorageObject(
                    connection_id=connection.id,
                    revision=run.revision,
                    key=item["key"],
                    sha256=digest,
                    workspace_id=run.workspace_id,
                    upload_id=upload.id,
                )
            )
            db.flush()
            known.add(upload_id)


def retire_connection(db, connection):
    backfill_connection(db, connection)
    for source in db.scalars(
        select(StorageObject).where(StorageObject.connection_id == connection.id)
    ):
        retire_object(db, source)
    for run in db.scalars(
        select(StorageImport).where(StorageImport.connection_id == connection.id)
    ):
        if run.status in {"pending", "running", "attention"}:
            run.status, run.lease_until = "cancelled", None
            run.items = [{**item, "status": "cancelled"} for item in run.items]
    for rule in db.scalars(select(StorageSync).where(StorageSync.connection_id == connection.id)):
        rule.enabled, rule.cursor, rule.seen_keys = False, None, []
    connection.revision += 1
