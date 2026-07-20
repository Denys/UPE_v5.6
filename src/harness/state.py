"""Strict, immutable runtime state contracts for the UPE harness.

The models in this module deliberately depend only on the Python standard
library.  They are the provider-neutral boundary used by later persistence and
adapter slices; no model performs I/O or an external action.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field, fields, replace
from datetime import UTC, datetime
from enum import StrEnum
from types import NoneType, UnionType
from typing import Any, ClassVar, Self, Union, cast, get_args, get_origin, get_type_hints
from urllib.parse import urlsplit

SCHEMA_VERSION = "1.0.0"
_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_RELATIVE_PATH_RE = re.compile(r"^(?![A-Za-z]:[\\/])(?![\\/])(?!.*(?:^|[\\/])\.\.(?:[\\/]|$)).+$")
_SHA256_RE = re.compile(r"^[A-Fa-f0-9]{64}$")
_GIT_COMMIT_RE = re.compile(r"^[A-Fa-f0-9]{7,64}$")
_RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$"
)


class StateValidationError(ValueError):
    """A state payload is well-typed but violates a domain invariant."""


class TransitionError(StateValidationError):
    """A requested lifecycle transition violates the transition contract."""


class InvalidTransitionError(TransitionError):
    """The requested prior/next lifecycle edge is not permitted."""


class DuplicateTransitionError(TransitionError):
    """The transition ID repeats the run's most recently applied transition."""


def _type_name(annotation: object) -> str:
    return getattr(annotation, "__name__", repr(annotation))


