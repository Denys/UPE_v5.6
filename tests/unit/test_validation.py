from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from harness.config import ValidationSettings
from harness.state import (
    BudgetState,
    BudgetValues,
    CompletionVerdict,
    LifecycleState,
    Run,
    Task,
    TaskStatus,
)
from harness.validation import (
    DeterministicValidator,
    SubprocessValidatorProcess,
    ValidationBatchResult,
    ValidationContractError,
    ValidationFailureKind,
    ValidationInfrastructureError,
    ValidatorCommand,
    ValidatorProcessResult,
)

BASE_TIME = datetime(2026, 7, 21, 10, 0, tzinfo=UTC)


class SteppingClock:
    def __init__(self) -> None:
        self._next = BASE_TIME

    def __call__(self) -> datetime:
        current = self._next
        self._next += timedelta(milliseconds=1)
        return current


class RecordingProcess:
    def __init__(self, *results: object) -> None:
        self._results = list(results)
        self.calls: list[dict[str, object]] = []

    def run(
        self,
        *,
        argv: tuple[str, ...],
        cwd: Path,
        timeout_seconds: float,
        environment: Mapping[str, str],
    ) -> object:
        self.calls.append(
            {
                "argv": argv,
                "cwd": cwd,
                "timeout_seconds": timeout_seconds,
                "environment": dict(environment),
            }
        )
        if not self._results:
            raise AssertionError("no scripted process result remains")
        result = self._results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return result


def budget_state() -> BudgetState:
    return BudgetState(
        limits=BudgetValues(iterations=8, elapsed_seconds=1200.0),
        consumed=BudgetValues(iterations=1, elapsed_seconds=1.0),
    )


def run_record(**changes: object) -> Run:
    values: dict[str, object] = {
        "run_id": "run.c404.001",
        "goal_id": "goal.c404",
        "provider": "fake",
        "model": "fake-model",
        "reasoning_effort": None,
        "provider_config_ref": None,
        "lifecycle_state": LifecycleState.VALIDATING,
        "started_at": BASE_TIME,
        "updated_at": BASE_TIME,
        "iteration_count": 1,
        "budget": budget_state(),
        "current_task_id": "C-404",
        "approval_state": None,
        "checkpoint_ref": None,
        "stop_reason": None,
        "completion_verdict": CompletionVerdict.NOT_EVALUATED,
        "completion_evidence_refs": (),
        "event_seq": 4,
        "last_transition_id": "run.c404.001.transition.000004.validating",
    }
    values.update(changes)
    return Run(**values)  # type: ignore[arg-type]


def command(
    *,
    validator_id: str = "validator.c404.unit",
    criterion_id: str = "criterion.c404.validation",
    argv: tuple[str, ...] | None = None,
) -> ValidatorCommand:
    return ValidatorCommand(
        validator_id=validator_id,
        argv=(argv if argv is not None else (sys.executable, "-c", f"print({validator_id!r})")),
        criterion_ids=(criterion_id,),
        runtime_identity="python-test-runtime",
    )


def task_record(workspace: Path, commands: tuple[ValidatorCommand, ...], **changes: object) -> Task:
    values: dict[str, object] = {
        "task_id": "C-404",
        "goal_id": "goal.c404",
        "description": "Implement deterministic validation and evidence records.",
        "dependencies": ("C-305", "C-403"),
        "status": TaskStatus.VALIDATING,
        "attempts": 1,
        "selected_workspace": str(workspace.resolve()),
        "allowed_paths": ("src/harness/validation.py", "tests/unit/test_validation.py"),
        "locked_paths": ("src/harness/state.py", "src/harness/orchestrator.py"),
        "criterion_ids": tuple(
            criterion_id for item in commands for criterion_id in item.criterion_ids
        ),
        "validation_commands": tuple(item.command_text for item in commands),
        "evidence_paths": (),
        "last_failure": None,
        "next_action": None,
    }
    values.update(changes)
    return Task(**values)  # type: ignore[arg-type]


