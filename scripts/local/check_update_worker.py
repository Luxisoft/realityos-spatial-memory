"""Pause only the installed local worker before an update; never terminate tasks."""

import json
import os
import socket
import sys
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from celery import Celery

STATE = Path("/tmp/realityos-local-update-worker.json")
QUEUE = "celery"
TIMEOUT = 5


class WorkerUpdateError(RuntimeError):
    pass


def local_worker(environment, hostname):
    required = {
        "ENVIRONMENT": "local",
        "LOCAL_LOGIN_ENABLED": "true",
        "LOCAL_EVALUATION_ENABLED": "true",
    }
    if any(environment.get(key) != value for key, value in required.items()):
        raise WorkerUpdateError("Worker is not in the local evaluation realm.")
    broker = environment.get("REDIS_URL", "")
    try:
        url = urlsplit(broker)
        valid = (
            url.scheme == "redis"
            and url.hostname == "redis"
            and url.port == 6379
            and url.path == "/0"
            and not (url.username or url.password or url.query or url.fragment)
        )
    except ValueError:
        valid = False
    if not valid:
        raise WorkerUpdateError("Worker does not use the isolated local Redis service.")
    return Celery("realityos-local-update", broker=broker), "celery@" + hostname


def rows(control, node, kind):
    try:
        inspector = control.inspect(destination=[node], timeout=TIMEOUT)
        result = getattr(inspector, kind)()
    except Exception as exc:
        raise WorkerUpdateError("Could not confirm the local worker's state.") from exc
    if (
        not isinstance(result, dict)
        or set(result) != {node}
        or not isinstance(result[node], list)
    ):
        raise WorkerUpdateError("The local worker did not confirm its state.")
    return result[node]


def queue_names(control, node):
    queues = rows(control, node, "active_queues")
    if any(
        not isinstance(queue, dict) or not isinstance(queue.get("name"), str)
        for queue in queues
    ):
        raise WorkerUpdateError(
            "The local worker returned an unknown queue configuration."
        )
    return [queue["name"] for queue in queues]


def consumer(control, node, action):
    try:
        response = getattr(control, action)(
            QUEUE, destination=[node], reply=True, timeout=TIMEOUT
        )
    except Exception as exc:
        raise WorkerUpdateError(
            "The local worker did not confirm the consumer change."
        ) from exc
    if (
        not isinstance(response, list)
        or len(response) != 1
        or not isinstance(response[0], dict)
        or set(response[0]) != {node}
        or not isinstance(response[0][node], dict)
        or set(response[0][node]) != {"ok"}
        or not isinstance(response[0][node]["ok"], str)
    ):
        raise WorkerUpdateError("The local worker did not confirm the consumer change.")


def resume(control, node, operation, state=STATE):
    if not state.exists():
        return
    try:
        marker = json.loads(state.read_text())
    except (OSError, ValueError) as exc:
        raise WorkerUpdateError(
            "Could not read the previous local update pause."
        ) from exc
    if marker != {"version": 1, "node": node, "queue": QUEUE, "operation": operation}:
        raise WorkerUpdateError(
            "The worker pause belongs to another update; it was preserved."
        )
    consumer(control, node, "add_consumer")
    if queue_names(control, node) != [QUEUE]:
        raise WorkerUpdateError(
            "Could not confirm that local queue consumption resumed."
        )
    state.unlink()


def recover(control, node, state=STATE):
    """Explicit operator recovery only; normal update failures must use their token."""
    if not state.exists():
        return
    try:
        marker = json.loads(state.read_text())
        operation = uuid.UUID(marker["operation"]).hex
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise WorkerUpdateError(
            "Could not read the previous local update pause."
        ) from exc
    resume(control, node, operation, state)


def prepare(control, node, operation, state=STATE):
    if queue_names(control, node) != [QUEUE]:
        raise WorkerUpdateError("Local worker queues are not ready for an update.")
    try:
        descriptor = os.open(state, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as marker:
            json.dump(
                {"version": 1, "node": node, "queue": QUEUE, "operation": operation},
                marker,
            )
    except OSError as exc:
        raise WorkerUpdateError(
            "A previous worker pause exists or could not be recorded."
        ) from exc
    try:
        consumer(control, node, "cancel_consumer")
        if queue_names(control, node):
            raise WorkerUpdateError("The local worker is still receiving tasks.")
        # Inspect waiting tasks before active tasks: no task can move from a
        # waiting list into execution unnoticed between these checks.
        for kind in ("scheduled", "reserved", "active"):
            if rows(control, node, kind):
                raise WorkerUpdateError(
                    "The local worker is busy. Wait for its tasks to finish and retry the update."
                )
    except BaseException:
        try:
            resume(control, node, operation, state)
        except Exception as exc:
            raise WorkerUpdateError(
                "Could not confirm queue restoration. No tasks were terminated; "
                "after confirming no other update is running, use update.sh --resume-worker "
                "or Update-RealityOS.ps1 -ResumeWorker."
            ) from exc
        raise


def main():
    recovery = sys.argv[1:] == ["recover"]
    if not recovery:
        if len(sys.argv) != 3 or sys.argv[1] not in {"prepare", "resume"}:
            raise SystemExit(
                "Use prepare/resume with the operation UUID, or explicit recover."
            )
        try:
            operation = uuid.UUID(sys.argv[2]).hex
        except ValueError:
            raise SystemExit("The local update operation UUID is invalid.") from None
    try:
        app, node = local_worker(os.environ, socket.gethostname())
        with app:
            if recovery:
                recover(app.control, node)
            else:
                action = prepare if sys.argv[1] == "prepare" else resume
                action(app.control, node, operation)
    except WorkerUpdateError as exc:
        raise SystemExit(str(exc)) from None
    print("Local worker update guard completed.")


if __name__ == "__main__":
    main()
