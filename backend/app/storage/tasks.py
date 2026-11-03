import uuid
from datetime import timedelta

from sqlalchemy import or_, select

from app.config import get_settings
from app.db import Database
from app.storage.models import StorageImport, StorageSync
from app.storage.service import dispatch, now, process_import, sync_page
from app.tasks import celery_app


@celery_app.task(name="realityos.storage_import")
def storage_import(run_id):
    settings = get_settings()
    with Database(settings.database_url).session_factory() as db:
        process_import(db, uuid.UUID(run_id), settings)


@celery_app.task(name="realityos.storage_tick")
def storage_tick():
    settings = get_settings()
    with Database(settings.database_url).session_factory() as db:
        rules = list(
            db.scalars(
                select(StorageSync)
                .where(StorageSync.enabled.is_(True), StorageSync.next_run <= now())
                .with_for_update(skip_locked=True)
                .limit(20)
            )
        )
        ids = [rule.id for rule in rules]
        for rule in rules:
            rule.next_run = now() + timedelta(minutes=5)
        db.commit()
        for rule_id in ids:
            rule = db.scalar(
                select(StorageSync)
                .where(StorageSync.id == rule_id)
                .with_for_update(skip_locked=True)
            )
            if not rule or not rule.enabled:
                continue
            try:
                sync_page(db, rule, settings)
            except Exception:
                db.rollback()
                rule = db.get(StorageSync, rule_id)
                rule.error = "Sync failed. Check access and file limits; retry manually."
                rule.next_run = now() + timedelta(minutes=rule.interval_minutes)
                db.commit()
        for run in db.scalars(
            select(StorageImport)
            .where(
                or_(
                    StorageImport.status == "pending",
                    (StorageImport.status == "running") & (StorageImport.lease_until < now()),
                )
            )
            .limit(50)
        ):
            dispatch(run, settings)
