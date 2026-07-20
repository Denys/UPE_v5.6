"""C-403 single-task orchestration against a provider adapter.

The orchestrator sequences C-401 state and C-402 provider operations through
the synchronous :class:`~harness.lifecycle.LifecycleCommitter` boundary.  It
does not implement durable storage, validators, policy, retries, budgets,
resume edges, or a real provider transport.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import cast

from harness.adapters.base import (
    AdapterIdentity,
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
from harness.lifecycle import LifecycleCoordinator, LifecycleOrchestrationError
from harness.state import (
    STOPPED_STATES,
    ApprovalStatus,
    CompletionVerdict,
    Event,
    LifecycleState,
    Run,
    StopReasonCode,
    Task,
    TaskStatus,
)


class OrchestrationError(RuntimeError):
    """The requested C-403 operation violates the bounded host contract."""


def _require_refs(values: tuple[str, ...], location: str, *, required: bool = False) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{location} must be a tuple")
    if required and not values:
        raise ValueError(f"{location} must not be empty")
    seen: set[str] = set()
    for index, value in enumerate(values):
        if type(value) is not str:
            raise TypeError(f"{location}[{index}] must be a string")
        if not value or value != value.strip():
            raise ValueError(f"{location}[{index}] must be non-empty and normalized")
        if value in seen:
            raise ValueError(f"{location} must not contain duplicates")
        seen.add(value)


def _unique_refs(*groups: tuple[str, ...]) -> tuple[str, ...]:
    ordered: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for value in group:
            if value not in seen:
                ordered.append(value)
                seen.add(value)
    return tuple(ordered)


@dataclass(frozen=True, slots=True, kw_only=True)
class InitializationResult:
    """Run state and optional provider session after initialization."""

    run: Run
    session: SessionHandle | None

    def __post_init__(self) -> None:
        if type(self.run) is not Run:
            raise TypeError("InitializationResult.run must be a Run")
        if self.session is not None and type(self.session) is not SessionHandle:
            raise TypeError("InitializationResult.session must be a SessionHandle or null")
        if self.session is None:
            if self.run.lifecycle_state not in STOPPED_STATES:
                raise ValueError("initialization without a session requires a stopped Run")
        else:
            if self.run.lifecycle_state is not LifecycleState.READY:
                raise ValueError("successful initialization requires a READY Run")
            if self.session.run_id != self.run.run_id or self.session.provider != self.run.provider:
                raise ValueError("initialization session identity must match the Run")


@dataclass(frozen=True, slots=True, kw_only=True)
class IterationResult:
    """One submitted task and the canonical provider events consumed for it."""

    run: Run
    task: Task
    turn: TurnHandle | None
    provider_events: tuple[Event, ...]

    def __post_init__(self) -> None:
        if type(self.run) is not Run:
            raise TypeError("IterationResult.run must be a Run")
        if type(self.task) is not Task:
            raise TypeError("IterationResult.task must be a Task")
        if self.turn is not None and type(self.turn) is not TurnHandle:
            raise TypeError("IterationResult.turn must be a TurnHandle or null")
        if type(self.provider_events) is not tuple or any(
            type(event) is not Event for event in self.provider_events
        ):
            raise TypeError("IterationResult.provider_events must contain only Event values")
        if self.run.current_task_id != self.task.task_id:
            raise ValueError("iteration Run.current_task_id must match Task.task_id")
        if self.run.lifecycle_state not in STOPPED_STATES | {LifecycleState.VALIDATING}:
            raise ValueError("iteration must end in VALIDATING or a stopped Run state")


@dataclass(frozen=True, slots=True, kw_only=True)
class FinalizationEvidence:
    """Explicit non-provider evidence accepted by C-403 finalization.

    C-404 will create deterministic validator evidence.  This record only
    transports already-decided references and therefore requires PASS rather
    than interpreting output or running a validator itself.
    """

    validation_verdict: CompletionVerdict
    validation_evidence_refs: tuple[str, ...]
    checkpoint_ref: str
    evaluation_verdict: CompletionVerdict | None = None
    evaluation_evidence_refs: tuple[str, ...] = ()
    goal_complete: bool = False
    completion_evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if type(self.validation_verdict) is not CompletionVerdict:
            raise TypeError("FinalizationEvidence.validation_verdict must be a CompletionVerdict")
        if self.validation_verdict is not CompletionVerdict.PASS:
            raise ValueError("FinalizationEvidence.validation_verdict must be PASS")
        _require_refs(
            self.validation_evidence_refs,
            "FinalizationEvidence.validation_evidence_refs",
            required=True,
        )
        if (
            type(self.checkpoint_ref) is not str
            or not self.checkpoint_ref
            or self.checkpoint_ref != self.checkpoint_ref.strip()
        ):
            raise ValueError("FinalizationEvidence.checkpoint_ref must be non-empty and normalized")
        _require_refs(
            self.evaluation_evidence_refs,
            "FinalizationEvidence.evaluation_evidence_refs",
        )
        if self.evaluation_verdict is None:
            if self.evaluation_evidence_refs:
                raise ValueError("evaluation evidence requires an explicit evaluation verdict")
        else:
            if type(self.evaluation_verdict) is not CompletionVerdict:
                raise TypeError(
                    "FinalizationEvidence.evaluation_verdict must be a CompletionVerdict or null"
                )
            if self.evaluation_verdict is not CompletionVerdict.PASS:
                raise ValueError("FinalizationEvidence.evaluation_verdict must be PASS")
            if not self.evaluation_evidence_refs:
                raise ValueError("FinalizationEvidence.evaluation_evidence_refs must not be empty")
        if type(self.goal_complete) is not bool:
            raise TypeError("FinalizationEvidence.goal_complete must be a boolean")
        _require_refs(
            self.completion_evidence_refs,
            "FinalizationEvidence.completion_evidence_refs",
        )
        if self.goal_complete and not self.completion_evidence_refs:
            raise ValueError("goal completion requires completion_evidence_refs")
        if not self.goal_complete and self.completion_evidence_refs:
            raise ValueError("a non-complete goal must not provide completion_evidence_refs")


@dataclass(frozen=True, slots=True, kw_only=True)
class FinalizationResult:
    """Checkpointed task state and the resulting READY or COMPLETED Run."""

    run: Run
    task: Task

    def __post_init__(self) -> None:
        if type(self.run) is not Run:
            raise TypeError("FinalizationResult.run must be a Run")
        if type(self.task) is not Task:
            raise TypeError("FinalizationResult.task must be a Task")
        expected_task_status = (
            TaskStatus.COMPLETE
            if self.run.lifecycle_state is LifecycleState.COMPLETED
            else TaskStatus.CHECKPOINTED
        )
        if self.run.lifecycle_state not in {
            LifecycleState.READY,
            LifecycleState.COMPLETED,
        }:
            raise ValueError("finalization must end in READY or COMPLETED")
        if self.task.status is not expected_task_status:
            raise ValueError("finalization Task status does not match the Run outcome")
        if self.run.current_task_id != self.task.task_id:
            raise ValueError("finalization Run.current_task_id must match Task.task_id")


class Orchestrator:
    """Drive one synchronous task through the C-403 lifecycle slice."""

    def __init__(
        self,
        *,
        adapter: ProviderAdapter,
        lifecycle: LifecycleCoordinator,
    ) -> None:
        if not isinstance(adapter, ProviderAdapter):
            raise TypeError("adapter must implement ProviderAdapter")
        if type(lifecycle) is not LifecycleCoordinator:
            raise TypeError("lifecycle must be a LifecycleCoordinator")
        self._adapter = adapter
        self._lifecycle = lifecycle

    def initialize(self, run: Run) -> InitializationResult:
        """Commit INITIALIZING before starting or inspecting the adapter."""

        if type(run) is not Run:
            raise TypeError("run must be a Run")
        if run.lifecycle_state is not LifecycleState.CREATED:
            raise OrchestrationError("initialize requires a CREATED Run")

        initializing, _ = self._lifecycle.transition(
            run,
            LifecycleState.INITIALIZING,
            reason="Provider initialization started",
        )
        try:
            started_identity = self._adapter.start()
            self._validate_identity(initializing, started_identity, "start")
            preflight_identity = self._adapter.preflight()
            self._validate_identity(initializing, preflight_identity, "preflight")
            session = self._adapter.create_session(run=initializing)
            self._validate_session(initializing, session)
        except ProviderAdapterError as exc:
            stopped, _ = self._stop_for_adapter_error(initializing, exc)
            return InitializationResult(run=stopped, session=None)

        ready, _ = self._lifecycle.transition(
            initializing,
            LifecycleState.READY,
            reason="Provider compatibility and session initialization passed",
        )
        return InitializationResult(run=ready, session=session)

    def execute_iteration(
        self,
        run: Run,
        task: Task,
        *,
        session: SessionHandle,
        request_id: str,
        instructions: str,
        input_refs: tuple[str, ...] = (),
    ) -> IterationResult:
        """Submit exactly one READY task and consume one provider event segment."""

        self._validate_iteration_inputs(run, task, session)
        _require_refs(input_refs, "input_refs")

        selecting_input = replace(run, current_task_id=None)
        selecting, _ = self._lifecycle.transition(
            selecting_input,
            LifecycleState.SELECTING_TASK,
            reason=f"Select task {task.task_id} for one iteration",
        )
        active_task = replace(
            task,
            status=TaskStatus.IN_PROGRESS,
            attempts=task.attempts + 1,
            evidence_paths=(),
            last_failure=None,
            next_action=None,
        )
        executing_input = replace(
            selecting,
            current_task_id=active_task.task_id,
            iteration_count=selecting.iteration_count + 1,
        )
        executing, _ = self._lifecycle.transition(
            executing_input,
            LifecycleState.EXECUTING,
            reason=f"Dispatch task {active_task.task_id} to provider",
        )

        request = TurnRequest(
            request_id=request_id,
            run=executing,
            task=active_task,
            instructions=instructions,
            input_refs=input_refs,
        )
        turn: TurnHandle | None = None
        canonical_events: list[Event] = []
        try:
            turn = self._adapter.submit_turn(session=session, request=request)
            self._validate_turn(executing, active_task, session, request, turn)
            expected_provider_sequence = 1
            seen_provider_ids: set[str] = set()
            for provider_event in self._adapter.stream_events(turn=turn):
                try:
                    self._validate_provider_order(
                        provider_event,
                        expected_sequence=expected_provider_sequence,
                        seen_ids=seen_provider_ids,
                    )
                    executing, canonical_event = self._lifecycle.record_provider_event(
                        executing,
                        provider_event,
                        turn=turn,
                    )
                except LifecycleOrchestrationError as exc:
                    return self._protocol_failure_result(
                        executing,
                        active_task,
                        turn,
                        tuple(canonical_events),
                        str(exc),
                    )
                canonical_events.append(canonical_event)
                seen_provider_ids.add(provider_event.event_id)
                expected_provider_sequence += 1

                if provider_event.kind is ProviderEventKind.APPROVAL_REQUIRED:
                    approval = provider_event.approval
                    if approval is None:
                        return self._protocol_failure_result(
                            executing,
                            active_task,
                            turn,
                            tuple(canonical_events),
                            "approval event omitted its approval request",
                        )
                    summary = f"Provider approval {approval.approval_id} is required"
                    stopped, _ = self._lifecycle.stop(
                        executing,
                        LifecycleState.APPROVAL_REQUIRED,
                        code=StopReasonCode.APPROVAL_REQUIRED,
                        summary=summary,
                        evidence_refs=self._provider_refs(provider_event),
                        approval_state=ApprovalStatus.REQUESTED,
                    )
                    approval_task = replace(
                        active_task,
                        status=TaskStatus.APPROVAL_REQUIRED,
                        next_action=(
                            f"Resolve provider approval {approval.approval_id} in a new run"
                        ),
                    )
                    return IterationResult(
                        run=stopped,
                        task=approval_task,
                        turn=turn,
                        provider_events=tuple(canonical_events),
                    )

                if provider_event.kind is ProviderEventKind.TURN_TERMINAL:
                    return self._terminal_result(
                        executing,
                        active_task,
                        turn,
                        tuple(canonical_events),
                        provider_event,
                    )
        except ProviderAdapterError as exc:
            stopped, stopped_task = self._stop_for_adapter_error(
                executing,
                exc,
                task=active_task,
            )
            return IterationResult(
                run=stopped,
                task=cast(Task, stopped_task),
                turn=turn,
                provider_events=tuple(canonical_events),
            )

        return self._protocol_failure_result(
            executing,
            active_task,
            turn,
            tuple(canonical_events),
            "provider event stream ended without a terminal or approval event",
        )

    def finalize_iteration(
        self,
        run: Run,
        task: Task,
        *,
        evidence: FinalizationEvidence,
    ) -> FinalizationResult:
        """Accept explicit evidence; never infer completion from provider output."""

        if type(run) is not Run:
            raise TypeError("run must be a Run")
        if type(task) is not Task:
            raise TypeError("task must be a Task")
        if type(evidence) is not FinalizationEvidence:
            raise TypeError("evidence must be FinalizationEvidence")
        if run.lifecycle_state is not LifecycleState.VALIDATING:
            raise OrchestrationError("finalize_iteration requires a VALIDATING Run")
        if task.status is not TaskStatus.VALIDATING:
            raise OrchestrationError("finalize_iteration requires a VALIDATING Task")
        if run.current_task_id != task.task_id or run.goal_id != task.goal_id:
            raise OrchestrationError("finalization Run and Task identity must match")

        accepted_evidence = evidence.validation_evidence_refs
        current = run
        if evidence.evaluation_verdict is not None:
            current, _ = self._lifecycle.transition(
                current,
                LifecycleState.EVALUATING,
                reason="Deterministic validation passed; evaluation evidence accepted",
                evidence_refs=evidence.validation_evidence_refs,
            )
            accepted_evidence = _unique_refs(
                accepted_evidence,
                evidence.evaluation_evidence_refs,
            )

        checkpoint_evidence = _unique_refs(
            accepted_evidence,
            (evidence.checkpoint_ref,),
        )
        current, _ = self._lifecycle.transition(
            current,
            LifecycleState.CHECKPOINTING,
            reason="Passing evidence accepted and checkpoint recorded",
            evidence_refs=checkpoint_evidence,
            checkpoint_ref=evidence.checkpoint_ref,
        )

        if evidence.goal_complete:
            completed_task = replace(
                task,
                status=TaskStatus.COMPLETE,
                evidence_paths=_unique_refs(
                    checkpoint_evidence,
                    evidence.completion_evidence_refs,
                ),
                last_failure=None,
                next_action=None,
            )
            completed, _ = self._lifecycle.complete(
                current,
                checkpoint_ref=evidence.checkpoint_ref,
                completion_evidence_refs=evidence.completion_evidence_refs,
            )
            return FinalizationResult(run=completed, task=completed_task)

        checkpointed_task = replace(
            task,
            status=TaskStatus.CHECKPOINTED,
            evidence_paths=checkpoint_evidence,
            last_failure=None,
            next_action=None,
        )
        ready, _ = self._lifecycle.transition(
            current,
            LifecycleState.READY,
            reason=f"Task {task.task_id} checkpointed; goal remains active",
            evidence_refs=checkpoint_evidence,
        )
        return FinalizationResult(run=ready, task=checkpointed_task)

    @staticmethod
    def _validate_identity(run: Run, identity: AdapterIdentity, operation: str) -> None:
        if type(identity) is not AdapterIdentity:
            raise ProviderAdapterError(
                f"adapter {operation} returned an invalid identity record",
                category=ProviderErrorCategory.PROTOCOL,
                retryable=False,
                provider_code="INVALID_ADAPTER_IDENTITY",
                correlation_id=run.run_id,
            )
        if identity.provider != run.provider:
            raise ProviderAdapterError(
                f"adapter {operation} provider does not match the Run",
                category=ProviderErrorCategory.COMPATIBILITY,
                retryable=False,
                provider_code="ADAPTER_PROVIDER_MISMATCH",
                correlation_id=run.run_id,
            )

    @staticmethod
    def _validate_session(run: Run, session: SessionHandle) -> None:
        if type(session) is not SessionHandle:
            raise ProviderAdapterError(
                "adapter returned an invalid session handle",
                category=ProviderErrorCategory.PROTOCOL,
                retryable=False,
                provider_code="INVALID_SESSION_HANDLE",
                correlation_id=run.run_id,
            )
        if session.run_id != run.run_id or session.provider != run.provider:
            raise ProviderAdapterError(
                "adapter session identity does not match the Run",
                category=ProviderErrorCategory.PROTOCOL,
                retryable=False,
                provider_code="SESSION_IDENTITY_MISMATCH",
                correlation_id=run.run_id,
            )

    @staticmethod
    def _validate_turn(
        run: Run,
        task: Task,
        session: SessionHandle,
        request: TurnRequest,
        turn: TurnHandle,
    ) -> None:
        if type(turn) is not TurnHandle:
            raise ProviderAdapterError(
                "adapter returned an invalid turn handle",
                category=ProviderErrorCategory.PROTOCOL,
                retryable=False,
                provider_code="INVALID_TURN_HANDLE",
                correlation_id=request.request_id,
            )
        if (
            turn.session_id != session.session_id
            or turn.request_id != request.request_id
            or turn.run_id != run.run_id
            or turn.task_id != task.task_id
        ):
            raise ProviderAdapterError(
                "adapter turn identity does not match the submitted request",
                category=ProviderErrorCategory.PROTOCOL,
                retryable=False,
                provider_code="TURN_IDENTITY_MISMATCH",
                correlation_id=request.request_id,
            )

    @staticmethod
    def _validate_provider_order(
        provider_event: ProviderEvent,
        *,
        expected_sequence: int,
        seen_ids: set[str],
    ) -> None:
        if type(provider_event) is not ProviderEvent:
            raise LifecycleOrchestrationError("provider stream returned a non-ProviderEvent value")
        if provider_event.sequence != expected_sequence:
            raise LifecycleOrchestrationError("provider event sequence is not contiguous from one")
        if provider_event.event_id in seen_ids:
            raise LifecycleOrchestrationError("provider event ID was repeated")

    @staticmethod
    def _validate_iteration_inputs(
        run: Run,
        task: Task,
        session: SessionHandle,
    ) -> None:
        if type(run) is not Run:
            raise TypeError("run must be a Run")
        if type(task) is not Task:
            raise TypeError("task must be a Task")
        if type(session) is not SessionHandle:
            raise TypeError("session must be a SessionHandle")
        if run.lifecycle_state is not LifecycleState.READY:
            raise OrchestrationError("execute_iteration requires a READY Run")
        if task.status is not TaskStatus.READY:
            raise OrchestrationError("execute_iteration requires a READY Task")
        if run.goal_id != task.goal_id:
            raise OrchestrationError("iteration Run and Task must reference the same goal")
        if task.selected_workspace is None:
            raise OrchestrationError("iteration Task requires selected_workspace")
        if session.run_id != run.run_id or session.provider != run.provider:
            raise OrchestrationError("iteration session identity must match the Run")

    def _terminal_result(
        self,
        run: Run,
        task: Task,
        turn: TurnHandle,
        canonical_events: tuple[Event, ...],
        provider_event: ProviderEvent,
    ) -> IterationResult:
        outcome = provider_event.outcome
        if outcome is None:
            return self._protocol_failure_result(
                run,
                task,
                turn,
                canonical_events,
                "terminal provider event omitted its outcome",
            )
        evidence_refs = self._provider_refs(provider_event)
        if outcome is ProviderTurnOutcome.SUCCEEDED:
            validating, _ = self._lifecycle.transition(
                run,
                LifecycleState.VALIDATING,
                reason="Provider turn succeeded; independent validation is required",
                evidence_refs=evidence_refs,
            )
            validating_task = replace(
                task,
                status=TaskStatus.VALIDATING,
                last_failure=None,
                next_action=None,
            )
            return IterationResult(
                run=validating,
                task=validating_task,
                turn=turn,
                provider_events=canonical_events,
            )
        if outcome is ProviderTurnOutcome.FAILED:
            failure = provider_event.failure
            if failure is None:
                return self._protocol_failure_result(
                    run,
                    task,
                    turn,
                    canonical_events,
                    "failed terminal provider event omitted normalized failure data",
                )
            stopped, _ = self._lifecycle.stop(
                run,
                LifecycleState.FAILED,
                code=StopReasonCode.FAILED,
                summary=failure.message,
                evidence_refs=evidence_refs,
            )
            failed_task = replace(
                task,
                status=TaskStatus.FAILED,
                last_failure=failure.message,
                next_action=None,
            )
            return IterationResult(
                run=stopped,
                task=failed_task,
                turn=turn,
                provider_events=canonical_events,
            )
        if outcome is ProviderTurnOutcome.INTERRUPTED:
            stopped, _ = self._lifecycle.stop(
                run,
                LifecycleState.BLOCKED,
                code=StopReasonCode.BLOCKED,
                summary=provider_event.summary,
                evidence_refs=evidence_refs,
            )
            blocked_task = replace(
                task,
                status=TaskStatus.BLOCKED,
                next_action="Reconcile interrupted provider work before starting a new run",
            )
            return IterationResult(
                run=stopped,
                task=blocked_task,
                turn=turn,
                provider_events=canonical_events,
            )

        stopped, _ = self._lifecycle.stop(
            run,
            LifecycleState.CANCELLED,
            code=StopReasonCode.CANCELLED,
            summary=provider_event.summary,
            evidence_refs=evidence_refs,
        )
        cancelled_task = replace(
            task,
            status=TaskStatus.CANCELLED,
            last_failure=None,
            next_action=None,
        )
        return IterationResult(
            run=stopped,
            task=cancelled_task,
            turn=turn,
            provider_events=canonical_events,
        )

    def _protocol_failure_result(
        self,
        run: Run,
        task: Task,
        turn: TurnHandle | None,
        canonical_events: tuple[Event, ...],
        detail: str,
    ) -> IterationResult:
        summary = f"Provider protocol failure: {detail}"
        stopped, _ = self._lifecycle.stop(
            run,
            LifecycleState.FAILED,
            code=StopReasonCode.FAILED,
            summary=summary,
        )
        failed_task = replace(
            task,
            status=TaskStatus.FAILED,
            last_failure=summary,
            next_action=None,
        )
        return IterationResult(
            run=stopped,
            task=failed_task,
            turn=turn,
            provider_events=canonical_events,
        )

    def _stop_for_adapter_error(
        self,
        run: Run,
        error: ProviderAdapterError,
        *,
        task: Task | None = None,
    ) -> tuple[Run, Task | None]:
        is_protocol_failure = error.category in {
            ProviderErrorCategory.STATE,
            ProviderErrorCategory.PROTOCOL,
        }
        next_state = LifecycleState.FAILED if is_protocol_failure else LifecycleState.BLOCKED
        code = (
            StopReasonCode.FAILED
            if is_protocol_failure
            else (
                StopReasonCode.MISSING_DEPENDENCY
                if error.category is ProviderErrorCategory.COMPATIBILITY
                else StopReasonCode.BLOCKED
            )
        )
        summary = f"Provider adapter {error.category.value.lower()} error: {error}"
        stopped, _ = self._lifecycle.stop(
            run,
            next_state,
            code=code,
            summary=summary,
            evidence_refs=self._adapter_error_refs(error),
        )
        if task is None:
            return stopped, None
        if is_protocol_failure:
            stopped_task = replace(
                task,
                status=TaskStatus.FAILED,
                last_failure=summary,
                next_action=None,
            )
        else:
            stopped_task = replace(
                task,
                status=TaskStatus.BLOCKED,
                next_action="Resolve the provider adapter failure before starting a new run",
            )
        return stopped, stopped_task

    @staticmethod
    def _adapter_error_refs(error: ProviderAdapterError) -> tuple[str, ...]:
        refs: list[str] = []
        if error.provider_code is not None:
            refs.append(f"provider-code:{error.provider_code}")
        if error.correlation_id is not None:
            refs.append(f"correlation:{error.correlation_id}")
        return tuple(refs)

    @staticmethod
    def _provider_refs(provider_event: ProviderEvent) -> tuple[str, ...]:
        failure_refs: tuple[str, ...] = ()
        if provider_event.failure is not None:
            values: list[str] = []
            if provider_event.failure.provider_code is not None:
                values.append(f"provider-code:{provider_event.failure.provider_code}")
            if provider_event.failure.correlation_id is not None:
                values.append(f"correlation:{provider_event.failure.correlation_id}")
            failure_refs = tuple(values)
        return _unique_refs(
            (f"provider-event:{provider_event.event_id}",),
            provider_event.evidence_refs,
            failure_refs,
        )


__all__ = [
    "FinalizationEvidence",
    "FinalizationResult",
    "InitializationResult",
    "IterationResult",
    "OrchestrationError",
    "Orchestrator",
]
