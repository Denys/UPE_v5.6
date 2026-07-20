"""C-403 lifecycle sequencing and canonical provider-event conversion.

This module owns transition ordering, not durable storage.  A
``LifecycleCommitter`` implementation must atomically record the supplied
``Run``/``Event`` pair before returning; C-406 will provide the SQLite/outbox
implementation of that port.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import Protocol, runtime_checkable

from harness.adapters.base import ProviderEvent, ProviderEventKind, TurnHandle
from harness.state import (
    STOPPED_STATES,
    ApprovalStatus,
    CompletionVerdict,
    Event,
    EventType,
    LifecycleState,
    Run,
    StopReason,
    StopReasonCode,
    TransitionError,
    transition_run,
)

LifecycleClock = Callable[[], datetime]
_PRESERVE_CHECKPOINT = object()


class LifecycleOrchestrationError(RuntimeError):
    """A C-403 lifecycle operation cannot satisfy its ordering contract."""


@runtime_checkable
class LifecycleCommitter(Protocol):
    """Atomic recording boundary for one complete Run/Event pair."""

    def commit(self, *, run: Run, event: Event) -> None:
        """Record the pair atomically and return only after commit succeeds."""


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


class LifecycleCoordinator:
    """Create, validate, and commit ordered lifecycle and provider events."""

    def __init__(self, *, committer: LifecycleCommitter, clock: LifecycleClock) -> None:
        if not isinstance(committer, LifecycleCommitter):
            raise TypeError("committer must implement LifecycleCommitter")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._committer = committer
        self._clock = clock

    def transition(
        self,
        run: Run,
        next_state: LifecycleState,
        *,
        reason: str,
        evidence_refs: tuple[str, ...] = (),
        stop_reason: StopReason | None = None,
        approval_state: ApprovalStatus | None = None,
        checkpoint_ref: str | None | object = _PRESERVE_CHECKPOINT,
        completion_verdict: CompletionVerdict | None = None,
        completion_evidence_refs: tuple[str, ...] | None = None,
    ) -> tuple[Run, Event]:
        """Create and commit one C-401 transition before returning its Run."""

        if type(run) is not Run:
            raise TypeError("run must be a Run")
        if type(next_state) is not LifecycleState:
            raise TypeError("next_state must be a LifecycleState")
        if type(reason) is not str or not reason or reason != reason.strip():
            raise ValueError("reason must be non-empty and normalized")
        _require_refs(evidence_refs, "evidence_refs")
        effective_checkpoint = (
            run.checkpoint_ref if checkpoint_ref is _PRESERVE_CHECKPOINT else checkpoint_ref
        )
        if effective_checkpoint is not None and type(effective_checkpoint) is not str:
            raise TypeError("checkpoint_ref must be a string or null")
        timestamp = self._clock()
        transition_id = (
            f"{run.run_id}.transition.{run.event_seq + 1:06d}.{next_state.value.lower()}"
        )
        try:
            updated_run, event = transition_run(
                run,
                next_state,
                transition_id=transition_id,
                timestamp=timestamp,
                reason=reason,
                stop_reason=stop_reason,
                completion_verdict=completion_verdict,
                completion_evidence_refs=completion_evidence_refs,
                checkpoint_ref=effective_checkpoint,
                approval_state=approval_state,
                evidence_refs=evidence_refs,
                correlation_id=transition_id,
            )
        except TransitionError as exc:
            raise LifecycleOrchestrationError(str(exc)) from exc
        self._committer.commit(run=updated_run, event=event)
        return updated_run, event

    def record_provider_event(
        self,
        run: Run,
        provider_event: ProviderEvent,
        *,
        turn: TurnHandle,
    ) -> tuple[Run, Event]:
        """Convert and commit one provider event without changing lifecycle state."""

        if type(run) is not Run:
            raise TypeError("run must be a Run")
        if type(provider_event) is not ProviderEvent:
            raise TypeError("provider_event must be a ProviderEvent")
        if type(turn) is not TurnHandle:
            raise TypeError("turn must be a TurnHandle")
        if run.lifecycle_state is not LifecycleState.EXECUTING:
            raise LifecycleOrchestrationError(
                "provider events may be recorded only while the Run is EXECUTING"
            )
        if turn.run_id != run.run_id or turn.task_id != run.current_task_id:
            raise LifecycleOrchestrationError("provider turn identity does not match Run state")
        if provider_event.session_id != turn.session_id or provider_event.turn_id != turn.turn_id:
            raise LifecycleOrchestrationError(
                "provider event session/turn identity does not match the submitted turn"
            )
        if provider_event.timestamp < run.updated_at:
            raise LifecycleOrchestrationError(
                "provider event timestamp must not precede Run.updated_at"
            )

        updated_run = replace(
            run,
            updated_at=provider_event.timestamp,
            event_seq=run.event_seq + 1,
        )
        event_type = (
            EventType.APPROVAL
            if provider_event.kind is ProviderEventKind.APPROVAL_REQUIRED
            else EventType.ACTION
        )
        provider_ref = f"provider-event:{provider_event.event_id}"
        provider_sequence_ref = f"provider-sequence:{provider_event.sequence}"
        canonical_event = Event(
            event_seq=updated_run.event_seq,
            timestamp=provider_event.timestamp,
            run_id=updated_run.run_id,
            task_id=updated_run.current_task_id,
            event_type=event_type,
            source=f"provider.{updated_run.provider}",
            action_summary=provider_event.summary,
            input_refs=_unique_refs(
                (provider_ref, provider_sequence_ref),
                provider_event.input_refs,
            ),
            output_refs=provider_event.output_refs,
            evidence_refs=provider_event.evidence_refs,
            result=(
                provider_event.outcome.value
                if provider_event.outcome is not None
                else provider_event.kind.value
            ),
            error_category=(
                provider_event.failure.category.value
                if provider_event.failure is not None
                else None
            ),
            redaction_status=provider_event.redaction_status,
            transition_id=None,
            prior_state=None,
            next_state=None,
            reason=None,
            correlation_id=(
                provider_event.correlation_id
                if provider_event.correlation_id is not None
                else provider_event.event_id
            ),
        )
        self._committer.commit(run=updated_run, event=canonical_event)
        return updated_run, canonical_event

    def stop(
        self,
        run: Run,
        next_state: LifecycleState,
        *,
        code: StopReasonCode,
        summary: str,
        evidence_refs: tuple[str, ...] = (),
        approval_state: ApprovalStatus | None = None,
    ) -> tuple[Run, Event]:
        """Commit one explicit reasoned stop other than successful completion."""

        if next_state not in STOPPED_STATES or next_state is LifecycleState.COMPLETED:
            raise LifecycleOrchestrationError(
                "stop requires a non-COMPLETED stopped lifecycle state"
            )
        _require_refs(evidence_refs, "evidence_refs")
        stop_reason = StopReason(
            code=code,
            summary=summary,
            evidence_refs=evidence_refs,
        )
        return self.transition(
            run,
            next_state,
            reason=summary,
            evidence_refs=evidence_refs,
            stop_reason=stop_reason,
            approval_state=approval_state,
        )

    def complete(
        self,
        run: Run,
        *,
        checkpoint_ref: str,
        completion_evidence_refs: tuple[str, ...],
        reason: str = "All mandatory criteria have passing evidence",
    ) -> tuple[Run, Event]:
        """Commit COMPLETED only from explicit checkpointed passing evidence."""

        if (
            type(checkpoint_ref) is not str
            or not checkpoint_ref
            or checkpoint_ref != checkpoint_ref.strip()
        ):
            raise ValueError("checkpoint_ref must be non-empty and normalized")
        _require_refs(
            completion_evidence_refs,
            "completion_evidence_refs",
            required=True,
        )
        stop_reason = StopReason(
            code=StopReasonCode.COMPLETED,
            summary=reason,
            evidence_refs=completion_evidence_refs,
        )
        return self.transition(
            run,
            LifecycleState.COMPLETED,
            reason=reason,
            evidence_refs=completion_evidence_refs,
            stop_reason=stop_reason,
            checkpoint_ref=checkpoint_ref,
            completion_verdict=CompletionVerdict.PASS,
            completion_evidence_refs=completion_evidence_refs,
        )


__all__ = [
    "LifecycleClock",
    "LifecycleCommitter",
    "LifecycleCoordinator",
    "LifecycleOrchestrationError",
]
