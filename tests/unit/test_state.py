"""Unit tests for strict immutable runtime state and lifecycle contracts."""

from __future__ import annotations

import copy
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import pytest
import yaml
from jsonschema import Draft202012Validator, FormatChecker

import harness.state as state_module
from harness.state import (
    ACTIVE_STATES,
    FINAL_STATES,
    RESUMABLE_STOP_STATES,
    STOPPED_STATES,
    ApprovalStatus,
    BudgetDimension,
    BudgetState,
    BudgetValues,
    CompletionVerdict,
    DuplicateTransitionError,
    Event,
    EventType,
    Goal,
    InvalidTransitionError,
    LifecycleState,
    RedactionStatus,
    Run,
    StateValidationError,
    StopReason,
    StopReasonCode,
    Task,
    TaskStatus,
    TransitionError,
    can_transition,
    transition_run,
)

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 7, 20, 10, 0, tzinfo=UTC)


def load_yaml_object(relative_path: str) -> dict[str, Any]:
    loaded = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))
    assert type(loaded) is dict
    return cast(dict[str, Any], loaded)


def validate_schema(schema_name: str, instance: dict[str, object]) -> None:
    schema_value = json.loads((ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
    assert type(schema_value) is dict
    schema = cast(dict[str, object], schema_value)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(instance)


def budget_state(*, consumed_iterations: int = 0, iteration_limit: int = 4) -> BudgetState:
    exhausted = (BudgetDimension.ITERATIONS,) if consumed_iterations >= iteration_limit else ()
    return BudgetState(
        limits=BudgetValues(
            iterations=iteration_limit,
            elapsed_seconds=600.0,
            input_tokens=1000,
            output_tokens=1000,
            total_tokens=2000,
            cost=5.0,
        ),
        consumed=BudgetValues(
            iterations=consumed_iterations,
            elapsed_seconds=0.0,
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost=0.0,
        ),
        exhausted_dimensions=exhausted,
    )


def initial_run(
    *,
    lifecycle_state: LifecycleState = LifecycleState.CREATED,
    budget: BudgetState | None = None,
) -> Run:
    return Run(
        run_id="run.c401.001",
        goal_id="goal.c401",
        provider="codex",
        model="gpt-5.6-sol",
        reasoning_effort="high",
        provider_config_ref="config/runtime.json",
        lifecycle_state=lifecycle_state,
        started_at=NOW,
        updated_at=NOW,
        iteration_count=0,
        budget=budget if budget is not None else budget_state(),
        current_task_id="C-401",
        approval_state=None,
        checkpoint_ref=None,
        stop_reason=None,
        completion_verdict=CompletionVerdict.NOT_EVALUATED,
        completion_evidence_refs=(),
        event_seq=0,
        last_transition_id=None,
    )


def task_record(**changes: object) -> Task:
    base: dict[str, object] = {
        "task_id": "C-401",
        "goal_id": "goal.c401",
        "description": "Implement strict runtime state models.",
        "dependencies": ("C-304", "C-305", "C-306"),
        "status": TaskStatus.READY,
        "attempts": 0,
        "selected_workspace": "worktrees/c401",
        "allowed_paths": ("src/harness/state.py", "tests/unit/test_state.py"),
        "locked_paths": ("src/harness/config.py",),
        "criterion_ids": ("criterion.transitions", "criterion.roundtrip"),
        "validation_commands": ("uv run pytest -q tests/unit/test_state.py",),
        "evidence_paths": (),
        "last_failure": None,
        "next_action": None,
    }
    base.update(changes)
    return Task(**base)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "example_path",
    [
        "examples/specifications/goal_contract.example.yaml",
        "examples/specifications/local_implementation_goal.example.yaml",
    ],
)
def test_w205_goal_examples_round_trip_and_validate(example_path: str) -> None:
    goal = Goal.from_dict(load_yaml_object(example_path))

    assert type(goal.scope.in_scope) is tuple
    assert goal.created_at.tzinfo is UTC
    serialized = goal.to_dict()
    assert cast(str, serialized["created_at"]).endswith("Z")
    assert Goal.from_dict(serialized) == goal
    validate_schema("goal.schema.json", serialized)


def test_goal_rejects_unknown_keys_types_bool_as_int_and_bad_stable_id() -> None:
    payload = load_yaml_object("examples/specifications/goal_contract.example.yaml")

    unknown = copy.deepcopy(payload)
    unknown["unexpected"] = True
    with pytest.raises(StateValidationError, match="unknown keys"):
        Goal.from_dict(unknown)

    coerced = copy.deepcopy(payload)
    coerced["goal_id"] = 401
    with pytest.raises(TypeError, match="must be a string"):
        Goal.from_dict(coerced)

    bool_integer = copy.deepcopy(payload)
    bool_integer["budget"]["max_iterations"] = True
    with pytest.raises(TypeError, match="must be an integer"):
        Goal.from_dict(bool_integer)

    invalid_id = copy.deepcopy(payload)
    invalid_id["goal_id"] = "-invalid"
    with pytest.raises(StateValidationError, match="must match"):
        Goal.from_dict(invalid_id)


def test_goal_rejects_duplicate_and_unresolved_or_asymmetric_cross_references() -> None:
    payload = load_yaml_object("examples/specifications/goal_contract.example.yaml")

    duplicate = copy.deepcopy(payload)
    duplicate["scope"]["in_scope"].append(duplicate["scope"]["in_scope"][0])
    with pytest.raises(StateValidationError, match="duplicate"):
        Goal.from_dict(duplicate)

    unresolved = copy.deepcopy(payload)
    unresolved["done_conditions"][0]["output_ids"] = ["missing.output"]
    with pytest.raises(StateValidationError, match="missing outputs"):
        Goal.from_dict(unresolved)

    asymmetric = copy.deepcopy(payload)
    asymmetric["done_conditions"][0]["output_ids"] = []
    with pytest.raises(StateValidationError, match="must be reciprocal"):
        Goal.from_dict(asymmetric)


def test_goal_rejects_naive_datetime_and_mutable_collection() -> None:
    goal = Goal.from_dict(
        load_yaml_object("examples/specifications/local_implementation_goal.example.yaml")
    )

    with pytest.raises(StateValidationError, match="timezone-aware"):
        replace(goal, created_at=datetime(2026, 7, 20, 10, 0))
    with pytest.raises(TypeError, match="must be a tuple"):
        replace(goal.scope, in_scope=["mutable"])  # type: ignore[arg-type]


def test_task_round_trip_schema_and_status_invariants() -> None:
    task = task_record()
    serialized = task.to_dict()

    assert Task.from_dict(serialized) == task
    validate_schema("task.schema.json", serialized)

    with pytest.raises(StateValidationError, match="requires evidence_paths"):
        task_record(status=TaskStatus.COMPLETE)
    with pytest.raises(StateValidationError, match="cannot have next_action"):
        task_record(
            status=TaskStatus.COMPLETE,
            evidence_paths=("evidence/result.json",),
            next_action="Do more work.",
        )
    with pytest.raises(StateValidationError, match="requires next_action"):
        task_record(status=TaskStatus.BLOCKED)
    with pytest.raises(StateValidationError, match="requires next_action"):
        task_record(status=TaskStatus.APPROVAL_REQUIRED)
    with pytest.raises(StateValidationError, match="requires last_failure"):
        task_record(status=TaskStatus.FAILED)


def test_task_rejects_unknown_keys_bool_attempts_duplicates_and_self_dependency() -> None:
    payload = task_record().to_dict()
    payload["extra"] = "rejected"
    with pytest.raises(StateValidationError, match="unknown keys"):
        Task.from_dict(payload)

    payload = task_record().to_dict()
    payload["attempts"] = True
    with pytest.raises(TypeError, match="integer"):
        Task.from_dict(payload)

    with pytest.raises(StateValidationError, match="duplicate"):
        task_record(allowed_paths=("src/harness/state.py", "src/harness/state.py"))
    with pytest.raises(StateValidationError, match="depend on itself"):
        task_record(dependencies=("C-401",))


def test_core_records_are_frozen_slotted_and_keyword_only() -> None:
    model_types: tuple[Any, ...] = tuple(
        value
        for value in vars(state_module).values()
        if isinstance(value, type)
        and value.__module__ == state_module.__name__
        and is_dataclass(value)
    )
    assert len(model_types) == 23
    for model_type in model_types:
        assert model_type.__dataclass_params__.frozen
        assert "__dict__" not in model_type.__slots__
        assert all(model_field.kw_only for model_field in fields(model_type))

    task = task_record()
    with pytest.raises(FrozenInstanceError):
        task.status = TaskStatus.COMPLETE  # type: ignore[misc]
    with pytest.raises(TypeError):
        Task("C-401")  # type: ignore[call-arg,misc]


def test_budget_values_are_strict_and_exhaustion_is_consistent() -> None:
    state = budget_state(consumed_iterations=4)
    assert state.exhausted_dimensions == (BudgetDimension.ITERATIONS,)
    assert BudgetState.from_dict(state.to_dict()) == state

    with pytest.raises(TypeError, match="does not match"):
        BudgetValues(elapsed_seconds=1)
    with pytest.raises(TypeError, match="does not match"):
        BudgetValues(iterations=True)
    with pytest.raises(StateValidationError, match="inconsistent"):
        BudgetState(
            limits=state.limits,
            consumed=state.consumed,
            exhausted_dimensions=(),
        )
    with pytest.raises(StateValidationError, match="inconsistent"):
        BudgetState(
            limits=budget_state().limits,
            consumed=budget_state().consumed,
            exhausted_dimensions=(BudgetDimension.COST,),
        )


def test_run_round_trip_schema_and_utc_serialization() -> None:
    run = initial_run()
    serialized = run.to_dict()

    assert serialized["started_at"] == "2026-07-20T10:00:00Z"
    assert Run.from_dict(serialized) == run
    validate_schema("run-state.schema.json", serialized)


def test_run_terminal_and_stop_reason_invariants() -> None:
    completed_reason = StopReason(
        code=StopReasonCode.COMPLETED,
        summary="All mandatory conditions passed.",
        evidence_refs=("evidence/completion.json",),
    )
    completed = replace(
        initial_run(lifecycle_state=LifecycleState.CHECKPOINTING),
        lifecycle_state=LifecycleState.COMPLETED,
        stop_reason=completed_reason,
        completion_verdict=CompletionVerdict.PASS,
        completion_evidence_refs=("evidence/completion.json",),
        checkpoint_ref="checkpoints/cp-1.json",
        event_seq=1,
        last_transition_id="transition.complete.1",
    )
    validate_schema("run-state.schema.json", completed.to_dict())

    with pytest.raises(StateValidationError, match="requires PASS"):
        replace(completed, completion_verdict=CompletionVerdict.FAIL)
    with pytest.raises(StateValidationError, match="requires completion evidence"):
        replace(completed, completion_evidence_refs=())
    with pytest.raises(StateValidationError, match="requires checkpoint_ref"):
        replace(completed, checkpoint_ref=None)
    with pytest.raises(StateValidationError, match="only a COMPLETED"):
        replace(initial_run(), completion_verdict=CompletionVerdict.PASS)
    with pytest.raises(StateValidationError, match="does not allow stop code"):
        replace(completed, stop_reason=replace(completed_reason, code=StopReasonCode.FAILED))
    with pytest.raises(StateValidationError, match="requires stop_reason"):
        replace(initial_run(), lifecycle_state=LifecycleState.BLOCKED)


def test_run_approval_budget_and_transition_sequence_invariants() -> None:
    approval_reason = StopReason(
        code=StopReasonCode.APPROVAL_REQUIRED,
        summary="Approval is required.",
    )
    with pytest.raises(StateValidationError, match="needs REQUIRED or REQUESTED"):
        replace(
            initial_run(),
            lifecycle_state=LifecycleState.APPROVAL_REQUIRED,
            stop_reason=approval_reason,
        )
    pending_approval = replace(
        initial_run(),
        lifecycle_state=LifecycleState.APPROVAL_REQUIRED,
        stop_reason=approval_reason,
        approval_state=ApprovalStatus.REQUIRED,
    )
    validate_schema("run-state.schema.json", pending_approval.to_dict())

    for approval_status in ApprovalStatus:
        with pytest.raises(StateValidationError, match="only an APPROVAL_REQUIRED"):
            replace(initial_run(), approval_state=approval_status)

    resolved_payload = initial_run().to_dict()
    resolved_payload["approval_state"] = ApprovalStatus.GRANTED.value
    with pytest.raises(StateValidationError, match="only an APPROVAL_REQUIRED"):
        Run.from_dict(resolved_payload)
    assert list(
        Draft202012Validator(
            json.loads((ROOT / "schemas" / "run-state.schema.json").read_text(encoding="utf-8"))
        ).iter_errors(resolved_payload)
    )

    exhausted_reason = StopReason(
        code=StopReasonCode.BUDGET_EXHAUSTED,
        summary="Iteration budget is exhausted.",
    )
    with pytest.raises(StateValidationError, match="exhausted budget dimension"):
        replace(
            initial_run(),
            lifecycle_state=LifecycleState.BUDGET_EXHAUSTED,
            stop_reason=exhausted_reason,
        )
    with pytest.raises(StateValidationError, match="positive event_seq"):
        replace(initial_run(), last_transition_id="transition.1")


def expected_edges() -> set[tuple[LifecycleState, LifecycleState]]:
    ordinary = {
        (LifecycleState.CREATED, LifecycleState.INITIALIZING),
        (LifecycleState.INITIALIZING, LifecycleState.READY),
        (LifecycleState.READY, LifecycleState.SELECTING_TASK),
        (LifecycleState.SELECTING_TASK, LifecycleState.EXECUTING),
        (LifecycleState.EXECUTING, LifecycleState.VALIDATING),
        (LifecycleState.VALIDATING, LifecycleState.EVALUATING),
        (LifecycleState.VALIDATING, LifecycleState.CHECKPOINTING),
        (LifecycleState.EVALUATING, LifecycleState.CHECKPOINTING),
        (LifecycleState.CHECKPOINTING, LifecycleState.READY),
        (LifecycleState.CHECKPOINTING, LifecycleState.COMPLETED),
    }
    interruptions = {
        (prior, stopped)
        for prior in ACTIVE_STATES
        for stopped in (
            LifecycleState.BLOCKED,
            LifecycleState.BUDGET_EXHAUSTED,
            LifecycleState.APPROVAL_REQUIRED,
            LifecycleState.FAILED,
            LifecycleState.CANCELLED,
        )
    }
    return ordinary | interruptions


def test_lifecycle_edges_are_exact_and_stopped_states_have_no_outbound_edges() -> None:
    allowed = expected_edges()
    for prior in LifecycleState:
        for next_state in LifecycleState:
            assert can_transition(prior, next_state) is ((prior, next_state) in allowed)

    assert FINAL_STATES == {
        LifecycleState.COMPLETED,
        LifecycleState.FAILED,
        LifecycleState.CANCELLED,
    }
    assert RESUMABLE_STOP_STATES == {
        LifecycleState.BLOCKED,
        LifecycleState.BUDGET_EXHAUSTED,
        LifecycleState.APPROVAL_REQUIRED,
    }
    assert STOPPED_STATES == FINAL_STATES | RESUMABLE_STOP_STATES
    assert can_transition("CREATED", LifecycleState.INITIALIZING) is False  # type: ignore[arg-type]


def test_transition_run_returns_one_new_immutable_run_event_pair() -> None:
    original = initial_run()
    updated, event = transition_run(
        original,
        LifecycleState.INITIALIZING,
        transition_id="transition.1",
        timestamp=NOW + timedelta(seconds=1),
        reason="Initialize the bounded run.",
        correlation_id="correlation.1",
    )

    assert original.lifecycle_state is LifecycleState.CREATED
    assert original.event_seq == 0
    assert updated is not original
    assert updated.lifecycle_state is LifecycleState.INITIALIZING
    assert updated.event_seq == 1
    assert updated.last_transition_id == "transition.1"
    assert event.event_seq == updated.event_seq
    assert event.event_type is EventType.LIFECYCLE
    assert event.prior_state is LifecycleState.CREATED
    assert event.next_state is LifecycleState.INITIALIZING
    assert event.transition_id == updated.last_transition_id
    assert Event.from_dict(event.to_dict()) == event
    with pytest.raises(FrozenInstanceError):
        updated.event_seq = 2  # type: ignore[misc]


def test_transition_run_uses_typed_invalid_and_duplicate_errors() -> None:
    run = initial_run()
    with pytest.raises(InvalidTransitionError, match="CREATED -> READY"):
        transition_run(
            run,
            LifecycleState.READY,
            transition_id="transition.invalid",
            timestamp=NOW + timedelta(seconds=1),
            reason="Skip initialization.",
        )

    updated, _ = transition_run(
        run,
        LifecycleState.INITIALIZING,
        transition_id="transition.duplicate",
        timestamp=NOW + timedelta(seconds=1),
        reason="Initialize.",
    )
    with pytest.raises(DuplicateTransitionError, match="already"):
        transition_run(
            updated,
            LifecycleState.READY,
            transition_id="transition.duplicate",
            timestamp=NOW + timedelta(seconds=2),
            reason="Ready the run.",
        )

    later_snapshot = replace(run, updated_at=NOW + timedelta(seconds=10))
    with pytest.raises(TransitionError, match="must not precede Run.updated_at"):
        transition_run(
            later_snapshot,
            LifecycleState.INITIALIZING,
            transition_id="transition.backward-time",
            timestamp=NOW + timedelta(seconds=5),
            reason="Reject a timestamp regression.",
        )


@pytest.mark.parametrize(
    "code",
    [
        StopReasonCode.BLOCKED,
        StopReasonCode.MISSING_DEPENDENCY,
        StopReasonCode.REPOSITORY_DIVERGENCE,
        StopReasonCode.UNSAFE_ACTION,
        StopReasonCode.REPEATED_NO_PROGRESS,
        StopReasonCode.REPEATED_INSUFFICIENT_EVIDENCE,
    ],
)
def test_blocked_transition_accepts_only_structured_block_codes(code: StopReasonCode) -> None:
    updated, event = transition_run(
        initial_run(),
        LifecycleState.BLOCKED,
        transition_id=f"transition.{code.value.lower()}",
        timestamp=NOW + timedelta(seconds=1),
        reason="The run cannot safely continue.",
        stop_reason=StopReason(
            code=code,
            summary="The run cannot safely continue.",
            evidence_refs=("evidence/blocker.json",),
        ),
    )

    assert updated.lifecycle_state is LifecycleState.BLOCKED
    assert event.event_type is EventType.TERMINAL
    assert event.evidence_refs == ("evidence/blocker.json",)
    assert all(not can_transition(updated.lifecycle_state, state) for state in LifecycleState)
    with pytest.raises(InvalidTransitionError):
        transition_run(
            updated,
            LifecycleState.READY,
            transition_id="transition.resume-not-yet-supported",
            timestamp=NOW + timedelta(seconds=2),
            reason="Resume without a recovery contract.",
        )


def test_stopped_transition_rejects_missing_or_mismatched_stop_reason() -> None:
    with pytest.raises(TransitionError, match="requires stop_reason"):
        transition_run(
            initial_run(),
            LifecycleState.FAILED,
            transition_id="transition.failed",
            timestamp=NOW + timedelta(seconds=1),
            reason="The run failed.",
        )
    with pytest.raises(TransitionError, match="does not allow stop code"):
        transition_run(
            initial_run(),
            LifecycleState.CANCELLED,
            transition_id="transition.cancelled",
            timestamp=NOW + timedelta(seconds=1),
            reason="The run was cancelled.",
            stop_reason=StopReason(
                code=StopReasonCode.FAILED,
                summary="Wrong structured reason.",
            ),
        )


def test_completed_transition_atomically_sets_terminal_contract() -> None:
    checkpointing = initial_run(lifecycle_state=LifecycleState.CHECKPOINTING)
    updated, event = transition_run(
        checkpointing,
        LifecycleState.COMPLETED,
        transition_id="transition.completed",
        timestamp=NOW + timedelta(seconds=1),
        reason="All mandatory conditions passed.",
        stop_reason=StopReason(
            code=StopReasonCode.COMPLETED,
            summary="All mandatory conditions passed.",
            evidence_refs=("evidence/completion.json",),
        ),
        completion_verdict=CompletionVerdict.PASS,
        completion_evidence_refs=("evidence/completion.json",),
        checkpoint_ref="checkpoints/cp-final.json",
    )

    assert updated.lifecycle_state is LifecycleState.COMPLETED
    assert updated.completion_verdict is CompletionVerdict.PASS
    assert updated.checkpoint_ref == "checkpoints/cp-final.json"
    assert event.event_type is EventType.TERMINAL
    validate_schema("run-state.schema.json", updated.to_dict())
    validate_schema("event.schema.json", event.to_dict())


@pytest.mark.parametrize(
    ("verdict", "evidence", "checkpoint", "expected"),
    [
        (CompletionVerdict.NOT_EVALUATED, ("evidence/result.json",), "cp.json", "PASS"),
        (CompletionVerdict.PASS, (), "cp.json", "completion evidence"),
        (CompletionVerdict.PASS, ("evidence/result.json",), None, "checkpoint_ref"),
    ],
)
def test_completed_transition_rejects_incomplete_terminal_contract(
    verdict: CompletionVerdict,
    evidence: tuple[str, ...],
    checkpoint: str | None,
    expected: str,
) -> None:
    with pytest.raises(TransitionError, match=expected):
        transition_run(
            initial_run(lifecycle_state=LifecycleState.CHECKPOINTING),
            LifecycleState.COMPLETED,
            transition_id="transition.incomplete",
            timestamp=NOW + timedelta(seconds=1),
            reason="Attempt incomplete completion.",
            stop_reason=StopReason(
                code=StopReasonCode.COMPLETED,
                summary="Attempt incomplete completion.",
            ),
            completion_verdict=verdict,
            completion_evidence_refs=evidence,
            checkpoint_ref=checkpoint,
        )


def test_approval_and_budget_stop_transitions_enforce_matching_state() -> None:
    approval_run, _ = transition_run(
        initial_run(),
        LifecycleState.APPROVAL_REQUIRED,
        transition_id="transition.approval",
        timestamp=NOW + timedelta(seconds=1),
        reason="A consequential action needs approval.",
        stop_reason=StopReason(
            code=StopReasonCode.APPROVAL_REQUIRED,
            summary="A consequential action needs approval.",
        ),
        approval_state=ApprovalStatus.REQUESTED,
    )
    assert approval_run.approval_state is ApprovalStatus.REQUESTED

    budget_run, _ = transition_run(
        initial_run(budget=budget_state(consumed_iterations=4)),
        LifecycleState.BUDGET_EXHAUSTED,
        transition_id="transition.budget",
        timestamp=NOW + timedelta(seconds=1),
        reason="The iteration budget is exhausted.",
        stop_reason=StopReason(
            code=StopReasonCode.BUDGET_EXHAUSTED,
            summary="The iteration budget is exhausted.",
        ),
    )
    assert budget_run.budget.exhausted_dimensions == (BudgetDimension.ITERATIONS,)


def test_generic_event_requires_null_transition_metadata_and_round_trips() -> None:
    event = Event(
        event_seq=1,
        timestamp=NOW,
        run_id="run.c401.001",
        task_id="C-401",
        event_type=EventType.ACTION,
        source="adapter.normalized",
        action_summary="Inspect repository state.",
        input_refs=("inputs/goal.json",),
        output_refs=("outputs/status.json",),
        evidence_refs=(),
        result="SUCCEEDED",
        error_category=None,
        redaction_status=RedactionStatus.NOT_REQUIRED,
        transition_id=None,
        prior_state=None,
        next_state=None,
        reason=None,
        correlation_id="correlation.action.1",
    )
    serialized = event.to_dict()

    assert serialized["transition_id"] is None
    assert serialized["prior_state"] is None
    assert serialized["next_state"] is None
    assert serialized["reason"] is None
    assert Event.from_dict(serialized) == event
    validate_schema("event.schema.json", serialized)


def test_event_transition_metadata_and_normalized_strings_are_strict() -> None:
    generic = Event(
        event_seq=1,
        timestamp=NOW,
        run_id="run.c401.001",
        task_id=None,
        event_type=EventType.ACTION,
        source="harness",
        action_summary="Record action.",
        input_refs=(),
        output_refs=(),
        evidence_refs=(),
        result="SUCCEEDED",
        error_category=None,
        redaction_status=RedactionStatus.NOT_REQUIRED,
        transition_id=None,
        prior_state=None,
        next_state=None,
        reason=None,
        correlation_id=None,
    )
    with pytest.raises(StateValidationError, match="null transition metadata"):
        replace(
            generic,
            transition_id="transition.1",
            prior_state=LifecycleState.CREATED,
            next_state=LifecycleState.INITIALIZING,
            reason="Initialize.",
        )
    with pytest.raises(StateValidationError, match="requires complete"):
        replace(generic, event_type=EventType.TERMINAL)
    with pytest.raises(StateValidationError, match="stopped lifecycle"):
        replace(
            generic,
            event_type=EventType.TERMINAL,
            transition_id="transition.1",
            prior_state=LifecycleState.CREATED,
            next_state=LifecycleState.INITIALIZING,
            reason="Initialize.",
        )
    with pytest.raises(StateValidationError, match="normalized"):
        replace(generic, source=" harness ")
    with pytest.raises(StateValidationError, match="normalized"):
        replace(generic, result="FAILED\nDETAIL")


def test_from_dict_rejects_naive_or_non_rfc3339_timestamps() -> None:
    payload = initial_run().to_dict()
    payload["started_at"] = "2026-07-20T10:00:00"
    with pytest.raises(StateValidationError, match="offset or Z"):
        Run.from_dict(payload)

    payload = initial_run().to_dict()
    payload["event_seq"] = False
    with pytest.raises(TypeError, match="integer"):
        Run.from_dict(payload)