def _validate_runtime_type(value: object, annotation: object, path: str) -> None:
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        for option in get_args(annotation):
            try:
                _validate_runtime_type(value, option, path)
            except TypeError:
                continue
            return
        raise TypeError(f"{path} does not match {_type_name(annotation)}")

    if annotation is NoneType:
        if value is not None:
            raise TypeError(f"{path} must be null")
        return

    if origin is tuple:
        if type(value) is not tuple:
            raise TypeError(f"{path} must be a tuple")
        item_args = get_args(annotation)
        if len(item_args) != 2 or item_args[1] is not Ellipsis:
            raise TypeError(f"unsupported tuple annotation for {path}")
        for index, item in enumerate(value):
            _validate_runtime_type(item, item_args[0], f"{path}[{index}]")
        return

    if annotation is Any or annotation is object:
        return
    if annotation is bool:
        if type(value) is not bool:
            raise TypeError(f"{path} must be a boolean")
        return
    if annotation is int:
        if type(value) is not int:
            raise TypeError(f"{path} must be an integer")
        return
    if annotation is float:
        if type(value) is not float:
            raise TypeError(f"{path} must be a float")
        return
    if annotation is str:
        if type(value) is not str:
            raise TypeError(f"{path} must be a string")
        return
    if annotation is datetime:
        if type(value) is not datetime:
            raise TypeError(f"{path} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise StateValidationError(f"{path} must be timezone-aware")
        return
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        if type(value) is not annotation:
            raise TypeError(f"{path} must be {_type_name(annotation)}")
        return
    if isinstance(annotation, type) and issubclass(annotation, _StrictModel):
        if type(value) is not annotation:
            raise TypeError(f"{path} must be {_type_name(annotation)}")
        return
    raise TypeError(f"unsupported annotation {_type_name(annotation)} for {path}")


def _parse_rfc3339(value: object, path: str) -> datetime:
    if type(value) is not str:
        raise TypeError(f"{path} must be an RFC 3339 string")
    if _RFC3339_RE.fullmatch(value) is None:
        raise StateValidationError(f"{path} must be an RFC 3339 date-time with an offset or Z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise StateValidationError(f"{path} is not a valid RFC 3339 date-time") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise StateValidationError(f"{path} must be timezone-aware")
    return parsed.astimezone(UTC)


def _format_rfc3339(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise StateValidationError("cannot serialize a naive datetime")
    utc_value = value.astimezone(UTC)
    timespec = "microseconds" if utc_value.microsecond else "seconds"
    return utc_value.isoformat(timespec=timespec).replace("+00:00", "Z")


def _decode_json(value: object, annotation: object, path: str) -> object:
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        if value is None and NoneType in get_args(annotation):
            return None
        failures: list[Exception] = []
        for option in get_args(annotation):
            if option is NoneType:
                continue
            try:
                return _decode_json(value, option, path)
            except (TypeError, ValueError) as exc:
                failures.append(exc)
        domain_failures = [
            failure for failure in failures if isinstance(failure, StateValidationError)
        ]
        if domain_failures:
            failure = domain_failures[-1]
            raise StateValidationError(f"{path} is invalid: {failure}") from failure
        detail = str(failures[-1]) if failures else "no union member accepted the value"
        raise TypeError(f"{path} has an invalid type: {detail}")

    if annotation is NoneType:
        if value is not None:
            raise TypeError(f"{path} must be null")
        return None
    if origin is tuple:
        if type(value) is not list:
            raise TypeError(f"{path} must be an array")
        item_args = get_args(annotation)
        if len(item_args) != 2 or item_args[1] is not Ellipsis:
            raise TypeError(f"unsupported tuple annotation for {path}")
        return tuple(
            _decode_json(item, item_args[0], f"{path}[{index}]") for index, item in enumerate(value)
        )
    if annotation is datetime:
        return _parse_rfc3339(value, path)
    if isinstance(annotation, type) and issubclass(annotation, StrEnum):
        if type(value) is not str:
            raise TypeError(f"{path} must be a string enum value")
        try:
            return annotation(value)
        except ValueError as exc:
            raise StateValidationError(f"{path} has unsupported value {value!r}") from exc
    if isinstance(annotation, type) and issubclass(annotation, _StrictModel):
        if type(value) is not dict:
            raise TypeError(f"{path} must be an object")
        return annotation.from_dict(value)

    _validate_runtime_type(value, annotation, path)
    return value


def _encode_json(value: object) -> object:
    if value is None or type(value) in (bool, int, float, str):
        return value
    if isinstance(value, StrEnum):
        return value.value
    if type(value) is datetime:
        return _format_rfc3339(value)
    if isinstance(value, _StrictModel):
        return value.to_dict()
    if type(value) is tuple:
        return [_encode_json(item) for item in value]
    raise TypeError(f"cannot serialize value of type {type(value).__name__}")


class _StrictModel:
    """Shared strict JSON conversion for frozen dataclass records."""

    def __post_init__(self) -> None:
        annotations = get_type_hints(type(self))
        for model_field in fields(self):  # type: ignore[arg-type]
            value = getattr(self, model_field.name)
            _validate_runtime_type(
                value,
                annotations[model_field.name],
                f"{type(self).__name__}.{model_field.name}",
            )
            if type(value) is datetime:
                object.__setattr__(self, model_field.name, value.astimezone(UTC))

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> Self:
        if type(data) is not dict:
            raise TypeError(f"{cls.__name__}.from_dict requires a dictionary")
        if any(type(key) is not str for key in data):
            raise TypeError(f"{cls.__name__} keys must be strings")

        model_fields = {
            model_field.name: model_field
            for model_field in fields(cls)  # type: ignore[arg-type]
        }
        unknown = set(data) - set(model_fields)
        if unknown:
            raise StateValidationError(f"{cls.__name__} has unknown keys: {sorted(unknown)!r}")
        missing = {
            name
            for name, model_field in model_fields.items()
            if name not in data and not model_field.metadata.get("json_optional", False)
        }
        if missing:
            raise StateValidationError(
                f"{cls.__name__} is missing required keys: {sorted(missing)!r}"
            )

        annotations = get_type_hints(cls)
        decoded = {
            name: _decode_json(value, annotations[name], f"{cls.__name__}.{name}")
            for name, value in data.items()
        }
        return cls(**decoded)

    def to_dict(self) -> dict[str, object]:
        return {
            model_field.name: _encode_json(getattr(self, model_field.name))
            for model_field in fields(self)  # type: ignore[arg-type]
        }


def _require_string(
    value: str,
    path: str,
    *,
    maximum: int = 4096,
    normalized: bool = False,
) -> None:
    if not value:
        raise StateValidationError(f"{path} must not be empty")
    if len(value) > maximum:
        raise StateValidationError(f"{path} must be at most {maximum} characters")
    if normalized and (value != value.strip() or any(ord(char) < 32 for char in value)):
        raise StateValidationError(f"{path} must be a normalized single-line string")


def _require_stable_id(value: str, path: str) -> None:
    if len(value) > 128 or _STABLE_ID_RE.fullmatch(value) is None:
        raise StateValidationError(
            f"{path} must match {_STABLE_ID_RE.pattern!r} and be at most 128 characters"
        )


def _require_unique(values: tuple[object, ...], path: str) -> None:
    for index, value in enumerate(values):
        if any(value == previous for previous in values[:index]):
            raise StateValidationError(f"{path} contains duplicate item at index {index}")


def _require_unique_ids(values: tuple[object, ...], attribute: str, path: str) -> None:
    identifiers = tuple(getattr(value, attribute) for value in values)
    _require_unique(identifiers, path)


def _require_string_items(
    values: tuple[str, ...],
    path: str,
    *,
    maximum: int = 4096,
    stable_ids: bool = False,
    normalized: bool = False,
) -> None:
    _require_unique(values, path)
    for index, value in enumerate(values):
        item_path = f"{path}[{index}]"
        if stable_ids:
            _require_stable_id(value, item_path)
        else:
            _require_string(value, item_path, maximum=maximum, normalized=normalized)


class LocationKind(StrEnum):
    REPOSITORY_PATH = "REPOSITORY_PATH"
    ARTIFACT_PATH = "ARTIFACT_PATH"
    URI = "URI"
    GIT_COMMIT = "GIT_COMMIT"
    PULL_REQUEST = "PULL_REQUEST"
    COMMAND_RESULT = "COMMAND_RESULT"
    EXTERNAL_RESOURCE = "EXTERNAL_RESOURCE"


class VerificationMethod(StrEnum):
    DETERMINISTIC = "DETERMINISTIC"
    MODEL_EVALUATOR = "MODEL_EVALUATOR"
    HUMAN_REVIEW = "HUMAN_REVIEW"


class EvaluatorAccess(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    READ_ONLY = "READ_ONLY"


class RequiredActionScope(StrEnum):
    NONE = "NONE"
    READ_ONLY = "READ_ONLY"
    TRANSFORM_ONLY = "TRANSFORM_ONLY"
    DRAFT = "DRAFT"
    WRITE = "WRITE"
    CONSEQUENTIAL = "CONSEQUENTIAL"
    IRREVERSIBLE = "IRREVERSIBLE"


class ActionClass(StrEnum):
    READ = "READ"
    TRANSFORM = "TRANSFORM"
    DRAFT = "DRAFT"
    WRITE = "WRITE"
    COMMIT = "COMMIT"
    PUSH = "PUSH"
    CREATE_PR = "CREATE_PR"
    UPDATE_PR = "UPDATE_PR"
    MERGE = "MERGE"
    RELEASE = "RELEASE"
    DEPLOY = "DEPLOY"
    VISIBILITY_CHANGE = "VISIBILITY_CHANGE"
    EXTERNAL_MESSAGE = "EXTERNAL_MESSAGE"
    PURCHASE = "PURCHASE"
    PRODUCTION_MUTATION = "PRODUCTION_MUTATION"
    DESTRUCTIVE_ACTION = "DESTRUCTIVE_ACTION"
    SECRET_HANDLING = "SECRET_HANDLING"
    OTHER_EXTERNAL_WRITE = "OTHER_EXTERNAL_WRITE"
    IRREVERSIBLE_OR_HIGH_CONSEQUENCE = "IRREVERSIBLE_OR_HIGH_CONSEQUENCE"


class ApprovalRequirement(StrEnum):
    NONE = "NONE"
    EXPLICIT_AUTHORIZATION = "EXPLICIT_AUTHORIZATION"
    STRICT_PREFLIGHT = "STRICT_PREFLIGHT"
    FORBIDDEN = "FORBIDDEN"


class EnforcementOwner(StrEnum):
    TRUSTED_HOST = "TRUSTED_HOST"
    WORK_COORDINATOR = "WORK_COORDINATOR"
    HUMAN = "HUMAN"


class CompletionRule(StrEnum):
    ALL_MANDATORY_CONDITIONS_PASS = "ALL_MANDATORY_CONDITIONS_PASS"


@dataclass(frozen=True, slots=True, kw_only=True)
class LocationReference(_StrictModel):
    kind: LocationKind
    ref: str
    description: str
    revision: str | None = field(default=None, metadata={"json_optional": True})
    sha256: str | None = field(default=None, metadata={"json_optional": True})

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_string(self.ref, "LocationReference.ref", maximum=2048)
        _require_string(self.description, "LocationReference.description")
        if self.revision is not None and len(self.revision) > 256:
            raise StateValidationError("LocationReference.revision must be at most 256 characters")
        if self.sha256 is not None and _SHA256_RE.fullmatch(self.sha256) is None:
            raise StateValidationError(
                "LocationReference.sha256 must be a 64-character hexadecimal digest"
            )

        if (
            self.kind
            in {
                LocationKind.REPOSITORY_PATH,
                LocationKind.ARTIFACT_PATH,
                LocationKind.COMMAND_RESULT,
            }
            and _RELATIVE_PATH_RE.fullmatch(self.ref) is None
        ):
            raise StateValidationError("LocationReference.ref must be a contained relative path")
        if self.kind is LocationKind.GIT_COMMIT and _GIT_COMMIT_RE.fullmatch(self.ref) is None:
            raise StateValidationError(
                "LocationReference.ref must be a 7-to-64 digit hexadecimal commit"
            )
        if self.kind in {LocationKind.URI, LocationKind.PULL_REQUEST}:
            try:
                parsed = urlsplit(self.ref)
            except ValueError as exc:
                raise StateValidationError("LocationReference.ref must be an absolute URI") from exc
            if not parsed.scheme or (parsed.scheme in {"http", "https"} and not parsed.netloc):
                raise StateValidationError("LocationReference.ref must be an absolute URI")


@dataclass(frozen=True, slots=True, kw_only=True)
class DoneConditionVerification(_StrictModel):
    method: VerificationMethod
    evidence_required: bool = True
    validator_refs: tuple[LocationReference, ...] = ()
    evaluator_access: EvaluatorAccess = EvaluatorAccess.NOT_APPLICABLE

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.evidence_required:
            raise StateValidationError("DoneConditionVerification.evidence_required must be true")
        _require_unique(self.validator_refs, "DoneConditionVerification.validator_refs")
        if self.method is VerificationMethod.DETERMINISTIC and not self.validator_refs:
            raise StateValidationError(
                "deterministic verification requires at least one validator reference"
            )
        if (
            self.method is VerificationMethod.MODEL_EVALUATOR
            and self.evaluator_access is not EvaluatorAccess.READ_ONLY
        ):
            raise StateValidationError("model evaluators must have READ_ONLY access")


@dataclass(frozen=True, slots=True, kw_only=True)
class DoneCondition(_StrictModel):
    id: str
    description: str
    mandatory: bool
    verification: DoneConditionVerification
    output_ids: tuple[str, ...]
    release_blocking: bool

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_stable_id(self.id, "DoneCondition.id")
        _require_string(self.description, "DoneCondition.description")
        _require_string_items(self.output_ids, "DoneCondition.output_ids", stable_ids=True)
        if self.release_blocking and not self.mandatory:
            raise StateValidationError("a release-blocking done condition must be mandatory")


@dataclass(frozen=True, slots=True, kw_only=True)
class Constraint(_StrictModel):
    id: str
    description: str
    source_ref: LocationReference | None = field(default=None, metadata={"json_optional": True})

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_stable_id(self.id, "Constraint.id")
        _require_string(self.description, "Constraint.description")


@dataclass(frozen=True, slots=True, kw_only=True)
class CapabilityRequirement(_StrictModel):
    capability_id: str
    purpose: str
    required_action_scope: RequiredActionScope
    fallback: str
    capability_record_ref: LocationReference | None = field(
        default=None, metadata={"json_optional": True}
    )

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_stable_id(self.capability_id, "CapabilityRequirement.capability_id")
        _require_string(self.purpose, "CapabilityRequirement.purpose")
        _require_string(self.fallback, "CapabilityRequirement.fallback")


@dataclass(frozen=True, slots=True, kw_only=True)
class AvoidedCapability(_StrictModel):
    capability_id: str
    reason: str

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_stable_id(self.capability_id, "AvoidedCapability.capability_id")
        _require_string(self.reason, "AvoidedCapability.reason")


@dataclass(frozen=True, slots=True, kw_only=True)
class ApprovalRule(_StrictModel):
    action_class: ActionClass
    requirement: ApprovalRequirement
    scope: str
    approver: str | None = field(default=None, metadata={"json_optional": True})

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_string(self.scope, "ApprovalRule.scope")
        if self.approver is not None and len(self.approver) > 256:
            raise StateValidationError("ApprovalRule.approver must be at most 256 characters")


@dataclass(frozen=True, slots=True, kw_only=True)
class RetryPolicy(_StrictModel):
    max_transient_retries: int
    identical_failure_limit: int
    no_progress_iteration_limit: int

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.max_transient_retries < 0:
            raise StateValidationError("RetryPolicy.max_transient_retries must be non-negative")
        if self.identical_failure_limit < 1:
            raise StateValidationError("RetryPolicy.identical_failure_limit must be at least one")
        if self.no_progress_iteration_limit < 1:
            raise StateValidationError(
                "RetryPolicy.no_progress_iteration_limit must be at least one"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class Money(_StrictModel):
    amount: int | float
    currency: str

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.amount < 0 or not math.isfinite(self.amount):
            raise StateValidationError("Money.amount must be a finite non-negative number")
        if re.fullmatch(r"[A-Z]{3}", self.currency) is None:
            raise StateValidationError("Money.currency must be a three-letter uppercase code")


@dataclass(frozen=True, slots=True, kw_only=True)
class GoalBudget(_StrictModel):
    max_iterations: int | None
    max_elapsed_seconds: int | None
    max_input_tokens: int | None
    max_output_tokens: int | None
    max_total_tokens: int | None
    max_cost: Money | None
    retry_policy: RetryPolicy
    enforcement_owner: EnforcementOwner
    stop_on_exhaustion: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        for name in ("max_iterations", "max_elapsed_seconds"):
            value = getattr(self, name)
            if value is not None and value < 1:
                raise StateValidationError(f"GoalBudget.{name} must be at least one")
        for name in ("max_input_tokens", "max_output_tokens", "max_total_tokens"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise StateValidationError(f"GoalBudget.{name} must be non-negative")
        if not self.stop_on_exhaustion:
            raise StateValidationError("GoalBudget.stop_on_exhaustion must be true")


@dataclass(frozen=True, slots=True, kw_only=True)
class GoalScope(_StrictModel):
    in_scope: tuple[str, ...]
    out_of_scope: tuple[str, ...]
    allowed_files: tuple[LocationReference, ...]
    allowed_systems: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_string_items(self.in_scope, "GoalScope.in_scope")
        if not self.in_scope:
            raise StateValidationError("GoalScope.in_scope must not be empty")
        _require_string_items(self.out_of_scope, "GoalScope.out_of_scope")
        _require_unique(self.allowed_files, "GoalScope.allowed_files")
        _require_string_items(self.allowed_systems, "GoalScope.allowed_systems")
        overlap = set(self.in_scope).intersection(self.out_of_scope)
        if overlap:
            raise StateValidationError(
                f"GoalScope scope and non-goals overlap: {sorted(overlap)!r}"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class GoalConstraints(_StrictModel):
    must: tuple[Constraint, ...]
    must_not: tuple[Constraint, ...]
    safety: tuple[Constraint, ...]
    evidence: tuple[Constraint, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        all_constraints = self.must + self.must_not + self.safety + self.evidence
        _require_unique(self.must, "GoalConstraints.must")
        _require_unique(self.must_not, "GoalConstraints.must_not")
        _require_unique(self.safety, "GoalConstraints.safety")
        _require_unique(self.evidence, "GoalConstraints.evidence")
        _require_unique_ids(all_constraints, "id", "GoalConstraints constraint IDs")


@dataclass(frozen=True, slots=True, kw_only=True)
class GoalTools(_StrictModel):
    required: tuple[CapabilityRequirement, ...]
    optional: tuple[CapabilityRequirement, ...]
    avoid_or_disable: tuple[AvoidedCapability, ...]
    actual_exposure_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_unique(self.required, "GoalTools.required")
        _require_unique(self.optional, "GoalTools.optional")
        _require_unique(self.avoid_or_disable, "GoalTools.avoid_or_disable")
        capability_ids = tuple(item.capability_id for item in self.required + self.optional)
        avoided_ids = tuple(item.capability_id for item in self.avoid_or_disable)
        _require_unique(capability_ids, "GoalTools required/optional capability IDs")
        _require_unique(avoided_ids, "GoalTools avoided capability IDs")
        conflict = set(capability_ids).intersection(avoided_ids)
        if conflict:
            raise StateValidationError(
                f"GoalTools capabilities are both enabled and avoided: {sorted(conflict)!r}"
            )
        if not self.actual_exposure_required:
            raise StateValidationError("GoalTools.actual_exposure_required must be true")


@dataclass(frozen=True, slots=True, kw_only=True)
class GoalApprovals(_StrictModel):
    external_write_default: ApprovalRequirement
    consequential_action_default: ApprovalRequirement
    rules: tuple[ApprovalRule, ...]
    authorization_refs: tuple[LocationReference, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.external_write_default is not ApprovalRequirement.EXPLICIT_AUTHORIZATION:
            raise StateValidationError(
                "GoalApprovals.external_write_default must be EXPLICIT_AUTHORIZATION"
            )
        if self.consequential_action_default is not ApprovalRequirement.STRICT_PREFLIGHT:
            raise StateValidationError(
                "GoalApprovals.consequential_action_default must be STRICT_PREFLIGHT"
            )
        _require_unique(self.rules, "GoalApprovals.rules")
        _require_unique(self.authorization_refs, "GoalApprovals.authorization_refs")


@dataclass(frozen=True, slots=True, kw_only=True)
class GoalOutput(_StrictModel):
    id: str
    description: str
    destination: LocationReference
    format: str
    required: bool
    done_condition_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_stable_id(self.id, "GoalOutput.id")
        _require_string(self.description, "GoalOutput.description")
        _require_string(self.format, "GoalOutput.format")
        _require_string_items(
            self.done_condition_ids, "GoalOutput.done_condition_ids", stable_ids=True
        )
        if self.required and not self.done_condition_ids:
            raise StateValidationError("a required GoalOutput needs at least one done condition")


@dataclass(frozen=True, slots=True, kw_only=True)
class CompletionPolicy(_StrictModel):
    rule: CompletionRule = CompletionRule.ALL_MANDATORY_CONDITIONS_PASS
    deterministic_validation_first: bool = True
    evidence_required: bool = True
    fail_blocks_completion: bool = True
    insufficient_evidence_blocks_completion: bool = True
    worker_self_attestation_sufficient: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.rule is not CompletionRule.ALL_MANDATORY_CONDITIONS_PASS:
            raise StateValidationError("CompletionPolicy.rule is unsupported")
        if not all(
            (
                self.deterministic_validation_first,
                self.evidence_required,
                self.fail_blocks_completion,
                self.insufficient_evidence_blocks_completion,
            )
        ):
            raise StateValidationError("CompletionPolicy blocking and evidence flags must be true")
        if self.worker_self_attestation_sufficient:
            raise StateValidationError(
                "worker self-attestation cannot be sufficient for completion"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class Goal(_StrictModel):
    schema_version: str = SCHEMA_VERSION
    goal_id: str
    objective: str
    scope: GoalScope
    authoritative_inputs: tuple[LocationReference, ...]
    done_conditions: tuple[DoneCondition, ...]
    constraints: GoalConstraints
    tools: GoalTools
    approvals: GoalApprovals
    budget: GoalBudget
    outputs: tuple[GoalOutput, ...]
    completion_policy: CompletionPolicy
    created_at: datetime
    updated_at: datetime | None = field(default=None, metadata={"json_optional": True})

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.schema_version != SCHEMA_VERSION:
            raise StateValidationError(f"Goal.schema_version must be {SCHEMA_VERSION}")
        _require_stable_id(self.goal_id, "Goal.goal_id")
        _require_string(self.objective, "Goal.objective")
        _require_unique(self.authoritative_inputs, "Goal.authoritative_inputs")
        if not self.done_conditions:
            raise StateValidationError("Goal.done_conditions must not be empty")
        if not self.outputs:
            raise StateValidationError("Goal.outputs must not be empty")
        _require_unique(self.done_conditions, "Goal.done_conditions")
        _require_unique_ids(self.done_conditions, "id", "Goal done-condition IDs")
        _require_unique(self.outputs, "Goal.outputs")
        _require_unique_ids(self.outputs, "id", "Goal output IDs")
        if self.updated_at is not None and self.updated_at < self.created_at:
            raise StateValidationError("Goal.updated_at must not precede created_at")

        output_ids = {output.id for output in self.outputs}
        done_ids = {condition.id for condition in self.done_conditions}
        for condition in self.done_conditions:
            missing = set(condition.output_ids) - output_ids
            if missing:
                raise StateValidationError(
                    f"DoneCondition {condition.id!r} references missing outputs {sorted(missing)!r}"
                )
        for output in self.outputs:
            missing = set(output.done_condition_ids) - done_ids
            if missing:
                raise StateValidationError(
                    f"GoalOutput {output.id!r} references missing done conditions "
                    f"{sorted(missing)!r}"
                )

        condition_links = {
            (condition.id, output_id)
            for condition in self.done_conditions
            for output_id in condition.output_ids
        }
        output_links = {
            (condition_id, output.id)
            for output in self.outputs
            for condition_id in output.done_condition_ids
        }
        if condition_links != output_links:
            raise StateValidationError("Goal done-condition/output references must be reciprocal")


class TaskStatus(StrEnum):
    PLANNED = "PLANNED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    VALIDATING = "VALIDATING"
    CHECKPOINTED = "CHECKPOINTED"
    COMPLETE = "COMPLETE"
    BLOCKED = "BLOCKED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True, slots=True, kw_only=True)
class Task(_StrictModel):
    schema_version: str = SCHEMA_VERSION
    task_id: str
    goal_id: str
    description: str
    dependencies: tuple[str, ...] = ()
    status: TaskStatus = TaskStatus.PLANNED
    attempts: int = 0
    selected_workspace: str | None = None
    allowed_paths: tuple[str, ...] = ()
    locked_paths: tuple[str, ...] = ()
    criterion_ids: tuple[str, ...] = ()
    validation_commands: tuple[str, ...] = ()
    evidence_paths: tuple[str, ...] = ()
    last_failure: str | None = None
    next_action: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.schema_version != SCHEMA_VERSION:
            raise StateValidationError(f"Task.schema_version must be {SCHEMA_VERSION}")
        _require_stable_id(self.task_id, "Task.task_id")
        _require_stable_id(self.goal_id, "Task.goal_id")
        _require_string(self.description, "Task.description")
        _require_string_items(self.dependencies, "Task.dependencies", stable_ids=True)
        if self.task_id in self.dependencies:
            raise StateValidationError("Task cannot depend on itself")
        if self.attempts < 0:
            raise StateValidationError("Task.attempts must be non-negative")
        if self.selected_workspace is not None:
            _require_string(self.selected_workspace, "Task.selected_workspace", maximum=2048)
            if "\x00" in self.selected_workspace:
                raise StateValidationError("Task.selected_workspace must not contain NUL")
        for name in ("allowed_paths", "locked_paths", "evidence_paths"):
            values = getattr(self, name)
            _require_string_items(values, f"Task.{name}", maximum=2048)
            if any("\x00" in value for value in values):
                raise StateValidationError(f"Task.{name} must not contain NUL")
        _require_string_items(self.criterion_ids, "Task.criterion_ids", stable_ids=True)
        _require_string_items(self.validation_commands, "Task.validation_commands", maximum=8192)
        if self.last_failure is not None:
            _require_string(self.last_failure, "Task.last_failure")
        if self.next_action is not None:
            _require_string(self.next_action, "Task.next_action")
        if self.status is TaskStatus.COMPLETE:
            if not self.evidence_paths:
                raise StateValidationError("a COMPLETE task requires evidence_paths")
            if self.next_action is not None:
                raise StateValidationError("a COMPLETE task cannot have next_action")
        if self.status in {TaskStatus.BLOCKED, TaskStatus.APPROVAL_REQUIRED}:
            if self.next_action is None:
                raise StateValidationError(f"a {self.status.value} task requires next_action")
        if self.status is TaskStatus.FAILED and self.last_failure is None:
            raise StateValidationError("a FAILED task requires last_failure")


class LifecycleState(StrEnum):
    CREATED = "CREATED"
    INITIALIZING = "INITIALIZING"
    READY = "READY"
    SELECTING_TASK = "SELECTING_TASK"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    EVALUATING = "EVALUATING"
    CHECKPOINTING = "CHECKPOINTING"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class CompletionVerdict(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    NOT_EVALUATED = "NOT_EVALUATED"


class ApprovalStatus(StrEnum):
    REQUIRED = "REQUIRED"
    REQUESTED = "REQUESTED"
    GRANTED = "GRANTED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class StopReasonCode(StrEnum):
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"
    REPOSITORY_DIVERGENCE = "REPOSITORY_DIVERGENCE"
    UNSAFE_ACTION = "UNSAFE_ACTION"
    REPEATED_NO_PROGRESS = "REPEATED_NO_PROGRESS"
    REPEATED_INSUFFICIENT_EVIDENCE = "REPEATED_INSUFFICIENT_EVIDENCE"


class BudgetDimension(StrEnum):
    ITERATIONS = "ITERATIONS"
    ELAPSED_SECONDS = "ELAPSED_SECONDS"
    INPUT_TOKENS = "INPUT_TOKENS"
    OUTPUT_TOKENS = "OUTPUT_TOKENS"
    TOTAL_TOKENS = "TOTAL_TOKENS"
    COST = "COST"


@dataclass(frozen=True, slots=True, kw_only=True)
class BudgetValues(_StrictModel):
    iterations: int | None = None
    elapsed_seconds: float | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None
    cost: float | None = None

    _FIELD_BY_DIMENSION: ClassVar[dict[BudgetDimension, str]] = {
        BudgetDimension.ITERATIONS: "iterations",
        BudgetDimension.ELAPSED_SECONDS: "elapsed_seconds",
        BudgetDimension.INPUT_TOKENS: "input_tokens",
        BudgetDimension.OUTPUT_TOKENS: "output_tokens",
        BudgetDimension.TOTAL_TOKENS: "total_tokens",
        BudgetDimension.COST: "cost",
    }

    def __post_init__(self) -> None:
        super().__post_init__()
        for name in ("iterations", "input_tokens", "output_tokens", "total_tokens"):
            value = getattr(self, name)
            if value is not None and value < 0:
                raise StateValidationError(f"BudgetValues.{name} must be non-negative")
        for name in ("elapsed_seconds", "cost"):
            value = getattr(self, name)
            if value is not None and (value < 0 or not math.isfinite(value)):
                raise StateValidationError(f"BudgetValues.{name} must be finite and non-negative")

    def for_dimension(self, dimension: BudgetDimension) -> int | float | None:
        if type(dimension) is not BudgetDimension:
            raise TypeError("dimension must be BudgetDimension")
        return cast(int | float | None, getattr(self, self._FIELD_BY_DIMENSION[dimension]))


@dataclass(frozen=True, slots=True, kw_only=True)
class BudgetState(_StrictModel):
    limits: BudgetValues
    consumed: BudgetValues
    exhausted_dimensions: tuple[BudgetDimension, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_unique(self.exhausted_dimensions, "BudgetState.exhausted_dimensions")
        calculated = {
            dimension
            for dimension in BudgetDimension
            if self.limits.for_dimension(dimension) is not None
            and self.consumed.for_dimension(dimension) is not None
            and self.consumed.for_dimension(dimension) >= self.limits.for_dimension(dimension)  # type: ignore[operator]
        }
        recorded = set(self.exhausted_dimensions)
        if calculated != recorded:
            missing = sorted(item.value for item in calculated - recorded)
            stale = sorted(item.value for item in recorded - calculated)
            raise StateValidationError(
                "BudgetState.exhausted_dimensions is inconsistent with limits/consumed "
                f"(missing={missing!r}, stale={stale!r})"
            )


@dataclass(frozen=True, slots=True, kw_only=True)
class StopReason(_StrictModel):
    code: StopReasonCode
    summary: str
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        super().__post_init__()
        _require_string(self.summary, "StopReason.summary", normalized=True)
        _require_string_items(
            self.evidence_refs, "StopReason.evidence_refs", maximum=2048, normalized=True
        )


FINAL_STATES = frozenset(
    {LifecycleState.COMPLETED, LifecycleState.FAILED, LifecycleState.CANCELLED}
)
RESUMABLE_STOP_STATES = frozenset(
    {
        LifecycleState.BLOCKED,
        LifecycleState.BUDGET_EXHAUSTED,
        LifecycleState.APPROVAL_REQUIRED,
    }
)
FINAL = FINAL_STATES
RESUMABLE_STOPS = RESUMABLE_STOP_STATES
STOPPED_STATES = FINAL_STATES | RESUMABLE_STOP_STATES
ACTIVE_STATES = frozenset(LifecycleState) - STOPPED_STATES

_ORDINARY_TRANSITIONS: dict[LifecycleState, frozenset[LifecycleState]] = {
    LifecycleState.CREATED: frozenset({LifecycleState.INITIALIZING}),
    LifecycleState.INITIALIZING: frozenset({LifecycleState.READY}),
    LifecycleState.READY: frozenset({LifecycleState.SELECTING_TASK}),
    LifecycleState.SELECTING_TASK: frozenset({LifecycleState.EXECUTING}),
    LifecycleState.EXECUTING: frozenset({LifecycleState.VALIDATING}),
    LifecycleState.VALIDATING: frozenset({LifecycleState.EVALUATING, LifecycleState.CHECKPOINTING}),
    LifecycleState.EVALUATING: frozenset({LifecycleState.CHECKPOINTING}),
    LifecycleState.CHECKPOINTING: frozenset({LifecycleState.READY, LifecycleState.COMPLETED}),
}

_BLOCKED_CODES = frozenset(
    {
        StopReasonCode.BLOCKED,
        StopReasonCode.MISSING_DEPENDENCY,
        StopReasonCode.REPOSITORY_DIVERGENCE,
        StopReasonCode.UNSAFE_ACTION,
        StopReasonCode.REPEATED_NO_PROGRESS,
        StopReasonCode.REPEATED_INSUFFICIENT_EVIDENCE,
    }
)
_STOP_CODES: dict[LifecycleState, frozenset[StopReasonCode]] = {
    LifecycleState.COMPLETED: frozenset({StopReasonCode.COMPLETED}),
    LifecycleState.BLOCKED: _BLOCKED_CODES,
    LifecycleState.BUDGET_EXHAUSTED: frozenset({StopReasonCode.BUDGET_EXHAUSTED}),
    LifecycleState.APPROVAL_REQUIRED: frozenset({StopReasonCode.APPROVAL_REQUIRED}),
    LifecycleState.FAILED: frozenset({StopReasonCode.FAILED}),
    LifecycleState.CANCELLED: frozenset({StopReasonCode.CANCELLED}),
}


def can_transition(prior_state: LifecycleState, next_state: LifecycleState) -> bool:
    """Return whether C-401 permits this lifecycle edge, without mutating state."""

    if type(prior_state) is not LifecycleState or type(next_state) is not LifecycleState:
        return False
    if prior_state in STOPPED_STATES:
        return False
    allowed = _ORDINARY_TRANSITIONS.get(prior_state, frozenset())
    return (
        next_state in allowed
        or next_state in RESUMABLE_STOP_STATES
        or next_state
        in {
            LifecycleState.FAILED,
            LifecycleState.CANCELLED,
        }
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class Run(_StrictModel):
    schema_version: str = SCHEMA_VERSION
    run_id: str
    goal_id: str
    provider: str
    model: str
    reasoning_effort: str | None
    provider_config_ref: str | None
    lifecycle_state: LifecycleState
    started_at: datetime
    updated_at: datetime
    iteration_count: int
    budget: BudgetState
    current_task_id: str | None
    approval_state: ApprovalStatus | None
    checkpoint_ref: str | None
    stop_reason: StopReason | None
    completion_verdict: CompletionVerdict
    completion_evidence_refs: tuple[str, ...]
    event_seq: int
    last_transition_id: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.schema_version != SCHEMA_VERSION:
            raise StateValidationError(f"Run.schema_version must be {SCHEMA_VERSION}")
        _require_stable_id(self.run_id, "Run.run_id")
        _require_stable_id(self.goal_id, "Run.goal_id")
        _require_stable_id(self.provider, "Run.provider")
        _require_string(self.model, "Run.model", maximum=256, normalized=True)
        if self.reasoning_effort is not None:
            _require_string(
                self.reasoning_effort, "Run.reasoning_effort", maximum=128, normalized=True
            )
        if self.provider_config_ref is not None:
            _require_string(
                self.provider_config_ref,
                "Run.provider_config_ref",
                maximum=2048,
                normalized=True,
            )
        if self.updated_at < self.started_at:
            raise StateValidationError("Run.updated_at must not precede started_at")
        if self.iteration_count < 0:
            raise StateValidationError("Run.iteration_count must be non-negative")
        if self.current_task_id is not None:
            _require_stable_id(self.current_task_id, "Run.current_task_id")
        if self.checkpoint_ref is not None:
            _require_string(
                self.checkpoint_ref, "Run.checkpoint_ref", maximum=2048, normalized=True
            )
        _require_string_items(
            self.completion_evidence_refs,
            "Run.completion_evidence_refs",
            maximum=2048,
            normalized=True,
        )
        if self.event_seq < 0:
            raise StateValidationError("Run.event_seq must be non-negative")
        if self.last_transition_id is not None:
            _require_stable_id(self.last_transition_id, "Run.last_transition_id")
            if self.event_seq == 0:
                raise StateValidationError("Run.last_transition_id requires a positive event_seq")

        if self.lifecycle_state in ACTIVE_STATES:
            if self.stop_reason is not None:
                raise StateValidationError("an active Run cannot have stop_reason")
        else:
            if self.stop_reason is None:
                raise StateValidationError(
                    f"a {self.lifecycle_state.value} Run requires stop_reason"
                )
            allowed_codes = _STOP_CODES[self.lifecycle_state]
            if self.stop_reason.code not in allowed_codes:
                raise StateValidationError(
                    f"{self.lifecycle_state.value} does not allow stop code "
                    f"{self.stop_reason.code.value}"
                )

        if self.lifecycle_state is LifecycleState.COMPLETED:
            if self.completion_verdict is not CompletionVerdict.PASS:
                raise StateValidationError("a COMPLETED Run requires PASS")
            if not self.completion_evidence_refs:
                raise StateValidationError("a COMPLETED Run requires completion evidence")
            if self.checkpoint_ref is None:
                raise StateValidationError("a COMPLETED Run requires checkpoint_ref")
        elif self.completion_verdict is CompletionVerdict.PASS:
            raise StateValidationError("only a COMPLETED Run may have PASS completion verdict")
        if self.lifecycle_state is LifecycleState.APPROVAL_REQUIRED and self.approval_state not in {
            ApprovalStatus.REQUIRED,
            ApprovalStatus.REQUESTED,
        }:
            raise StateValidationError(
                "an APPROVAL_REQUIRED Run needs REQUIRED or REQUESTED approval state"
            )
        if (
            self.lifecycle_state is not LifecycleState.APPROVAL_REQUIRED
            and self.approval_state is not None
        ):
            raise StateValidationError(
                "only an APPROVAL_REQUIRED Run may retain a pending approval state"
            )
        if self.lifecycle_state is LifecycleState.BUDGET_EXHAUSTED:
            if not self.budget.exhausted_dimensions:
                raise StateValidationError(
                    "a BUDGET_EXHAUSTED Run requires an exhausted budget dimension"
                )


class EventType(StrEnum):
    LIFECYCLE = "LIFECYCLE"
    VALIDATION = "VALIDATION"
    APPROVAL = "APPROVAL"
    ACTION = "ACTION"
    RETRY = "RETRY"
    CHECKPOINT = "CHECKPOINT"
    RECOVERY = "RECOVERY"
    POLICY = "POLICY"
    TERMINAL = "TERMINAL"


class RedactionStatus(StrEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REDACTED = "REDACTED"


@dataclass(frozen=True, slots=True, kw_only=True)
class Event(_StrictModel):
    schema_version: str = SCHEMA_VERSION
    event_seq: int
    timestamp: datetime
    run_id: str
    task_id: str | None
    event_type: EventType
    source: str
    action_summary: str
    input_refs: tuple[str, ...]
    output_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    result: str
    error_category: str | None
    redaction_status: RedactionStatus
    transition_id: str | None
    prior_state: LifecycleState | None
    next_state: LifecycleState | None
    reason: str | None
    correlation_id: str | None

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.schema_version != SCHEMA_VERSION:
            raise StateValidationError(f"Event.schema_version must be {SCHEMA_VERSION}")
        if self.event_seq < 1:
            raise StateValidationError("Event.event_seq must be at least one")
        _require_stable_id(self.run_id, "Event.run_id")
        if self.task_id is not None:
            _require_stable_id(self.task_id, "Event.task_id")
        _require_string(self.source, "Event.source", maximum=256, normalized=True)
        _require_string(self.action_summary, "Event.action_summary", normalized=True)
        for name in ("input_refs", "output_refs", "evidence_refs"):
            _require_string_items(
                getattr(self, name), f"Event.{name}", maximum=2048, normalized=True
            )
        _require_string(self.result, "Event.result", normalized=True)
        if self.error_category is not None:
            _require_string(
                self.error_category, "Event.error_category", maximum=256, normalized=True
            )
        if self.transition_id is not None:
            _require_stable_id(self.transition_id, "Event.transition_id")
        if self.reason is not None:
            _require_string(self.reason, "Event.reason", normalized=True)
        if self.correlation_id is not None:
            _require_stable_id(self.correlation_id, "Event.correlation_id")

        transition_values = (
            self.transition_id,
            self.prior_state,
            self.next_state,
            self.reason,
        )
        transition_event_types = {EventType.LIFECYCLE, EventType.TERMINAL}
        if self.event_type in transition_event_types:
            if any(value is None for value in transition_values):
                raise StateValidationError(
                    f"a {self.event_type.value} Event requires complete transition metadata"
                )
        elif any(value is not None for value in transition_values):
            raise StateValidationError("a non-transition Event requires null transition metadata")
        if all(value is not None for value in transition_values):
            if not can_transition(self.prior_state, self.next_state):  # type: ignore[arg-type]
                raise StateValidationError("Event contains an invalid lifecycle edge")
        if self.event_type is EventType.TERMINAL and self.next_state not in STOPPED_STATES:
            raise StateValidationError("a TERMINAL Event must enter a stopped lifecycle state")


_UNSET = object()


def transition_run(
    run: Run,
    next_state: LifecycleState,
    *,
    transition_id: str,
    timestamp: datetime,
    reason: str,
    stop_reason: StopReason | None = None,
    completion_verdict: CompletionVerdict | None = None,
    completion_evidence_refs: tuple[str, ...] | None = None,
    checkpoint_ref: str | None | object = _UNSET,
    approval_state: ApprovalStatus | None | object = _UNSET,
    source: str = "harness.lifecycle",
    action_summary: str | None = None,
    input_refs: tuple[str, ...] = (),
    output_refs: tuple[str, ...] = (),
    evidence_refs: tuple[str, ...] | None = None,
    result: str | None = None,
    error_category: str | None = None,
    redaction_status: RedactionStatus = RedactionStatus.NOT_REQUIRED,
    correlation_id: str | None = None,
) -> tuple[Run, Event]:
    """Return one validated immutable Run/Event transition pair.

    This function has no persistence or provider side effects.  A later state
    store must commit the returned pair atomically before dispatching another
    external action.
    """

    if type(run) is not Run:
        raise TypeError("run must be a Run")
    if type(next_state) is not LifecycleState:
        raise TypeError("next_state must be a LifecycleState")
    try:
        _require_stable_id(transition_id, "transition_id")
    except StateValidationError as exc:
        raise TransitionError(str(exc)) from exc
    if transition_id == run.last_transition_id:
        raise DuplicateTransitionError(
            f"transition_id {transition_id!r} is already the run's last transition"
        )
    if not can_transition(run.lifecycle_state, next_state):
        raise InvalidTransitionError(
            f"invalid lifecycle transition {run.lifecycle_state.value} -> {next_state.value}"
        )
    _validate_runtime_type(timestamp, datetime, "timestamp")
    if timestamp < run.updated_at:
        raise TransitionError("transition timestamp must not precede Run.updated_at")
    try:
        _require_string(reason, "reason", normalized=True)
    except StateValidationError as exc:
        raise TransitionError(str(exc)) from exc
    if stop_reason is not None and type(stop_reason) is not StopReason:
        raise TypeError("stop_reason must be StopReason or null")

    if next_state in STOPPED_STATES:
        if stop_reason is None:
            raise TransitionError(f"transition to {next_state.value} requires stop_reason")
        if stop_reason.code not in _STOP_CODES[next_state]:
            raise TransitionError(
                f"transition to {next_state.value} does not allow stop code "
                f"{stop_reason.code.value}"
            )
    elif stop_reason is not None:
        raise TransitionError("an active lifecycle transition cannot set stop_reason")

    new_completion_verdict = (
        run.completion_verdict if completion_verdict is None else completion_verdict
    )
    new_completion_evidence_refs = run.completion_evidence_refs
    if completion_evidence_refs is not None:
        if type(completion_evidence_refs) is not tuple:
            raise TypeError("completion_evidence_refs must be a tuple")
        new_completion_evidence_refs = completion_evidence_refs
    new_checkpoint_ref = run.checkpoint_ref
    if checkpoint_ref is not _UNSET:
        if checkpoint_ref is not None and type(checkpoint_ref) is not str:
            raise TypeError("checkpoint_ref must be a string or null")
        new_checkpoint_ref = checkpoint_ref
    new_approval_state = run.approval_state
    if approval_state is not _UNSET:
        if approval_state is not None and type(approval_state) is not ApprovalStatus:
            raise TypeError("approval_state must be ApprovalStatus or null")
        new_approval_state = approval_state

    try:
        updated_run = replace(
            run,
            lifecycle_state=next_state,
            updated_at=timestamp,
            approval_state=new_approval_state,
            checkpoint_ref=new_checkpoint_ref,
            stop_reason=stop_reason,
            completion_verdict=new_completion_verdict,
            completion_evidence_refs=new_completion_evidence_refs,
            event_seq=run.event_seq + 1,
            last_transition_id=transition_id,
        )
    except StateValidationError as exc:
        raise TransitionError(f"transition would create invalid run state: {exc}") from exc
    effective_evidence = evidence_refs
    if effective_evidence is None:
        if stop_reason is not None and stop_reason.evidence_refs:
            effective_evidence = stop_reason.evidence_refs
        elif next_state is LifecycleState.COMPLETED:
            effective_evidence = updated_run.completion_evidence_refs
        else:
            effective_evidence = ()

    event = Event(
        event_seq=updated_run.event_seq,
        timestamp=timestamp,
        run_id=updated_run.run_id,
        task_id=updated_run.current_task_id,
        event_type=(EventType.TERMINAL if next_state in STOPPED_STATES else EventType.LIFECYCLE),
        source=source,
        action_summary=(
            action_summary
            if action_summary is not None
            else f"Transition {run.lifecycle_state.value} -> {next_state.value}"
        ),
        input_refs=input_refs,
        output_refs=output_refs,
        evidence_refs=effective_evidence,
        result=result if result is not None else next_state.value,
        error_category=error_category,
        redaction_status=redaction_status,
        transition_id=transition_id,
        prior_state=run.lifecycle_state,
        next_state=next_state,
        reason=reason,
        correlation_id=correlation_id,
    )
    return updated_run, event


__all__ = [
    "ACTIVE_STATES",
    "ActionClass",
    "ApprovalRequirement",
    "ApprovalRule",
    "ApprovalStatus",
    "AvoidedCapability",
    "BudgetDimension",
    "BudgetState",
    "BudgetValues",
    "CapabilityRequirement",
    "CompletionPolicy",
    "CompletionRule",
    "CompletionVerdict",
    "Constraint",
    "DoneCondition",
    "DoneConditionVerification",
    "DuplicateTransitionError",
    "EnforcementOwner",
    "EvaluatorAccess",
    "Event",
    "EventType",
    "FINAL",
    "FINAL_STATES",
    "Goal",
    "GoalApprovals",
    "GoalBudget",
    "GoalConstraints",
    "GoalOutput",
    "GoalScope",
    "GoalTools",
    "InvalidTransitionError",
    "LifecycleState",
    "LocationKind",
    "LocationReference",
    "Money",
    "RedactionStatus",
    "RequiredActionScope",
    "RESUMABLE_STOPS",
    "RESUMABLE_STOP_STATES",
    "RetryPolicy",
    "Run",
    "SCHEMA_VERSION",
    "STOPPED_STATES",
    "StateValidationError",
    "StopReason",
    "StopReasonCode",
    "Task",
    "TaskStatus",
    "TransitionError",
    "VerificationMethod",
    "can_transition",
    "transition_run",
]
