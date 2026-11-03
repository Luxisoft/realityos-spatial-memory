from __future__ import annotations

import uuid

from celery import Celery

from app.config import get_settings
from app.db import Database
from app.meta import build_meta_client
from app.services import process_job

settings = get_settings()
celery_app = Celery("realityos", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.update(
    imports=("app.storage.tasks",),
    beat_schedule={"storage-sync": {"task": "realityos.storage_tick", "schedule": 60.0}},
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    task_track_started=True,
)


@celery_app.task(
    name="realityos.process_media",
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def process_media(job_id: str) -> dict[str, str]:
    """Worker entry point; business processing is safe to retry by job key."""
    database = Database(settings.database_url)
    with database.session_factory() as db:
        job = process_job(
            db,
            uuid.UUID(job_id),
            build_meta_client(settings),
            video_segment_seconds=settings.video_segment_seconds,
            video_frames_per_segment=settings.video_frames_per_segment,
        )
        db.commit()
        return {"job_id": str(job.id), "status": job.status.value}


@celery_app.task(
    name="realityos.index_gallery_media",
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def index_gallery_media(publication_id: str, force: bool = False) -> dict[str, object]:
    """Worker entry point for one bounded AI pass over a publication."""

    import uuid

    from app.faces import FaceEngineError, build_face_engine
    from app.gallery_index import index_publication

    try:
        engine = build_face_engine(settings)
    except FaceEngineError:
        engine = None
    database = Database(settings.database_url)
    with database.session_factory() as db:
        publication = index_publication(
            db,
            uuid.UUID(publication_id),
            build_meta_client(settings),
            engine,
            force=force,
            checkpoint=True,
        )
        db.commit()
        return {
            "publication_id": publication_id,
            "indexed": bool(publication is not None and publication.indexed_at),
        }


@celery_app.task(
    name="realityos.import_facebook_media",
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def import_facebook_media_task(user_id: str) -> dict[str, object]:
    """Worker entry point for bounded Facebook media import and face enrollment."""

    from app.gallery_index import queue_publication_index
    from app.social import import_facebook_media

    database = Database(settings.database_url)
    with database.session_factory() as db:
        result = import_facebook_media(db, settings, uuid.UUID(user_id))
        db.commit()
        for publication_id in result.get("publication_ids", []):
            queue_publication_index(uuid.UUID(publication_id))
        return {"user_id": user_id, **result}


@celery_app.task(name="realityos.process_publication_upload", rate_limit="30/m")
def process_publication_upload(upload_id: str):
    from app.social_features.upload_service import process_upload

    database = Database(settings.database_url)
    with database.session_factory() as db:
        upload = process_upload(db, uuid.UUID(upload_id), build_meta_client(settings))
        db.commit()
        return {"id": upload_id, "status": upload.status if upload else "missing"}


@celery_app.task(
    name="realityos.rebuild_gallery_evidence", acks_late=True, reject_on_worker_lost=True
)
def rebuild_gallery_evidence(limit: int = 0):
    from app.social_features.maintenance import rebuild

    return rebuild(Database(settings.database_url), build_meta_client(settings), limit=limit)


@celery_app.task(
    bind=True,
    name="realityos.repair_gallery_publication",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=None,
)
def repair_gallery_publication(self, publication_id: str, media_id: str, provider_attempt: int = 0):
    """One resumable unit in a serial repair chain; completed work is idempotent."""
    from datetime import UTC, datetime

    from sqlalchemy import select

    from app.gallery_index import index_publication
    from app.social_features.evidence_models import GalleryIndexRun
    from app.social_features.models import Publication
    from app.social_features.repair_inventory import pending_inventory

    database = Database(settings.database_url)
    try:
        with database.session_factory() as db:
            post = db.get(Publication, uuid.UUID(publication_id))
            if post is None or post.hidden or str(post.media_id) != media_id:
                return {"publication_id": publication_id, "status": "skipped"}
            if publication_id not in {item["post_id"] for item in pending_inventory(db)}:
                return {"publication_id": publication_id, "status": "ready"}
            index_publication(
                db,
                post.id,
                build_meta_client(settings),
                force=True,
                deduplicate=False,
                checkpoint=True,
                recover_legacy=True,
                review_only=post.evidence_version >= 2,
            )
            db.commit()
            run = db.scalar(
                select(GalleryIndexRun)
                .where(
                    GalleryIndexRun.post_id == post.id, GalleryIndexRun.media_id == post.media_id
                )
                .order_by(GalleryIndexRun.created_at.desc())
                .limit(1)
            )
            if (
                run
                and run.status == "running"
                and run.lease_until
                and run.lease_until.replace(tzinfo=UTC) > datetime.now(UTC)
            ):
                raise self.retry(countdown=30)
            if run and (run.error or {}).get("retryable") and provider_attempt < 2:
                raise self.retry(countdown=20, kwargs={"provider_attempt": provider_attempt + 1})
            return {
                "publication_id": publication_id,
                "status": run.status if run else "failed",
                "error": post.index_error,
            }

    finally:
        database.engine.dispose()


@celery_app.task(name="realityos.prepare_chat_languages")
def prepare_chat_languages(user_id: str, message_id: int) -> dict:
    """A message lock serializes repeated requests without locking history reads."""
    from sqlalchemy import select

    from app.models import User
    from app.social_features.chat_localization import prepare_message
    from app.social_features.models import ChatMessage

    database = Database(settings.database_url)
    try:
        with database.session_factory() as db:
            user = db.get(User, uuid.UUID(user_id))
            if user is None or not user.is_active:
                return {"status": "unavailable"}
            message = db.scalar(
                select(ChatMessage)
                .where(
                    ChatMessage.id == message_id,
                    ChatMessage.user_id == user.id,
                    ChatMessage.role == "ai",
                )
                .with_for_update(skip_locked=True)
            )
            if message is None:
                return {"status": "skipped"}
            try:
                client = build_meta_client(settings)
            except Exception:
                client = None
            prepare_message(db, message, client)
            db.commit()
            return {"status": "processed"}
    finally:
        database.engine.dispose()
