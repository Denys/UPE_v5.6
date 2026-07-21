"""C-406 tests for SQLite-authoritative Run/Event/outbox persistence."""

from __future__ import annotations

import sqlite3
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from harness.lifecycle import LifecycleCommitter, LifecycleCoordinator
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
from harness.state_store import (
    InlinePayloadTooLargeError,
    SQLiteStateStore,
    StateConflictError,
    StateStoreCorruptionError,
)

NOW = datetime(2026, 7, 21, 15, 0, tzinfo=UTC)


def initial_run() -> Run:
    budget = BudgetValues(
        iterations=4,
        elapsed_seconds=600.0,
        input_tokens=1000,
        output_tokens=1000,
        total_tokens=2000,
        cost=5.0,
    )
    return Run(
        run_id="run.c406.001",
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
            limits=budget,
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
    *,
    sequence: int,
    redaction_status: RedactionStatus = RedactionStatus.NOT_REQUIRED,
) -> tuple[Run, Event]:
    return transition_run(
        run,
        next_state,
        transition_id=f"run.c406.001.transition.{sequence:06d}",
        timestamp=NOW + timedelta(seconds=sequence),
        reason=f"Enter {next_state.value}.",
        output_refs=(f"artifacts/event-{sequence}.json",),
        redaction_status=redaction_status,
    )


def test_store_is_lifecycle_committer_and_atomically_records_pair(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "state" / "harness.sqlite3")
    assert isinstance(store, LifecycleCommitter)
    coordinator = LifecycleCoordinator(
        committer=store,
        clock=lambda: NOW + timedelta(seconds=1),
    )

    updated, event = coordinator.transition(
        initial_run(),
        LifecycleState.INITIALIZING,
        reason="Initialize durable state.",
    )

    assert store.load_run(updated.run_id) == updated
    assert store.load_event(updated.run_id, updated.event_seq) == event
    pending = store.pending_outbox()
    assert len(pending) == 1
    assert pending[0].event == event
    assert pending[0].delivered_at is None


def test_exact_duplicate_is_idempotent_but_conflicting_replay_fails(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    updated, event = transition(initial_run(), LifecycleState.INITIALIZING, sequence=1)
    store.commit(run=updated, event=event)
    store.commit(run=updated, event=event)

    assert len(store.all_outbox()) == 1
    conflicting = replace(event, action_summary="A conflicting replay.")
    with pytest.raises(StateConflictError, match="conflicts with outbox"):
        store.commit(run=updated, event=conflicting)
    assert store.load_run(updated.run_id) == updated
    assert len(store.all_outbox()) == 1


def test_duplicate_transition_rolls_back_state_and_outbox_together(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    first, first_event = transition(initial_run(), LifecycleState.INITIALIZING, sequence=1)
    store.commit(run=first, event=first_event)
    second, second_event = transition(first, LifecycleState.READY, sequence=2)
    duplicate_id = first_event.transition_id
    assert duplicate_id is not None
    conflicting_run = replace(second, last_transition_id=duplicate_id)
    conflicting_event = replace(second_event, transition_id=duplicate_id)

    with pytest.raises(StateConflictError, match="already committed"):
        store.commit(run=conflicting_run, event=conflicting_event)

    assert store.load_run(first.run_id) == first
    assert store.load_event(first.run_id, 2) is None
    assert len(store.pending_outbox()) == 1


def test_exact_old_replay_fails_after_authoritative_state_advances(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    first, first_event = transition(initial_run(), LifecycleState.INITIALIZING, sequence=1)
    second, second_event = transition(first, LifecycleState.READY, sequence=2)
    store.commit(run=first, event=first_event)
    store.commit(run=second, event=second_event)

    with pytest.raises(StateConflictError, match="already advanced"):
        store.commit(run=first, event=first_event)
    assert store.load_run(first.run_id) == second
    assert len(store.all_outbox()) == 2


def test_new_store_refuses_to_invent_missing_event_history(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    first, _ = transition(initial_run(), LifecycleState.INITIALIZING, sequence=1)
    second, second_event = transition(first, LifecycleState.READY, sequence=2)

    with pytest.raises(StateConflictError, match="must begin with event_seq 1"):
        store.commit(run=second, event=second_event)
    assert store.load_run(second.run_id) is None
    assert store.pending_outbox() == ()


def test_redaction_marker_and_references_round_trip_without_large_value(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    updated, event = transition(
        initial_run(),
        LifecycleState.INITIALIZING,
        sequence=1,
        redaction_status=RedactionStatus.REDACTED,
    )
    large_output = tmp_path / "artifacts" / "large.log"
    large_output.parent.mkdir()
    large_output.write_bytes(b"x" * (2 * 1024 * 1024))

    store.commit(run=updated, event=event)

    stored = store.load_event(updated.run_id, 1)
    assert stored is not None
    assert stored.redaction_status is RedactionStatus.REDACTED
    assert stored.output_refs == ("artifacts/event-1.json",)
    database_bytes = store.database_path.read_bytes()
    assert len(database_bytes) < large_output.stat().st_size
    assert b"x" * 4096 not in database_bytes


def test_oversized_inline_event_is_rejected_before_sqlite_write(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    updated, event = transition(initial_run(), LifecycleState.INITIALIZING, sequence=1)
    oversized_refs = tuple(f"artifacts/{index:03d}-{'x' * 1900}" for index in range(40))
    oversized_event = replace(event, output_refs=oversized_refs)

    with pytest.raises(InlinePayloadTooLargeError, match="referenced files"):
        store.commit(run=updated, event=oversized_event)
    assert store.load_run(updated.run_id) is None
    assert store.pending_outbox() == ()


def test_persisted_event_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    store = SQLiteStateStore(tmp_path / "harness.sqlite3")
    updated, event = transition(initial_run(), LifecycleState.INITIALIZING, sequence=1)
    store.commit(run=updated, event=event)
    with sqlite3.connect(store.database_path) as connection:
        connection.execute("UPDATE outbox SET event_json = event_json || ' ' WHERE outbox_id = 1")

    with pytest.raises(StateStoreCorruptionError, match="event_sha256"):
        store.load_event(updated.run_id, 1)
    with pytest.raises(StateStoreCorruptionError, match="event_sha256"):
        store.pending_outbox()
