from __future__ import annotations

import math
from dataclasses import FrozenInstanceError, replace

import pytest

from harness.config import RetrySettings
from harness.retry_policy import (
    ActionRetryContext,
    ExternalActionOutcome,
    FailureClass,
    FailureSignal,
    ProgressSignal,
    ProgressState,
    RetryDecisionCode,
    advance_progress_state,
    calculate_backoff,
    decide_action_retry_safety,
    decide_transient_retry,
)
from harness.state import (
    BudgetDimension,
    BudgetState,
    BudgetValues,
    CompletionVerdict,
    StateValidationError,
    StopReasonCode,
)


def settings(**overrides: object) -> RetrySettings:
    data: dict[str, object] = {
        "max_transient_retries": 2,
        "identical_failure_limit": 2,
        "no_progress_iteration_limit": 2,
        "initial_backoff_seconds": 1.0,
        "maximum_backoff_seconds": 10.0,
        "backoff_multiplier": 2.0,
        "jitter_ratio": 0.25,
    }
    data.update(overrides)
    return RetrySettings(**data)  # type: ignore[arg-type]


def transient(sig: str = "net-timeout") -> FailureSignal:
    return FailureSignal(category=FailureClass.TRANSIENT, signature=sig)


def test_exponential_cap_jitter_samples_zero_jitter_and_extreme_attempt() -> None:
    cfg = settings()
    assert calculate_backoff(cfg, 1, 0.0) == 0.75
    assert calculate_backoff(cfg, 1, 0.5) == 1.0
    assert calculate_backoff(cfg, 1, 1.0) == 1.25
    assert calculate_backoff(cfg, 4, 0.5) == 8.0
    assert calculate_backoff(settings(jitter_ratio=0.0), 3, 0.0) == 4.0
    huge = calculate_backoff(cfg, 10_000, 1.0)
    assert math.isfinite(huge)
    assert 0.0 <= huge <= cfg.maximum_backoff_seconds


def test_extreme_multiplier_caps_without_overflow() -> None:
    cfg = settings(backoff_multiplier=1e308)
    assert calculate_backoff(cfg, 3, 0.5) == cfg.maximum_backoff_seconds


@pytest.mark.parametrize("sample", [-0.1, 1.1, float("nan")])
def test_invalid_jitter_sample_rejected(sample: float) -> None:
    with pytest.raises(StateValidationError):
        calculate_backoff(settings(), 1, sample)


def test_retry_count_zero_and_exact_last_retry_boundaries() -> None:
    zero = settings(max_transient_retries=0)
    assert (
        decide_transient_retry(settings=zero, failure=transient(), completed_retries=0).code
        is RetryDecisionCode.STOP
    )
    cfg = settings(max_transient_retries=2)
    first = decide_transient_retry(settings=cfg, failure=transient(), completed_retries=0)
    last = decide_transient_retry(settings=cfg, failure=transient(), completed_retries=1)
    exhausted = decide_transient_retry(settings=cfg, failure=transient(), completed_retries=2)
    assert first.code is RetryDecisionCode.RETRY
    assert last.code is RetryDecisionCode.RETRY
    assert exhausted.code is RetryDecisionCode.STOP


@pytest.mark.parametrize(
    ("failure", "code"),
    [
        (
            FailureSignal(category=FailureClass.DETERMINISTIC_VALIDATION, signature="pytest-fail"),
            RetryDecisionCode.REPAIR_REQUIRED,
        ),
        (
            FailureSignal(category=FailureClass.PERMANENT, signature="missing-python"),
            RetryDecisionCode.STOP,
        ),
        (
            FailureSignal(category=FailureClass.POLICY, signature="forbidden"),
            RetryDecisionCode.STOP,
        ),
        (
            FailureSignal(category=FailureClass.APPROVAL_REQUIRED, signature="commit"),
            RetryDecisionCode.APPROVAL_REQUIRED,
        ),
    ],
)
def test_failure_classification(failure: FailureSignal, code: RetryDecisionCode) -> None:
    assert (
        decide_transient_retry(settings=settings(), failure=failure, completed_retries=0).code
        is code
    )


