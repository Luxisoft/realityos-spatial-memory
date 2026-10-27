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
