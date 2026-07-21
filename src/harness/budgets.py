"""Pure host-side budget accounting and enforcement policy."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from harness.state import (
    BudgetDimension,
    BudgetState,
    BudgetValues,
    LifecycleState,
    StateValidationError,
    StopReason,
    StopReasonCode,
)

_NUMERIC_DIMENSIONS: Final[tuple[BudgetDimension, ...]] = tuple(BudgetDimension)


class BudgetDecisionCode(StrEnum):
    """Budget policy outcomes for callers to map into lifecycle transitions."""

    WITHIN_BUDGET = "WITHIN_BUDGET"
    WOULD_EXCEED_BUDGET = "WOULD_EXCEED_BUDGET"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"


@dataclass(frozen=True, slots=True, kw_only=True)
class BudgetDecision:
    """A bounded, immutable host decision about current or prospective budget state."""

    code: BudgetDecisionCode
    state: BudgetState
    exhausted_dimensions: tuple[BudgetDimension, ...]
    blocked_dimensions: tuple[BudgetDimension, ...]
    dispatch_allowed: bool
    lifecycle_state: LifecycleState | None
    stop_reason: StopReason | None
    summary: str

    def __post_init__(self) -> None:
        if type(self.code) is not BudgetDecisionCode:
            raise TypeError("BudgetDecision.code must be BudgetDecisionCode")
        if type(self.state) is not BudgetState:
            raise TypeError("BudgetDecision.state must be BudgetState")
        _validate_dimensions(self.exhausted_dimensions, "exhausted_dimensions")
        _validate_dimensions(self.blocked_dimensions, "blocked_dimensions")
        if type(self.dispatch_allowed) is not bool:
            raise TypeError("BudgetDecision.dispatch_allowed must be a boolean")
        if self.lifecycle_state is not None and type(self.lifecycle_state) is not LifecycleState:
            raise TypeError("BudgetDecision.lifecycle_state must be LifecycleState or None")
        if self.stop_reason is not None and type(self.stop_reason) is not StopReason:
            raise TypeError("BudgetDecision.stop_reason must be StopReason or None")
        _validate_text(self.summary, "BudgetDecision.summary")
        if self.exhausted_dimensions != self.state.exhausted_dimensions:
            raise StateValidationError(
                "BudgetDecision.exhausted_dimensions must match its budget state"
            )
        if self.code is BudgetDecisionCode.WITHIN_BUDGET:
            if self.blocked_dimensions:
                raise StateValidationError("WITHIN_BUDGET must not block dimensions")
            if (
                not self.dispatch_allowed
                or self.lifecycle_state is not None
                or self.stop_reason is not None
            ):
                raise StateValidationError("WITHIN_BUDGET must be allowed and have no stop state")
            return
        if self.lifecycle_state is not LifecycleState.BUDGET_EXHAUSTED:
            raise StateValidationError("blocked budget decisions require BUDGET_EXHAUSTED state")
        if self.stop_reason is None or self.stop_reason.code is not StopReasonCode.BUDGET_EXHAUSTED:
            raise StateValidationError("blocked budget decisions require a budget stop reason")
        if self.code is BudgetDecisionCode.WOULD_EXCEED_BUDGET:
            if self.dispatch_allowed or not self.blocked_dimensions or self.exhausted_dimensions:
                raise StateValidationError("WOULD_EXCEED_BUDGET must block at least one dimension")
        elif self.blocked_dimensions or not self.exhausted_dimensions:
            raise StateValidationError("BUDGET_EXHAUSTED requires an exhausted dimension")

    @property
    def allowed(self) -> bool:
        return self.dispatch_allowed


def _value_for(values: BudgetValues, dimension: BudgetDimension) -> int | float | None:
    return values.for_dimension(dimension)


def _normalized_token_values(values: BudgetValues, location: str) -> BudgetValues:
    input_tokens = values.input_tokens
    output_tokens = values.output_tokens
    total_tokens = values.total_tokens
    has_components = input_tokens is not None or output_tokens is not None
    known = (input_tokens or 0) + (output_tokens or 0)
    if total_tokens is not None and has_components:
        if total_tokens < known:
            raise StateValidationError(
                f"{location}.total_tokens must be at least input_tokens plus output_tokens"
            )
        if input_tokens is not None and output_tokens is not None and total_tokens != known:
            raise StateValidationError(
                f"{location}.total_tokens must equal input_tokens plus output_tokens "
                "when supplied together"
            )
    normalized_total = known if total_tokens is None and has_components else total_tokens
    return BudgetValues(
        iterations=values.iterations,
        elapsed_seconds=values.elapsed_seconds,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=normalized_total,
        cost=values.cost,
    )


def _validate_state_consistency(state: BudgetState) -> None:
    consumed = state.consumed
    known = (consumed.input_tokens or 0) + (consumed.output_tokens or 0)
    if consumed.total_tokens is not None and consumed.total_tokens < known:
        raise StateValidationError(
            "BudgetState.consumed total_tokens must be at least known input plus output tokens"
        )


def _normalized_state(state: BudgetState) -> BudgetState:
    if type(state) is not BudgetState:
        raise TypeError("state must be BudgetState")
    _validate_state_consistency(state)
    consumed = _normalized_token_values(state.consumed, "BudgetState.consumed")
    return BudgetState(
        limits=state.limits,
        consumed=consumed,
        exhausted_dimensions=_exhausted(state.limits, consumed),
    )


def _add_values(left: int | float | None, right: int | float | None) -> int | float | None:
    if left is None and right is None:
        return None
    total = (left or 0) + (right or 0)
    if not math.isfinite(float(total)):
        raise StateValidationError("budget consumption must remain finite")
    return total


def _exhausted(limits: BudgetValues, consumed: BudgetValues) -> tuple[BudgetDimension, ...]:
    result: list[BudgetDimension] = []
    for dimension in _NUMERIC_DIMENSIONS:
        limit = _value_for(limits, dimension)
        value = _value_for(consumed, dimension)
        if limit is not None and value is not None and value >= limit:
            result.append(dimension)
    return tuple(result)


def _over_limit(limits: BudgetValues, consumed: BudgetValues) -> tuple[BudgetDimension, ...]:
    result: list[BudgetDimension] = []
    for dimension in _NUMERIC_DIMENSIONS:
        limit = _value_for(limits, dimension)
        value = _value_for(consumed, dimension)
        if limit is not None and value is not None and value > limit:
            result.append(dimension)
    return tuple(result)


def initial_budget_state(limits: BudgetValues) -> BudgetState:
    """Create an empty immutable budget state for the supplied configured limits."""

    if type(limits) is not BudgetValues:
        raise TypeError("limits must be BudgetValues")
    consumed = BudgetValues()
    return BudgetState(limits=limits, consumed=consumed, exhausted_dimensions=())


def account_usage(state: BudgetState, usage: BudgetValues) -> BudgetState:
    """Return a new budget state with monotonic usage accumulated."""

    if type(usage) is not BudgetValues:
        raise TypeError("usage must be BudgetValues")
    normalized_state = _normalized_state(state)
    normalized_usage = _normalized_token_values(usage, "BudgetValues")
    consumed = BudgetValues(
        iterations=_as_int(
            _add_values(normalized_state.consumed.iterations, normalized_usage.iterations),
            "iterations",
        ),
        elapsed_seconds=_as_float(
            _add_values(
                normalized_state.consumed.elapsed_seconds, normalized_usage.elapsed_seconds
            ),
            "elapsed_seconds",
        ),
        input_tokens=_as_int(
            _add_values(normalized_state.consumed.input_tokens, normalized_usage.input_tokens),
            "input_tokens",
        ),
        output_tokens=_as_int(
            _add_values(normalized_state.consumed.output_tokens, normalized_usage.output_tokens),
            "output_tokens",
        ),
        total_tokens=_as_int(
            _add_values(normalized_state.consumed.total_tokens, normalized_usage.total_tokens),
            "total_tokens",
        ),
        cost=_as_float(_add_values(normalized_state.consumed.cost, normalized_usage.cost), "cost"),
    )
    result = BudgetState(
        limits=normalized_state.limits,
        consumed=consumed,
        exhausted_dimensions=_exhausted(normalized_state.limits, consumed),
    )
    _validate_state_consistency(result)
    return result


def prospective_budget_decision(
    state: BudgetState, prospective_usage: BudgetValues
) -> BudgetDecision:
    """Decide whether a proposed action can dispatch without exceeding limits."""

    state = _normalized_state(state)
    if state.exhausted_dimensions:
        return _decision(
            BudgetDecisionCode.BUDGET_EXHAUSTED,
            state,
            (),
            "configured budget already exhausted",
            dispatch_allowed=False,
        )
    candidate = account_usage(state, prospective_usage)
    blocked = _over_limit(candidate.limits, candidate.consumed)
    if blocked:
        return _decision(
            BudgetDecisionCode.WOULD_EXCEED_BUDGET,
            state,
            blocked,
            "prospective usage would exceed configured budget",
            dispatch_allowed=False,
        )
    if candidate.exhausted_dimensions:
        return _decision(
            BudgetDecisionCode.BUDGET_EXHAUSTED,
            candidate,
            (),
            "budget limit reached exactly",
            dispatch_allowed=True,
        )
    return _decision(
        BudgetDecisionCode.WITHIN_BUDGET,
        candidate,
        (),
        "within budget",
        dispatch_allowed=True,
    )


def current_budget_decision(state: BudgetState) -> BudgetDecision:
    """Represent whether already-recorded usage has exhausted a configured budget."""

    state = _normalized_state(state)
    if state.exhausted_dimensions:
        return _decision(
            BudgetDecisionCode.BUDGET_EXHAUSTED,
            state,
            (),
            "configured budget exhausted",
            dispatch_allowed=False,
        )
    return _decision(
        BudgetDecisionCode.WITHIN_BUDGET,
        state,
        (),
        "within budget",
        dispatch_allowed=True,
    )


def _decision(
    code: BudgetDecisionCode,
    state: BudgetState,
    blocked_dimensions: tuple[BudgetDimension, ...],
    summary: str,
    *,
    dispatch_allowed: bool,
) -> BudgetDecision:
    exhausted = state.exhausted_dimensions
    stop = None
    lifecycle = None
    if code is not BudgetDecisionCode.WITHIN_BUDGET:
        lifecycle = LifecycleState.BUDGET_EXHAUSTED
        dimensions = blocked_dimensions or exhausted
        stop = StopReason(
            code=StopReasonCode.BUDGET_EXHAUSTED,
            summary=summary,
            evidence_refs=tuple(dimension.value for dimension in dimensions),
        )
    return BudgetDecision(
        code=code,
        state=state,
        exhausted_dimensions=exhausted,
        blocked_dimensions=blocked_dimensions,
        dispatch_allowed=dispatch_allowed,
        lifecycle_state=lifecycle,
        stop_reason=stop,
        summary=summary,
    )


def _as_int(value: int | float | None, name: str) -> int | None:
    if value is None:
        return None
    if type(value) is not int:
        raise StateValidationError(f"BudgetValues.{name} must remain an integer")
    return value


def _as_float(value: int | float | None, _name: str) -> float | None:
    if value is None:
        return None
    return float(value)


def _validate_dimensions(values: tuple[BudgetDimension, ...], name: str) -> None:
    if type(values) is not tuple:
        raise TypeError(f"BudgetDecision.{name} must be a tuple")
    if any(type(value) is not BudgetDimension for value in values):
        raise TypeError(f"BudgetDecision.{name} must contain BudgetDimension values")
    if len(set(values)) != len(values):
        raise StateValidationError(f"BudgetDecision.{name} must not contain duplicates")


def _validate_text(value: str, name: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{name} must be a string")
    if not value or value != value.strip() or len(value) > 2048:
        raise StateValidationError(f"{name} must be normalized non-empty text")
