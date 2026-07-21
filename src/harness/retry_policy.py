"""Pure retry, backoff, no-progress, and action-reconciliation policy."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum

from harness.budgets import BudgetDecisionCode, current_budget_decision
from harness.config import RetrySettings
from harness.state import (
    BudgetState,
    CompletionVerdict,
    StateValidationError,
    StopReasonCode,
)


class FailureClass(StrEnum):
    TRANSIENT = "TRANSIENT"
    DETERMINISTIC_VALIDATION = "DETERMINISTIC_VALIDATION"
    PERMANENT = "PERMANENT"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    POLICY = "POLICY"


class RetryDecisionCode(StrEnum):
    RETRY = "RETRY"
    STOP = "STOP"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"


class ExternalActionOutcome(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    STARTED = "STARTED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True, kw_only=True)
class FailureSignal:
    category: FailureClass
    signature: str

    def __post_init__(self) -> None:
        _require_enum(self.category, FailureClass, "FailureSignal.category")
        _require_text(self.signature, "FailureSignal.signature")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProgressSignal:
    failure: FailureSignal | None
    validator_verdict: CompletionVerdict | None = None
    artifact_hash: str | None = None
    diff_hash: str | None = None
    satisfied_criteria: tuple[str, ...] = ()
    remaining_delta: str | None = None
    dependency_state: str | None = None
    approved_action_state: str | None = None
    checkpoint_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.failure is not None and type(self.failure) is not FailureSignal:
            raise TypeError("ProgressSignal.failure must be FailureSignal or None")
        if self.validator_verdict is not None:
            _require_enum(
                self.validator_verdict,
                CompletionVerdict,
                "ProgressSignal.validator_verdict",
            )
        for name in (
            "artifact_hash",
            "diff_hash",
            "remaining_delta",
            "dependency_state",
            "approved_action_state",
            "checkpoint_ref",
        ):
            _require_optional_text(getattr(self, name), f"ProgressSignal.{name}")
        _require_text_tuple(self.satisfied_criteria, "ProgressSignal.satisfied_criteria")
        _require_text_tuple(self.evidence_refs, "ProgressSignal.evidence_refs")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProgressState:
    last_signal: ProgressSignal | None = None
    consecutive_identical_failures: int = 0
    consecutive_no_progress: int = 0
    last_stable_checkpoint_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.last_signal is not None and type(self.last_signal) is not ProgressSignal:
            raise TypeError("ProgressState.last_signal must be ProgressSignal or None")
        _require_nonnegative_int(
            self.consecutive_identical_failures,
            "ProgressState.consecutive_identical_failures",
        )
        _require_nonnegative_int(
            self.consecutive_no_progress,
            "ProgressState.consecutive_no_progress",
        )
        _require_optional_text(
            self.last_stable_checkpoint_ref,
            "ProgressState.last_stable_checkpoint_ref",
        )
        _require_text_tuple(self.evidence_refs, "ProgressState.evidence_refs")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProgressDecision:
    should_stop: bool
    reason_code: StopReasonCode | None
    state: ProgressState
    summary: str
    checkpoint_ref: str | None
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.should_stop) is not bool:
            raise TypeError("ProgressDecision.should_stop must be a boolean")
        if self.reason_code is not None:
            _require_enum(self.reason_code, StopReasonCode, "ProgressDecision.reason_code")
        if type(self.state) is not ProgressState:
            raise TypeError("ProgressDecision.state must be ProgressState")
        _require_text(self.summary, "ProgressDecision.summary")
        _require_optional_text(self.checkpoint_ref, "ProgressDecision.checkpoint_ref")
        _require_text_tuple(self.evidence_refs, "ProgressDecision.evidence_refs")
        if self.should_stop != (self.reason_code is not None):
            raise StateValidationError("ProgressDecision stop flag and reason_code must agree")


@dataclass(frozen=True, slots=True, kw_only=True)
class RetryDecision:
    code: RetryDecisionCode
    reason: str
    retry_after_seconds: float | None = None
    stop_reason_code: StopReasonCode | None = None
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_enum(self.code, RetryDecisionCode, "RetryDecision.code")
        _require_text(self.reason, "RetryDecision.reason")
        if self.retry_after_seconds is not None:
            _require_finite_nonnegative(
                self.retry_after_seconds,
                "RetryDecision.retry_after_seconds",
            )
        if self.stop_reason_code is not None:
            _require_enum(
                self.stop_reason_code,
                StopReasonCode,
                "RetryDecision.stop_reason_code",
            )
        _require_text_tuple(self.evidence_refs, "RetryDecision.evidence_refs")
        if self.code is RetryDecisionCode.RETRY and self.stop_reason_code is not None:
            raise StateValidationError("RETRY decisions must not include a stop reason")
        if self.code is RetryDecisionCode.STOP and self.stop_reason_code is None:
            raise StateValidationError("STOP decisions require a stop reason")
        if self.code is not RetryDecisionCode.RETRY and self.retry_after_seconds is not None:
            raise StateValidationError("non-retry decisions must not include a retry delay")
        if (
            self.code is RetryDecisionCode.APPROVAL_REQUIRED
            and self.stop_reason_code is not StopReasonCode.APPROVAL_REQUIRED
        ):
            raise StateValidationError(
                "APPROVAL_REQUIRED decisions require the approval stop reason"
            )

    @property
    def should_retry(self) -> bool:
        return self.code is RetryDecisionCode.RETRY


@dataclass(frozen=True, slots=True, kw_only=True)
class ActionRetryContext:
    idempotent: bool
    outcome: ExternalActionOutcome
    action_id: str
    target_identity: str
    reconciled_action_id: str | None = None
    reconciled_target_identity: str | None = None
    reconciliation_evidence_ref: str | None = None
    reconciled_outcome: ExternalActionOutcome | None = None

    def __post_init__(self) -> None:
        if type(self.idempotent) is not bool:
            raise TypeError("ActionRetryContext.idempotent must be a boolean")
        _require_enum(self.outcome, ExternalActionOutcome, "ActionRetryContext.outcome")
        _require_text(self.action_id, "ActionRetryContext.action_id")
        _require_text(self.target_identity, "ActionRetryContext.target_identity")
        _require_optional_text(
            self.reconciled_action_id,
            "ActionRetryContext.reconciled_action_id",
        )
        _require_optional_text(
            self.reconciled_target_identity,
            "ActionRetryContext.reconciled_target_identity",
        )
        _require_optional_text(
            self.reconciliation_evidence_ref,
            "ActionRetryContext.reconciliation_evidence_ref",
        )
        if self.reconciled_outcome is not None:
            _require_enum(
                self.reconciled_outcome,
                ExternalActionOutcome,
                "ActionRetryContext.reconciled_outcome",
            )


def calculate_backoff(
    settings: RetrySettings, attempt_index: int, unit_sample: float = 0.5
) -> float:
    """Calculate capped exponential backoff for a retry attempt after initial dispatch."""

    if type(settings) is not RetrySettings:
        raise TypeError("settings must be RetrySettings")
    if type(attempt_index) is not int or attempt_index < 1:
        raise StateValidationError("attempt_index must be an integer retry attempt starting at one")
    if type(unit_sample) not in (int, float):
        raise StateValidationError("unit_sample must be a finite number")
    sample = float(unit_sample)
    if not math.isfinite(sample) or sample < 0.0 or sample > 1.0:
        raise StateValidationError("unit_sample must be between zero and one")
    exponent = attempt_index - 1
    if (
        settings.backoff_multiplier == 1.0
        or settings.initial_backoff_seconds >= settings.maximum_backoff_seconds
    ):
        base = settings.initial_backoff_seconds
    else:
        cap_ratio = settings.maximum_backoff_seconds / settings.initial_backoff_seconds
        steps_to_cap = math.log(cap_ratio) / math.log(settings.backoff_multiplier)
        if exponent >= steps_to_cap:
            base = settings.maximum_backoff_seconds
        else:
            base = min(
                settings.maximum_backoff_seconds,
                settings.initial_backoff_seconds * (settings.backoff_multiplier**exponent),
            )
    jitter_width = base * settings.jitter_ratio
    jittered = base - jitter_width + (2.0 * jitter_width * sample)
    return min(settings.maximum_backoff_seconds, max(0.0, float(jittered)))


def decide_transient_retry(
    *,
    settings: RetrySettings,
    failure: FailureSignal,
    completed_retries: int,
    budget_state: BudgetState | None = None,
    unit_sample: float = 0.5,
) -> RetryDecision:
    if type(settings) is not RetrySettings:
        raise TypeError("settings must be RetrySettings")
    if type(failure) is not FailureSignal:
        raise TypeError("failure must be FailureSignal")
    if type(completed_retries) is not int or completed_retries < 0:
        raise StateValidationError("completed_retries must be a non-negative integer")
    if budget_state is not None and type(budget_state) is not BudgetState:
        raise TypeError("budget_state must be BudgetState or None")
    if (
        budget_state is not None
        and current_budget_decision(budget_state).code is BudgetDecisionCode.BUDGET_EXHAUSTED
    ):
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="budget already exhausted",
            stop_reason_code=StopReasonCode.BUDGET_EXHAUSTED,
        )
    if failure.category is FailureClass.DETERMINISTIC_VALIDATION:
        return RetryDecision(
            code=RetryDecisionCode.REPAIR_REQUIRED,
            reason="deterministic validation failure requires material repair",
        )
    if failure.category is FailureClass.APPROVAL_REQUIRED:
        return RetryDecision(
            code=RetryDecisionCode.APPROVAL_REQUIRED,
            reason="approval required",
            stop_reason_code=StopReasonCode.APPROVAL_REQUIRED,
        )
    if failure.category is not FailureClass.TRANSIENT:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="failure is not retryable",
            stop_reason_code=StopReasonCode.BLOCKED,
        )
    if completed_retries >= settings.max_transient_retries:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="transient retry limit reached",
            stop_reason_code=StopReasonCode.BLOCKED,
        )
    retry_number = completed_retries + 1
    return RetryDecision(
        code=RetryDecisionCode.RETRY,
        reason="transient failure is retryable",
        retry_after_seconds=calculate_backoff(settings, retry_number, unit_sample),
    )


def advance_progress_state(
    settings: RetrySettings, state: ProgressState, signal: ProgressSignal
) -> ProgressDecision:
    if type(settings) is not RetrySettings:
        raise TypeError("settings must be RetrySettings")
    if type(state) is not ProgressState:
        raise TypeError("state must be ProgressState")
    if type(signal) is not ProgressSignal:
        raise TypeError("signal must be ProgressSignal")
    previous = state.last_signal
    identical_failure = previous is not None and _failure_key(previous) == _failure_key(signal)
    progress = previous is None or _progress_key(previous) != _progress_key(signal)
    identical_count = state.consecutive_identical_failures
    no_progress_count = state.consecutive_no_progress
    if signal.failure is None or not identical_failure:
        identical_count = 0
    if signal.failure is not None:
        identical_count += 1
    no_progress_count = 0 if progress else no_progress_count + 1
    if previous is None or progress:
        checkpoint = signal.checkpoint_ref or state.last_stable_checkpoint_ref
        evidence = signal.evidence_refs or state.evidence_refs
    else:
        checkpoint = state.last_stable_checkpoint_ref
        evidence = state.evidence_refs
    next_state = ProgressState(
        last_signal=signal,
        consecutive_identical_failures=identical_count,
        consecutive_no_progress=no_progress_count,
        last_stable_checkpoint_ref=checkpoint,
        evidence_refs=evidence,
    )
    if identical_count >= settings.identical_failure_limit:
        return ProgressDecision(
            should_stop=True,
            reason_code=StopReasonCode.BLOCKED,
            state=next_state,
            summary="identical failure threshold reached",
            checkpoint_ref=checkpoint,
            evidence_refs=evidence,
        )
    if no_progress_count >= settings.no_progress_iteration_limit:
        return ProgressDecision(
            should_stop=True,
            reason_code=StopReasonCode.REPEATED_NO_PROGRESS,
            state=next_state,
            summary="no-progress threshold reached",
            checkpoint_ref=checkpoint,
            evidence_refs=evidence,
        )
    return ProgressDecision(
        should_stop=False,
        reason_code=None,
        state=next_state,
        summary="progress policy permits another attempt",
        checkpoint_ref=checkpoint,
        evidence_refs=evidence,
    )


def decide_action_retry_safety(context: ActionRetryContext) -> RetryDecision:
    if type(context) is not ActionRetryContext:
        raise TypeError("context must be ActionRetryContext")
    if context.outcome is ExternalActionOutcome.SUCCEEDED:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="action already succeeded",
            stop_reason_code=StopReasonCode.BLOCKED,
        )
    if context.outcome in {
        ExternalActionOutcome.NOT_STARTED,
        ExternalActionOutcome.FAILED,
    }:
        return RetryDecision(code=RetryDecisionCode.RETRY, reason="action retry is safe")
    if context.idempotent and context.outcome is ExternalActionOutcome.UNKNOWN:
        return RetryDecision(
            code=RetryDecisionCode.RETRY,
            reason="idempotent action can reuse its stable identity after unknown result",
        )
    if context.idempotent and context.outcome is ExternalActionOutcome.STARTED:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="action is still recorded as started",
            stop_reason_code=StopReasonCode.BLOCKED,
        )
    if context.outcome not in {ExternalActionOutcome.STARTED, ExternalActionOutcome.UNKNOWN}:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="action outcome is not retryable",
            stop_reason_code=StopReasonCode.BLOCKED,
        )
    if context.reconciled_outcome in {
        None,
        ExternalActionOutcome.STARTED,
        ExternalActionOutcome.UNKNOWN,
    }:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="ambiguous action outcome is unresolved",
            stop_reason_code=StopReasonCode.UNSAFE_ACTION,
        )
    if context.reconciled_action_id != context.action_id:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="reconciled action identity does not match",
            stop_reason_code=StopReasonCode.UNSAFE_ACTION,
        )
    if context.reconciled_target_identity != context.target_identity:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="reconciled target identity does not match",
            stop_reason_code=StopReasonCode.UNSAFE_ACTION,
        )
    if not context.reconciliation_evidence_ref:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="reconciliation evidence is missing",
            stop_reason_code=StopReasonCode.UNSAFE_ACTION,
        )
    if context.reconciled_outcome is ExternalActionOutcome.SUCCEEDED:
        return RetryDecision(
            code=RetryDecisionCode.STOP,
            reason="reconciliation proved the action already succeeded",
            stop_reason_code=StopReasonCode.UNSAFE_ACTION,
            evidence_refs=(context.reconciliation_evidence_ref,),
        )
    return RetryDecision(
        code=RetryDecisionCode.RETRY,
        reason="ambiguous non-idempotent action reconciled before retry",
        evidence_refs=(context.reconciliation_evidence_ref,),
    )


def _failure_key(signal: ProgressSignal) -> tuple[str | None, str | None]:
    if signal.failure is None:
        return (None, None)
    return (signal.failure.category.value, signal.failure.signature)


def _progress_key(signal: ProgressSignal) -> tuple[object, ...]:
    return (
        _failure_key(signal),
        signal.validator_verdict,
        signal.artifact_hash,
        signal.diff_hash,
        signal.satisfied_criteria,
        signal.remaining_delta,
        signal.dependency_state,
        signal.approved_action_state,
    )


def _require_enum(value: object, expected: type[StrEnum], location: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{location} must be {expected.__name__}")


def _require_text(value: object, location: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{location} must be a string")
    if not value or value != value.strip() or len(value) > 2048:
        raise StateValidationError(f"{location} must be normalized non-empty text")


def _require_optional_text(value: object, location: str) -> None:
    if value is not None:
        _require_text(value, location)


def _require_text_tuple(value: object, location: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{location} must be a tuple")
    for item in value:
        _require_text(item, location)
    if len(set(value)) != len(value):
        raise StateValidationError(f"{location} must not contain duplicates")


def _require_nonnegative_int(value: object, location: str) -> None:
    if type(value) is not int:
        raise TypeError(f"{location} must be an integer")
    if value < 0:
        raise StateValidationError(f"{location} must be non-negative")


def _require_finite_nonnegative(value: object, location: str) -> None:
    if type(value) is int:
        checked = float(value)
    elif type(value) is float:
        checked = value
    else:
        raise TypeError(f"{location} must be numeric")
    if not math.isfinite(checked) or checked < 0:
        raise StateValidationError(f"{location} must be finite and non-negative")
