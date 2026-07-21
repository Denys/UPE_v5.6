from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from harness.budgets import (
    BudgetDecisionCode,
    account_usage,
    current_budget_decision,
    initial_budget_state,
    prospective_budget_decision,
)
from harness.state import (
    BudgetDimension,
    BudgetState,
    BudgetValues,
    LifecycleState,
    StateValidationError,
)


def full_limits() -> BudgetValues:
    return BudgetValues(
        iterations=2,
        elapsed_seconds=10.0,
        input_tokens=100,
        output_tokens=50,
        total_tokens=150,
        cost=1.5,
    )


def test_initial_and_unconfigured_dimensions_are_unenforced() -> None:
    state = initial_budget_state(BudgetValues(iterations=1))
    decision = prospective_budget_decision(
        state,
        BudgetValues(elapsed_seconds=999.0, input_tokens=1000, output_tokens=1, total_tokens=1001),
    )
    assert decision.code is BudgetDecisionCode.WITHIN_BUDGET
    assert decision.state.consumed.elapsed_seconds == 999.0
    assert decision.state.exhausted_dimensions == ()


@pytest.mark.parametrize(
    ("usage", "dimension"),
    [
        (BudgetValues(iterations=2), BudgetDimension.ITERATIONS),
        (BudgetValues(elapsed_seconds=10.0), BudgetDimension.ELAPSED_SECONDS),
        (BudgetValues(input_tokens=100, total_tokens=100), BudgetDimension.INPUT_TOKENS),
        (BudgetValues(output_tokens=50, total_tokens=50), BudgetDimension.OUTPUT_TOKENS),
        (
            BudgetValues(input_tokens=100, output_tokens=50, total_tokens=150),
            BudgetDimension.TOTAL_TOKENS,
        ),
        (BudgetValues(cost=1.5), BudgetDimension.COST),
    ],
)
def test_each_configured_dimension_exhausts_exactly(
    usage: BudgetValues, dimension: BudgetDimension
) -> None:
    state = initial_budget_state(full_limits())
    decision = prospective_budget_decision(state, usage)
    assert decision.code is BudgetDecisionCode.BUDGET_EXHAUSTED
    assert dimension in decision.exhausted_dimensions
    assert decision.lifecycle_state is LifecycleState.BUDGET_EXHAUSTED
    assert decision.stop_reason is not None


def test_prospective_overrun_blocks_without_mutating_input_state() -> None:
    state = initial_budget_state(BudgetValues(iterations=1))
    decision = prospective_budget_decision(state, BudgetValues(iterations=2))
    assert decision.code is BudgetDecisionCode.WOULD_EXCEED_BUDGET
    assert decision.blocked_dimensions == (BudgetDimension.ITERATIONS,)
    assert state.consumed.iterations is None


def test_exact_boundary_allows_final_dispatch_then_blocks_future_dispatch() -> None:
    state = initial_budget_state(BudgetValues(iterations=1))
    prospective = prospective_budget_decision(state, BudgetValues(iterations=1))
    assert prospective.code is BudgetDecisionCode.BUDGET_EXHAUSTED
    assert prospective.allowed
    assert not current_budget_decision(prospective.state).allowed


def test_component_tokens_derive_total_and_cannot_bypass_total_limit() -> None:
    state = initial_budget_state(BudgetValues(total_tokens=5))
    decision = prospective_budget_decision(
        state,
        BudgetValues(input_tokens=4, output_tokens=4),
    )
    assert decision.code is BudgetDecisionCode.WOULD_EXCEED_BUDGET
    assert decision.blocked_dimensions == (BudgetDimension.TOTAL_TOKENS,)
    accounted = account_usage(
        initial_budget_state(BudgetValues(total_tokens=10)),
        BudgetValues(input_tokens=4, output_tokens=4),
    )
    assert accounted.consumed.total_tokens == 8


def test_accumulation_is_monotonic_and_immutable() -> None:
    state = initial_budget_state(
        BudgetValues(iterations=3, input_tokens=5, output_tokens=5, total_tokens=10)
    )
    next_state = account_usage(state, BudgetValues(iterations=1, input_tokens=2, total_tokens=2))
    final_state = account_usage(
        next_state, BudgetValues(iterations=1, output_tokens=3, total_tokens=3)
    )
    assert state.consumed.iterations is None
    assert final_state.consumed.iterations == 2
    assert final_state.consumed.input_tokens == 2
    assert final_state.consumed.output_tokens == 3
    assert final_state.consumed.total_tokens == 5
    with pytest.raises(FrozenInstanceError):
        final_state.exhausted_dimensions = ()  # type: ignore[misc]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"iterations": -1},
        {"elapsed_seconds": -0.1},
        {"elapsed_seconds": float("inf")},
        {"cost": float("nan")},
    ],
)
def test_invalid_usage_rejected(kwargs: dict[str, object]) -> None:
    with pytest.raises((StateValidationError, TypeError)):
        BudgetValues(**kwargs)  # type: ignore[arg-type]


@pytest.mark.parametrize("kwargs", [{"iterations": True}, {"input_tokens": False}, {"cost": True}])
def test_booleans_do_not_pass_as_numbers(kwargs: dict[str, object]) -> None:
    with pytest.raises(TypeError):
        BudgetValues(**kwargs)  # type: ignore[arg-type]


def test_token_total_consistency_is_enforced_for_usage_and_state() -> None:
    state = initial_budget_state(BudgetValues(total_tokens=10))
    with pytest.raises(StateValidationError):
        account_usage(state, BudgetValues(input_tokens=2, output_tokens=3, total_tokens=6))
    with pytest.raises(StateValidationError):
        current_budget_decision(
            BudgetState(
                limits=BudgetValues(total_tokens=10),
                consumed=BudgetValues(input_tokens=2, output_tokens=3, total_tokens=4),
                exhausted_dimensions=(),
            )
        )


def test_decreasing_or_inconsistent_state_rejected_by_budget_state() -> None:
    with pytest.raises(StateValidationError):
        BudgetState(
            limits=BudgetValues(iterations=1),
            consumed=BudgetValues(iterations=0),
            exhausted_dimensions=(BudgetDimension.ITERATIONS,),
        )
