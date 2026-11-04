"""Server integration workers; excluded from the local application's task registry."""

import uuid

from app.db import Database
from app.tasks import celery_app, settings


@celery_app.task(
    name="realityos.import_facebook_media",
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 2},
)
def import_facebook_media(user_id: str) -> dict[str, object]:
    from app.gallery_index import queue_publication_index
    from app.social_features.facebook_import import import_facebook_media as import_media

    if settings.environment == "local":
        raise RuntimeError("External integration tasks are unavailable in the local runtime.")
    database = Database(settings.database_url)
    try:
        with database.session_factory() as db:
            result = import_media(db, settings, uuid.UUID(user_id))
            db.commit()
            for publication_id in result.get("publication_ids", []):
                queue_publication_index(uuid.UUID(publication_id))
            return {"user_id": user_id, **result}
    finally:
        database.engine.dispose()
