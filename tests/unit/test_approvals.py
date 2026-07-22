from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta

import pytest

from harness.approvals import (
    ApprovalCheck,
    ApprovalReason,
    ApprovalRecord,
    Decision,
    classify_action,
    evaluate_action,
    validate_approval,
)
from harness.state import ActionClass, ApprovalStatus

NOW = datetime(2026, 7, 22, 9, 0, tzinfo=UTC)
DIGEST_A = "a" * 64
DIGEST_B = "b" * 64


def approval_record(**changes: object) -> ApprovalRecord:
    values: dict[str, object] = {
        "approval_id": "AP-c505-001",
        "requested_by_run": "run-c505",
        "action_class": ActionClass.PUSH,
        "target_identity": "origin:refs/heads/codex/c505",
        "normalized_arguments_digest": DIGEST_A,
        "content_or_patch_digest": DIGEST_B,
        "repository_identity": "Denys/UPE_v5.6",
        "branch_identity": "codex/c505-cloud-coordinator@abc1234",
        "maximum_effects": 1,
        "expires_at": NOW + timedelta(minutes=10),
        "status": ApprovalStatus.GRANTED,
        "decided_by": "user-denys",
        "decided_at": NOW - timedelta(minutes=1),
    }
    values.update(changes)
    return ApprovalRecord(**values)  # type: ignore[arg-type]


def approval_check(**changes: object) -> ApprovalCheck:
    values: dict[str, object] = {
        "requested_by_run": "run-c505",
        "action_class": ActionClass.PUSH,
        "target_identity": "origin:refs/heads/codex/c505",
        "normalized_arguments_digest": DIGEST_A,
        "content_or_patch_digest": DIGEST_B,
        "repository_identity": "Denys/UPE_v5.6",
        "branch_identity": "codex/c505-cloud-coordinator@abc1234",
        "effect_count": 1,
        "checked_at": NOW,
    }
    values.update(changes)
    return ApprovalCheck(**values)  # type: ignore[arg-type]


def test_exact_current_grant_allows_one_effect() -> None:
    result = validate_approval(approval_record(), approval_check())

    assert result.decision is Decision.ALLOWED
    assert result.reason_code is ApprovalReason.EXACT_GRANT
    assert result.status is ApprovalStatus.GRANTED
    assert result.approval_id == "AP-c505-001"
    assert result.allowed


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("requested_by_run", "run-other"),
        ("action_class", ActionClass.MERGE),
        ("target_identity", "origin:refs/heads/main"),
        ("normalized_arguments_digest", DIGEST_B),
        ("content_or_patch_digest", None),
        ("repository_identity", "someone/other"),
        ("branch_identity", "main@def5678"),
    ],
)
def test_every_scope_change_requires_a_new_approval(field: str, value: object) -> None:
    result = validate_approval(approval_record(), approval_check(**{field: value}))

    assert result.decision is Decision.APPROVAL_REQUIRED
    assert result.reason_code is ApprovalReason.SCOPE_MISMATCH


def test_null_content_digest_is_exact_scope_not_a_wildcard() -> None:
    exact = validate_approval(
        approval_record(content_or_patch_digest=None),
        approval_check(content_or_patch_digest=None),
    )
    changed = validate_approval(
        approval_record(content_or_patch_digest=None),
        approval_check(content_or_patch_digest=DIGEST_B),
    )

    assert exact.allowed
    assert changed.decision is Decision.APPROVAL_REQUIRED


@pytest.mark.parametrize(
    ("status", "expected_reason"),
    [
        (ApprovalStatus.DENIED, ApprovalReason.APPROVAL_DENIED),
        (ApprovalStatus.EXPIRED, ApprovalReason.APPROVAL_EXPIRED),
        (ApprovalStatus.REVOKED, ApprovalReason.APPROVAL_REVOKED),
    ],
)
def test_terminal_negative_decisions_are_forbidden(
    status: ApprovalStatus, expected_reason: ApprovalReason
) -> None:
    result = validate_approval(approval_record(status=status), approval_check())

    assert result.decision is Decision.FORBIDDEN
    assert result.reason_code is expected_reason