def test_already_exhausted_budget_blocks_retry() -> None:
    budget = BudgetState(
        limits=BudgetValues(iterations=1),
        consumed=BudgetValues(iterations=1),
        exhausted_dimensions=(BudgetDimension.ITERATIONS,),
    )
    decision = decide_transient_retry(
        settings=settings(), failure=transient(), completed_retries=0, budget_state=budget
    )
    assert decision.code is RetryDecisionCode.STOP
    assert decision.stop_reason_code is StopReasonCode.BUDGET_EXHAUSTED


def progress_signal(
    sig: str = "same", *, diff: str = "d1", checkpoint: str = "cp1"
) -> ProgressSignal:
    return ProgressSignal(
        failure=transient(sig),
        validator_verdict=CompletionVerdict.FAIL,
        diff_hash=diff,
        remaining_delta="one failing criterion",
        checkpoint_ref=checkpoint,
        evidence_refs=("evidence/fail.txt",),
    )


def test_identical_failure_threshold_minus_one_exact_and_reset() -> None:
    cfg = settings(identical_failure_limit=3, no_progress_iteration_limit=10)
    state = ProgressState()
    one = advance_progress_state(cfg, state, progress_signal())
    two = advance_progress_state(cfg, one.state, progress_signal())
    three = advance_progress_state(cfg, two.state, progress_signal())
    assert not one.should_stop
    assert not two.should_stop
    assert three.should_stop
    assert three.reason_code is StopReasonCode.BLOCKED
    reset = advance_progress_state(cfg, three.state, progress_signal("different"))
    assert reset.state.consecutive_identical_failures == 1


def test_no_progress_threshold_and_material_progress_reset_mixed_sequence() -> None:
    cfg = settings(identical_failure_limit=10, no_progress_iteration_limit=2)
    state = ProgressState()
    one = advance_progress_state(cfg, state, progress_signal(diff="d1", checkpoint="cp-good"))
    two = advance_progress_state(cfg, one.state, progress_signal(diff="d1", checkpoint="cp-good"))
    three = advance_progress_state(cfg, two.state, progress_signal(diff="d1", checkpoint="cp-good"))
    assert not one.should_stop
    assert not two.should_stop
    assert three.should_stop
    assert three.reason_code is StopReasonCode.REPEATED_NO_PROGRESS
    assert three.checkpoint_ref == "cp-good"
    progressed = advance_progress_state(
        cfg, three.state, progress_signal(diff="d2", checkpoint="cp-better")
    )
    assert progressed.state.consecutive_no_progress == 0
    assert progressed.state.last_stable_checkpoint_ref == "cp-better"


def test_no_progress_attempt_cannot_overwrite_last_stable_evidence() -> None:
    cfg = settings(identical_failure_limit=10, no_progress_iteration_limit=1)
    first = advance_progress_state(
        cfg,
        ProgressState(),
        progress_signal(diff="same", checkpoint="stable"),
    )
    second_signal = ProgressSignal(
        failure=transient("same"),
        validator_verdict=CompletionVerdict.FAIL,
        diff_hash="same",
        remaining_delta="one failing criterion",
        checkpoint_ref="unstable",
        evidence_refs=("evidence/new-failure.txt",),
    )
    stopped = advance_progress_state(cfg, first.state, second_signal)
    assert stopped.should_stop
    assert stopped.checkpoint_ref == "stable"
    assert stopped.evidence_refs == ("evidence/fail.txt",)


def test_progress_records_are_immutable_and_inputs_not_mutated() -> None:
    signal = progress_signal()
    state = ProgressState()
    decision = advance_progress_state(settings(), state, signal)
    assert state.last_signal is None
    with pytest.raises(FrozenInstanceError):
        decision.state.consecutive_no_progress = 99  # type: ignore[misc]


