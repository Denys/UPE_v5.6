"""Deterministic in-memory provider adapter for lifecycle and orchestration tests."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import NoReturn, Self

from harness.state import ActionClass, ApprovalStatus, RedactionStatus, Run

from .base import (
    AdapterIdentity,
    ApprovalRequest,
    ApprovalResponse,
    ProviderAdapterError,
    ProviderErrorCategory,
    ProviderEvent,
    ProviderEventKind,
    ProviderFailure,
    ProviderTurnOutcome,
    SessionHandle,
    TurnHandle,
    TurnRequest,
    _normalize_datetime,
    _require_refs,
    _require_string,
    _validate_event_payload,
)

DEFAULT_FAKE_BASE_TIME = datetime(2000, 1, 1, tzinfo=UTC)
DEFAULT_FAKE_IDENTITY = AdapterIdentity(
    adapter="fake",
    provider="fake",
    implementation_version="1.0.0",
    protocol_version="fake-v1",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class FakeEventSpec:
    """Provider event payload before deterministic identity and time materialization."""

    kind: ProviderEventKind
    summary: str
    input_refs: tuple[str, ...] = ()
    output_refs: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    correlation_id: str | None = None
    redaction_status: RedactionStatus = RedactionStatus.NOT_REQUIRED
    approval: ApprovalRequest | None = None
    outcome: ProviderTurnOutcome | None = None
    failure: ProviderFailure | None = None

    def __post_init__(self) -> None:
        _require_string(self.summary, "FakeEventSpec.summary")
        _require_refs(self.input_refs, "FakeEventSpec.input_refs")
        _require_refs(self.output_refs, "FakeEventSpec.output_refs")
        _require_refs(self.evidence_refs, "FakeEventSpec.evidence_refs")
        if self.correlation_id is not None:
            _require_string(
                self.correlation_id,
                "FakeEventSpec.correlation_id",
                stable_id=True,
                maximum=256,
            )
        if type(self.redaction_status) is not RedactionStatus:
            raise TypeError("FakeEventSpec.redaction_status must be a RedactionStatus")
        _validate_event_payload(
            kind=self.kind,
            approval=self.approval,
            outcome=self.outcome,
            failure=self.failure,
            location="FakeEventSpec",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class FakeTurnScript:
    """A finite, ordered fake turn ending in exactly one terminal event."""

    name: str
    events: tuple[FakeEventSpec, ...]

    def __post_init__(self) -> None:
        _require_string(self.name, "FakeTurnScript.name", stable_id=True, maximum=256)
        if type(self.events) is not tuple:
            raise TypeError("FakeTurnScript.events must be a tuple")
        if not self.events:
            raise ValueError("FakeTurnScript.events must not be empty")
        if any(type(event) is not FakeEventSpec for event in self.events):
            raise TypeError("FakeTurnScript.events must contain only FakeEventSpec values")
        if self.events[0].kind is not ProviderEventKind.TURN_STARTED:
            raise ValueError("FakeTurnScript must begin with TURN_STARTED")
        if any(event.kind is ProviderEventKind.TURN_STARTED for event in self.events[1:]):
            raise ValueError("FakeTurnScript may contain TURN_STARTED only as its first event")
        terminal_indexes = [
            index
            for index, event in enumerate(self.events)
            if event.kind is ProviderEventKind.TURN_TERMINAL
        ]
        if terminal_indexes != [len(self.events) - 1]:
            raise ValueError("FakeTurnScript must end with exactly one TURN_TERMINAL event")
        approval_ids = [
            event.approval.approval_id for event in self.events if event.approval is not None
        ]
        if len(approval_ids) != len(set(approval_ids)):
            raise ValueError("FakeTurnScript approval IDs must be unique")

    @classmethod
    def success(
        cls,
        *,
        name: str = "success",
        output_refs: tuple[str, ...] = (),
    ) -> Self:
        """Return a start/output/success script."""

        return cls(
            name=name,
            events=(
                FakeEventSpec(
                    kind=ProviderEventKind.TURN_STARTED,
                    summary="Fake turn started",
                ),
                FakeEventSpec(
                    kind=ProviderEventKind.OUTPUT,
                    summary="Fake output produced",
                    output_refs=output_refs,
                ),
                FakeEventSpec(
                    kind=ProviderEventKind.TURN_TERMINAL,
                    summary="Fake turn succeeded",
                    output_refs=output_refs,
                    outcome=ProviderTurnOutcome.SUCCEEDED,
                ),
            ),
        )

    @classmethod
    def failure(
        cls,
        *,
        name: str = "failure",
        category: ProviderErrorCategory = ProviderErrorCategory.PERMANENT,
        message: str = "Scripted provider failure",
        retryable: bool = False,
        provider_code: str | None = "FAKE_FAILURE",
    ) -> Self:
        """Return a start/failed-terminal script with normalized failure data."""

        failure = ProviderFailure(
            category=category,
            message=message,
            retryable=retryable,
            provider_code=provider_code,
        )
        return cls(
            name=name,
            events=(
                FakeEventSpec(
                    kind=ProviderEventKind.TURN_STARTED,
                    summary="Fake turn started",
                ),
                FakeEventSpec(
                    kind=ProviderEventKind.TURN_TERMINAL,
                    summary=message,
                    outcome=ProviderTurnOutcome.FAILED,
                    failure=failure,
                ),
            ),
        )

    @classmethod
    def interrupted(
        cls,
        *,
        name: str = "interrupted",
        reason: str = "Scripted provider interruption",
    ) -> Self:
        """Return a start/interrupted-terminal script."""

        return cls(
            name=name,
            events=(
                FakeEventSpec(
                    kind=ProviderEventKind.TURN_STARTED,
                    summary="Fake turn started",
                ),
                FakeEventSpec(
                    kind=ProviderEventKind.TURN_TERMINAL,
                    summary=reason,
                    outcome=ProviderTurnOutcome.INTERRUPTED,
                ),
            ),
        )

    @classmethod
    def approval_then_success(
        cls,
        *,
        name: str = "approval_then_success",
        approval_id: str = "fake.approval.0001",
        action_class: ActionClass = ActionClass.WRITE,
        approval_summary: str = "Approve scripted write",
        output_refs: tuple[str, ...] = (),
    ) -> Self:
        """Return a script that pauses once for approval before success."""

        approval = ApprovalRequest(
            approval_id=approval_id,
            action_class=action_class,
            summary=approval_summary,
        )
        return cls(
            name=name,
            events=(
                FakeEventSpec(
                    kind=ProviderEventKind.TURN_STARTED,
                    summary="Fake turn started",
                ),
                FakeEventSpec(
                    kind=ProviderEventKind.APPROVAL_REQUIRED,
                    summary=approval_summary,
                    approval=approval,
                ),
                FakeEventSpec(
                    kind=ProviderEventKind.OUTPUT,
                    summary="Fake approved output produced",
                    output_refs=output_refs,
                ),
                FakeEventSpec(
                    kind=ProviderEventKind.TURN_TERMINAL,
                    summary="Fake turn succeeded after approval",
                    output_refs=output_refs,
                    outcome=ProviderTurnOutcome.SUCCEEDED,
                ),
            ),
        )


class FakeOperationKind(StrEnum):
    """Inspectable operations performed against the in-memory fake."""

    START = "START"
    STOP = "STOP"
    PREFLIGHT = "PREFLIGHT"
    CREATE_SESSION = "CREATE_SESSION"
    RESUME_SESSION = "RESUME_SESSION"
    SUBMIT_TURN = "SUBMIT_TURN"
    STREAM_EVENTS = "STREAM_EVENTS"
    APPROVAL_RESPONSE = "APPROVAL_RESPONSE"
    INTERRUPT = "INTERRUPT"
    CANCEL = "CANCEL"


@dataclass(frozen=True, slots=True, kw_only=True)
class FakeOperation:
    """One immutable fake-adapter call trace entry."""

    sequence: int
    kind: FakeOperationKind
    summary: str
    session_id: str | None = None
    turn_id: str | None = None
    request_id: str | None = None
    approval_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.sequence) is not int:
            raise TypeError("FakeOperation.sequence must be an integer")
        if self.sequence < 1:
            raise ValueError("FakeOperation.sequence must be at least one")
        if type(self.kind) is not FakeOperationKind:
            raise TypeError("FakeOperation.kind must be a FakeOperationKind")
        _require_string(self.summary, "FakeOperation.summary")
        for name in ("session_id", "turn_id", "request_id", "approval_id"):
            value = getattr(self, name)
            if value is not None:
                _require_string(value, f"FakeOperation.{name}", stable_id=True)


@dataclass(slots=True)
class _TurnState:
    handle: TurnHandle
    script: FakeTurnScript
    cursor: int = 0
    next_sequence: int = 1
    pending_approval: ApprovalRequest | None = None
    resolved_approval_ids: set[str] = field(default_factory=set)
    terminal: bool = False
    forced_outcome: ProviderTurnOutcome | None = None
    forced_summary: str | None = None


class FakeAdapter:
    """Stateful deterministic implementation of the provider adapter protocol."""

    def __init__(
        self,
        scripts: tuple[FakeTurnScript, ...],
        *,
        base_time: datetime = DEFAULT_FAKE_BASE_TIME,
        identity: AdapterIdentity = DEFAULT_FAKE_IDENTITY,
        compatible: bool = True,
    ) -> None:
        if type(scripts) is not tuple:
            raise TypeError("FakeAdapter.scripts must be a tuple")
        if any(type(script) is not FakeTurnScript for script in scripts):
            raise TypeError("FakeAdapter.scripts must contain only FakeTurnScript values")
        if type(identity) is not AdapterIdentity:
            raise TypeError("FakeAdapter.identity must be an AdapterIdentity")
        if type(compatible) is not bool:
            raise TypeError("FakeAdapter.compatible must be a boolean")
        self._scripts: deque[FakeTurnScript] = deque(scripts)
        self._base_time = _normalize_datetime(base_time, "FakeAdapter.base_time")
        self._identity = identity
        self._compatible = compatible
        self._started = False
        self._session_counter = 0
        self._turn_counter = 0
        self._event_counter = 0
        self._operation_counter = 0
        self._sessions: dict[str, SessionHandle] = {}
        self._turns: dict[str, _TurnState] = {}
        self._request_ids: set[str] = set()
        self._operations: list[FakeOperation] = []

    @property
    def identity(self) -> AdapterIdentity:
        return self._identity

    @property
    def started(self) -> bool:
        return self._started

    @property
    def operations(self) -> tuple[FakeOperation, ...]:
        """Return an immutable snapshot of adapter calls."""

        return tuple(self._operations)

    def start(self) -> AdapterIdentity:
        self._started = True
        self._record(FakeOperationKind.START, "Start fake adapter")
        return self._identity

    def stop(self) -> None:
        self._started = False
        self._record(FakeOperationKind.STOP, "Stop fake adapter")

    def preflight(self) -> AdapterIdentity:
        self._require_started()
        self._record(FakeOperationKind.PREFLIGHT, "Check fake adapter compatibility")
        if not self._compatible:
            self._raise_error(
                "fake adapter compatibility preflight failed",
                category=ProviderErrorCategory.COMPATIBILITY,
                code="FAKE_INCOMPATIBLE",
            )
        return self._identity

    def create_session(self, *, run: Run) -> SessionHandle:
        self._validate_run(run)
        self.preflight()
        session_id = self._next_session_id()
        session = SessionHandle(
            session_id=session_id,
            run_id=run.run_id,
            provider=self._identity.provider,
        )
        self._sessions[session_id] = session
        self._record(
            FakeOperationKind.CREATE_SESSION,
            "Create fake provider session",
            session_id=session_id,
        )
        return session

    def resume_session(self, *, run: Run, session_id: str) -> SessionHandle:
        self._validate_run(run)
        _require_string(session_id, "FakeAdapter.resume_session.session_id", stable_id=True)
        self.preflight()
        expected = SessionHandle(
            session_id=session_id,
            run_id=run.run_id,
            provider=self._identity.provider,
        )
        existing = self._sessions.get(session_id)
        if existing is not None and existing != expected:
            self._raise_error(
                "session identity does not match the requested run",
                code="SESSION_IDENTITY_MISMATCH",
                correlation_id=run.run_id,
            )
        self._sessions[session_id] = expected
        self._record(
            FakeOperationKind.RESUME_SESSION,
            "Resume fake provider session",
            session_id=session_id,
        )
        return expected

    def submit_turn(
        self,
        *,
        session: SessionHandle,
        request: TurnRequest,
    ) -> TurnHandle:
        self._require_started()
        stored_session = self._get_session(session)
        if type(request) is not TurnRequest:
            raise TypeError("FakeAdapter.submit_turn.request must be a TurnRequest")
        if stored_session.run_id != request.run.run_id:
            self._raise_error(
                "turn request run does not match the session run",
                code="TURN_RUN_MISMATCH",
                correlation_id=request.request_id,
            )
        if stored_session.provider != request.run.provider:
            self._raise_error(
                "turn request provider does not match the session provider",
                code="TURN_PROVIDER_MISMATCH",
                correlation_id=request.request_id,
            )
        if request.request_id in self._request_ids:
            self._raise_error(
                "turn request ID has already been submitted",
                code="DUPLICATE_TURN_REQUEST",
                correlation_id=request.request_id,
            )
        if not self._scripts:
            self._raise_error(
                "no fake turn script remains",
                category=ProviderErrorCategory.PERMANENT,
                code="FAKE_SCRIPT_EXHAUSTED",
                correlation_id=request.request_id,
            )
        self._turn_counter += 1
        turn = TurnHandle(
            turn_id=f"fake.turn.{self._turn_counter:04d}",
            session_id=stored_session.session_id,
            request_id=request.request_id,
            run_id=request.run.run_id,
            task_id=request.task.task_id,
        )
        self._request_ids.add(request.request_id)
        self._turns[turn.turn_id] = _TurnState(
            handle=turn,
            script=self._scripts.popleft(),
        )
        self._record(
            FakeOperationKind.SUBMIT_TURN,
            "Submit fake provider turn",
            session_id=turn.session_id,
            turn_id=turn.turn_id,
            request_id=turn.request_id,
        )
        return turn

    def stream_events(self, *, turn: TurnHandle) -> Iterator[ProviderEvent]:
        self._require_started()
        state = self._get_turn(turn)
        self._record(
            FakeOperationKind.STREAM_EVENTS,
            "Read next fake event segment",
            session_id=turn.session_id,
            turn_id=turn.turn_id,
            request_id=turn.request_id,
        )
        if state.terminal:
            return iter(())
        if state.pending_approval is not None:
            self._raise_error(
                "approval response is required before event streaming can continue",
                code="APPROVAL_PENDING",
                correlation_id=state.pending_approval.approval_id,
            )
        return self._stream_turn(state)

    def respond_to_approval(
        self,
        *,
        turn: TurnHandle,
        response: ApprovalResponse,
    ) -> None:
        self._require_started()
        state = self._get_turn(turn)
        if type(response) is not ApprovalResponse:
            raise TypeError("FakeAdapter.response must be an ApprovalResponse")
        if response.approval_id in state.resolved_approval_ids:
            self._raise_error(
                "approval response has already been recorded",
                code="DUPLICATE_APPROVAL_RESPONSE",
                correlation_id=response.approval_id,
            )
        pending = state.pending_approval
        if pending is None:
            self._raise_error(
                "turn has no pending approval request",
                code="NO_PENDING_APPROVAL",
                correlation_id=response.approval_id,
            )
        if pending.approval_id != response.approval_id:
            self._raise_error(
                "approval response does not match the pending request",
                code="APPROVAL_ID_MISMATCH",
                correlation_id=response.approval_id,
            )
        state.resolved_approval_ids.add(response.approval_id)
        state.pending_approval = None
        if response.decision is ApprovalStatus.DENIED:
            state.forced_outcome = ProviderTurnOutcome.INTERRUPTED
            state.forced_summary = f"Approval denied: {response.reason}"
        self._record(
            FakeOperationKind.APPROVAL_RESPONSE,
            f"Record {response.decision.value} fake approval response",
            session_id=turn.session_id,
            turn_id=turn.turn_id,
            request_id=turn.request_id,
            approval_id=response.approval_id,
        )

    def interrupt(self, *, turn: TurnHandle, reason: str) -> None:
        self._require_started()
        _require_string(reason, "FakeAdapter.interrupt.reason")
        state = self._get_turn(turn)
        self._force_terminal(
            state,
            outcome=ProviderTurnOutcome.INTERRUPTED,
            summary=f"Turn interrupted: {reason}",
            duplicate_code="INTERRUPT_ALREADY_PENDING",
        )
        self._record(
            FakeOperationKind.INTERRUPT,
            "Interrupt fake provider turn",
            session_id=turn.session_id,
            turn_id=turn.turn_id,
            request_id=turn.request_id,
        )

    def cancel(self, *, session: SessionHandle, reason: str) -> None:
        self._require_started()
        _require_string(reason, "FakeAdapter.cancel.reason")
        stored_session = self._get_session(session)
        for state in self._turns.values():
            if state.handle.session_id != stored_session.session_id or state.terminal:
                continue
            if state.pending_approval is not None:
                state.resolved_approval_ids.add(state.pending_approval.approval_id)
                state.pending_approval = None
            state.forced_outcome = ProviderTurnOutcome.CANCELLED
            state.forced_summary = f"Session cancelled: {reason}"
        self._record(
            FakeOperationKind.CANCEL,
            "Cancel fake provider session",
            session_id=stored_session.session_id,
        )

    def _stream_turn(self, state: _TurnState) -> Iterator[ProviderEvent]:
        while not state.terminal:
            if state.forced_outcome is not None:
                summary = state.forced_summary
                if summary is None:
                    self._raise_error(
                        "forced fake terminal outcome lacks a summary",
                        category=ProviderErrorCategory.PROTOCOL,
                        code="INVALID_FORCED_TERMINAL",
                        correlation_id=state.handle.request_id,
                    )
                spec = FakeEventSpec(
                    kind=ProviderEventKind.TURN_TERMINAL,
                    summary=summary,
                    outcome=state.forced_outcome,
                )
                state.cursor = len(state.script.events)
                state.terminal = True
                state.forced_outcome = None
                state.forced_summary = None
                yield self._materialize(state, spec)
                return

            if state.cursor >= len(state.script.events):
                self._raise_error(
                    "fake script ended without a terminal event",
                    category=ProviderErrorCategory.PROTOCOL,
                    code="FAKE_SCRIPT_INCOMPLETE",
                    correlation_id=state.handle.request_id,
                )
            spec = state.script.events[state.cursor]
            state.cursor += 1
            if spec.approval is not None:
                state.pending_approval = spec.approval
            if spec.kind is ProviderEventKind.TURN_TERMINAL:
                state.terminal = True
            event = self._materialize(state, spec)
            yield event
            if spec.approval is not None or state.terminal:
                return

    def _materialize(self, state: _TurnState, spec: FakeEventSpec) -> ProviderEvent:
        self._event_counter += 1
        event = ProviderEvent(
            event_id=f"fake.event.{self._event_counter:04d}",
            sequence=state.next_sequence,
            timestamp=self._base_time + timedelta(microseconds=self._event_counter - 1),
            session_id=state.handle.session_id,
            turn_id=state.handle.turn_id,
            kind=spec.kind,
            summary=spec.summary,
            input_refs=spec.input_refs,
            output_refs=spec.output_refs,
            evidence_refs=spec.evidence_refs,
            correlation_id=(
                spec.correlation_id if spec.correlation_id is not None else state.handle.request_id
            ),
            redaction_status=spec.redaction_status,
            approval=spec.approval,
            outcome=spec.outcome,
            failure=spec.failure,
        )
        state.next_sequence += 1
        return event

    def _force_terminal(
        self,
        state: _TurnState,
        *,
        outcome: ProviderTurnOutcome,
        summary: str,
        duplicate_code: str,
    ) -> None:
        if state.terminal:
            self._raise_error(
                "turn is already terminal",
                code="TURN_ALREADY_TERMINAL",
                correlation_id=state.handle.request_id,
            )
        if state.forced_outcome is not None:
            self._raise_error(
                "turn already has a pending terminal request",
                code=duplicate_code,
                correlation_id=state.handle.request_id,
            )
        if state.pending_approval is not None:
            state.resolved_approval_ids.add(state.pending_approval.approval_id)
            state.pending_approval = None
        state.forced_outcome = outcome
        state.forced_summary = summary

    def _validate_run(self, run: Run) -> None:
        if type(run) is not Run:
            raise TypeError("FakeAdapter run must be a Run")
        if run.provider != self._identity.provider:
            self._raise_error(
                "run provider does not match fake adapter identity",
                code="RUN_PROVIDER_MISMATCH",
                correlation_id=run.run_id,
            )

    def _get_session(self, session: SessionHandle) -> SessionHandle:
        if type(session) is not SessionHandle:
            raise TypeError("session must be a SessionHandle")
        stored = self._sessions.get(session.session_id)
        if stored is None:
            self._raise_error(
                "unknown provider session",
                code="UNKNOWN_SESSION",
                correlation_id=session.session_id,
            )
        if stored != session:
            self._raise_error(
                "provider session handle does not match recorded identity",
                code="SESSION_HANDLE_MISMATCH",
                correlation_id=session.session_id,
            )
        return stored

    def _get_turn(self, turn: TurnHandle) -> _TurnState:
        if type(turn) is not TurnHandle:
            raise TypeError("turn must be a TurnHandle")
        state = self._turns.get(turn.turn_id)
        if state is None:
            self._raise_error(
                "unknown provider turn",
                code="UNKNOWN_TURN",
                correlation_id=turn.turn_id,
            )
        if state.handle != turn:
            self._raise_error(
                "provider turn handle does not match recorded identity",
                code="TURN_HANDLE_MISMATCH",
                correlation_id=turn.turn_id,
            )
        return state

    def _next_session_id(self) -> str:
        while True:
            self._session_counter += 1
            candidate = f"fake.session.{self._session_counter:04d}"
            if candidate not in self._sessions:
                return candidate

    def _require_started(self) -> None:
        if not self._started:
            self._raise_error(
                "fake adapter is not started",
                code="ADAPTER_NOT_STARTED",
            )

    def _record(
        self,
        kind: FakeOperationKind,
        summary: str,
        *,
        session_id: str | None = None,
        turn_id: str | None = None,
        request_id: str | None = None,
        approval_id: str | None = None,
    ) -> None:
        self._operation_counter += 1
        self._operations.append(
            FakeOperation(
                sequence=self._operation_counter,
                kind=kind,
                summary=summary,
                session_id=session_id,
                turn_id=turn_id,
                request_id=request_id,
                approval_id=approval_id,
            )
        )

    @staticmethod
    def _raise_error(
        message: str,
        *,
        category: ProviderErrorCategory = ProviderErrorCategory.STATE,
        code: str,
        correlation_id: str | None = None,
        retryable: bool = False,
    ) -> NoReturn:
        raise ProviderAdapterError(
            message,
            category=category,
            retryable=retryable,
            provider_code=code,
            correlation_id=correlation_id,
        )


__all__ = [
    "DEFAULT_FAKE_BASE_TIME",
    "DEFAULT_FAKE_IDENTITY",
    "FakeAdapter",
    "FakeEventSpec",
    "FakeOperation",
    "FakeOperationKind",
    "FakeTurnScript",
]
