"""C-406 tests for durable append-only JSONL outbox delivery and replay."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from harness.events import EventMirrorCorruptionError, JsonlEventMirror
from harness.state import (
    BudgetState,
    BudgetValues,
    CompletionVerdict,
    Event,
    LifecycleState,
    RedactionStatus,
    Run,
    transition_run,
)
from harness.state_store import OutboxRecord, SQLiteStateStore

NOW = datetime(2026, 7, 21, 16, 0, tzinfo=UTC)


def initial_run() -> Run:
    return Run(
        run_id="run.c406.events",
        goal_id="goal.c406",
        provider="codex",
        model="gpt-5.6-sol",
        reasoning_effort="high",
        provider_config_ref="config/runtime.json",
        lifecycle_state=LifecycleState.CREATED,
        started_at=NOW,
        updated_at=NOW,
        iteration_count=0,
        budget=BudgetState(
            limits=BudgetValues(
                iterations=4,
                elapsed_seconds=600.0,
                input_tokens=1000,
                output_tokens=1000,
                total_tokens=2000,
                cost=5.0,
            ),
            consumed=BudgetValues(
                iterations=0,
                elapsed_seconds=0.0,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                cost=0.0,
            ),
            exhausted_dimensions=(),
        ),
        current_task_id="C-406",
        approval_state=None,
        checkpoint_ref=None,
        stop_reason=None,
        completion_verdict=CompletionVerdict.NOT_EVALUATED,
        completion_evidence_refs=(),
        event_seq=0,
        last_transition_id=None,
    )


def transition(
    run: Run,
    next_state: LifecycleState,
    sequence: int,
    *,
    redacted: bool = False,
) -> tuple[Run, Event]:
    return transition_run(
        run,
        next_state,
        transition_id=f"run.c406.events.transition.{sequence:06d}",
        timestamp=NOW + timedelta(seconds=sequence),
        reason=f"Enter {next_state.value}.",
        evidence_refs=(f"evidence/event-{sequence}.json",),
        redaction_status=(RedactionStatus.REDACTED if redacted else RedactionStatus.NOT_REQUIRED),
    )


class CrashAfterAppendMirror(JsonlEventMirror):
    """Inject one process-style interruption after fsync and before SQLite ack."""

    def __init__(self, path: Path) -> None:
        super().__init__(path, clock=lambda: NOW + timedelta(minutes=1))
        self.crash = True

    def _after_durable_append(self, record: OutboxRecord) -> None:
        if self.crash:
            self.crash = False
            raise RuntimeError(f"crash after durable append {record.outbox_id}")


def test_delivery_is_ordered_durable_and_preserves_redaction(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    first, first_event = transition(initial_run(), LifecycleState.INITIALIZING, 1)
    second, second_event = transition(first, LifecycleState.READY, 2, redacted=True)
    store.commit(run=first, event=first_event)
    store.commit(run=second, event=second_event)
    mirror = JsonlEventMirror(
        tmp_path / "events" / "events.jsonl",
        clock=lambda: NOW + timedelta(minutes=1),
    )

    summary = mirror.deliver_pending(store)

    assert summary.inspected == 2
    assert summary.appended == 2
    assert summary.acknowledged == 2
    assert store.pending_outbox() == ()
    assert mirror.read_events() == (first_event, second_event)
    assert mirror.read_events()[1].redaction_status is RedactionStatus.REDACTED
    assert mirror.path.read_bytes().count(b"\n") == 2


def test_lost_ack_replay_deduplicates_existing_jsonl_event(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    updated, event = transition(initial_run(), LifecycleState.INITIALIZING, 1)
    store.commit(run=updated, event=event)
    path = tmp_path / "events.jsonl"
    crashing = CrashAfterAppendMirror(path)

    with pytest.raises(RuntimeError, match="after durable append"):
        crashing.deliver_pending(store)

    durable_bytes = path.read_bytes()
    assert durable_bytes.count(b"\n") == 1
    assert len(store.pending_outbox()) == 1

    recovered = JsonlEventMirror(path, clock=lambda: NOW + timedelta(minutes=2))
    summary = recovered.deliver_pending(store)
    assert summary.inspected == 1
    assert summary.appended == 0
    assert summary.acknowledged == 1
    assert path.read_bytes() == durable_bytes
    assert recovered.read_events() == (event,)
    assert store.pending_outbox() == ()


def test_later_delivery_preserves_existing_append_only_prefix(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    first, first_event = transition(initial_run(), LifecycleState.INITIALIZING, 1)
    store.commit(run=first, event=first_event)
    mirror = JsonlEventMirror(tmp_path / "events.jsonl", clock=lambda: NOW)
    mirror.deliver_pending(store)
    prefix = mirror.path.read_bytes()

    second, second_event = transition(first, LifecycleState.READY, 2)
    store.commit(run=second, event=second_event)
    summary = mirror.deliver_pending(store)

    combined = mirror.path.read_bytes()
    assert combined.startswith(prefix)
    assert len(combined) > len(prefix)
    assert summary.appended == 1
    assert mirror.read_events() == (first_event, second_event)


def test_partial_jsonl_tail_fails_closed_and_never_invents_state(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    updated, event = transition(initial_run(), LifecycleState.INITIALIZING, 1)
    store.commit(run=updated, event=event)
    path = tmp_path / "events.jsonl"
    path.write_bytes(b'{"event_seq":1')
    mirror = JsonlEventMirror(path, clock=lambda: NOW)

    with pytest.raises(EventMirrorCorruptionError, match="partial"):
        mirror.deliver_pending(store)

    assert path.read_bytes() == b'{"event_seq":1'
    assert len(store.pending_outbox()) == 1
    assert store.load_run(updated.run_id) == updated
