from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest

from harness.evaluation import (
    CorrectionOwner,
    EvaluationBudgetUsage,
    EvaluationContractError,
    EvaluationCorrection,
    EvaluationCriterion,
    EvaluationCriterionResult,
    EvaluationProtocolError,
    EvaluationRequest,
    EvaluatorIdentity,
    ModelEvaluationResult,
    OptionalModelEvaluator,
)
from harness.state import (
    CompletionVerdict,
    EvaluatorAccess,
    LocationKind,
    LocationReference,
)
from harness.validation import (
    ValidationBatchResult,
    ValidationEvidence,
    ValidationFailureKind,
)

BASE_TIME = datetime(2026, 7, 21, 17, 0, tzinfo=UTC)


class RecordingEvaluator:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls: list[EvaluationRequest] = []

    def evaluate(self, *, request: EvaluationRequest) -> object:
        self.calls.append(request)
        return self.result


def location(
    kind: LocationKind,
    ref: str,
    description: str,
) -> LocationReference:
    return LocationReference(kind=kind, ref=ref, description=description)


def deterministic_batch(verdict: CompletionVerdict) -> ValidationBatchResult:
    if verdict is CompletionVerdict.PASS:
        exit_code = 0
        failure_kind = None
    elif verdict is CompletionVerdict.FAIL:
        exit_code = 2
        failure_kind = ValidationFailureKind.NONZERO_EXIT
    elif verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE:
        exit_code = None
        failure_kind = ValidationFailureKind.TIMEOUT
    else:
        raise AssertionError("test fixture requires an evidence verdict")
    evidence = ValidationEvidence(
        validator_id="validator.c408.deterministic",
        run_id="run.c408.001",
        task_id="C-408",
        criterion_ids=("criterion.c408.deterministic",),
        command="uv run pytest -q",
        working_directory=r"C:\workspace",
        runtime_identity="python-test-runtime",
        started_at=BASE_TIME,
        finished_at=BASE_TIME + timedelta(milliseconds=1),
        verdict=verdict,
        exit_code=exit_code,
        failure_kind=failure_kind,
        summary="Structured deterministic evidence",
        stdout_ref=location(
            LocationKind.ARTIFACT_PATH,
            "artifacts/validation/run.c408.001/stdout",
            "Captured deterministic stdout",
        ),
        stderr_ref=location(
            LocationKind.ARTIFACT_PATH,
            "artifacts/validation/run.c408.001/stderr",
            "Captured deterministic stderr",
        ),
        record_ref=location(
            LocationKind.COMMAND_RESULT,
            "artifacts/validation/run.c408.001/result.json",
            "Structured deterministic result",
        ),
    )
    return ValidationBatchResult(
        run_id="run.c408.001",
        task_id="C-408",
        records=(evidence,),
        overall_verdict=verdict,
    )


def semantic_criterion(
    criterion_id: str = "criterion.c408.semantic",
    statement: str = "The artifact faithfully explains the accepted design intent.",
) -> EvaluationCriterion:
    return EvaluationCriterion(
        criterion_id=criterion_id,
        statement=statement,
        mandatory=True,
        release_blocking=True,
    )


def evaluation_request(
    batch: ValidationBatchResult,
    *,
    criteria: tuple[EvaluationCriterion, ...] | None = None,
    deterministic_results: tuple[LocationReference, ...] | None = None,
) -> EvaluationRequest:
    return EvaluationRequest(
        request_id="VR-C-408-001",
        contract_version="1.0.0",
        goal_id="goal.c408",
        task_id="C-408",
        goal_contract_ref=location(
            LocationKind.REPOSITORY_PATH,
            "docs/work/GENERATOR_VERIFIER_PROTOCOL.md",
            "Frozen generator verifier contract",
        ),
        assigned_criteria=criteria or (semantic_criterion(),),
        authoritative_inputs=(
            location(
                LocationKind.REPOSITORY_PATH,
                "docs/architecture/ADR-001-harness-boundary.md",
                "Accepted architecture boundary",
            ),
        ),
        artifact_refs=(
            location(
                LocationKind.REPOSITORY_PATH,
                "docs/design.md",
                "Actual artifact for semantic inspection",
            ),
        ),
        deterministic_results=(
            deterministic_results
            if deterministic_results is not None
            else tuple(record.record_ref for record in batch.records)
        ),
        scope_in=("Judge only fidelity to the frozen accepted design intent.",),
        scope_out=("Do not add requirements, write files, or waive deterministic evidence.",),
        known_evidence_limits=(),
    )