def ambiguous_context(**overrides: object) -> ActionRetryContext:
    data = {
        "idempotent": False,
        "outcome": ExternalActionOutcome.UNKNOWN,
        "action_id": "act-1",
        "target_identity": "target-1",
        "reconciled_action_id": None,
        "reconciled_target_identity": None,
        "reconciliation_evidence_ref": None,
        "reconciled_outcome": None,
    }
    data.update(overrides)
    return ActionRetryContext(**data)  # type: ignore[arg-type]


def test_non_idempotent_unknown_retry_requires_matching_reconciliation() -> None:
    assert decide_action_retry_safety(ambiguous_context()).code is RetryDecisionCode.STOP
    ok = ambiguous_context(
        reconciled_action_id="act-1",
        reconciled_target_identity="target-1",
        reconciliation_evidence_ref="reconcile/act-1.yaml",
        reconciled_outcome=ExternalActionOutcome.FAILED,
    )
    decision = decide_action_retry_safety(ok)
    assert decision.code is RetryDecisionCode.RETRY
    assert decision.evidence_refs == ("reconcile/act-1.yaml",)


@pytest.mark.parametrize(
    "context",
    [
        ambiguous_context(
            reconciled_action_id="act-2",
            reconciled_target_identity="target-1",
            reconciliation_evidence_ref="e",
            reconciled_outcome=ExternalActionOutcome.FAILED,
        ),
        ambiguous_context(
            reconciled_action_id="act-1",
            reconciled_target_identity="target-2",
            reconciliation_evidence_ref="e",
            reconciled_outcome=ExternalActionOutcome.FAILED,
        ),
        ambiguous_context(
            reconciled_action_id="act-1",
            reconciled_target_identity="target-1",
            reconciliation_evidence_ref=None,
            reconciled_outcome=ExternalActionOutcome.FAILED,
        ),
    ],
)
def test_identity_target_and_evidence_mismatches_block(context: ActionRetryContext) -> None:
    assert decide_action_retry_safety(context).code is RetryDecisionCode.STOP


def test_started_is_ambiguous_but_failed_or_idempotent_can_retry() -> None:
    assert (
        decide_action_retry_safety(ambiguous_context(outcome=ExternalActionOutcome.STARTED)).code
        is RetryDecisionCode.STOP
    )
    assert (
        decide_action_retry_safety(ambiguous_context(outcome=ExternalActionOutcome.FAILED)).code
        is RetryDecisionCode.RETRY
    )
    assert (
        decide_action_retry_safety(ambiguous_context(idempotent=True)).code
        is RetryDecisionCode.RETRY
    )


def test_succeeded_action_is_never_retried_and_reconciled_success_blocks() -> None:
    succeeded = ambiguous_context(idempotent=True, outcome=ExternalActionOutcome.SUCCEEDED)
    assert decide_action_retry_safety(succeeded).code is RetryDecisionCode.STOP
    reconciled_success = ambiguous_context(
        reconciled_action_id="act-1",
        reconciled_target_identity="target-1",
        reconciliation_evidence_ref="reconcile/act-1.yaml",
        reconciled_outcome=ExternalActionOutcome.SUCCEEDED,
    )
    assert decide_action_retry_safety(reconciled_success).code is RetryDecisionCode.STOP


def test_public_policy_records_reject_type_confusion_and_invalid_counters() -> None:
    with pytest.raises(TypeError):
        FailureSignal(category="TRANSIENT", signature="x")  # type: ignore[arg-type]
    with pytest.raises(StateValidationError):
        FailureSignal(category=FailureClass.TRANSIENT, signature="")
    with pytest.raises((TypeError, StateValidationError)):
        ProgressState(consecutive_no_progress=True)


def test_no_sleep_or_io_protocol_is_injected_by_value() -> None:
    cfg = settings()
    before = replace(cfg)
    assert calculate_backoff(cfg, 2, 0.5) == 2.0
    assert cfg == before
