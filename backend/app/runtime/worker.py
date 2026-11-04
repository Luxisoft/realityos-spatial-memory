"""Queue capabilities shared by the API dispatcher and Celery workers."""

from celery import Celery

from app.config import Settings


def create_worker(settings: Settings) -> Celery:
    from app.local_runtime import validate_local_settings

    validate_local_settings(settings)
    local = settings.environment == "local"
    worker = Celery("realityos", broker=settings.redis_url, backend=settings.redis_url)
    worker.conf.update(
        imports=() if local else ("app.storage.tasks", "app.runtime.server_tasks"),
        beat_schedule={}
        if local
        else {"storage-sync": {"task": "realityos.storage_tick", "schedule": 60.0}},
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        task_track_started=True,
    )
    return worker


class ServerTaskDispatcher:
    """Stable dispatch interface without registering remote tasks in a local worker."""

    def __init__(self, worker: Celery, settings: Settings, name: str):
        self.worker = worker
        self.settings = settings
        self.name = name

    def delay(self, *args, **kwargs):
        if self.settings.environment == "local":
            raise RuntimeError("External integration tasks are unavailable in the local runtime.")
        return self.worker.send_task(self.name, args=args, kwargs=kwargs)
