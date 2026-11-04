"""The local update guard preserves in-flight work and restores only its own pause."""

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "check_update_worker", ROOT / "scripts/local/check_update_worker.py"
)
guard = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(guard)
NODE = "celery@local-worker"
OPERATION = "38a4f69dc9b649e19d3b36e727379c2b"


class Control:
    def __init__(self):
        self.queues = [guard.QUEUE]
        self.tasks = {kind: [] for kind in ("scheduled", "reserved", "active")}
        self.calls = []
        self.unknown = None
        self.cancel_error = False
        self.resume_error = False

    def inspect(self, *, destination, timeout):
        assert destination == [NODE] and timeout == 5
        return self

    def active_queues(self):
        self.calls.append("active_queues")
        return {NODE: [{"name": queue} for queue in self.queues]}

    def __getattr__(self, name):
        if name not in self.tasks:
            raise AttributeError(name)

        def inspect_tasks():
            self.calls.append(name)
            return None if name == self.unknown else {NODE: self.tasks[name]}

        return inspect_tasks

    def cancel_consumer(self, queue, **kwargs):
        assert queue == "celery"
        assert kwargs == {"destination": [NODE], "reply": True, "timeout": 5}
        self.calls.append("cancel_consumer")
        self.queues = []
        if self.cancel_error:
            raise TimeoutError("Reply lost after cancellation")
        return [{NODE: {"ok": "Consumer cancelled"}}]

    def add_consumer(self, queue, **kwargs):
        assert queue == "celery"
        assert kwargs == {"destination": [NODE], "reply": True, "timeout": 5}
        self.calls.append("add_consumer")
        if self.resume_error:
            raise TimeoutError("Worker unavailable")
        self.queues = [queue]
        return [{NODE: {"ok": "Consumer restored"}}]


def test_idle_worker_pauses_and_resumes_only_its_local_queue(tmp_path):
    control = Control()
    state = tmp_path / "pause.json"
    guard.prepare(control, NODE, OPERATION, state)
    assert control.queues == []
    assert control.calls == [
        "active_queues",
        "cancel_consumer",
        "active_queues",
        "scheduled",
        "reserved",
        "active",
    ]
    assert json.loads(state.read_text())["operation"] == OPERATION
    assert state.stat().st_mode & 0o777 == 0o600
    guard.resume(control, NODE, OPERATION, state)
    assert control.queues == ["celery"] and not state.exists()
    previous = list(control.calls)
    guard.resume(control, NODE, OPERATION, state)
    assert control.calls == previous


@pytest.mark.parametrize("kind", ["scheduled", "reserved", "active"])
def test_busy_worker_resumes_without_terminating_or_revoking_tasks(tmp_path, kind):
    control = Control()
    task = {"id": "existing-work", "name": "realityos.process_media"}
    control.tasks[kind] = [task]
    state = tmp_path / "pause.json"
    with pytest.raises(guard.WorkerUpdateError, match="worker is busy"):
        guard.prepare(control, NODE, OPERATION, state)
    assert control.tasks[kind] == [task]
    assert control.queues == ["celery"] and not state.exists()
    assert control.calls[-2:] == ["add_consumer", "active_queues"]


@pytest.mark.parametrize("kind", ["scheduled", "reserved", "active"])
def test_unknown_worker_state_restores_consumption_and_rejects_update(tmp_path, kind):
    control = Control()
    control.unknown = kind
    state = tmp_path / "pause.json"
    with pytest.raises(guard.WorkerUpdateError, match="did not confirm its state"):
        guard.prepare(control, NODE, OPERATION, state)
    assert control.queues == ["celery"] and not state.exists()


def test_lost_cancellation_reply_still_restores_consumer(tmp_path):
    control = Control()
    control.cancel_error = True
    state = tmp_path / "pause.json"
    with pytest.raises(guard.WorkerUpdateError, match="consumer change"):
        guard.prepare(control, NODE, OPERATION, state)
    assert control.queues == ["celery"] and not state.exists()


