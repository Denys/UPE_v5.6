"""Provider-neutral contracts for synchronous harness adapters.

The adapter boundary transports one provider session and turn at a time.  It
does not own canonical run sequencing, lifecycle transitions, persistence,
approval policy, retries, or provider-specific wire payloads.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from harness.state import (
    ActionClass,
    ApprovalStatus,
    LifecycleState,
    RedactionStatus,
    Run,
    Task,
    TaskStatus,
)

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class ProviderEventKind(StrEnum):
    """Normalized provider-local event categories."""

    TURN_STARTED = "TURN_STARTED"
    OUTPUT = "OUTPUT"
    ACTION = "ACTION"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    TURN_TERMINAL = "TURN_TERMINAL"


class ProviderTurnOutcome(StrEnum):
    """Provider-local terminal outcomes, distinct from Run lifecycle state."""

    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    INTERRUPTED = "INTERRUPTED"
    CANCELLED = "CANCELLED"


class ProviderErrorCategory(StrEnum):
    """Stable error categories exposed outside an adapter implementation."""

    STATE = "STATE"
    COMPATIBILITY = "COMPATIBILITY"
    PROTOCOL = "PROTOCOL"
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"


def _require_string(
    value: str,
    location: str,
    *,
    stable_id: bool = False,
    maximum: int = 2048,
) -> None:
    if type(value) is not str:
        raise TypeError(f"{location} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{location} must be non-empty and normalized")
    if len(value) > maximum:
        raise ValueError(f"{location} must be at most {maximum} characters")
    if stable_id and _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{location} must be a stable identifier")


def _require_refs(values: tuple[str, ...], location: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{location} must be a tuple")
    seen: set[str] = set()
    for index, value in enumerate(values):
        _require_string(value, f"{location}[{index}]")
        if value in seen:
            raise ValueError(f"{location} must not contain duplicates")
        seen.add(value)


def _normalize_datetime(value: datetime, location: str) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{location} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{location} must be timezone-aware")
    return value.astimezone(UTC)


def _validate_event_payload(
    *,
    kind: ProviderEventKind,
    approval: ApprovalRequest | None,
    outcome: ProviderTurnOutcome | None,
    failure: ProviderFailure | None,
    location: str,
) -> None:
    if type(kind) is not ProviderEventKind:
        raise TypeError(f"{location}.kind must be a ProviderEventKind")
    if approval is not None and type(approval) is not ApprovalRequest:
        raise TypeError(f"{location}.approval must be an ApprovalRequest or null")
    if outcome is not None and type(outcome) is not ProviderTurnOutcome:
        raise TypeError(f"{location}.outcome must be a ProviderTurnOutcome or null")
    if failure is not None and type(failure) is not ProviderFailure:
        raise TypeError(f"{location}.failure must be a ProviderFailure or null")

    if kind is ProviderEventKind.APPROVAL_REQUIRED:
        if approval is None or outcome is not None or failure is not None:
            raise ValueError(
                f"{location} APPROVAL_REQUIRED needs approval and forbids outcome/failure"
            )
        return
    if kind is ProviderEventKind.TURN_TERMINAL:
        if approval is not None or outcome is None:
            raise ValueError(f"{location} TURN_TERMINAL needs outcome and forbids approval")
        if outcome is ProviderTurnOutcome.FAILED and failure is None:
            raise ValueError(f"{location} FAILED terminal event requires failure")
        if outcome is not ProviderTurnOutcome.FAILED and failure is not None:
            raise ValueError(f"{location} non-failure terminal event forbids failure")
        return
    if approval is not None or outcome is not None or failure is not None:
        raise ValueError(
            f"{location} non-approval/non-terminal event forbids approval, outcome, and failure"
        )


class ProviderAdapterError(RuntimeError):
    """A normalized exceptional adapter failure.

    Expected provider turn failure is represented by a terminal
    :class:`ProviderEvent`; this exception is for adapter state, compatibility,
    protocol, and transport failures that prevent a valid event from being
    returned.
    """

    def __init__(
        self,
        message: str,
        *,
        category: ProviderErrorCategory,
        retryable: bool,
        provider_code: str | None = None,
        correlation_id: str | None = None,
    ) -> None:
        _require_string(message, "ProviderAdapterError.message")
        if type(category) is not ProviderErrorCategory:
            raise TypeError("ProviderAdapterError.category must be a ProviderErrorCategory")
        if type(retryable) is not bool:
            raise TypeError("ProviderAdapterError.retryable must be a boolean")
        if provider_code is not None:
            _require_string(provider_code, "ProviderAdapterError.provider_code", maximum=256)
        if correlation_id is not None:
            _require_string(
                correlation_id,
                "ProviderAdapterError.correlation_id",
                stable_id=True,
                maximum=256,
            )
        super().__init__(message)
        self.category = category
        self.retryable = retryable
        self.provider_code = provider_code
        self.correlation_id = correlation_id


@dataclass(frozen=True, slots=True, kw_only=True)
class AdapterIdentity:
    """Version and protocol evidence returned by compatibility preflight."""

    adapter: str
    provider: str
    implementation_version: str
    protocol_version: str
    schema_ref: str | None = None

    def __post_init__(self) -> None:
        _require_string(self.adapter, "AdapterIdentity.adapter", stable_id=True, maximum=256)
        _require_string(self.provider, "AdapterIdentity.provider", stable_id=True, maximum=256)
        _require_string(
            self.implementation_version,
            "AdapterIdentity.implementation_version",
            maximum=256,
        )
        _require_string(
            self.protocol_version,
            "AdapterIdentity.protocol_version",
            maximum=256,
        )
        if self.schema_ref is not None:
            _require_string(self.schema_ref, "AdapterIdentity.schema_ref")


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionHandle:
    """Provider-neutral identity for one run-scoped provider session."""

    session_id: str
    run_id: str
    provider: str

    def __post_init__(self) -> None:
        _require_string(self.session_id, "SessionHandle.session_id", stable_id=True)
        _require_string(self.run_id, "SessionHandle.run_id", stable_id=True)
        _require_string(self.provider, "SessionHandle.provider", stable_id=True, maximum=256)


@dataclass(frozen=True, slots=True, kw_only=True)
class TurnRequest:
    """Validated C-401 state and instructions supplied for one provider turn."""

    request_id: str
    run: Run
    task: Task
    instructions: str
    input_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_string(self.request_id, "TurnRequest.request_id", stable_id=True)
        if type(self.run) is not Run:
            raise TypeError("TurnRequest.run must be a Run")
        if type(self.task) is not Task:
            raise TypeError("TurnRequest.task must be a Task")
        _require_string(self.instructions, "TurnRequest.instructions", maximum=32_768)
        _require_refs(self.input_refs, "TurnRequest.input_refs")
        if self.run.goal_id != self.task.goal_id:
            raise ValueError("TurnRequest Run and Task must reference the same goal")
        if self.run.current_task_id != self.task.task_id:
            raise ValueError("TurnRequest Run.current_task_id must match Task.task_id")
        if self.run.lifecycle_state is not LifecycleState.EXECUTING:
            raise ValueError("TurnRequest Run must be in EXECUTING lifecycle state")
        if self.task.status is not TaskStatus.IN_PROGRESS:
            raise ValueError("TurnRequest Task must be IN_PROGRESS")
        if self.task.selected_workspace is None:
            raise ValueError("TurnRequest Task requires selected_workspace")


@dataclass(frozen=True, slots=True, kw_only=True)
class TurnHandle:
    """Stable provider-local turn identity correlated to C-401 state."""

    turn_id: str
    session_id: str
    request_id: str
    run_id: str
    task_id: str

    def __post_init__(self) -> None:
        for name in ("turn_id", "session_id", "request_id", "run_id", "task_id"):
            _require_string(getattr(self, name), f"TurnHandle.{name}", stable_id=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class ApprovalRequest:
    """A provider request for a host-owned approval decision."""

    approval_id: str
    action_class: ActionClass
    summary: str
    input_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_string(self.approval_id, "ApprovalRequest.approval_id", stable_id=True)
        if type(self.action_class) is not ActionClass:
            raise TypeError("ApprovalRequest.action_class must be an ActionClass")
        _require_string(self.summary, "ApprovalRequest.summary")
        _require_refs(self.input_refs, "ApprovalRequest.input_refs")


@dataclass(frozen=True, slots=True, kw_only=True)
class ApprovalResponse:
    """A granted or denied decision transported back to the provider."""

    approval_id: str
    decision: ApprovalStatus
    reason: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_string(self.approval_id, "ApprovalResponse.approval_id", stable_id=True)
        if type(self.decision) is not ApprovalStatus:
            raise TypeError("ApprovalResponse.decision must be an ApprovalStatus")
        if self.decision not in {ApprovalStatus.GRANTED, ApprovalStatus.DENIED}:
            raise ValueError("ApprovalResponse.decision must be GRANTED or DENIED")
        _require_string(self.reason, "ApprovalResponse.reason")
        _require_refs(self.evidence_refs, "ApprovalResponse.evidence_refs")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderFailure:
    """Normalized expected failure carried by a failed terminal event."""

    category: ProviderErrorCategory
    message: str
    retryable: bool
    provider_code: str | None = None
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if type(self.category) is not ProviderErrorCategory:
            raise TypeError("ProviderFailure.category must be a ProviderErrorCategory")
        if self.category is ProviderErrorCategory.STATE:
            raise ValueError("ProviderFailure cannot use adapter STATE category")
        _require_string(self.message, "ProviderFailure.message")
        if type(self.retryable) is not bool:
            raise TypeError("ProviderFailure.retryable must be a boolean")
        if self.provider_code is not None:
            _require_string(self.provider_code, "ProviderFailure.provider_code", maximum=256)
        if self.correlation_id is not None:
            _require_string(
                self.correlation_id,
                "ProviderFailure.correlation_id",
                stable_id=True,
                maximum=256,
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderEvent:
    """One normalized provider event with provider-local sequencing."""

    event_id: str
    sequence: int
    timestamp: datetime
    session_id: str
    turn_id: str
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
        _require_string(self.event_id, "ProviderEvent.event_id", stable_id=True)
        if type(self.sequence) is not int:
            raise TypeError("ProviderEvent.sequence must be an integer")
        if self.sequence < 1:
            raise ValueError("ProviderEvent.sequence must be at least one")
        object.__setattr__(
            self,
            "timestamp",
            _normalize_datetime(self.timestamp, "ProviderEvent.timestamp"),
        )
        _require_string(self.session_id, "ProviderEvent.session_id", stable_id=True)
        _require_string(self.turn_id, "ProviderEvent.turn_id", stable_id=True)
        _require_string(self.summary, "ProviderEvent.summary")
        _require_refs(self.input_refs, "ProviderEvent.input_refs")
        _require_refs(self.output_refs, "ProviderEvent.output_refs")
        _require_refs(self.evidence_refs, "ProviderEvent.evidence_refs")
        if self.correlation_id is not None:
            _require_string(
                self.correlation_id,
                "ProviderEvent.correlation_id",
                stable_id=True,
                maximum=256,
            )
        if type(self.redaction_status) is not RedactionStatus:
            raise TypeError("ProviderEvent.redaction_status must be a RedactionStatus")
        _validate_event_payload(
            kind=self.kind,
            approval=self.approval,
            outcome=self.outcome,
            failure=self.failure,
            location="ProviderEvent",
        )


@runtime_checkable
class ProviderAdapter(Protocol):
    """Synchronous single-agent provider boundary used by the v0 harness."""

    @property
    def identity(self) -> AdapterIdentity:
        """Return the adapter's declared version identity."""

    @property
    def started(self) -> bool:
        """Return whether the adapter transport is started."""

    def start(self) -> AdapterIdentity:
        """Start the adapter transport idempotently."""

    def stop(self) -> None:
        """Stop the adapter transport idempotently."""

    def preflight(self) -> AdapterIdentity:
        """Fail closed unless version/protocol compatibility is accepted."""

    def create_session(self, *, run: Run) -> SessionHandle:
        """Create a new provider session scoped to a run."""

    def resume_session(self, *, run: Run, session_id: str) -> SessionHandle:
        """Resume a provider session without changing Run lifecycle state."""

    def submit_turn(
        self,
        *,
        session: SessionHandle,
        request: TurnRequest,
    ) -> TurnHandle:
        """Submit one validated turn request."""

    def stream_events(self, *, turn: TurnHandle) -> Iterator[ProviderEvent]:
        """Return the next exactly-once provider event segment."""

    def respond_to_approval(
        self,
        *,
        turn: TurnHandle,
        response: ApprovalResponse,
    ) -> None:
        """Transport one approval decision for the active turn."""

    def interrupt(self, *, turn: TurnHandle, reason: str) -> None:
        """Request deterministic interruption of one active turn."""

    def cancel(self, *, session: SessionHandle, reason: str) -> None:
        """Cancel every active turn in one provider session."""


__all__ = [
    "AdapterIdentity",
    "ApprovalRequest",
    "ApprovalResponse",
    "ProviderAdapter",
    "ProviderAdapterError",
    "ProviderErrorCategory",
    "ProviderEvent",
    "ProviderEventKind",
    "ProviderFailure",
    "ProviderTurnOutcome",
    "SessionHandle",
    "TurnHandle",
    "TurnRequest",
]
