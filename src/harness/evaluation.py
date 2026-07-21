"""C-408 optional read-only model evaluation boundary.

Deterministic validation remains authoritative.  This module calls a model
evaluator only after an aggregate deterministic PASS and only when a frozen
semantic request is supplied.  It passes immutable references and criteria,
rejects rewritten criteria or expanded evidence scope, and owns no provider,
prompt-routing, persistence, retry, CLI, or external-effect behavior.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol, runtime_checkable

from harness.state import CompletionVerdict, EvaluatorAccess, LocationReference
from harness.validation import ValidationBatchResult

__all__ = [
    "CorrectionOwner",
    "EvaluationBudgetUsage",
    "EvaluationContractError",
    "EvaluationCorrection",
    "EvaluationCriterion",
    "EvaluationCriterionResult",
    "EvaluationOutcome",
    "EvaluationProtocolError",
    "EvaluationRequest",
    "EvaluatorIdentity",
    "ModelEvaluationResult",
    "OptionalModelEvaluator",
    "ReadOnlyModelEvaluator",
]

_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")


class EvaluationContractError(ValueError):
    """The host supplied an invalid or unfrozen evaluation contract."""


class EvaluationProtocolError(RuntimeError):
    """The evaluator returned malformed, rewritten, or out-of-scope output."""


class CorrectionOwner(StrEnum):
    """W-207 owners allowed to perform a separately authorized correction."""

    GENERATOR = "GENERATOR"
    LOCAL_CODEX = "LOCAL_CODEX"
    TRUSTED_HOST = "TRUSTED_HOST"
    HUMAN = "HUMAN"


def _require_stable_id(value: str, location: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{location} must be a string")
    if _STABLE_ID_RE.fullmatch(value) is None:
        raise ValueError(f"{location} must be a stable identifier")


def _require_normalized_string(value: str, location: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{location} must be a string")
    if not value or value != value.strip() or "\x00" in value:
        raise ValueError(f"{location} must be non-empty and normalized")


def _require_strings(values: tuple[str, ...], location: str, *, required: bool) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{location} must be a tuple")
    if required and not values:
        raise ValueError(f"{location} must not be empty")
    if len(set(values)) != len(values):
        raise ValueError(f"{location} must not contain duplicates")
    for index, value in enumerate(values):
        _require_normalized_string(value, f"{location}[{index}]")


def _require_refs(
    values: tuple[LocationReference, ...],
    location: str,
    *,
    required: bool = False,
) -> None:
    if type(values) is not tuple:
        raise TypeError(f"{location} must be a tuple")
    if required and not values:
        raise ValueError(f"{location} must not be empty")
    if any(type(value) is not LocationReference for value in values):
        raise TypeError(f"{location} must contain LocationReference values")
    if len(set(values)) != len(values):
        raise ValueError(f"{location} must not contain duplicates")


def _require_verdict(value: CompletionVerdict, location: str) -> None:
    if type(value) is not CompletionVerdict:
        raise TypeError(f"{location} must be a CompletionVerdict")
    if value is CompletionVerdict.NOT_EVALUATED:
        raise ValueError(f"{location} must be PASS, FAIL, or INSUFFICIENT_EVIDENCE")


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationCriterion:
    """One frozen irreducible criterion assigned to model judgment."""

    criterion_id: str
    statement: str
    mandatory: bool
    release_blocking: bool

    def __post_init__(self) -> None:
        _require_stable_id(self.criterion_id, "EvaluationCriterion.criterion_id")
        _require_normalized_string(self.statement, "EvaluationCriterion.statement")
        if type(self.mandatory) is not bool or type(self.release_blocking) is not bool:
            raise TypeError("criterion mandatory and release_blocking flags must be booleans")
        if self.mandatory is not self.release_blocking:
            raise ValueError("W-207 model criteria must be release-blocking exactly when mandatory")


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationRequest:
    """Immutable read-only context for only the remaining semantic criteria."""

    request_id: str
    contract_version: str
    goal_id: str
    task_id: str
    goal_contract_ref: LocationReference
    assigned_criteria: tuple[EvaluationCriterion, ...]
    authoritative_inputs: tuple[LocationReference, ...]
    artifact_refs: tuple[LocationReference, ...]
    deterministic_results: tuple[LocationReference, ...]
    scope_in: tuple[str, ...]
    scope_out: tuple[str, ...]
    known_evidence_limits: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_stable_id(self.request_id, "EvaluationRequest.request_id")
        _require_stable_id(self.contract_version, "EvaluationRequest.contract_version")
        _require_stable_id(self.goal_id, "EvaluationRequest.goal_id")
        _require_stable_id(self.task_id, "EvaluationRequest.task_id")
        if type(self.goal_contract_ref) is not LocationReference:
            raise TypeError("EvaluationRequest.goal_contract_ref must be a LocationReference")
        if type(self.assigned_criteria) is not tuple:
            raise TypeError("EvaluationRequest.assigned_criteria must be a tuple")
        if not self.assigned_criteria:
            raise ValueError("EvaluationRequest requires at least one assigned model criterion")
        if any(type(item) is not EvaluationCriterion for item in self.assigned_criteria):
            raise TypeError("assigned_criteria must contain EvaluationCriterion values")
        criterion_ids = tuple(item.criterion_id for item in self.assigned_criteria)
        if len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("assigned model criterion IDs must be unique")
        if any(not item.mandatory for item in self.assigned_criteria):
            raise ValueError("assigned model criteria must be mandatory")
        _require_refs(self.authoritative_inputs, "authoritative_inputs", required=True)
        _require_refs(self.artifact_refs, "artifact_refs", required=True)
        _require_refs(self.deterministic_results, "deterministic_results", required=True)
        _require_strings(self.scope_in, "scope_in", required=True)
        _require_strings(self.scope_out, "scope_out", required=True)
        _require_strings(
            self.known_evidence_limits,
            "known_evidence_limits",
            required=False,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationCorrection:
    """Smallest proposed correction; this record grants no write authority."""

    action: str
    owner: CorrectionOwner
    target_refs: tuple[LocationReference, ...]
    verification: str

    def __post_init__(self) -> None:
        _require_normalized_string(self.action, "EvaluationCorrection.action")
        if type(self.owner) is not CorrectionOwner:
            raise TypeError("EvaluationCorrection.owner must be a CorrectionOwner")
        _require_refs(self.target_refs, "EvaluationCorrection.target_refs")
        _require_normalized_string(
            self.verification,
            "EvaluationCorrection.verification",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationCriterionResult:
    """W-207 criterion result with exact three-valued verdict semantics."""

    criterion_id: str
    statement: str
    mandatory: bool
    verdict: CompletionVerdict
    evidence_refs: tuple[LocationReference, ...]
    missing_evidence: tuple[str, ...]
    smallest_correction: EvaluationCorrection | None
    release_blocking: bool

    def __post_init__(self) -> None:
        _require_stable_id(self.criterion_id, "criterion_result.criterion_id")
        _require_normalized_string(self.statement, "criterion_result.statement")
        if type(self.mandatory) is not bool or type(self.release_blocking) is not bool:
            raise TypeError("criterion result flags must be booleans")
        _require_verdict(self.verdict, "criterion_result.verdict")
        _require_refs(self.evidence_refs, "criterion_result.evidence_refs")
        _require_strings(
            self.missing_evidence,
            "criterion_result.missing_evidence",
            required=False,
        )
        if (
            self.smallest_correction is not None
            and type(self.smallest_correction) is not EvaluationCorrection
        ):
            raise TypeError("smallest_correction must be an EvaluationCorrection or null")
        if self.verdict is CompletionVerdict.PASS:
            if not self.evidence_refs:
                raise ValueError("PASS criterion results require evidence references")
            if self.missing_evidence or self.smallest_correction is not None:
                raise ValueError(
                    "PASS criterion results cannot report missing evidence or correction"
                )
            if self.release_blocking:
                raise ValueError("PASS criterion results cannot be release-blocking")
        elif self.verdict is CompletionVerdict.FAIL:
            if not self.evidence_refs:
                raise ValueError("FAIL criterion results require evidence references")
            if self.smallest_correction is None:
                raise ValueError("FAIL criterion results require a smallest correction")
        else:
            if not self.missing_evidence:
                raise ValueError("INSUFFICIENT_EVIDENCE criterion results require missing evidence")
            if self.smallest_correction is None:
                raise ValueError(
                    "INSUFFICIENT_EVIDENCE criterion results require a smallest correction"
                )
        if self.mandatory and self.verdict is not CompletionVerdict.PASS:
            if not self.release_blocking:
                raise ValueError("nonpassing mandatory criteria must be release-blocking")


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluatorIdentity:
    """Identity and enforced authority declarations for one evaluator result."""

    evaluator_id: str
    runtime_identity: str | None
    actual_artifact_inspection: bool
    independent_from_generator: bool = True
    access_mode: EvaluatorAccess = EvaluatorAccess.READ_ONLY
    kind: str = "MODEL_EVALUATOR"

    def __post_init__(self) -> None:
        _require_stable_id(self.evaluator_id, "EvaluatorIdentity.evaluator_id")
        if self.runtime_identity is not None:
            _require_normalized_string(
                self.runtime_identity,
                "EvaluatorIdentity.runtime_identity",
            )
        if self.independent_from_generator is not True:
            raise ValueError("model evaluator must be independent from the generator")
        if self.access_mode is not EvaluatorAccess.READ_ONLY:
            raise ValueError("model evaluator access must be READ_ONLY")
        if self.kind != "MODEL_EVALUATOR":
            raise ValueError("evaluator kind must be MODEL_EVALUATOR")
        if type(self.actual_artifact_inspection) is not bool:
            raise TypeError("actual_artifact_inspection must be a boolean")


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationBudgetUsage:
    """Observed evaluator usage without owning budget enforcement."""

    elapsed_seconds: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_amount: float | None = None
    cost_currency: str | None = None

    def __post_init__(self) -> None:
        if self.elapsed_seconds is not None and (
            type(self.elapsed_seconds) not in {float, int} or self.elapsed_seconds < 0
        ):
            raise ValueError("elapsed_seconds must be non-negative or null")
        for name in ("input_tokens", "output_tokens"):
            value = getattr(self, name)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{name} must be a non-negative integer or null")
        if self.cost_amount is not None and (
            type(self.cost_amount) not in {float, int} or self.cost_amount < 0
        ):
            raise ValueError("cost_amount must be non-negative or null")
        if (self.cost_amount is None) is not (self.cost_currency is None):
            raise ValueError("cost amount and currency must be supplied together")
        if self.cost_currency is not None:
            if (
                type(self.cost_currency) is not str
                or len(self.cost_currency) != 3
                or not self.cost_currency.isascii()
                or not self.cost_currency.isupper()
            ):
                raise ValueError("cost_currency must be a three-letter uppercase code")


def _aggregate_verdict(
    criteria: tuple[EvaluationCriterionResult, ...],
) -> CompletionVerdict:
    if any(item.verdict is CompletionVerdict.FAIL for item in criteria):
        return CompletionVerdict.FAIL
    if any(item.verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE for item in criteria):
        return CompletionVerdict.INSUFFICIENT_EVIDENCE
    return CompletionVerdict.PASS


def _aggregate_missing(criteria: tuple[EvaluationCriterionResult, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(item for result in criteria for item in result.missing_evidence))


@dataclass(frozen=True, slots=True, kw_only=True)
class ModelEvaluationResult:
    """Structured W-207 result returned by a read-only evaluator implementation."""

    result_id: str
    goal_id: str
    task_id: str
    evaluator: EvaluatorIdentity
    goal_contract_ref: LocationReference
    artifact_refs: tuple[LocationReference, ...]
    criteria: tuple[EvaluationCriterionResult, ...]
    overall_verdict: CompletionVerdict
    release_blocking: bool
    smallest_correction: EvaluationCorrection | None
    insufficient_evidence: tuple[str, ...]
    evaluated_at: datetime
    budget_usage: EvaluationBudgetUsage
    scope_preserved: bool = True
    criteria_preserved: bool = True
    schema_version: str = "1.0.0"

    def __post_init__(self) -> None:
        if self.schema_version != "1.0.0":
            raise ValueError("ModelEvaluationResult.schema_version must be 1.0.0")
        _require_stable_id(self.result_id, "ModelEvaluationResult.result_id")
        _require_stable_id(self.goal_id, "ModelEvaluationResult.goal_id")
        _require_stable_id(self.task_id, "ModelEvaluationResult.task_id")
        if type(self.evaluator) is not EvaluatorIdentity:
            raise TypeError("evaluator must be an EvaluatorIdentity")
        if type(self.goal_contract_ref) is not LocationReference:
            raise TypeError("goal_contract_ref must be a LocationReference")
        _require_refs(self.artifact_refs, "ModelEvaluationResult.artifact_refs")
        if type(self.criteria) is not tuple or not self.criteria:
            raise ValueError("ModelEvaluationResult.criteria must be a non-empty tuple")
        if any(type(item) is not EvaluationCriterionResult for item in self.criteria):
            raise TypeError("criteria must contain EvaluationCriterionResult values")
        criterion_ids = tuple(item.criterion_id for item in self.criteria)
        if len(set(criterion_ids)) != len(criterion_ids):
            raise ValueError("result criterion IDs must be unique")
        _require_verdict(self.overall_verdict, "ModelEvaluationResult.overall_verdict")
        if self.overall_verdict is not _aggregate_verdict(self.criteria):
            raise ValueError("overall_verdict does not match W-203 aggregate precedence")
        if type(self.release_blocking) is not bool:
            raise TypeError("release_blocking must be a boolean")
        if self.release_blocking is not any(item.release_blocking for item in self.criteria):
            raise ValueError("release_blocking does not match criterion results")
        if (
            self.smallest_correction is not None
            and type(self.smallest_correction) is not EvaluationCorrection
        ):
            raise TypeError("smallest_correction must be an EvaluationCorrection or null")
        _require_strings(
            self.insufficient_evidence,
            "ModelEvaluationResult.insufficient_evidence",
            required=False,
        )
        if self.insufficient_evidence != _aggregate_missing(self.criteria):
            raise ValueError("insufficient_evidence must exactly aggregate criterion results")
        if self.overall_verdict is CompletionVerdict.PASS:
            if self.smallest_correction is not None or self.insufficient_evidence:
                raise ValueError("PASS results cannot report correction or missing evidence")
        elif self.smallest_correction is None:
            raise ValueError("nonpassing results require a smallest correction")
        if type(self.evaluated_at) is not datetime:
            raise TypeError("evaluated_at must be a datetime")
        if self.evaluated_at.tzinfo is None or self.evaluated_at.utcoffset() is None:
            raise ValueError("evaluated_at must include a timezone offset")
        if type(self.budget_usage) is not EvaluationBudgetUsage:
            raise TypeError("budget_usage must be an EvaluationBudgetUsage")
        if self.scope_preserved is not True or self.criteria_preserved is not True:
            raise ValueError("scope and frozen criteria must be preserved")


@runtime_checkable
class ReadOnlyModelEvaluator(Protocol):
    """Narrow evaluator port: immutable references in, structured judgment out."""

    def evaluate(self, *, request: EvaluationRequest) -> object:
        """Judge only the supplied frozen criteria without causing effects."""


@dataclass(frozen=True, slots=True, kw_only=True)
class EvaluationOutcome:
    """Deterministic-first decision and optional accepted model result."""

    deterministic_result: ValidationBatchResult
    overall_verdict: CompletionVerdict
    evaluator_invoked: bool
    model_result: ModelEvaluationResult | None
    reason: str

    def __post_init__(self) -> None:
        if type(self.deterministic_result) is not ValidationBatchResult:
            raise TypeError("deterministic_result must be a ValidationBatchResult")
        _require_verdict(self.overall_verdict, "EvaluationOutcome.overall_verdict")
        if type(self.evaluator_invoked) is not bool:
            raise TypeError("evaluator_invoked must be a boolean")
        _require_normalized_string(self.reason, "EvaluationOutcome.reason")
        if self.evaluator_invoked:
            if type(self.model_result) is not ModelEvaluationResult:
                raise ValueError("an invoked evaluator requires a model result")
            if self.deterministic_result.overall_verdict is not CompletionVerdict.PASS:
                raise ValueError("model evaluation requires deterministic PASS")
            if self.overall_verdict is not self.model_result.overall_verdict:
                raise ValueError("outcome must preserve the model result verdict")
        else:
            if self.model_result is not None:
                raise ValueError("a suppressed evaluator cannot have a model result")
            if self.overall_verdict is not self.deterministic_result.overall_verdict:
                raise ValueError("suppressed evaluation must preserve the deterministic verdict")


class OptionalModelEvaluator:
    """Apply deterministic-first invocation and validate the read-only response."""

    def __init__(self, *, evaluator: ReadOnlyModelEvaluator) -> None:
        if not isinstance(evaluator, ReadOnlyModelEvaluator):
            raise TypeError("evaluator must implement ReadOnlyModelEvaluator")
        self._evaluator = evaluator

    def evaluate_if_needed(
        self,
        *,
        deterministic_result: ValidationBatchResult,
        request: EvaluationRequest | None = None,
    ) -> EvaluationOutcome:
        """Invoke only after deterministic PASS and for an explicit semantic request."""

        if type(deterministic_result) is not ValidationBatchResult:
            raise TypeError("deterministic_result must be a ValidationBatchResult")
        if deterministic_result.overall_verdict is not CompletionVerdict.PASS:
            return EvaluationOutcome(
                deterministic_result=deterministic_result,
                overall_verdict=deterministic_result.overall_verdict,
                evaluator_invoked=False,
                model_result=None,
                reason="Deterministic evidence is authoritative and is not PASS",
            )
        if request is None:
            return EvaluationOutcome(
                deterministic_result=deterministic_result,
                overall_verdict=CompletionVerdict.PASS,
                evaluator_invoked=False,
                model_result=None,
                reason="Deterministic evidence is sufficient; no semantic criteria remain",
            )
        if type(request) is not EvaluationRequest:
            raise TypeError("request must be an EvaluationRequest or null")
        self._validate_request(deterministic_result, request)
        raw_result = self._evaluator.evaluate(request=request)
        if type(raw_result) is not ModelEvaluationResult:
            raise EvaluationProtocolError("evaluator returned a malformed result")
        self._validate_response(request, raw_result)
        return EvaluationOutcome(
            deterministic_result=deterministic_result,
            overall_verdict=raw_result.overall_verdict,
            evaluator_invoked=True,
            model_result=raw_result,
            reason="Deterministic validation passed; frozen semantic criteria were evaluated",
        )

    @staticmethod
    def _validate_request(
        deterministic_result: ValidationBatchResult,
        request: EvaluationRequest,
    ) -> None:
        if request.task_id != deterministic_result.task_id:
            raise EvaluationContractError("request task does not match deterministic evidence")
        expected_refs = deterministic_result.evidence_refs
        actual_refs = tuple(item.ref for item in request.deterministic_results)
        if actual_refs != expected_refs:
            raise EvaluationContractError(
                "request deterministic references must exactly match the validation batch"
            )

    @staticmethod
    def _validate_response(
        request: EvaluationRequest,
        result: ModelEvaluationResult,
    ) -> None:
        if result.goal_id != request.goal_id or result.task_id != request.task_id:
            raise EvaluationProtocolError("evaluator changed goal or task identity")
        if result.goal_contract_ref != request.goal_contract_ref:
            raise EvaluationProtocolError("evaluator changed the goal-contract reference")
        if result.artifact_refs != request.artifact_refs:
            raise EvaluationProtocolError("evaluator changed the inspected artifact set")
        expected_criteria = tuple(
            (item.criterion_id, item.statement, item.mandatory)
            for item in request.assigned_criteria
        )
        actual_criteria = tuple(
            (item.criterion_id, item.statement, item.mandatory) for item in result.criteria
        )
        if actual_criteria != expected_criteria:
            raise EvaluationProtocolError(
                "evaluator rewrote, removed, reordered, or added criteria"
            )

        allowed_refs = set(
            request.authoritative_inputs
            + request.artifact_refs
            + request.deterministic_results
            + (request.goal_contract_ref,)
        )
        correction_refs = set(request.artifact_refs)
        for frozen, judged in zip(request.assigned_criteria, result.criteria, strict=True):
            expected_blocking = (
                False if judged.verdict is CompletionVerdict.PASS else frozen.release_blocking
            )
            if judged.release_blocking is not expected_blocking:
                raise EvaluationProtocolError("evaluator changed criterion blocking semantics")
            OptionalModelEvaluator._require_bounded_refs(
                judged.evidence_refs,
                allowed_refs,
                "criterion evidence",
            )
            if judged.smallest_correction is not None:
                OptionalModelEvaluator._require_bounded_refs(
                    judged.smallest_correction.target_refs,
                    correction_refs,
                    "criterion correction",
                )
        if result.smallest_correction is not None:
            OptionalModelEvaluator._require_bounded_refs(
                result.smallest_correction.target_refs,
                correction_refs,
                "aggregate correction",
            )
        if (
            any(
                item.verdict in {CompletionVerdict.PASS, CompletionVerdict.FAIL}
                for item in result.criteria
            )
            and not result.evaluator.actual_artifact_inspection
        ):
            raise EvaluationProtocolError(
                "a PASS or FAIL criterion requires actual artifact inspection"
            )

    @staticmethod
    def _require_bounded_refs(
        references: tuple[LocationReference, ...],
        allowed_refs: set[LocationReference],
        location: str,
    ) -> None:
        if any(reference not in allowed_refs for reference in references):
            raise EvaluationProtocolError(f"{location} expanded the supplied evidence scope")
