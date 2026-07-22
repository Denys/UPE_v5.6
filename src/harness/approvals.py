"""Trusted-host action classification and exact-scope approval validation.

Repository text, provider events, model output, and prior unrelated approvals
are untrusted inputs.  Only an immutable host record that matches the complete
requested effect may authorize a consequential action.  This module performs
no persistence or external action.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from harness.state import ActionClass, ApprovalStatus

_STABLE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


class Decision(StrEnum):
    """Host policy result; only ``ALLOWED`` permits the requested effect."""

    ALLOWED = "ALLOWED"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED"
    FORBIDDEN = "FORBIDDEN"


class ApprovalReason(StrEnum):
    """Stable audit reason for an approval decision."""

    NON_CONSEQUENTIAL = "NON_CONSEQUENTIAL"
    EXACT_GRANT = "EXACT_GRANT"
    APPROVAL_MISSING = "APPROVAL_MISSING"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    APPROVAL_EXPIRED = "APPROVAL_EXPIRED"
    APPROVAL_REVOKED = "APPROVAL_REVOKED"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    MALFORMED_INPUT = "MALFORMED_INPUT"
    FORBIDDEN_ACTION = "FORBIDDEN_ACTION"
    FUTURE_DECISION = "FUTURE_DECISION"


@dataclass(frozen=True, slots=True, kw_only=True)
class ApprovalRecord:
    """Durable host decision bound to one exact requested effect."""

    approval_id: str
    requested_by_run: str
    action_class: ActionClass
    target_identity: str
    normalized_arguments_digest: str
    content_or_patch_digest: str | None
    repository_identity: str
    branch_identity: str
    maximum_effects: int
    expires_at: datetime
    status: ApprovalStatus
    decided_by: str | None = None
    decided_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_id(self.approval_id, "ApprovalRecord.approval_id")
        _require_id(self.requested_by_run, "ApprovalRecord.requested_by_run")
        _require_enum(self.action_class, ActionClass, "ApprovalRecord.action_class")
        _require_text(self.target_identity, "ApprovalRecord.target_identity")
        _require_digest(
            self.normalized_arguments_digest,
            "ApprovalRecord.normalized_arguments_digest",
        )
        _require_optional_digest(
            self.content_or_patch_digest,
            "ApprovalRecord.content_or_patch_digest",
        )
        _require_text(self.repository_identity, "ApprovalRecord.repository_identity")
        _require_text(self.branch_identity, "ApprovalRecord.branch_identity")
        if type(self.maximum_effects) is not int or self.maximum_effects != 1:
            raise ValueError("ApprovalRecord.maximum_effects must be exactly one")
        object.__setattr__(
            self,
            "expires_at",
            _require_time(self.expires_at, "ApprovalRecord.expires_at"),
        )
        _require_enum(self.status, ApprovalStatus, "ApprovalRecord.status")

        resolved = self.status in {
            ApprovalStatus.GRANTED,
            ApprovalStatus.DENIED,
            ApprovalStatus.EXPIRED,
            ApprovalStatus.REVOKED,
        }
        if resolved:
            if self.decided_by is None or self.decided_at is None:
                raise ValueError("a resolved ApprovalRecord requires decision metadata")
            _require_id(self.decided_by, "ApprovalRecord.decided_by")
            decided_at = _require_time(self.decided_at, "ApprovalRecord.decided_at")
            object.__setattr__(self, "decided_at", decided_at)
            if self.status is ApprovalStatus.GRANTED and decided_at >= self.expires_at:
                raise ValueError("a granted ApprovalRecord must be decided before expiry")
        elif self.decided_by is not None or self.decided_at is not None:
            raise ValueError("a pending ApprovalRecord cannot contain decision metadata")


@dataclass(frozen=True, slots=True, kw_only=True)
class ApprovalCheck:
    """The exact effect the trusted host is about to dispatch."""

    requested_by_run: str
    action_class: ActionClass
    target_identity: str
    normalized_arguments_digest: str
    content_or_patch_digest: str | None
    repository_identity: str
    branch_identity: str
    effect_count: int
    checked_at: datetime

    def __post_init__(self) -> None:
        _require_id(self.requested_by_run, "ApprovalCheck.requested_by_run")
        _require_enum(self.action_class, ActionClass, "ApprovalCheck.action_class")
        _require_text(self.target_identity, "ApprovalCheck.target_identity")
        _require_digest(
            self.normalized_arguments_digest,
            "ApprovalCheck.normalized_arguments_digest",
        )
        _require_optional_digest(
            self.content_or_patch_digest,
            "ApprovalCheck.content_or_patch_digest",
        )
        _require_text(self.repository_identity, "ApprovalCheck.repository_identity")
        _require_text(self.branch_identity, "ApprovalCheck.branch_identity")
        if type(self.effect_count) is not int or self.effect_count != 1:
            raise ValueError("ApprovalCheck.effect_count must be exactly one")
        object.__setattr__(
            self,
            "checked_at",
            _require_time(self.checked_at, "ApprovalCheck.checked_at"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ApprovalDecision:
    """Fail-closed validation result for one action boundary."""

    decision: Decision
    reason_code: ApprovalReason
    reason: str
    approval_id: str | None = None
    status: ApprovalStatus | None = None

    def __post_init__(self) -> None:
        _require_enum(self.decision, Decision, "ApprovalDecision.decision")
        _require_enum(self.reason_code, ApprovalReason, "ApprovalDecision.reason_code")
        _require_text(self.reason, "ApprovalDecision.reason")
        if self.approval_id is not None:
            _require_id(self.approval_id, "ApprovalDecision.approval_id")
        if self.status is not None:
            _require_enum(self.status, ApprovalStatus, "ApprovalDecision.status")
        if self.reason_code is ApprovalReason.EXACT_GRANT and (
            self.decision is not Decision.ALLOWED
            or self.approval_id is None
            or self.status is not ApprovalStatus.GRANTED
        ):
            raise ValueError("an exact-grant decision requires a granted approval")

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOWED


_ACTION_POLICY: dict[ActionClass, Decision] = {
    ActionClass.READ: Decision.ALLOWED,
    ActionClass.TRANSFORM: Decision.ALLOWED,
    ActionClass.DRAFT: Decision.ALLOWED,
    # WRITE means a local write that must separately pass the assigned-worktree
    # permission boundary.  External writes have their own action class.
    ActionClass.WRITE: Decision.ALLOWED,
    ActionClass.COMMIT: Decision.APPROVAL_REQUIRED,
    ActionClass.PUSH: Decision.APPROVAL_REQUIRED,
    ActionClass.CREATE_PR: Decision.APPROVAL_REQUIRED,
    ActionClass.UPDATE_PR: Decision.APPROVAL_REQUIRED,
    ActionClass.MERGE: Decision.APPROVAL_REQUIRED,
    ActionClass.RELEASE: Decision.APPROVAL_REQUIRED,
    ActionClass.DEPLOY: Decision.APPROVAL_REQUIRED,
    ActionClass.VISIBILITY_CHANGE: Decision.APPROVAL_REQUIRED,
    ActionClass.EXTERNAL_MESSAGE: Decision.APPROVAL_REQUIRED,
    ActionClass.PURCHASE: Decision.APPROVAL_REQUIRED,
    ActionClass.PRODUCTION_MUTATION: Decision.APPROVAL_REQUIRED,
    ActionClass.DESTRUCTIVE_ACTION: Decision.APPROVAL_REQUIRED,
    ActionClass.SECRET_HANDLING: Decision.APPROVAL_REQUIRED,
    ActionClass.OTHER_EXTERNAL_WRITE: Decision.APPROVAL_REQUIRED,
    # This umbrella class is too ambiguous to approve.  It must first be
    # narrowed to one concrete class and exact target.
    ActionClass.IRREVERSIBLE_OR_HIGH_CONSEQUENCE: Decision.FORBIDDEN,
}
if set(_ACTION_POLICY) != set(ActionClass):  # pragma: no cover - import invariant
    raise RuntimeError("every ActionClass must have an explicit host policy")


def classify_action(action_class: object) -> Decision:
    """Classify every known action explicitly and reject unknown values."""

    if type(action_class) is not ActionClass:
        return Decision.FORBIDDEN
    return _ACTION_POLICY[action_class]


def validate_approval(record: object, check: object) -> ApprovalDecision:
    """Allow only a current ``GRANTED`` record with identical complete scope."""

    if type(record) is not ApprovalRecord or type(check) is not ApprovalCheck:
        return _decision(
            Decision.FORBIDDEN,
            ApprovalReason.MALFORMED_INPUT,
            "approval record or check is malformed",
        )
    if record.status in {ApprovalStatus.REQUIRED, ApprovalStatus.REQUESTED}:
        return _decision(
            Decision.APPROVAL_REQUIRED,
            ApprovalReason.APPROVAL_PENDING,
            "approval is not granted",
            record=record,
        )
    terminal_reasons = {
        ApprovalStatus.DENIED: ApprovalReason.APPROVAL_DENIED,
        ApprovalStatus.EXPIRED: ApprovalReason.APPROVAL_EXPIRED,
        ApprovalStatus.REVOKED: ApprovalReason.APPROVAL_REVOKED,
    }
    if record.status in terminal_reasons:
        return _decision(
            Decision.FORBIDDEN,
            terminal_reasons[record.status],
            f"approval is {record.status.value.lower()}",
            record=record,
        )
    if record.status is not ApprovalStatus.GRANTED:
        return _decision(
            Decision.FORBIDDEN,
            ApprovalReason.MALFORMED_INPUT,
            "approval has an unknown status",
            record=record,
        )
    if record.decided_by is None or record.decided_at is None:
        return _decision(
            Decision.FORBIDDEN,
            ApprovalReason.MALFORMED_INPUT,
            "granted approval lacks trusted decision metadata",
            record=record,
        )
    if record.decided_at > check.checked_at:
        return _decision(
            Decision.FORBIDDEN,
            ApprovalReason.FUTURE_DECISION,
            "approval decision is later than the dispatch check",
            record=record,
        )
    if check.checked_at >= record.expires_at:
        return _decision(
            Decision.FORBIDDEN,
            ApprovalReason.APPROVAL_EXPIRED,
            "approval is expired at dispatch time",
            record=record,
            status=ApprovalStatus.EXPIRED,
        )

    comparisons = (
        (record.requested_by_run, check.requested_by_run),
        (record.action_class, check.action_class),
        (record.target_identity, check.target_identity),
        (record.normalized_arguments_digest, check.normalized_arguments_digest),
        (record.content_or_patch_digest, check.content_or_patch_digest),
        (record.repository_identity, check.repository_identity),
        (record.branch_identity, check.branch_identity),
        (record.maximum_effects, check.effect_count),
    )
    if any(approved != requested for approved, requested in comparisons):
        return _decision(
            Decision.APPROVAL_REQUIRED,
            ApprovalReason.SCOPE_MISMATCH,
            "approval scope does not match the requested effect",
            record=record,
        )
    return _decision(
        Decision.ALLOWED,
        ApprovalReason.EXACT_GRANT,
        "exact granted approval is valid for one effect",
        record=record,
    )


def evaluate_action(
    action_class: object,
    *,
    record: object | None = None,
    check: object | None = None,
) -> ApprovalDecision:
    """Apply taxonomy first, then exact approval validation when required."""

    classification = classify_action(action_class)
    if classification is Decision.FORBIDDEN:
        return _decision(
            Decision.FORBIDDEN,
            ApprovalReason.FORBIDDEN_ACTION,
            "action class is unknown, ambiguous, or forbidden",
        )
    if classification is Decision.ALLOWED:
        return _decision(
            Decision.ALLOWED,
            ApprovalReason.NON_CONSEQUENTIAL,
            "action class does not require consequential authority",
        )
    if record is None or check is None:
        return _decision(
            Decision.APPROVAL_REQUIRED,
            ApprovalReason.APPROVAL_MISSING,
            "consequential action requires an exact trusted-host approval",
        )
    if type(check) is ApprovalCheck and check.action_class is not action_class:
        return _decision(
            Decision.APPROVAL_REQUIRED,
            ApprovalReason.SCOPE_MISMATCH,
            "approval check action class does not match the requested action boundary",
            record=record if type(record) is ApprovalRecord else None,
        )
    return validate_approval(record, check)


def _decision(
    decision: Decision,
    reason_code: ApprovalReason,
    reason: str,
    *,
    record: ApprovalRecord | None = None,
    status: ApprovalStatus | None = None,
) -> ApprovalDecision:
    return ApprovalDecision(
        decision=decision,
        reason_code=reason_code,
        reason=reason,
        approval_id=record.approval_id if record is not None else None,
        status=status if status is not None else (record.status if record is not None else None),
    )


def _require_enum(value: object, expected: type[StrEnum], location: str) -> None:
    if type(value) is not expected:
        raise TypeError(f"{location} must be {expected.__name__}")


def _require_id(value: object, location: str) -> None:
    if type(value) is not str or _STABLE_ID.fullmatch(value) is None:
        raise ValueError(f"{location} must be a stable identifier")


def _require_text(value: object, location: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{location} must be a string")
    if not value or value != value.strip() or len(value) > 4096:
        raise ValueError(f"{location} must be normalized non-empty text")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{location} must be single-line text")


def _require_digest(value: object, location: str) -> None:
    if type(value) is not str or _DIGEST.fullmatch(value) is None:
        raise ValueError(f"{location} must be a lowercase SHA-256 digest")


def _require_optional_digest(value: object, location: str) -> None:
    if value is not None:
        _require_digest(value, location)


def _require_time(value: object, location: str) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{location} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{location} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = [
    "ApprovalCheck",
    "ApprovalDecision",
    "ApprovalReason",
    "ApprovalRecord",
    "Decision",
    "classify_action",
    "evaluate_action",
    "validate_approval",
]