def validator(
    tmp_path: Path,
    process: RecordingProcess | SubprocessValidatorProcess,
    *,
    max_output_bytes: int = 4096,
) -> DeterministicValidator:
    return DeterministicValidator(
        process=process,
        artifact_root=tmp_path / "host-state" / "artifacts",
        settings=ValidationSettings(
            default_timeout_seconds=5.0,
            max_output_bytes=max_output_bytes,
        ),
        environment={"C404_TEST_ENV": "explicit"},
        clock=SteppingClock(),
    )


def successful_result(stdout: bytes = b"validator output\n") -> ValidatorProcessResult:
    return ValidatorProcessResult(returncode=0, stdout=stdout, stderr=b"")


def run_validation(
    tmp_path: Path,
    process: RecordingProcess | SubprocessValidatorProcess,
    commands: tuple[ValidatorCommand, ...],
    *,
    max_output_bytes: int = 4096,
) -> ValidationBatchResult:
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    return validator(tmp_path, process, max_output_bytes=max_output_bytes).validate(
        run=run_record(),
        task=task_record(workspace, commands),
        commands=commands,
        workspace=workspace,
    )


def referenced_path(tmp_path: Path, ref: str) -> Path:
    return tmp_path / "host-state" / Path(ref)


def test_validator_command_is_immutable_structured_and_canonical() -> None:
    item = command(argv=("uv", "run", "pytest", "-q", "tests/unit/test_validation.py"))

    assert item.command_text == "uv run pytest -q tests/unit/test_validation.py"
    with pytest.raises(FrozenInstanceError):
        item.__setattr__("validator_id", "changed")
    with pytest.raises(ValueError, match="argv must not be empty"):
        command(argv=())
    with pytest.raises(ValueError, match="non-empty and normalized"):
        command(argv=("uv", " "))