def test_uncertain_restoration_keeps_owned_marker_for_retry(tmp_path):
    control = Control()
    control.tasks["active"] = [{"id": "existing-work"}]
    control.resume_error = True
    state = tmp_path / "pause.json"
    with pytest.raises(
        guard.WorkerUpdateError, match="Could not confirm queue restoration"
    ):
        guard.prepare(control, NODE, OPERATION, state)
    assert state.exists() and control.queues == []
    assert control.tasks["active"] == [{"id": "existing-work"}]
    control.resume_error = False
    guard.resume(control, NODE, OPERATION, state)
    assert control.queues == ["celery"] and not state.exists()


def test_another_update_cannot_resume_or_replace_an_existing_pause(tmp_path):
    control = Control()
    state = tmp_path / "pause.json"
    guard.prepare(control, NODE, OPERATION, state)
    original = state.read_bytes()
    with pytest.raises(guard.WorkerUpdateError, match="another update"):
        guard.resume(control, NODE, "f" * 32, state)
    with pytest.raises(guard.WorkerUpdateError, match="not ready"):
        guard.prepare(control, NODE, "f" * 32, state)
    assert state.read_bytes() == original and control.queues == []
    guard.resume(control, NODE, OPERATION, state)


def test_explicit_recovery_restores_the_recorded_pause_without_a_new_token(tmp_path):
    control = Control()
    state = tmp_path / "pause.json"
    guard.prepare(control, NODE, OPERATION, state)
    guard.recover(control, NODE, state)
    assert control.queues == ["celery"] and not state.exists()


def test_recovery_does_not_change_an_unmarked_manual_pause(tmp_path):
    control = Control()
    control.queues = []
    guard.recover(control, NODE, tmp_path / "missing.json")
    assert control.queues == [] and control.calls == []


def test_recovery_preserves_a_marker_for_another_worker(tmp_path):
    control = Control()
    state = tmp_path / "pause.json"
    guard.prepare(control, NODE, OPERATION, state)
    original = state.read_bytes()
    with pytest.raises(guard.WorkerUpdateError, match="another update"):
        guard.recover(control, "celery@foreign-worker", state)
    assert control.queues == [] and state.read_bytes() == original


@pytest.mark.parametrize("queues", [[], ["manual"], ["celery", "manual"]])
def test_unexpected_or_already_paused_queues_are_not_changed(tmp_path, queues):
    control = Control()
    control.queues = queues.copy()
    state = tmp_path / "pause.json"
    with pytest.raises(guard.WorkerUpdateError, match="not ready"):
        guard.prepare(control, NODE, OPERATION, state)
    guard.resume(control, NODE, OPERATION, state)
    assert control.queues == queues and not state.exists()
    assert control.calls == ["active_queues"]


@pytest.mark.parametrize(
    "changed",
    [
        {"ENVIRONMENT": "production"},
        {"LOCAL_LOGIN_ENABLED": "false"},
        {"LOCAL_EVALUATION_ENABLED": "false"},
        {"REDIS_URL": "redis://external:6379/0"},
        {"REDIS_URL": "redis://redis:6379/1"},
        {"REDIS_URL": "redis://user:secret@redis:6379/0"},
        {"REDIS_URL": "redis://redis:invalid/0"},
    ],
)
def test_guard_refuses_other_realms_or_brokers_before_creating_client(
    monkeypatch, changed
):
    monkeypatch.setattr(
        guard,
        "Celery",
        lambda *args, **kwargs: pytest.fail("No client may be created."),
    )
    environment = {
        "ENVIRONMENT": "local",
        "LOCAL_LOGIN_ENABLED": "true",
        "LOCAL_EVALUATION_ENABLED": "true",
        "REDIS_URL": "redis://redis:6379/0",
        **changed,
    }
    with pytest.raises(guard.WorkerUpdateError):
        guard.local_worker(environment, "local-worker")