@pytest.mark.parametrize("status", [ApprovalStatus.REQUIRED, ApprovalStatus.REQUESTED])
def test_pending_decisions_pause_without_dispatch(status: ApprovalStatus) -> None:
    result = validate_approval(
        approval_record(status=status, decided_by=None, decided_at=None),
        approval_check(),
    )

    assert result.decision is Decision.APPROVAL_REQUIRED
    assert result.reason_code is ApprovalReason.APPROVAL_PENDING


def test_expiry_and_future_decision_fail_closed() -> None:
    expired = validate_approval(
        approval_record(expires_at=NOW),
        approval_check(checked_at=NOW),
    )
    future = validate_approval(
        approval_record(decided_at=NOW + timedelta(seconds=1)),
        approval_check(checked_at=NOW),
    )

    assert expired.reason_code is ApprovalReason.APPROVAL_EXPIRED
    assert expired.decision is Decision.FORBIDDEN
    assert future.reason_code is ApprovalReason.FUTURE_DECISION
    assert future.decision is Decision.FORBIDDEN


def test_malformed_inputs_and_unknown_action_fail_closed() -> None:
    malformed = validate_approval({"status": "GRANTED"}, approval_check())

    assert malformed.decision is Decision.FORBIDDEN
    assert malformed.reason_code is ApprovalReason.MALFORMED_INPUT
    assert classify_action("PUSH") is Decision.FORBIDDEN
    assert evaluate_action("PUSH").reason_code is ApprovalReason.FORBIDDEN_ACTION


def test_action_taxonomy_is_exhaustive_and_consequential_actions_pause() -> None:
    local = {
        ActionClass.READ,
        ActionClass.TRANSFORM,
        ActionClass.DRAFT,
        ActionClass.WRITE,
    }
    approval_required = set(ActionClass) - local - {ActionClass.IRREVERSIBLE_OR_HIGH_CONSEQUENCE}

    assert {item for item in ActionClass if classify_action(item) is Decision.ALLOWED} == local
    assert {
        item for item in ActionClass if classify_action(item) is Decision.APPROVAL_REQUIRED
    } == approval_required
    assert classify_action(ActionClass.IRREVERSIBLE_OR_HIGH_CONSEQUENCE) is Decision.FORBIDDEN
    for action_class in approval_required:
        result = evaluate_action(action_class)
        assert result.decision is Decision.APPROVAL_REQUIRED
        assert result.reason_code is ApprovalReason.APPROVAL_MISSING


def test_evaluate_action_never_uses_an_approval_for_a_different_class() -> None:
    result = evaluate_action(
        ActionClass.MERGE,
        record=approval_record(),
        check=approval_check(),
    )

    assert result.decision is Decision.APPROVAL_REQUIRED
    assert result.reason_code is ApprovalReason.SCOPE_MISMATCH


@pytest.mark.parametrize(
    "changes",
    [
        {"approval_id": "bad id"},
        {"normalized_arguments_digest": "A" * 64},
        {"content_or_patch_digest": "short"},
        {"maximum_effects": 2},
        {"expires_at": datetime(2026, 7, 22, 9, 0)},
        {"status": ApprovalStatus.GRANTED, "decided_by": None},
        {"status": ApprovalStatus.REQUESTED, "decided_by": "user", "decided_at": NOW},
    ],
)
def test_record_validation_rejects_malformed_authority(changes: dict[str, object]) -> None:
    with pytest.raises((TypeError, ValueError)):
        approval_record(**changes)


def test_effect_count_is_exactly_one_and_records_are_immutable() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        approval_check(effect_count=0)

    record = approval_record()
    with pytest.raises(FrozenInstanceError):
        record.status = ApprovalStatus.REVOKED  # type: ignore[misc]

    changed = replace(record, status=ApprovalStatus.REVOKED)
    assert changed.status is ApprovalStatus.REVOKED