def test_scope_mismatch_is_rejected_before_process_execution(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    configured = command()
    unexpected = command(
        validator_id="validator.c404.unexpected",
        argv=(sys.executable, "-c", "print('unexpected')"),
    )
    process = RecordingProcess(successful_result())
    task = task_record(workspace, (configured,))

    with pytest.raises(ValidationContractError, match="exactly match Task.validation_commands"):
        validator(tmp_path, process).validate(
            run=run_record(),
            task=task,
            commands=(unexpected,),
            workspace=workspace,
        )

    assert process.calls == []


def test_workspace_and_criterion_scope_are_checked_before_execution(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    other = tmp_path / "other"
    workspace.mkdir()
    other.mkdir()
    configured = command()
    process = RecordingProcess(successful_result())
    task = task_record(workspace, (configured,))

    with pytest.raises(ValidationContractError, match="selected workspace"):
        validator(tmp_path, process).validate(
            run=run_record(), task=task, commands=(configured,), workspace=other
        )
    outside = command(criterion_id="criterion.outside")
    with pytest.raises(ValidationContractError, match="outside Task.criterion_ids"):
        validator(tmp_path, process).validate(
            run=run_record(),
            task=task,
            commands=(outside,),
            workspace=workspace,
        )

    assert process.calls == []


def test_passing_validation_writes_referenced_outputs_and_result(tmp_path: Path) -> None:
    configured = command()
    process = RecordingProcess(
        ValidatorProcessResult(returncode=0, stdout=b"pass output\n", stderr=b"warning\n")
    )

    batch = run_validation(tmp_path, process, (configured,))

    assert batch.overall_verdict is CompletionVerdict.PASS
    evidence = batch.records[0]
    assert evidence.verdict is CompletionVerdict.PASS
    assert evidence.failure_kind is None
    assert evidence.exit_code == 0
    assert referenced_path(tmp_path, evidence.stdout_ref.ref).read_bytes() == b"pass output\n"
    assert referenced_path(tmp_path, evidence.stderr_ref.ref).read_bytes() == b"warning\n"
    result_path = referenced_path(tmp_path, evidence.record_ref.ref)
    result_data = json.loads(result_path.read_text(encoding="utf-8"))
    assert result_data["stdout_ref"]["ref"] == evidence.stdout_ref.ref
    assert result_data["stderr_ref"]["ref"] == evidence.stderr_ref.ref
    assert "pass output" not in result_path.read_text(encoding="utf-8")
    assert process.calls == [
        {
            "argv": configured.argv,
            "cwd": (tmp_path / "workspace").resolve(),
            "timeout_seconds": 5.0,
            "environment": {"C404_TEST_ENV": "explicit"},
        }
    ]


def test_real_subprocess_execution_is_shell_free_and_referenced(tmp_path: Path) -> None:
    configured = command(
        validator_id="validator.c404.real",
        argv=(sys.executable, "-c", "print('real process output')"),
    )
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True)
    runner = DeterministicValidator(
        process=SubprocessValidatorProcess(),
        artifact_root=tmp_path / "host-state" / "artifacts",
        settings=ValidationSettings(default_timeout_seconds=5.0, max_output_bytes=4096),
        environment=dict(os.environ),
        clock=SteppingClock(),
    )

    batch = runner.validate(
        run=run_record(),
        task=task_record(workspace, (configured,)),
        commands=(configured,),
        workspace=workspace,
    )

    evidence = batch.records[0]
    assert batch.overall_verdict is CompletionVerdict.PASS
    assert b"real process output" in referenced_path(tmp_path, evidence.stdout_ref.ref).read_bytes()


def test_nonzero_exit_is_normalized_to_fail(tmp_path: Path) -> None:
    batch = run_validation(
        tmp_path,
        RecordingProcess(ValidatorProcessResult(returncode=7, stdout=b"", stderr=b"failed")),
        (command(),),
    )

    evidence = batch.records[0]
    assert batch.overall_verdict is CompletionVerdict.FAIL
    assert evidence.verdict is CompletionVerdict.FAIL
    assert evidence.failure_kind is ValidationFailureKind.NONZERO_EXIT
    assert evidence.exit_code == 7


def test_timeout_is_normalized_to_insufficient_evidence_with_partial_output(
    tmp_path: Path,
) -> None:
    timeout = subprocess.TimeoutExpired(
        cmd=("validator",), timeout=5.0, output=b"partial stdout", stderr=b"partial stderr"
    )

    batch = run_validation(tmp_path, RecordingProcess(timeout), (command(),))

    evidence = batch.records[0]
    assert batch.overall_verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE
    assert evidence.failure_kind is ValidationFailureKind.TIMEOUT
    assert evidence.exit_code is None
    assert referenced_path(tmp_path, evidence.stdout_ref.ref).read_bytes() == b"partial stdout"
    assert referenced_path(tmp_path, evidence.stderr_ref.ref).read_bytes() == b"partial stderr"


def test_execution_error_is_normalized_to_insufficient_evidence(tmp_path: Path) -> None:
    batch = run_validation(
        tmp_path,
        RecordingProcess(OSError("validator executable is unavailable")),
        (command(),),
    )

    evidence = batch.records[0]
    assert batch.overall_verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE
    assert evidence.failure_kind is ValidationFailureKind.EXECUTION_ERROR
    assert evidence.exit_code is None
    assert (
        b"validator executable is unavailable"
        in referenced_path(tmp_path, evidence.stderr_ref.ref).read_bytes()
    )


def test_malformed_process_result_is_normalized_to_insufficient_evidence(tmp_path: Path) -> None:
    batch = run_validation(tmp_path, RecordingProcess({"returncode": 0}), (command(),))

    evidence = batch.records[0]
    assert batch.overall_verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE
    assert evidence.failure_kind is ValidationFailureKind.MALFORMED_RESULT
    assert evidence.exit_code is None


def test_output_limit_is_fail_closed_and_files_remain_bounded(tmp_path: Path) -> None:
    batch = run_validation(
        tmp_path,
        RecordingProcess(ValidatorProcessResult(returncode=0, stdout=b"a" * 12, stderr=b"b" * 12)),
        (command(),),
        max_output_bytes=16,
    )

    evidence = batch.records[0]
    assert batch.overall_verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE
    assert evidence.failure_kind is ValidationFailureKind.OUTPUT_LIMIT_EXCEEDED
    stored_size = len(referenced_path(tmp_path, evidence.stdout_ref.ref).read_bytes()) + len(
        referenced_path(tmp_path, evidence.stderr_ref.ref).read_bytes()
    )
    assert stored_size == 16


def test_aggregate_fail_precedes_insufficient_evidence_and_preserves_order(
    tmp_path: Path,
) -> None:
    commands = (
        command(validator_id="validator.c404.pass", criterion_id="criterion.pass"),
        command(validator_id="validator.c404.timeout", criterion_id="criterion.timeout"),
        command(validator_id="validator.c404.fail", criterion_id="criterion.fail"),
    )
    timeout = subprocess.TimeoutExpired(cmd=("validator",), timeout=5.0)
    process = RecordingProcess(
        successful_result(),
        timeout,
        ValidatorProcessResult(returncode=2, stdout=b"", stderr=b"failed"),
    )

    batch = run_validation(tmp_path, process, commands)

    assert batch.overall_verdict is CompletionVerdict.FAIL
    assert [record.validator_id for record in batch.records] == [
        "validator.c404.pass",
        "validator.c404.timeout",
        "validator.c404.fail",
    ]
    assert len(process.calls) == 3


def test_only_passing_batch_can_create_c403_finalization_evidence(tmp_path: Path) -> None:
    passing = run_validation(tmp_path, RecordingProcess(successful_result()), (command(),))

    finalization = passing.to_finalization_evidence(
        checkpoint_ref="checkpoints/run.c404.001.json",
        goal_complete=True,
    )

    assert finalization.validation_verdict is CompletionVerdict.PASS
    assert finalization.validation_evidence_refs == passing.evidence_refs
    assert finalization.evaluation_verdict is None
    assert finalization.evaluation_evidence_refs == ()
    assert finalization.completion_evidence_refs == passing.evidence_refs

    other_root = tmp_path / "failed"
    failed = run_validation(
        other_root,
        RecordingProcess(ValidatorProcessResult(returncode=1, stdout=b"", stderr=b"fail")),
        (command(),),
    )
    with pytest.raises(ValidationContractError, match="requires aggregate PASS"):
        failed.to_finalization_evidence(checkpoint_ref="checkpoints/failed.json")


def test_empty_contract_and_wrong_lifecycle_are_rejected(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    configured = command()
    process = RecordingProcess(successful_result())
    runner = validator(tmp_path, process)

    with pytest.raises(ValidationContractError, match="at least one validator command"):
        runner.validate(
            run=run_record(),
            task=task_record(workspace, (), validation_commands=()),
            commands=(),
            workspace=workspace,
        )
    with pytest.raises(ValidationContractError, match="VALIDATING Run and Task"):
        runner.validate(
            run=run_record(lifecycle_state=LifecycleState.READY),
            task=task_record(workspace, (configured,)),
            commands=(configured,),
            workspace=workspace,
        )

    assert process.calls == []


def test_artifact_write_failure_prevents_passing_evidence(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    artifact_root.write_text("not a directory", encoding="utf-8")
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    configured = command()
    runner = DeterministicValidator(
        process=RecordingProcess(successful_result()),
        artifact_root=artifact_root,
        settings=ValidationSettings(default_timeout_seconds=5.0, max_output_bytes=4096),
        environment={},
        clock=SteppingClock(),
    )

    with pytest.raises(ValidationInfrastructureError, match="could not store validation evidence"):
        runner.validate(
            run=run_record(),
            task=task_record(workspace, (configured,)),
            commands=(configured,),
            workspace=workspace,
        )