def correction(request: EvaluationRequest) -> EvaluationCorrection:
    return EvaluationCorrection(
        action="Correct only the cited semantic mismatch.",
        owner=CorrectionOwner.GENERATOR,
        target_refs=request.artifact_refs,
        verification="Re-evaluate the same frozen criterion against the corrected artifact.",
    )


def criterion_result(
    request: EvaluationRequest,
    verdict: CompletionVerdict,
    *,
    criterion: EvaluationCriterion | None = None,
    evidence_refs: tuple[LocationReference, ...] | None = None,
    actual_statement: str | None = None,
) -> EvaluationCriterionResult:
    frozen = criterion or request.assigned_criteria[0]
    if verdict is CompletionVerdict.PASS:
        evidence = request.artifact_refs if evidence_refs is None else evidence_refs
        missing: tuple[str, ...] = ()
        smallest = None
        blocking = False
    elif verdict is CompletionVerdict.FAIL:
        evidence = request.artifact_refs if evidence_refs is None else evidence_refs
        missing = ()
        smallest = correction(request)
        blocking = frozen.release_blocking
    elif verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE:
        evidence = () if evidence_refs is None else evidence_refs
        missing = ("The cited artifact could not be inspected.",)
        smallest = correction(request)
        blocking = frozen.release_blocking
    else:
        raise AssertionError("test fixture requires an evidence verdict")
    return EvaluationCriterionResult(
        criterion_id=frozen.criterion_id,
        statement=actual_statement or frozen.statement,
        mandatory=frozen.mandatory,
        verdict=verdict,
        evidence_refs=evidence,
        missing_evidence=missing,
        smallest_correction=smallest,
        release_blocking=blocking,
    )


def model_result(
    request: EvaluationRequest,
    verdict: CompletionVerdict,
    *,
    criteria: tuple[EvaluationCriterionResult, ...] | None = None,
    actual_artifact_inspection: bool | None = None,
    goal_id: str | None = None,
) -> ModelEvaluationResult:
    results = criteria or (criterion_result(request, verdict),)
    missing = tuple(
        dict.fromkeys(item for item_result in results for item in item_result.missing_evidence)
    )
    smallest = None if verdict is CompletionVerdict.PASS else correction(request)
    inspected = (
        verdict is not CompletionVerdict.INSUFFICIENT_EVIDENCE
        if actual_artifact_inspection is None
        else actual_artifact_inspection
    )
    return ModelEvaluationResult(
        result_id="ER-C-408-001",
        goal_id=goal_id or request.goal_id,
        task_id=request.task_id,
        evaluator=EvaluatorIdentity(
            evaluator_id="evaluator.c408.fake",
            runtime_identity="fake-model-test-double",
            actual_artifact_inspection=inspected,
        ),
        goal_contract_ref=request.goal_contract_ref,
        artifact_refs=request.artifact_refs,
        criteria=results,
        overall_verdict=verdict,
        release_blocking=any(item.release_blocking for item in results),
        smallest_correction=smallest,
        insufficient_evidence=missing,
        evaluated_at=BASE_TIME + timedelta(seconds=1),
        budget_usage=EvaluationBudgetUsage(
            elapsed_seconds=0.25,
            input_tokens=100,
            output_tokens=20,
        ),
    )


def test_request_and_identity_are_immutable_and_read_only() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    request = evaluation_request(batch)

    with pytest.raises(FrozenInstanceError):
        request.__setattr__("scope_in", ("Expanded scope",))
    with pytest.raises(ValueError, match="READ_ONLY"):
        EvaluatorIdentity(
            evaluator_id="evaluator.c408.invalid",
            runtime_identity=None,
            actual_artifact_inspection=False,
            access_mode=EvaluatorAccess.NOT_APPLICABLE,
        )
    with pytest.raises(ValueError, match="MODEL_EVALUATOR"):
        EvaluatorIdentity(
            evaluator_id="evaluator.c408.invalid-kind",
            runtime_identity=None,
            actual_artifact_inspection=False,
            kind="HUMAN_REVIEWER",
        )
    with pytest.raises(ValueError, match="exactly when mandatory"):
        EvaluationCriterion(
            criterion_id="criterion.invalid",
            statement="Invalid blocking declaration.",
            mandatory=True,
            release_blocking=False,
        )


def test_request_rejects_nonmandatory_semantic_criteria() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    nonmandatory = replace(
        semantic_criterion(),
        mandatory=False,
        release_blocking=False,
    )

    with pytest.raises(ValueError, match="must be mandatory"):
        evaluation_request(batch, criteria=(nonmandatory,))


