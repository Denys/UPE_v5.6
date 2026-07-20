"""Focused tests for the provider-neutral protocol and deterministic fake adapter."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest

from harness.adapters.base import (
    AdapterIdentity,
    ApprovalRequest,
    ApprovalResponse,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderErrorCategory,
    ProviderEvent,
    ProviderEventKind,
    ProviderFailure,
    ProviderTurnOutcome,
    SessionHandle,
    TurnHandle,
    TurnRequest,
)
from harness.adapters.fake import (
    DEFAULT_FAKE_BASE_TIME,
    FakeAdapter,
    FakeEventSpec,
    FakeOperationKind,
    FakeTurnScript,
)
from harness.state import (
    ActionClass,
    ApprovalStatus,
    BudgetState,
    BudgetValues,
    CompletionVerdict,
    LifecycleState,
    RedactionStatus,
    Run,
    Task,
    TaskStatus,
)

NOW = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)


def budget_state() -> BudgetState:
    return BudgetState(
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
    )


def run_record(**changes: object) -> Run:
    values: dict[str, object] = {
        "run_id": "run.c402.001",
        "goal_id": "goal.c402",
        "provider": "fake",
        "model": "fake-model",
        "reasoning_effort": None,
        "provider_config_ref": None,
        "lifecycle_state": LifecycleState.EXECUTING,
        "started_at": NOW,
        "updated_at": NOW,
        "iteration_count": 0,
        "budget": budget_state(),
        "current_task_id": "C-402",
        "approval_state": None,
        "checkpoint_ref": None,
        "stop_reason": None,
        "completion_verdict": CompletionVerdict.NOT_EVALUATED,
        "completion_evidence_refs": (),
        "event_seq": 4,
        "last_transition_id": "transition.c402.executing",
    }
    values.update(changes)
    return Run(**values)  # type: ignore[arg-type]


def task_record(**changes: object) -> Task:
    values: dict[str, object] = {
        "task_id": "C-402",
        "goal_id": "goal.c402",
        "description": "Implement provider-neutral adapter contracts and a fake adapter.",
        "dependencies": ("C-401",),
        "status": TaskStatus.IN_PROGRESS,
        "attempts": 1,
        "selected_workspace": r"C:\worktrees\c402",
        "allowed_paths": (
            "src/harness/adapters/base.py",
            "src/harness/adapters/fake.py",
            "tests/unit/test_fake_adapter.py",
        ),
        "locked_paths": ("src/harness/state.py", "src/harness/config.py"),
        "criterion_ids": ("criterion.fake_adapter",),
        "validation_commands": ("uv run pytest -q tests/unit/test_fake_adapter.py",),
        "evidence_paths": (),
        "last_failure": None,
        "next_action": None,
    }
    values.update(changes)
    return Task(**values)  # type: ignore[arg-type]


def turn_request(
    *,
    request_id: str = "request.c402.001",
    run: Run | None = None,
    task: Task | None = None,
) -> TurnRequest:
    return TurnRequest(
        request_id=request_id,
        run=run if run is not None else run_record(),
        task=task if task is not None else task_record(),
        instructions="Apply the bounded C-402 fake-adapter script.",
        input_refs=("agent/state/C-402-pre-edit-context.yaml",),
    )


def prepared_turn(
    script: FakeTurnScript,
    *,
    request_id: str = "request.c402.001",
    base_time: datetime = DEFAULT_FAKE_BASE_TIME,
) -> tuple[FakeAdapter, Run, Task, SessionHandle, TurnHandle]:
    run = run_record()
    task = task_record()
    adapter = FakeAdapter((script,), base_time=base_time)
    adapter.start()
    session = adapter.create_session(run=run)
    turn = adapter.submit_turn(
        session=session,
        request=turn_request(request_id=request_id, run=run, task=task),
    )
    return adapter, run, task, session, turn


def test_fake_adapter_satisfies_runtime_protocol_and_public_records_are_frozen() -> None:
    adapter = FakeAdapter((FakeTurnScript.success(),))

    assert isinstance(adapter, ProviderAdapter)
    assert adapter.identity == AdapterIdentity(
        adapter="fake",
        provider="fake",
        implementation_version="1.0.0",
        protocol_version="fake-v1",
    )

    adapter.start()
    operation = adapter.operations[0]
    with pytest.raises(FrozenInstanceError):
        operation.__setattr__("summary", "mutated")


@pytest.mark.parametrize(
    ("run", "task", "message"),
    [
        (run_record(goal_id="goal.other"), task_record(), "same goal"),
        (run_record(current_task_id="C-999"), task_record(), "current_task_id"),
        (
            run_record(lifecycle_state=LifecycleState.VALIDATING),
            task_record(),
            "EXECUTING",
        ),
        (run_record(), task_record(status=TaskStatus.READY), "IN_PROGRESS"),
        (run_record(), task_record(selected_workspace=None), "selected_workspace"),
    ],
)
def test_turn_request_rejects_misaligned_c401_state(
    run: Run,
    task: Task,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        turn_request(run=run, task=task)


def test_adapter_types_reject_coercion_naive_time_and_invalid_payload_combinations() -> None:
    with pytest.raises(TypeError, match="ApprovalStatus"):
        ApprovalResponse(
            approval_id="approval.001",
            decision=cast(ApprovalStatus, "GRANTED"),
            reason="Approved",
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        ProviderEvent(
            event_id="event.001",
            sequence=1,
            timestamp=datetime(2026, 7, 20, 12, 0),
            session_id="session.001",
            turn_id="turn.001",
            kind=ProviderEventKind.TURN_STARTED,
            summary="Started",
        )

    with pytest.raises(ValueError, match="requires failure"):
        FakeEventSpec(
            kind=ProviderEventKind.TURN_TERMINAL,
            summary="Failed",
            outcome=ProviderTurnOutcome.FAILED,
        )

    with pytest.raises(ValueError, match="forbids outcome/failure"):
        FakeEventSpec(
            kind=ProviderEventKind.APPROVAL_REQUIRED,
            summary="Approve",
            approval=ApprovalRequest(
                approval_id="approval.001",
                action_class=ActionClass.WRITE,
                summary="Approve",
            ),
            outcome=ProviderTurnOutcome.SUCCEEDED,
        )


def test_fake_script_rejects_invalid_ordering_and_duplicate_approval_ids() -> None:
    start = FakeEventSpec(
        kind=ProviderEventKind.TURN_STARTED,
        summary="Started",
    )
    terminal = FakeEventSpec(
        kind=ProviderEventKind.TURN_TERMINAL,
        summary="Succeeded",
        outcome=ProviderTurnOutcome.SUCCEEDED,
    )
    approval = FakeEventSpec(
        kind=ProviderEventKind.APPROVAL_REQUIRED,
        summary="Approve",
        approval=ApprovalRequest(
            approval_id="approval.duplicate",
            action_class=ActionClass.WRITE,
            summary="Approve",
        ),
    )

    with pytest.raises(ValueError, match="begin with TURN_STARTED"):
        FakeTurnScript(name="bad.first", events=(terminal,))
    with pytest.raises(ValueError, match="end with exactly one"):
        FakeTurnScript(name="missing.terminal", events=(start,))
    with pytest.raises(ValueError, match="approval IDs must be unique"):
        FakeTurnScript(
            name="duplicate.approval",
            events=(start, approval, approval, terminal),
        )


def test_start_stop_are_idempotent_and_preflight_fails_closed() -> None:
    adapter = FakeAdapter((FakeTurnScript.success(),))

    with pytest.raises(ProviderAdapterError) as not_started:
        adapter.preflight()
    assert not_started.value.category is ProviderErrorCategory.STATE
    assert not_started.value.provider_code == "ADAPTER_NOT_STARTED"

    assert adapter.start() == adapter.identity
    assert adapter.start() == adapter.identity
    assert adapter.preflight() == adapter.identity
    adapter.stop()
    adapter.stop()
    assert not adapter.started

    incompatible = FakeAdapter((FakeTurnScript.success(),), compatible=False)
    incompatible.start()
    with pytest.raises(ProviderAdapterError) as failed_preflight:
        incompatible.preflight()
    assert failed_preflight.value.category is ProviderErrorCategory.COMPATIBILITY
    assert failed_preflight.value.provider_code == "FAKE_INCOMPATIBLE"


def test_create_and_resume_session_are_deterministic_and_identity_checked() -> None:
    adapter = FakeAdapter((FakeTurnScript.success(),))
    run = run_record()
    adapter.start()

    created = adapter.create_session(run=run)
    resumed = adapter.resume_session(run=run, session_id="provider.session.external")

    assert created.session_id == "fake.session.0001"
    assert resumed == SessionHandle(
        session_id="provider.session.external",
        run_id=run.run_id,
        provider="fake",
    )
    assert adapter.resume_session(run=run, session_id=resumed.session_id) == resumed

    with pytest.raises(ProviderAdapterError) as mismatch:
        adapter.resume_session(
            run=run_record(run_id="run.c402.other"),
            session_id=resumed.session_id,
        )
    assert mismatch.value.provider_code == "SESSION_IDENTITY_MISMATCH"

    with pytest.raises(ProviderAdapterError) as wrong_provider:
        adapter.create_session(run=run_record(provider="codex"))
    assert wrong_provider.value.provider_code == "RUN_PROVIDER_MISMATCH"


def test_scripted_success_is_exactly_once_ordered_and_does_not_mutate_c401_inputs() -> None:
    adapter, run, task, _, turn = prepared_turn(
        FakeTurnScript.success(output_refs=("artifacts/fake.patch",))
    )
    original_run = run
    original_task = task

    events = tuple(adapter.stream_events(turn=turn))

    assert [event.kind for event in events] == [
        ProviderEventKind.TURN_STARTED,
        ProviderEventKind.OUTPUT,
        ProviderEventKind.TURN_TERMINAL,
    ]
    assert [event.sequence for event in events] == [1, 2, 3]
    assert [event.event_id for event in events] == [
        "fake.event.0001",
        "fake.event.0002",
        "fake.event.0003",
    ]
    assert [event.timestamp for event in events] == [
        DEFAULT_FAKE_BASE_TIME,
        DEFAULT_FAKE_BASE_TIME + timedelta(microseconds=1),
        DEFAULT_FAKE_BASE_TIME + timedelta(microseconds=2),
    ]
    assert events[-1].outcome is ProviderTurnOutcome.SUCCEEDED
    assert events[-1].output_refs == ("artifacts/fake.patch",)
    assert tuple(adapter.stream_events(turn=turn)) == ()
    assert run == original_run
    assert task == original_task
    assert run.event_seq == 4


def test_identical_scripts_and_calls_produce_identical_events_and_operations() -> None:
    script = FakeTurnScript.success(output_refs=("artifacts/fake.patch",))
    first, _, _, _, first_turn = prepared_turn(script)
    second, _, _, _, second_turn = prepared_turn(script)

    assert tuple(first.stream_events(turn=first_turn)) == tuple(
        second.stream_events(turn=second_turn)
    )
    assert first.operations == second.operations


def test_scripted_failure_is_a_normalized_terminal_event_not_an_exception() -> None:
    adapter, _, _, _, turn = prepared_turn(
        FakeTurnScript.failure(
            category=ProviderErrorCategory.TRANSIENT,
            message="Synthetic overload",
            retryable=True,
            provider_code="FAKE_OVERLOAD",
        )
    )

    events = tuple(adapter.stream_events(turn=turn))
    terminal = events[-1]

    assert terminal.kind is ProviderEventKind.TURN_TERMINAL
    assert terminal.outcome is ProviderTurnOutcome.FAILED
    assert terminal.failure == ProviderFailure(
        category=ProviderErrorCategory.TRANSIENT,
        message="Synthetic overload",
        retryable=True,
        provider_code="FAKE_OVERLOAD",
    )


def test_scripted_interruption_is_reproducible() -> None:
    adapter, _, _, _, turn = prepared_turn(
        FakeTurnScript.interrupted(reason="Synthetic disconnect")
    )

    events = tuple(adapter.stream_events(turn=turn))

    assert [event.kind for event in events] == [
        ProviderEventKind.TURN_STARTED,
        ProviderEventKind.TURN_TERMINAL,
    ]
    assert events[-1].outcome is ProviderTurnOutcome.INTERRUPTED
    assert events[-1].summary == "Synthetic disconnect"


def test_explicit_interrupt_replaces_remaining_script_with_terminal_event() -> None:
    adapter, _, _, _, turn = prepared_turn(FakeTurnScript.success())
    iterator = adapter.stream_events(turn=turn)

    assert next(iterator).kind is ProviderEventKind.TURN_STARTED
    adapter.interrupt(turn=turn, reason="Operator requested stop")
    remaining = tuple(iterator)

    assert len(remaining) == 1
    assert remaining[0].sequence == 2
    assert remaining[0].outcome is ProviderTurnOutcome.INTERRUPTED
    assert remaining[0].summary == "Turn interrupted: Operator requested stop"
    with pytest.raises(ProviderAdapterError) as terminal:
        adapter.interrupt(turn=turn, reason="Duplicate")
    assert terminal.value.provider_code == "TURN_ALREADY_TERMINAL"


def test_cancel_forces_every_active_session_turn_to_cancelled() -> None:
    scripts = (FakeTurnScript.success(name="one"), FakeTurnScript.success(name="two"))
    adapter = FakeAdapter(scripts)
    run = run_record()
    task = task_record()
    adapter.start()
    session = adapter.create_session(run=run)
    first = adapter.submit_turn(
        session=session,
        request=turn_request(request_id="request.c402.one", run=run, task=task),
    )
    second = adapter.submit_turn(
        session=session,
        request=turn_request(request_id="request.c402.two", run=run, task=task),
    )

    adapter.cancel(session=session, reason="Operator cancelled run")

    first_events = tuple(adapter.stream_events(turn=first))
    second_events = tuple(adapter.stream_events(turn=second))
    assert first_events[-1].outcome is ProviderTurnOutcome.CANCELLED
    assert second_events[-1].outcome is ProviderTurnOutcome.CANCELLED
    assert first_events[-1].summary == "Session cancelled: Operator cancelled run"
    assert second_events[-1].summary == "Session cancelled: Operator cancelled run"


def test_approval_grant_pauses_then_resumes_exactly_once() -> None:
    adapter, _, _, _, turn = prepared_turn(
        FakeTurnScript.approval_then_success(
            approval_id="approval.c402.write",
            output_refs=("artifacts/approved.patch",),
        )
    )

    first_segment = tuple(adapter.stream_events(turn=turn))
    assert [event.kind for event in first_segment] == [
        ProviderEventKind.TURN_STARTED,
        ProviderEventKind.APPROVAL_REQUIRED,
    ]
    assert first_segment[-1].approval is not None
    assert first_segment[-1].approval.approval_id == "approval.c402.write"

    with pytest.raises(ProviderAdapterError) as pending:
        adapter.stream_events(turn=turn)
    assert pending.value.provider_code == "APPROVAL_PENDING"

    response = ApprovalResponse(
        approval_id="approval.c402.write",
        decision=ApprovalStatus.GRANTED,
        reason="Bounded local write approved",
        evidence_refs=("authorization/user-message",),
    )
    adapter.respond_to_approval(turn=turn, response=response)
    second_segment = tuple(adapter.stream_events(turn=turn))

    assert [event.sequence for event in second_segment] == [3, 4]
    assert second_segment[-1].outcome is ProviderTurnOutcome.SUCCEEDED
    assert second_segment[-1].output_refs == ("artifacts/approved.patch",)
    assert adapter.operations[-2].kind is FakeOperationKind.APPROVAL_RESPONSE


def test_approval_mismatch_denial_and_duplicate_response_fail_closed() -> None:
    adapter, _, _, _, turn = prepared_turn(
        FakeTurnScript.approval_then_success(approval_id="approval.c402.write")
    )
    tuple(adapter.stream_events(turn=turn))

    with pytest.raises(ProviderAdapterError) as mismatch:
        adapter.respond_to_approval(
            turn=turn,
            response=ApprovalResponse(
                approval_id="approval.c402.other",
                decision=ApprovalStatus.GRANTED,
                reason="Wrong request",
            ),
        )
    assert mismatch.value.provider_code == "APPROVAL_ID_MISMATCH"

    denied = ApprovalResponse(
        approval_id="approval.c402.write",
        decision=ApprovalStatus.DENIED,
        reason="Scope not authorized",
    )
    adapter.respond_to_approval(turn=turn, response=denied)
    terminal = tuple(adapter.stream_events(turn=turn))

    assert len(terminal) == 1
    assert terminal[0].outcome is ProviderTurnOutcome.INTERRUPTED
    assert terminal[0].summary == "Approval denied: Scope not authorized"
    with pytest.raises(ProviderAdapterError) as duplicate:
        adapter.respond_to_approval(turn=turn, response=denied)
    assert duplicate.value.provider_code == "DUPLICATE_APPROVAL_RESPONSE"


def test_duplicate_requests_script_exhaustion_and_forged_handles_are_rejected() -> None:
    adapter = FakeAdapter((FakeTurnScript.success(),))
    run = run_record()
    task = task_record()
    adapter.start()
    session = adapter.create_session(run=run)
    request = turn_request(run=run, task=task)
    turn = adapter.submit_turn(session=session, request=request)

    with pytest.raises(ProviderAdapterError) as duplicate:
        adapter.submit_turn(session=session, request=request)
    assert duplicate.value.provider_code == "DUPLICATE_TURN_REQUEST"

    with pytest.raises(ProviderAdapterError) as exhausted:
        adapter.submit_turn(
            session=session,
            request=turn_request(
                request_id="request.c402.002",
                run=run,
                task=task,
            ),
        )
    assert exhausted.value.category is ProviderErrorCategory.PERMANENT
    assert exhausted.value.provider_code == "FAKE_SCRIPT_EXHAUSTED"

    forged_session = replace(session, run_id="run.forged")
    with pytest.raises(ProviderAdapterError) as session_mismatch:
        adapter.cancel(session=forged_session, reason="Test forged handle")
    assert session_mismatch.value.provider_code == "SESSION_HANDLE_MISMATCH"

    forged_turn = replace(turn, request_id="request.forged")
    with pytest.raises(ProviderAdapterError) as turn_mismatch:
        adapter.stream_events(turn=forged_turn)
    assert turn_mismatch.value.provider_code == "TURN_HANDLE_MISMATCH"


def test_provider_events_use_c401_redaction_vocabulary_without_canonical_transitions() -> None:
    adapter, _, _, _, turn = prepared_turn(FakeTurnScript.success())

    events = tuple(adapter.stream_events(turn=turn))

    assert all(event.redaction_status is RedactionStatus.NOT_REQUIRED for event in events)
    assert all(event.correlation_id == "request.c402.001" for event in events)
    assert not any(hasattr(event, "prior_state") for event in events)
    assert not any(hasattr(event, "event_seq") for event in events)
