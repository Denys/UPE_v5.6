"""Focused C-403 lifecycle and fake-adapter orchestration tests."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest

from harness.adapters.base import (
    AdapterIdentity,
    ApprovalResponse,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderErrorCategory,
    ProviderEvent,
    ProviderEventKind,
    ProviderTurnOutcome,
    SessionHandle,
    TurnHandle,
    TurnRequest,
)
from harness.adapters.fake import (
    FakeAdapter,
    FakeEventSpec,
    FakeOperationKind,
    FakeTurnScript,
)
from harness.lifecycle import (
    LifecycleCommitter,
    LifecycleCoordinator,
    LifecycleOrchestrationError,
)
from harness.orchestrator import (
    FinalizationEvidence,
    Orchestrator,
)
from harness.state import (
    ApprovalStatus,
    BudgetDimension,
    BudgetState,
    BudgetValues,
    CompletionVerdict,
    Event,
    EventType,
    LifecycleState,
    RedactionStatus,
    Run,
    StopReasonCode,
    Task,
    TaskStatus,
)

BASE_TIME = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
PROVIDER_BASE_TIME = BASE_TIME + timedelta(minutes=4, seconds=30)


class SteppingClock:
    """Return deterministic timestamps one minute apart."""

    def __init__(self, base_time: datetime = BASE_TIME) -> None:
        self._base_time = base_time
        self._calls = 0

    def __call__(self) -> datetime:
        self._calls += 1
        return self._base_time + timedelta(minutes=self._calls)


class RecordingCommitter:
    """Test-only atomic boundary with an optional deterministic failure."""

    def __init__(
        self,
        timeline: list[str] | None = None,
        *,
        fail_on: int | None = None,
    ) -> None:
        self.records: list[tuple[Run, Event]] = []
        self.timeline = timeline if timeline is not None else []
        self.fail_on = fail_on
        self.attempts = 0

    def commit(self, *, run: Run, event: Event) -> None:
        self.attempts += 1
        if event.next_state is not None:
            label = event.next_state.value
        else:
            label = next(
                value for value in event.input_refs if value.startswith("provider-sequence:")
            )
        if self.fail_on == self.attempts:
            self.timeline.append(f"commit-failed:{label}")
            raise RuntimeError("scripted commit failure")
        self.records.append((run, event))
        self.timeline.append(f"commit:{label}")


class TracingAdapter:
    """Protocol-complete wrapper that exposes external-action ordering."""

    def __init__(self, delegate: FakeAdapter, timeline: list[str]) -> None:
        self.delegate = delegate
        self.timeline = timeline

    @property
    def identity(self) -> AdapterIdentity:
        return self.delegate.identity

    @property
    def started(self) -> bool:
        return self.delegate.started

    def start(self) -> AdapterIdentity:
        self.timeline.append("adapter:start")
        return self.delegate.start()

    def stop(self) -> None:
        self.timeline.append("adapter:stop")
        self.delegate.stop()

    def preflight(self) -> AdapterIdentity:
        self.timeline.append("adapter:preflight")
        return self.delegate.preflight()

    def create_session(self, *, run: Run) -> SessionHandle:
        self.timeline.append("adapter:create-session")
        return self.delegate.create_session(run=run)

    def resume_session(self, *, run: Run, session_id: str) -> SessionHandle:
        self.timeline.append("adapter:resume-session")
        return self.delegate.resume_session(run=run, session_id=session_id)

    def submit_turn(
        self,
        *,
        session: SessionHandle,
        request: TurnRequest,
    ) -> TurnHandle:
        self.timeline.append("adapter:submit-turn")
        return self.delegate.submit_turn(session=session, request=request)

    def stream_events(self, *, turn: TurnHandle) -> Iterator[ProviderEvent]:
        self.timeline.append("adapter:stream-events")
        for event in self.delegate.stream_events(turn=turn):
            self.timeline.append(f"provider-yield:{event.sequence}")
            yield event

    def respond_to_approval(
        self,
        *,
        turn: TurnHandle,
        response: ApprovalResponse,
    ) -> None:
        self.timeline.append("adapter:approval-response")
        self.delegate.respond_to_approval(turn=turn, response=response)

    def interrupt(self, *, turn: TurnHandle, reason: str) -> None:
        self.timeline.append("adapter:interrupt")
        self.delegate.interrupt(turn=turn, reason=reason)

    def cancel(self, *, session: SessionHandle, reason: str) -> None:
        self.timeline.append("adapter:cancel")
        self.delegate.cancel(session=session, reason=reason)


class RaisingSubmitAdapter(TracingAdapter):
    def __init__(
        self,
        delegate: FakeAdapter,
        timeline: list[str],
        *,
        category: ProviderErrorCategory,
    ) -> None:
        super().__init__(delegate, timeline)
        self.category = category

    def submit_turn(
        self,
        *,
        session: SessionHandle,
        request: TurnRequest,
    ) -> TurnHandle:
        self.timeline.append("adapter:submit-turn")
        raise ProviderAdapterError(
            "scripted adapter exception",
            category=self.category,
            retryable=self.category is ProviderErrorCategory.TRANSIENT,
            provider_code="SCRIPTED_ADAPTER_ERROR",
            correlation_id=request.request_id,
        )


class TruncatedStreamAdapter(TracingAdapter):
    def stream_events(self, *, turn: TurnHandle) -> Iterator[ProviderEvent]:
        self.timeline.append("adapter:stream-events")
        for event in self.delegate.stream_events(turn=turn):
            if event.kind is ProviderEventKind.TURN_TERMINAL:
                return
            self.timeline.append(f"provider-yield:{event.sequence}")
            yield event


class CorruptSequenceAdapter(TracingAdapter):
    def stream_events(self, *, turn: TurnHandle) -> Iterator[ProviderEvent]:
        self.timeline.append("adapter:stream-events")
        for event in self.delegate.stream_events(turn=turn):
            corrupted = replace(event, sequence=event.sequence + 1)
            self.timeline.append(f"provider-yield:{corrupted.sequence}")
            yield corrupted


def budget_state() -> BudgetState:
    return BudgetState(
        limits=BudgetValues(
            iterations=8,
            elapsed_seconds=1200.0,
            input_tokens=4000,
            output_tokens=4000,
            total_tokens=8000,
            cost=10.0,
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
        "run_id": "run.c403.001",
        "goal_id": "goal.c403",
        "provider": "fake",
        "model": "fake-model",
        "reasoning_effort": None,
        "provider_config_ref": None,
        "lifecycle_state": LifecycleState.CREATED,
        "started_at": BASE_TIME,
        "updated_at": BASE_TIME,
        "iteration_count": 0,
        "budget": budget_state(),
        "current_task_id": None,
        "approval_state": None,
        "checkpoint_ref": None,
        "stop_reason": None,
        "completion_verdict": CompletionVerdict.NOT_EVALUATED,
        "completion_evidence_refs": (),
        "event_seq": 0,
        "last_transition_id": None,
    }
    values.update(changes)
    return Run(**values)  # type: ignore[arg-type]


def task_record(**changes: object) -> Task:
    values: dict[str, object] = {
        "task_id": "C-403",
        "goal_id": "goal.c403",
        "description": "Drive one fake-provider task through the lifecycle.",
        "dependencies": ("C-402",),
        "status": TaskStatus.READY,
        "attempts": 0,
        "selected_workspace": r"C:\worktrees\c403",
        "allowed_paths": (
            "src/harness/lifecycle.py",
            "src/harness/orchestrator.py",
            "tests/unit/test_lifecycle.py",
        ),
        "locked_paths": ("src/harness/state.py", "src/harness/adapters/fake.py"),
        "criterion_ids": ("criterion.c403.lifecycle",),
        "validation_commands": ("uv run pytest -q tests/unit/test_lifecycle.py",),
        "evidence_paths": (),
        "last_failure": None,
        "next_action": None,
    }
    values.update(changes)
    return Task(**values)  # type: ignore[arg-type]


def initialize_adapter(
    adapter: ProviderAdapter,
    timeline: list[str],
    *,
    committer: RecordingCommitter | None = None,
) -> tuple[Orchestrator, RecordingCommitter, Run, SessionHandle]:
    effective_committer = committer if committer is not None else RecordingCommitter(timeline)
    lifecycle = LifecycleCoordinator(
        committer=effective_committer,
        clock=SteppingClock(),
    )
    orchestrator = Orchestrator(adapter=adapter, lifecycle=lifecycle)
    initialized = orchestrator.initialize(run_record())
    assert initialized.session is not None
    return orchestrator, effective_committer, initialized.run, initialized.session


def ready_harness(
    script: FakeTurnScript,
) -> tuple[
    Orchestrator,
    TracingAdapter,
    RecordingCommitter,
    Run,
    SessionHandle,
    list[str],
]:
    timeline: list[str] = []
    adapter = TracingAdapter(
        FakeAdapter((script,), base_time=PROVIDER_BASE_TIME),
        timeline,
    )
    orchestrator, committer, run, session = initialize_adapter(adapter, timeline)
    return orchestrator, adapter, committer, run, session, timeline


def cancelled_script() -> FakeTurnScript:
    return FakeTurnScript(
        name="cancelled",
        events=(
            FakeEventSpec(
                kind=ProviderEventKind.TURN_STARTED,
                summary="Fake turn started",
            ),
            FakeEventSpec(
                kind=ProviderEventKind.TURN_TERMINAL,
                summary="Host cancelled fake turn",
                outcome=ProviderTurnOutcome.CANCELLED,
            ),
        ),
    )


def test_coordinator_is_runtime_protocol_compatible_and_commits_deterministic_transition() -> None:
    committer = RecordingCommitter()
    coordinator = LifecycleCoordinator(committer=committer, clock=SteppingClock())

    assert isinstance(committer, LifecycleCommitter)
    updated, event = coordinator.transition(
        run_record(),
        LifecycleState.INITIALIZING,
        reason="Provider initialization started",
    )

    assert committer.records == [(updated, event)]
    assert updated.event_seq == event.event_seq == 1
    assert event.transition_id == "run.c403.001.transition.000001.initializing"
    assert event.prior_state is LifecycleState.CREATED
    assert event.next_state is LifecycleState.INITIALIZING
    assert event.reason == "Provider initialization started"


def test_initialize_commits_before_adapter_actions_and_returns_ready_session() -> None:
    timeline: list[str] = []
    adapter = TracingAdapter(
        FakeAdapter((FakeTurnScript.success(),), base_time=PROVIDER_BASE_TIME),
        timeline,
    )
    _, _, run, session = initialize_adapter(adapter, timeline)

    assert isinstance(adapter, ProviderAdapter)
    assert run.lifecycle_state is LifecycleState.READY
    assert session.run_id == run.run_id
    assert timeline == [
        "commit:INITIALIZING",
        "adapter:start",
        "adapter:preflight",
        "adapter:create-session",
        "commit:READY",
    ]


def test_commit_failure_prevents_initial_adapter_action() -> None:
    timeline: list[str] = []
    committer = RecordingCommitter(timeline, fail_on=1)
    adapter = TracingAdapter(
        FakeAdapter((FakeTurnScript.success(),), base_time=PROVIDER_BASE_TIME),
        timeline,
    )
    orchestrator = Orchestrator(
        adapter=adapter,
        lifecycle=LifecycleCoordinator(committer=committer, clock=SteppingClock()),
    )

    with pytest.raises(RuntimeError, match="scripted commit failure"):
        orchestrator.initialize(run_record())

    assert timeline == ["commit-failed:INITIALIZING"]
    assert adapter.delegate.operations == ()


def test_executing_commit_failure_prevents_turn_submission() -> None:
    timeline: list[str] = []
    committer = RecordingCommitter(timeline, fail_on=4)
    adapter = TracingAdapter(
        FakeAdapter((FakeTurnScript.success(),), base_time=PROVIDER_BASE_TIME),
        timeline,
    )
    orchestrator, _, run, session = initialize_adapter(
        adapter,
        timeline,
        committer=committer,
    )

    with pytest.raises(RuntimeError, match="scripted commit failure"):
        orchestrator.execute_iteration(
            run,
            task_record(),
            session=session,
            request_id="request.c403.commit-failure",
            instructions="Run exactly one fake task.",
        )

    assert "commit-failed:EXECUTING" in timeline
    assert "adapter:submit-turn" not in timeline
    assert all(
        operation.kind is not FakeOperationKind.SUBMIT_TURN
        for operation in adapter.delegate.operations
    )


def test_success_runs_one_coherent_task_and_commits_each_event_before_next_yield() -> None:
    orchestrator, adapter, _, ready, session, timeline = ready_harness(
        FakeTurnScript.success(output_refs=("artifact:fake-output",))
    )
    original_run = ready
    original_task = task_record()
    timeline.clear()

    result = orchestrator.execute_iteration(
        ready,
        original_task,
        session=session,
        request_id="request.c403.success",
        instructions="Produce the bounded fake output.",
        input_refs=("plan:C-403",),
    )

    assert original_run.lifecycle_state is LifecycleState.READY
    assert original_run.current_task_id is None
    assert original_task.status is TaskStatus.READY
    assert original_task.attempts == 0
    assert result.run.lifecycle_state is LifecycleState.VALIDATING
    assert result.run.current_task_id == result.task.task_id == "C-403"
    assert result.run.iteration_count == 1
    assert result.task.status is TaskStatus.VALIDATING
    assert result.task.attempts == 1
    assert len(result.provider_events) == 3
    assert (
        sum(
            operation.kind is FakeOperationKind.SUBMIT_TURN
            for operation in adapter.delegate.operations
        )
        == 1
    )
    assert timeline.index("commit:EXECUTING") < timeline.index("adapter:submit-turn")
    assert timeline.index("provider-yield:1") < timeline.index("commit:provider-sequence:1")
    assert timeline.index("commit:provider-sequence:1") < timeline.index("provider-yield:2")
    assert timeline.index("commit:provider-sequence:2") < timeline.index("provider-yield:3")
    assert timeline.index("commit:provider-sequence:3") < timeline.index("commit:VALIDATING")


def test_provider_events_receive_run_sequence_without_becoming_lifecycle_events() -> None:
    committer = RecordingCommitter()
    coordinator = LifecycleCoordinator(committer=committer, clock=SteppingClock())
    run = run_record(
        lifecycle_state=LifecycleState.EXECUTING,
        current_task_id="C-403",
        event_seq=2,
        last_transition_id="transition.c403.executing",
    )
    turn = TurnHandle(
        turn_id="turn.c403.001",
        session_id="session.c403.001",
        request_id="request.c403.001",
        run_id=run.run_id,
        task_id="C-403",
    )
    provider_event = ProviderEvent(
        event_id="provider.event.007",
        sequence=7,
        timestamp=BASE_TIME + timedelta(seconds=30),
        session_id=turn.session_id,
        turn_id=turn.turn_id,
        kind=ProviderEventKind.ACTION,
        summary="Provider-local action",
        input_refs=("input:one",),
        output_refs=("output:one",),
        evidence_refs=("evidence:one",),
        correlation_id="provider.correlation.007",
        redaction_status=RedactionStatus.REDACTED,
    )

    updated, event = coordinator.record_provider_event(run, provider_event, turn=turn)

    assert updated.lifecycle_state is LifecycleState.EXECUTING
    assert updated.event_seq == event.event_seq == 3
    assert updated.last_transition_id == run.last_transition_id
    assert event.event_type is EventType.ACTION
    assert event.input_refs == (
        "provider-event:provider.event.007",
        "provider-sequence:7",
        "input:one",
    )
    assert event.correlation_id == "provider.correlation.007"
    assert event.transition_id is event.prior_state is event.next_state is event.reason is None


@pytest.mark.parametrize("mutation", ["timestamp", "session", "turn"])
def test_provider_event_identity_and_time_mismatches_fail_closed(mutation: str) -> None:
    coordinator = LifecycleCoordinator(
        committer=RecordingCommitter(),
        clock=SteppingClock(),
    )
    run = run_record(
        lifecycle_state=LifecycleState.EXECUTING,
        current_task_id="C-403",
        event_seq=2,
        last_transition_id="transition.c403.executing",
    )
    turn = TurnHandle(
        turn_id="turn.c403.001",
        session_id="session.c403.001",
        request_id="request.c403.001",
        run_id=run.run_id,
        task_id="C-403",
    )
    event = ProviderEvent(
        event_id="provider.event.001",
        sequence=1,
        timestamp=BASE_TIME + timedelta(seconds=30),
        session_id=turn.session_id,
        turn_id=turn.turn_id,
        kind=ProviderEventKind.TURN_STARTED,
        summary="Started",
    )
    if mutation == "timestamp":
        event = replace(event, timestamp=BASE_TIME - timedelta(seconds=1))
    elif mutation == "session":
        event = replace(event, session_id="session.other")
    else:
        event = replace(event, turn_id="turn.other")

    with pytest.raises(LifecycleOrchestrationError):
        coordinator.record_provider_event(run, event, turn=turn)


def test_worker_completion_message_only_reaches_validating() -> None:
    script = FakeTurnScript(
        name="worker_claims_complete",
        events=(
            FakeEventSpec(
                kind=ProviderEventKind.TURN_STARTED,
                summary="Started",
            ),
            FakeEventSpec(
                kind=ProviderEventKind.OUTPUT,
                summary="Task complete; all checks pass",
                output_refs=("worker:claim",),
            ),
            FakeEventSpec(
                kind=ProviderEventKind.TURN_TERMINAL,
                summary="Worker reports completion",
                output_refs=("worker:claim",),
                outcome=ProviderTurnOutcome.SUCCEEDED,
            ),
        ),
    )
    orchestrator, _, _, ready, session, _ = ready_harness(script)

    result = orchestrator.execute_iteration(
        ready,
        task_record(),
        session=session,
        request_id="request.c403.worker-claim",
        instructions="Report work, but do not decide completion.",
    )

    assert result.run.lifecycle_state is LifecycleState.VALIDATING
    assert result.run.completion_verdict is CompletionVerdict.NOT_EVALUATED
    assert result.run.completion_evidence_refs == ()
    assert result.task.status is TaskStatus.VALIDATING


def test_finalization_evidence_is_immutable_and_rejects_missing_or_nonpassing_proof() -> None:
    evidence = FinalizationEvidence(
        validation_verdict=CompletionVerdict.PASS,
        validation_evidence_refs=("validation:C-403",),
        checkpoint_ref="checkpoint:C-403",
    )
    with pytest.raises(FrozenInstanceError):
        evidence.__setattr__("goal_complete", True)

    with pytest.raises(ValueError, match="validation_verdict must be PASS"):
        FinalizationEvidence(
            validation_verdict=CompletionVerdict.FAIL,
            validation_evidence_refs=("validation:C-403",),
            checkpoint_ref="checkpoint:C-403",
        )
    with pytest.raises(ValueError, match="must not be empty"):
        FinalizationEvidence(
            validation_verdict=CompletionVerdict.PASS,
            validation_evidence_refs=(),
            checkpoint_ref="checkpoint:C-403",
        )
    with pytest.raises(ValueError, match="explicit evaluation verdict"):
        FinalizationEvidence(
            validation_verdict=CompletionVerdict.PASS,
            validation_evidence_refs=("validation:C-403",),
            checkpoint_ref="checkpoint:C-403",
            evaluation_evidence_refs=("evaluation:C-403",),
        )
    with pytest.raises(TypeError, match="must be a tuple"):
        FinalizationEvidence(
            validation_verdict=CompletionVerdict.PASS,
            validation_evidence_refs=("validation:C-403",),
            checkpoint_ref="checkpoint:C-403",
            evaluation_evidence_refs=[],  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="goal completion requires"):
        FinalizationEvidence(
            validation_verdict=CompletionVerdict.PASS,
            validation_evidence_refs=("validation:C-403",),
            checkpoint_ref="checkpoint:C-403",
            goal_complete=True,
        )


def test_passing_validation_checkpoints_task_and_returns_ready() -> None:
    orchestrator, _, committer, ready, session, _ = ready_harness(FakeTurnScript.success())
    iteration = orchestrator.execute_iteration(
        ready,
        task_record(),
        session=session,
        request_id="request.c403.checkpoint",
        instructions="Produce work for validation.",
    )
    prior_record_count = len(committer.records)

    finalized = orchestrator.finalize_iteration(
        iteration.run,
        iteration.task,
        evidence=FinalizationEvidence(
            validation_verdict=CompletionVerdict.PASS,
            validation_evidence_refs=("validation:C-403",),
            checkpoint_ref="checkpoint:C-403",
        ),
    )

    transitions = [event.next_state for _, event in committer.records[prior_record_count:]]
    assert transitions == [LifecycleState.CHECKPOINTING, LifecycleState.READY]
    assert finalized.run.lifecycle_state is LifecycleState.READY
    assert finalized.run.checkpoint_ref == "checkpoint:C-403"
    assert finalized.run.completion_verdict is CompletionVerdict.NOT_EVALUATED
    assert finalized.task.status is TaskStatus.CHECKPOINTED
    assert finalized.task.evidence_paths == (
        "validation:C-403",
        "checkpoint:C-403",
    )


def test_explicit_validation_evaluation_and_completion_evidence_complete_goal() -> None:
    orchestrator, _, committer, ready, session, _ = ready_harness(
        FakeTurnScript.success(output_refs=("worker:output",))
    )
    iteration = orchestrator.execute_iteration(
        ready,
        task_record(),
        session=session,
        request_id="request.c403.complete",
        instructions="Produce work for independent evidence checks.",
    )
    prior_record_count = len(committer.records)

    finalized = orchestrator.finalize_iteration(
        iteration.run,
        iteration.task,
        evidence=FinalizationEvidence(
            validation_verdict=CompletionVerdict.PASS,
            validation_evidence_refs=("validation:C-403",),
            checkpoint_ref="checkpoint:C-403",
            evaluation_verdict=CompletionVerdict.PASS,
            evaluation_evidence_refs=("evaluation:C-403",),
            goal_complete=True,
            completion_evidence_refs=("completion:C-403",),
        ),
    )

    transitions = [event.next_state for _, event in committer.records[prior_record_count:]]
    assert transitions == [
        LifecycleState.EVALUATING,
        LifecycleState.CHECKPOINTING,
        LifecycleState.COMPLETED,
    ]
    assert finalized.run.lifecycle_state is LifecycleState.COMPLETED
    assert finalized.run.completion_verdict is CompletionVerdict.PASS
    assert finalized.run.completion_evidence_refs == ("completion:C-403",)
    assert "worker:output" not in finalized.run.completion_evidence_refs
    assert finalized.task.status is TaskStatus.COMPLETE


def test_approval_event_pauses_without_response_or_further_streaming() -> None:
    orchestrator, adapter, _, ready, session, timeline = ready_harness(
        FakeTurnScript.approval_then_success(approval_id="approval.c403.001")
    )
    timeline.clear()

    result = orchestrator.execute_iteration(
        ready,
        task_record(),
        session=session,
        request_id="request.c403.approval",
        instructions="Pause when approval is requested.",
    )

    assert result.run.lifecycle_state is LifecycleState.APPROVAL_REQUIRED
    assert result.run.approval_state is ApprovalStatus.REQUESTED
    assert result.run.stop_reason is not None
    assert result.run.stop_reason.code is StopReasonCode.APPROVAL_REQUIRED
    assert result.task.status is TaskStatus.APPROVAL_REQUIRED
    assert result.task.next_action is not None
    assert "provider-yield:3" not in timeline
    assert all(
        operation.kind is not FakeOperationKind.APPROVAL_RESPONSE
        for operation in adapter.delegate.operations
    )


def test_expected_provider_failure_is_terminal_failed_state() -> None:
    orchestrator, _, _, ready, session, _ = ready_harness(
        FakeTurnScript.failure(
            category=ProviderErrorCategory.PERMANENT,
            message="Fixture rejected the task",
        )
    )

    result = orchestrator.execute_iteration(
        ready,
        task_record(),
        session=session,
        request_id="request.c403.failure",
        instructions="Exercise normalized provider failure.",
    )

    assert result.run.lifecycle_state is LifecycleState.FAILED
    assert result.run.stop_reason is not None
    assert result.run.stop_reason.code is StopReasonCode.FAILED
    assert result.task.status is TaskStatus.FAILED
    assert result.task.last_failure == "Fixture rejected the task"
    assert result.provider_events[-1].error_category == "PERMANENT"


@pytest.mark.parametrize(
    ("script", "expected_run", "expected_task", "expected_code"),
    [
        (
            FakeTurnScript.interrupted(reason="Fixture interrupted"),
            LifecycleState.BLOCKED,
            TaskStatus.BLOCKED,
            StopReasonCode.BLOCKED,
        ),
        (
            cancelled_script(),
            LifecycleState.CANCELLED,
            TaskStatus.CANCELLED,
            StopReasonCode.CANCELLED,
        ),
    ],
)
def test_interruption_and_cancellation_emit_reasoned_stop_states(
    script: FakeTurnScript,
    expected_run: LifecycleState,
    expected_task: TaskStatus,
    expected_code: StopReasonCode,
) -> None:
    orchestrator, _, _, ready, session, _ = ready_harness(script)

    result = orchestrator.execute_iteration(
        ready,
        task_record(),
        session=session,
        request_id=f"request.c403.{expected_run.value.lower()}",
        instructions="Exercise a reasoned provider stop.",
    )

    assert result.run.lifecycle_state is expected_run
    assert result.run.stop_reason is not None
    assert result.run.stop_reason.code is expected_code
    assert result.task.status is expected_task
    if expected_task is TaskStatus.BLOCKED:
        assert result.task.next_action is not None


@pytest.mark.parametrize(
    ("category", "expected_run", "expected_task", "expected_code"),
    [
        (
            ProviderErrorCategory.STATE,
            LifecycleState.FAILED,
            TaskStatus.FAILED,
            StopReasonCode.FAILED,
        ),
        (
            ProviderErrorCategory.PROTOCOL,
            LifecycleState.FAILED,
            TaskStatus.FAILED,
            StopReasonCode.FAILED,
        ),
        (
            ProviderErrorCategory.COMPATIBILITY,
            LifecycleState.BLOCKED,
            TaskStatus.BLOCKED,
            StopReasonCode.MISSING_DEPENDENCY,
        ),
        (
            ProviderErrorCategory.TRANSIENT,
            LifecycleState.BLOCKED,
            TaskStatus.BLOCKED,
            StopReasonCode.BLOCKED,
        ),
        (
            ProviderErrorCategory.PERMANENT,
            LifecycleState.BLOCKED,
            TaskStatus.BLOCKED,
            StopReasonCode.BLOCKED,
        ),
    ],
)
def test_adapter_exceptions_are_normalized_to_reasoned_stops(
    category: ProviderErrorCategory,
    expected_run: LifecycleState,
    expected_task: TaskStatus,
    expected_code: StopReasonCode,
) -> None:
    timeline: list[str] = []
    adapter = RaisingSubmitAdapter(
        FakeAdapter((FakeTurnScript.success(),), base_time=PROVIDER_BASE_TIME),
        timeline,
        category=category,
    )
    orchestrator, _, ready, session = initialize_adapter(adapter, timeline)

    result = orchestrator.execute_iteration(
        ready,
        task_record(),
        session=session,
        request_id=f"request.c403.adapter-{category.value.lower()}",
        instructions="Exercise normalized adapter exception handling.",
    )

    assert result.run.lifecycle_state is expected_run
    assert result.run.stop_reason is not None
    assert result.run.stop_reason.code is expected_code
    assert result.run.stop_reason.evidence_refs == (
        "provider-code:SCRIPTED_ADAPTER_ERROR",
        f"correlation:request.c403.adapter-{category.value.lower()}",
    )
    assert result.task.status is expected_task


def test_incompatible_preflight_blocks_initialization_without_session() -> None:
    timeline: list[str] = []
    adapter = TracingAdapter(
        FakeAdapter(
            (FakeTurnScript.success(),),
            base_time=PROVIDER_BASE_TIME,
            compatible=False,
        ),
        timeline,
    )
    lifecycle = LifecycleCoordinator(
        committer=RecordingCommitter(timeline),
        clock=SteppingClock(),
    )

    result = Orchestrator(adapter=adapter, lifecycle=lifecycle).initialize(run_record())

    assert result.session is None
    assert result.run.lifecycle_state is LifecycleState.BLOCKED
    assert result.run.stop_reason is not None
    assert result.run.stop_reason.code is StopReasonCode.MISSING_DEPENDENCY
    assert "adapter:create-session" not in timeline


@pytest.mark.parametrize("adapter_kind", ["truncated", "sequence"])
def test_malformed_provider_stream_fails_closed(adapter_kind: str) -> None:
    timeline: list[str] = []
    delegate = FakeAdapter((FakeTurnScript.success(),), base_time=PROVIDER_BASE_TIME)
    adapter: TracingAdapter
    if adapter_kind == "truncated":
        adapter = TruncatedStreamAdapter(delegate, timeline)
    else:
        adapter = CorruptSequenceAdapter(delegate, timeline)
    orchestrator, _, ready, session = initialize_adapter(adapter, timeline)

    result = orchestrator.execute_iteration(
        ready,
        task_record(),
        session=session,
        request_id=f"request.c403.{adapter_kind}",
        instructions="Exercise malformed provider stream handling.",
    )

    assert result.run.lifecycle_state is LifecycleState.FAILED
    assert result.run.stop_reason is not None
    assert result.run.stop_reason.code is StopReasonCode.FAILED
    assert result.task.status is TaskStatus.FAILED
    assert result.task.last_failure is not None
    assert "Provider protocol failure" in result.task.last_failure


@pytest.mark.parametrize(
    ("next_state", "code", "approval_state"),
    [
        (LifecycleState.BLOCKED, StopReasonCode.BLOCKED, None),
        (
            LifecycleState.APPROVAL_REQUIRED,
            StopReasonCode.APPROVAL_REQUIRED,
            ApprovalStatus.REQUESTED,
        ),
        (LifecycleState.FAILED, StopReasonCode.FAILED, None),
        (LifecycleState.CANCELLED, StopReasonCode.CANCELLED, None),
    ],
)
def test_lifecycle_stop_emits_terminal_event_with_explicit_reason(
    next_state: LifecycleState,
    code: StopReasonCode,
    approval_state: ApprovalStatus | None,
) -> None:
    coordinator = LifecycleCoordinator(
        committer=RecordingCommitter(),
        clock=SteppingClock(),
    )
    active = run_record(
        lifecycle_state=LifecycleState.READY,
        event_seq=2,
        last_transition_id="transition.c403.ready",
    )

    stopped, event = coordinator.stop(
        active,
        next_state,
        code=code,
        summary=f"Explicit {next_state.value.lower()} reason",
        evidence_refs=(f"evidence:{next_state.value.lower()}",),
        approval_state=approval_state,
    )

    assert stopped.lifecycle_state is next_state
    assert stopped.stop_reason is not None
    assert stopped.stop_reason.code is code
    assert event.event_type is EventType.TERMINAL
    assert event.reason == f"Explicit {next_state.value.lower()} reason"


def test_budget_exhausted_stop_requires_and_preserves_exhausted_dimension() -> None:
    exhausted_budget = BudgetState(
        limits=BudgetValues(iterations=1),
        consumed=BudgetValues(iterations=1),
        exhausted_dimensions=(BudgetDimension.ITERATIONS,),
    )
    active = run_record(
        lifecycle_state=LifecycleState.READY,
        budget=exhausted_budget,
        event_seq=2,
        last_transition_id="transition.c403.ready",
    )
    coordinator = LifecycleCoordinator(
        committer=RecordingCommitter(),
        clock=SteppingClock(),
    )

    stopped, _ = coordinator.stop(
        active,
        LifecycleState.BUDGET_EXHAUSTED,
        code=StopReasonCode.BUDGET_EXHAUSTED,
        summary="Iteration budget is exhausted",
        evidence_refs=("budget:iterations",),
    )

    assert stopped.lifecycle_state is LifecycleState.BUDGET_EXHAUSTED
    assert stopped.budget.exhausted_dimensions == (BudgetDimension.ITERATIONS,)


def test_complete_helper_rejects_completion_without_checkpoint_or_evidence() -> None:
    coordinator = LifecycleCoordinator(
        committer=RecordingCommitter(),
        clock=SteppingClock(),
    )
    checkpointing = run_record(
        lifecycle_state=LifecycleState.CHECKPOINTING,
        current_task_id="C-403",
        event_seq=7,
        last_transition_id="transition.c403.checkpointing",
    )

    with pytest.raises(ValueError, match="checkpoint_ref"):
        coordinator.complete(
            checkpointing,
            checkpoint_ref="",
            completion_evidence_refs=("completion:C-403",),
        )
    with pytest.raises(ValueError, match="must not be empty"):
        coordinator.complete(
            checkpointing,
            checkpoint_ref="checkpoint:C-403",
            completion_evidence_refs=(),
        )