def test_deterministic_pass_without_semantic_request_suppresses_evaluator() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    evaluator = RecordingEvaluator(object())

    outcome = OptionalModelEvaluator(evaluator=evaluator).evaluate_if_needed(
        deterministic_result=batch
    )

    assert outcome.overall_verdict is CompletionVerdict.PASS
    assert not outcome.evaluator_invoked
    assert outcome.model_result is None
    assert evaluator.calls == []


def test_deterministic_fail_cannot_be_overridden_and_suppresses_evaluator() -> None:
    failed = deterministic_batch(CompletionVerdict.FAIL)
    request = evaluation_request(failed)
    scripted_pass = model_result(request, CompletionVerdict.PASS)
    evaluator = RecordingEvaluator(scripted_pass)

    outcome = OptionalModelEvaluator(evaluator=evaluator).evaluate_if_needed(
        deterministic_result=failed,
        request=request,
    )

    assert outcome.overall_verdict is CompletionVerdict.FAIL
    assert not outcome.evaluator_invoked
    assert outcome.model_result is None
    assert evaluator.calls == []


def test_deterministic_evidence_gap_is_not_waived_by_model_evaluation() -> None:
    incomplete = deterministic_batch(CompletionVerdict.INSUFFICIENT_EVIDENCE)
    request = evaluation_request(incomplete)
    evaluator = RecordingEvaluator(model_result(request, CompletionVerdict.PASS))

    outcome = OptionalModelEvaluator(evaluator=evaluator).evaluate_if_needed(
        deterministic_result=incomplete,
        request=request,
    )

    assert outcome.overall_verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE
    assert not outcome.evaluator_invoked
    assert evaluator.calls == []


@pytest.mark.parametrize(
    "verdict",
    [
        CompletionVerdict.PASS,
        CompletionVerdict.FAIL,
        CompletionVerdict.INSUFFICIENT_EVIDENCE,
    ],
)
def test_explicit_semantic_request_preserves_all_three_model_verdicts(
    verdict: CompletionVerdict,
) -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    request = evaluation_request(batch)
    returned = model_result(request, verdict)
    evaluator = RecordingEvaluator(returned)

    outcome = OptionalModelEvaluator(evaluator=evaluator).evaluate_if_needed(
        deterministic_result=batch,
        request=request,
    )

    assert outcome.evaluator_invoked
    assert outcome.overall_verdict is verdict
    assert outcome.model_result is returned
    assert evaluator.calls == [request]


def test_fail_precedes_insufficient_evidence_in_model_aggregation() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    criteria = (
        semantic_criterion("criterion.c408.fail", "The artifact satisfies semantic rule A."),
        semantic_criterion(
            "criterion.c408.incomplete",
            "The artifact satisfies semantic rule B.",
        ),
    )
    request = evaluation_request(batch, criteria=criteria)
    judged = (
        criterion_result(request, CompletionVerdict.FAIL, criterion=criteria[0]),
        criterion_result(
            request,
            CompletionVerdict.INSUFFICIENT_EVIDENCE,
            criterion=criteria[1],
        ),
    )
    returned = model_result(request, CompletionVerdict.FAIL, criteria=judged)

    outcome = OptionalModelEvaluator(evaluator=RecordingEvaluator(returned)).evaluate_if_needed(
        deterministic_result=batch, request=request
    )

    assert outcome.overall_verdict is CompletionVerdict.FAIL
    assert returned.insufficient_evidence == ("The cited artifact could not be inspected.",)


def test_rewritten_criterion_is_rejected() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    request = evaluation_request(batch)
    rewritten = criterion_result(
        request,
        CompletionVerdict.PASS,
        actual_statement="A rewritten and expanded acceptance criterion.",
    )
    evaluator = RecordingEvaluator(
        model_result(request, CompletionVerdict.PASS, criteria=(rewritten,))
    )

    with pytest.raises(EvaluationProtocolError, match="rewrote"):
        OptionalModelEvaluator(evaluator=evaluator).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )


def test_added_or_reordered_criteria_are_rejected() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    criteria = (
        semantic_criterion("criterion.c408.first", "Judge only the first semantic rule."),
        semantic_criterion("criterion.c408.second", "Judge only the second semantic rule."),
    )
    request = evaluation_request(batch, criteria=criteria)
    reversed_results = (
        criterion_result(request, CompletionVerdict.PASS, criterion=criteria[1]),
        criterion_result(request, CompletionVerdict.PASS, criterion=criteria[0]),
    )
    evaluator = RecordingEvaluator(
        model_result(request, CompletionVerdict.PASS, criteria=reversed_results)
    )

    with pytest.raises(EvaluationProtocolError, match="reordered"):
        OptionalModelEvaluator(evaluator=evaluator).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )


def test_evidence_and_correction_references_cannot_expand_request_scope() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    request = evaluation_request(batch)
    outside = location(
        LocationKind.EXTERNAL_RESOURCE,
        "unprovided-external-resource",
        "Reference not supplied to the evaluator",
    )
    expanded = criterion_result(
        request,
        CompletionVerdict.PASS,
        evidence_refs=(outside,),
    )
    evaluator = RecordingEvaluator(
        model_result(request, CompletionVerdict.PASS, criteria=(expanded,))
    )

    with pytest.raises(EvaluationProtocolError, match="expanded"):
        OptionalModelEvaluator(evaluator=evaluator).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )

    contract_correction = replace(
        correction(request),
        target_refs=(request.goal_contract_ref,),
    )
    failed = replace(
        criterion_result(request, CompletionVerdict.FAIL),
        smallest_correction=contract_correction,
    )
    changed_contract = model_result(
        request,
        CompletionVerdict.FAIL,
        criteria=(failed,),
    )
    with pytest.raises(EvaluationProtocolError, match="correction expanded"):
        OptionalModelEvaluator(evaluator=RecordingEvaluator(changed_contract)).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )


def test_request_must_bind_exact_deterministic_result_references() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    wrong_ref = location(
        LocationKind.COMMAND_RESULT,
        "artifacts/validation/other/result.json",
        "Wrong deterministic result",
    )
    request = evaluation_request(batch, deterministic_results=(wrong_ref,))
    evaluator = RecordingEvaluator(model_result(request, CompletionVerdict.PASS))

    with pytest.raises(EvaluationContractError, match="exactly match"):
        OptionalModelEvaluator(evaluator=evaluator).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )

    assert evaluator.calls == []


def test_malformed_result_and_changed_identity_are_rejected() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    request = evaluation_request(batch)

    with pytest.raises(EvaluationProtocolError, match="malformed"):
        OptionalModelEvaluator(
            evaluator=RecordingEvaluator({"overall_verdict": "PASS"})
        ).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )

    changed_goal = model_result(
        request,
        CompletionVerdict.PASS,
        goal_id="goal.changed",
    )
    with pytest.raises(EvaluationProtocolError, match="goal or task"):
        OptionalModelEvaluator(evaluator=RecordingEvaluator(changed_goal)).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )


def test_pass_or_fail_requires_actual_artifact_inspection() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    request = evaluation_request(batch)
    uninspected = model_result(
        request,
        CompletionVerdict.PASS,
        actual_artifact_inspection=False,
    )

    with pytest.raises(EvaluationProtocolError, match="actual artifact inspection"):
        OptionalModelEvaluator(evaluator=RecordingEvaluator(uninspected)).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )


def test_mixed_insufficient_result_with_pass_requires_artifact_inspection() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    criteria = (
        semantic_criterion(
            "criterion.c408.inspected-pass",
            "The available artifact satisfies the first semantic rule.",
        ),
        semantic_criterion(
            "criterion.c408.missing",
            "The unavailable artifact satisfies the second semantic rule.",
        ),
    )
    request = evaluation_request(batch, criteria=criteria)
    judged = (
        criterion_result(request, CompletionVerdict.PASS, criterion=criteria[0]),
        criterion_result(
            request,
            CompletionVerdict.INSUFFICIENT_EVIDENCE,
            criterion=criteria[1],
        ),
    )
    uninspected = model_result(
        request,
        CompletionVerdict.INSUFFICIENT_EVIDENCE,
        criteria=judged,
        actual_artifact_inspection=False,
    )

    with pytest.raises(EvaluationProtocolError, match="PASS or FAIL criterion"):
        OptionalModelEvaluator(evaluator=RecordingEvaluator(uninspected)).evaluate_if_needed(
            deterministic_result=batch,
            request=request,
        )


def test_result_semantics_reject_unknown_and_invalid_pass_payloads() -> None:
    batch = deterministic_batch(CompletionVerdict.PASS)
    request = evaluation_request(batch)

    with pytest.raises(ValueError, match="PASS, FAIL, or INSUFFICIENT_EVIDENCE"):
        EvaluationCriterionResult(
            criterion_id=request.assigned_criteria[0].criterion_id,
            statement=request.assigned_criteria[0].statement,
            mandatory=True,
            verdict=CompletionVerdict.NOT_EVALUATED,
            evidence_refs=request.artifact_refs,
            missing_evidence=(),
            smallest_correction=None,
            release_blocking=False,
        )
    with pytest.raises(ValueError, match="cannot report missing evidence"):
        replace(
            criterion_result(request, CompletionVerdict.PASS),
            missing_evidence=("Unexpected missing evidence",),
        )
