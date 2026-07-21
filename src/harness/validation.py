"""C-404 deterministic validator execution and referenced evidence records.

This module executes only validator commands frozen on a ``Task``.  It owns
process-result normalization and file-backed command evidence, but not workspace
creation/containment, SQLite/JSONL persistence, retries, model evaluation, or
CLI orchestration.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol, runtime_checkable

from harness.config import ValidationSettings
from harness.orchestrator import FinalizationEvidence
from harness.state import (
    CompletionVerdict,
    LifecycleState,
    LocationKind,
    LocationReference,
    Run,
    Task,
    TaskStatus,
)

__all__ = [
    "DeterministicValidator",
    "SubprocessValidatorProcess",
    "ValidationBatchResult",
    "ValidationClock",
    "ValidationContractError",
    "ValidationEvidence",
    "ValidationFailureKind",
    "ValidationInfrastructureError",
    "ValidatorCommand",
    "ValidatorProcess",
    "ValidatorProcessResult",
]

ValidationClock = Callable[[], datetime]
_STABLE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_UNSAFE_FILE_CHARACTER_RE = re.compile(r"[^A-Za-z0-9._-]")


class ValidationContractError(ValueError):
    """Frozen validator scope or lifecycle state is invalid."""


class ValidationInfrastructureError(RuntimeError):
    """Required validation evidence could not be stored safely."""


class ValidationFailureKind(StrEnum):
    """Normalized deterministic validation failures and evidence gaps."""

    NONZERO_EXIT = "NONZERO_EXIT"
    TIMEOUT = "TIMEOUT"
    EXECUTION_ERROR = "EXECUTION_ERROR"
    MALFORMED_RESULT = "MALFORMED_RESULT"
    OUTPUT_LIMIT_EXCEEDED = "OUTPUT_LIMIT_EXCEEDED"


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


def _require_aware_timestamp(value: datetime, location: str) -> None:
    if type(value) is not datetime:
        raise TypeError(f"{location} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{location} must include a timezone offset")


def _safe_summary(value: object) -> str:
    normalized = " ".join(str(value).split())
    return normalized or type(value).__name__


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidatorCommand:
    """One structured command whose canonical text is frozen on a Task."""

    validator_id: str
    argv: tuple[str, ...]
    criterion_ids: tuple[str, ...]
    runtime_identity: str

    def __post_init__(self) -> None:
        _require_stable_id(self.validator_id, "ValidatorCommand.validator_id")
        if type(self.argv) is not tuple:
            raise TypeError("ValidatorCommand.argv must be a tuple")
        if not self.argv:
            raise ValueError("ValidatorCommand.argv must not be empty")
        for index, argument in enumerate(self.argv):
            _require_normalized_string(argument, f"ValidatorCommand.argv[{index}]")
        if type(self.criterion_ids) is not tuple:
            raise TypeError("ValidatorCommand.criterion_ids must be a tuple")
        if not self.criterion_ids:
            raise ValueError("ValidatorCommand.criterion_ids must not be empty")
        if len(set(self.criterion_ids)) != len(self.criterion_ids):
            raise ValueError("ValidatorCommand.criterion_ids must not contain duplicates")
        for index, criterion_id in enumerate(self.criterion_ids):
            _require_stable_id(
                criterion_id,
                f"ValidatorCommand.criterion_ids[{index}]",
            )
        _require_normalized_string(
            self.runtime_identity,
            "ValidatorCommand.runtime_identity",
        )

    @property
    def command_text(self) -> str:
        """Return the canonical Windows command line used for Task matching."""

        return subprocess.list2cmdline(list(self.argv))


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidatorProcessResult:
    """Well-formed process output before evidence normalization."""

    returncode: int
    stdout: bytes
    stderr: bytes

    def __post_init__(self) -> None:
        if type(self.returncode) is not int:
            raise TypeError("ValidatorProcessResult.returncode must be an integer")
        if type(self.stdout) is not bytes:
            raise TypeError("ValidatorProcessResult.stdout must be bytes")
        if type(self.stderr) is not bytes:
            raise TypeError("ValidatorProcessResult.stderr must be bytes")


@runtime_checkable
class ValidatorProcess(Protocol):
    """Shell-free process boundary used by deterministic validation."""

    def run(
        self,
        *,
        argv: tuple[str, ...],
        cwd: Path,
        timeout_seconds: float,
        environment: Mapping[str, str],
    ) -> object:
        """Execute exactly one structured command and return a process result."""


class SubprocessValidatorProcess:
    """Standard-library validator process implementation with no shell."""

    def run(
        self,
        *,
        argv: tuple[str, ...],
        cwd: Path,
        timeout_seconds: float,
        environment: Mapping[str, str],
    ) -> ValidatorProcessResult:
        completed: subprocess.CompletedProcess[bytes] = subprocess.run(
            list(argv),
            cwd=cwd,
            env=dict(environment),
            check=False,
            capture_output=True,
            timeout=timeout_seconds,
            shell=False,
        )
        return ValidatorProcessResult(
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationEvidence:
    """Immutable normalized command evidence containing references, not output."""

    validator_id: str
    run_id: str
    task_id: str
    criterion_ids: tuple[str, ...]
    command: str
    working_directory: str
    runtime_identity: str
    started_at: datetime
    finished_at: datetime
    verdict: CompletionVerdict
    exit_code: int | None
    failure_kind: ValidationFailureKind | None
    summary: str
    stdout_ref: LocationReference
    stderr_ref: LocationReference
    record_ref: LocationReference

    def __post_init__(self) -> None:
        _require_stable_id(self.validator_id, "ValidationEvidence.validator_id")
        _require_stable_id(self.run_id, "ValidationEvidence.run_id")
        _require_stable_id(self.task_id, "ValidationEvidence.task_id")
        if type(self.criterion_ids) is not tuple or not self.criterion_ids:
            raise ValueError("ValidationEvidence.criterion_ids must be a non-empty tuple")
        for index, criterion_id in enumerate(self.criterion_ids):
            _require_stable_id(criterion_id, f"ValidationEvidence.criterion_ids[{index}]")
        _require_normalized_string(self.command, "ValidationEvidence.command")
        _require_normalized_string(
            self.working_directory,
            "ValidationEvidence.working_directory",
        )
        _require_normalized_string(
            self.runtime_identity,
            "ValidationEvidence.runtime_identity",
        )
        _require_aware_timestamp(self.started_at, "ValidationEvidence.started_at")
        _require_aware_timestamp(self.finished_at, "ValidationEvidence.finished_at")
        if self.finished_at < self.started_at:
            raise ValueError("ValidationEvidence.finished_at must not precede started_at")
        if type(self.verdict) is not CompletionVerdict:
            raise TypeError("ValidationEvidence.verdict must be a CompletionVerdict")
        if self.verdict is CompletionVerdict.NOT_EVALUATED:
            raise ValueError("ValidationEvidence.verdict must be an evidence verdict")
        if self.exit_code is not None and type(self.exit_code) is not int:
            raise TypeError("ValidationEvidence.exit_code must be an integer or null")
        if self.failure_kind is not None and type(self.failure_kind) is not ValidationFailureKind:
            raise TypeError(
                "ValidationEvidence.failure_kind must be a ValidationFailureKind or null"
            )
        _require_normalized_string(self.summary, "ValidationEvidence.summary")
        if self.stdout_ref.kind is not LocationKind.ARTIFACT_PATH:
            raise ValueError("ValidationEvidence.stdout_ref must be an ARTIFACT_PATH")
        if self.stderr_ref.kind is not LocationKind.ARTIFACT_PATH:
            raise ValueError("ValidationEvidence.stderr_ref must be an ARTIFACT_PATH")
        if self.record_ref.kind is not LocationKind.COMMAND_RESULT:
            raise ValueError("ValidationEvidence.record_ref must be a COMMAND_RESULT")
        if self.verdict is CompletionVerdict.PASS:
            if self.exit_code != 0 or self.failure_kind is not None:
                raise ValueError("PASS validation evidence requires exit code 0 and no failure")
        elif self.verdict is CompletionVerdict.FAIL:
            if self.exit_code is None or self.exit_code == 0:
                raise ValueError("FAIL validation evidence requires a nonzero exit code")
            if self.failure_kind is not ValidationFailureKind.NONZERO_EXIT:
                raise ValueError("FAIL validation evidence requires NONZERO_EXIT")
        elif self.failure_kind is None:
            raise ValueError("INSUFFICIENT_EVIDENCE requires a normalized failure kind")

    def to_dict(self) -> dict[str, object]:
        """Return the structured evidence record without captured stream content."""

        return {
            "schema_version": "1.0",
            "validator_id": self.validator_id,
            "run_id": self.run_id,
            "task_id": self.task_id,
            "criterion_ids": list(self.criterion_ids),
            "command": self.command,
            "working_directory": self.working_directory,
            "runtime_identity": self.runtime_identity,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "verdict": self.verdict.value,
            "exit_code": self.exit_code,
            "failure_kind": self.failure_kind.value if self.failure_kind is not None else None,
            "summary": self.summary,
            "stdout_ref": self.stdout_ref.to_dict(),
            "stderr_ref": self.stderr_ref.to_dict(),
            "record_ref": self.record_ref.to_dict(),
        }


def _aggregate_verdict(records: tuple[ValidationEvidence, ...]) -> CompletionVerdict:
    if any(record.verdict is CompletionVerdict.FAIL for record in records):
        return CompletionVerdict.FAIL
    if any(record.verdict is CompletionVerdict.INSUFFICIENT_EVIDENCE for record in records):
        return CompletionVerdict.INSUFFICIENT_EVIDENCE
    return CompletionVerdict.PASS


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationBatchResult:
    """Ordered deterministic evidence and its W-203 aggregate verdict."""

    run_id: str
    task_id: str
    records: tuple[ValidationEvidence, ...]
    overall_verdict: CompletionVerdict

    def __post_init__(self) -> None:
        _require_stable_id(self.run_id, "ValidationBatchResult.run_id")
        _require_stable_id(self.task_id, "ValidationBatchResult.task_id")
        if type(self.records) is not tuple or not self.records:
            raise ValueError("ValidationBatchResult.records must be a non-empty tuple")
        if any(type(record) is not ValidationEvidence for record in self.records):
            raise TypeError("ValidationBatchResult.records must contain ValidationEvidence")
        if any(
            record.run_id != self.run_id or record.task_id != self.task_id
            for record in self.records
        ):
            raise ValueError("ValidationBatchResult record identity must match the batch")
        expected = _aggregate_verdict(self.records)
        if self.overall_verdict is not expected:
            raise ValueError("ValidationBatchResult.overall_verdict does not match its records")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValueError("ValidationBatchResult evidence references must be unique")

    @property
    def evidence_refs(self) -> tuple[str, ...]:
        """Return result-record references accepted by C-403 finalization."""

        return tuple(record.record_ref.ref for record in self.records)

    def to_finalization_evidence(
        self,
        *,
        checkpoint_ref: str,
        goal_complete: bool = False,
    ) -> FinalizationEvidence:
        """Create deterministic-only C-403 evidence, failing closed unless PASS."""

        if self.overall_verdict is not CompletionVerdict.PASS:
            raise ValidationContractError("finalization requires aggregate PASS validation")
        return FinalizationEvidence(
            validation_verdict=CompletionVerdict.PASS,
            validation_evidence_refs=self.evidence_refs,
            checkpoint_ref=checkpoint_ref,
            evaluation_verdict=None,
            evaluation_evidence_refs=(),
            goal_complete=goal_complete,
            completion_evidence_refs=self.evidence_refs if goal_complete else (),
        )


class DeterministicValidator:
    """Run a frozen validator set and store normalized evidence by reference."""

    def __init__(
        self,
        *,
        process: ValidatorProcess,
        artifact_root: Path,
        settings: ValidationSettings,
        environment: Mapping[str, str],
        clock: ValidationClock,
    ) -> None:
        if not isinstance(process, ValidatorProcess):
            raise TypeError("process must implement ValidatorProcess")
        if not isinstance(artifact_root, Path):
            raise TypeError("artifact_root must be a Path")
        if not artifact_root.is_absolute():
            raise ValueError("artifact_root must be absolute")
        if artifact_root.name.casefold() != "artifacts":
            raise ValueError("artifact_root must be the configured artifacts directory")
        if not isinstance(settings, ValidationSettings):
            raise TypeError("settings must be ValidationSettings")
        if not isinstance(environment, Mapping):
            raise TypeError("environment must be a mapping")
        copied_environment: dict[str, str] = {}
        for key, value in environment.items():
            _require_normalized_string(key, "environment key")
            if type(value) is not str or "\x00" in value:
                raise ValueError("environment values must be strings without NUL")
            copied_environment[key] = value
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._process = process
        self._artifact_root = artifact_root
        self._settings = settings
        self._environment = copied_environment
        self._clock = clock

    def validate(
        self,
        *,
        run: Run,
        task: Task,
        commands: tuple[ValidatorCommand, ...],
        workspace: Path,
    ) -> ValidationBatchResult:
        """Execute every frozen command in order and return referenced evidence."""

        workspace = self._validate_contract(run, task, commands, workspace)
        records = tuple(
            self._run_one(
                run=run,
                task=task,
                command=command,
                ordinal=index,
                workspace=workspace,
            )
            for index, command in enumerate(commands, start=1)
        )
        return ValidationBatchResult(
            run_id=run.run_id,
            task_id=task.task_id,
            records=records,
            overall_verdict=_aggregate_verdict(records),
        )

    def _validate_contract(
        self,
        run: Run,
        task: Task,
        commands: tuple[ValidatorCommand, ...],
        workspace: Path,
    ) -> Path:
        if type(run) is not Run or type(task) is not Task:
            raise TypeError("run and task must be accepted C-401 records")
        if (
            run.lifecycle_state is not LifecycleState.VALIDATING
            or task.status is not TaskStatus.VALIDATING
        ):
            raise ValidationContractError("validation requires a VALIDATING Run and Task")
        if run.current_task_id != task.task_id or run.goal_id != task.goal_id:
            raise ValidationContractError("validation Run and Task identity must match")
        if type(commands) is not tuple:
            raise TypeError("commands must be a tuple")
        if not commands:
            raise ValidationContractError("validation requires at least one validator command")
        if any(type(command) is not ValidatorCommand for command in commands):
            raise TypeError("commands must contain ValidatorCommand records")
        if tuple(command.command_text for command in commands) != task.validation_commands:
            raise ValidationContractError(
                "validator commands must exactly match Task.validation_commands"
            )
        validator_ids = tuple(command.validator_id for command in commands)
        if len(set(validator_ids)) != len(validator_ids):
            raise ValidationContractError("validator IDs must be unique within a batch")
        task_criteria = set(task.criterion_ids)
        for command in commands:
            outside = set(command.criterion_ids) - task_criteria
            if outside:
                raise ValidationContractError(
                    f"validator criterion IDs are outside Task.criterion_ids: {sorted(outside)!r}"
                )
        if not isinstance(workspace, Path):
            raise TypeError("workspace must be a Path")
        if task.selected_workspace is None:
            raise ValidationContractError("Task.selected_workspace is required for validation")
        try:
            resolved_workspace = workspace.resolve(strict=True)
            selected_workspace = Path(task.selected_workspace).resolve(strict=True)
        except OSError as exc:
            raise ValidationContractError(
                f"selected workspace is unavailable: {_safe_summary(exc)}"
            ) from exc
        if not resolved_workspace.is_dir():
            raise ValidationContractError("selected workspace must be a directory")
        if os.path.normcase(str(resolved_workspace)) != os.path.normcase(str(selected_workspace)):
            raise ValidationContractError("workspace does not match the Task selected workspace")
        return resolved_workspace

    def _run_one(
        self,
        *,
        run: Run,
        task: Task,
        command: ValidatorCommand,
        ordinal: int,
        workspace: Path,
    ) -> ValidationEvidence:
        started_at = self._timestamp("validation start")
        stdout = b""
        stderr = b""
        exit_code: int | None = None
        failure_kind: ValidationFailureKind | None = None
        verdict = CompletionVerdict.INSUFFICIENT_EVIDENCE
        summary = "Validator did not produce sufficient evidence"

        try:
            raw_result = self._process.run(
                argv=command.argv,
                cwd=workspace,
                timeout_seconds=self._settings.default_timeout_seconds,
                environment=self._environment,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = _partial_output(exc.output)
            stderr = _partial_output(exc.stderr)
            failure_kind = ValidationFailureKind.TIMEOUT
            summary = (
                f"Validator timed out after {self._settings.default_timeout_seconds:g} seconds"
            )
        except OSError as exc:
            stderr = f"{type(exc).__name__}: {_safe_summary(exc)}\n".encode()
            failure_kind = ValidationFailureKind.EXECUTION_ERROR
            summary = f"Validator execution failed: {_safe_summary(exc)}"
        else:
            if type(raw_result) is not ValidatorProcessResult:
                stderr = (
                    f"Malformed validator process result: {type(raw_result).__name__}\n"
                ).encode()
                failure_kind = ValidationFailureKind.MALFORMED_RESULT
                summary = "Validator returned a malformed process result"
            else:
                stdout = raw_result.stdout
                stderr = raw_result.stderr
                exit_code = raw_result.returncode
                output_exceeded = len(stdout) + len(stderr) > self._settings.max_output_bytes
                if exit_code != 0:
                    verdict = CompletionVerdict.FAIL
                    failure_kind = ValidationFailureKind.NONZERO_EXIT
                    summary = f"Validator exited with status {exit_code}"
                elif output_exceeded:
                    failure_kind = ValidationFailureKind.OUTPUT_LIMIT_EXCEEDED
                    summary = (
                        "Validator output exceeded the configured "
                        f"{self._settings.max_output_bytes}-byte limit"
                    )
                else:
                    verdict = CompletionVerdict.PASS
                    summary = "Validator exited successfully with referenced evidence"

        stdout, stderr = _bounded_outputs(
            stdout,
            stderr,
            self._settings.max_output_bytes,
        )
        finished_at = self._timestamp("validation finish")
        if finished_at < started_at:
            raise ValidationContractError("validation clock moved backwards")
        return self._store_evidence(
            run=run,
            task=task,
            command=command,
            ordinal=ordinal,
            workspace=workspace,
            started_at=started_at,
            finished_at=finished_at,
            verdict=verdict,
            exit_code=exit_code,
            failure_kind=failure_kind,
            summary=summary,
            stdout=stdout,
            stderr=stderr,
        )

    def _timestamp(self, action: str) -> datetime:
        value = self._clock()
        _require_aware_timestamp(value, action)
        return value

    def _store_evidence(
        self,
        *,
        run: Run,
        task: Task,
        command: ValidatorCommand,
        ordinal: int,
        workspace: Path,
        started_at: datetime,
        finished_at: datetime,
        verdict: CompletionVerdict,
        exit_code: int | None,
        failure_kind: ValidationFailureKind | None,
        summary: str,
        stdout: bytes,
        stderr: bytes,
    ) -> ValidationEvidence:
        relative_directory = (
            Path("validation")
            / _safe_file_segment(run.run_id)
            / _safe_file_segment(task.task_id)
            / f"attempt-{task.attempts:03d}"
        )
        stem = f"{ordinal:03d}-{_safe_file_segment(command.validator_id)}"
        stdout_relative = relative_directory / f"{stem}.stdout"
        stderr_relative = relative_directory / f"{stem}.stderr"
        record_relative = relative_directory / f"{stem}.json"
        stdout_ref = _location_ref(
            LocationKind.ARTIFACT_PATH,
            Path("artifacts") / stdout_relative,
            f"Captured stdout for {command.validator_id}",
        )
        stderr_ref = _location_ref(
            LocationKind.ARTIFACT_PATH,
            Path("artifacts") / stderr_relative,
            f"Captured stderr for {command.validator_id}",
        )
        record_ref = _location_ref(
            LocationKind.COMMAND_RESULT,
            Path("artifacts") / record_relative,
            f"Structured deterministic result for {command.validator_id}",
        )
        evidence = ValidationEvidence(
            validator_id=command.validator_id,
            run_id=run.run_id,
            task_id=task.task_id,
            criterion_ids=command.criterion_ids,
            command=command.command_text,
            working_directory=str(workspace),
            runtime_identity=command.runtime_identity,
            started_at=started_at,
            finished_at=finished_at,
            verdict=verdict,
            exit_code=exit_code,
            failure_kind=failure_kind,
            summary=summary,
            stdout_ref=stdout_ref,
            stderr_ref=stderr_ref,
            record_ref=record_ref,
        )
        directory = self._artifact_root / relative_directory
        try:
            directory.mkdir(parents=True, exist_ok=True)
            _write_new(directory / stdout_relative.name, stdout)
            _write_new(directory / stderr_relative.name, stderr)
            serialized = (
                json.dumps(
                    evidence.to_dict(),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ).encode("utf-8")
                + b"\n"
            )
            _write_new(directory / record_relative.name, serialized)
        except OSError as exc:
            raise ValidationInfrastructureError(
                f"could not store validation evidence: {_safe_summary(exc)}"
            ) from exc
        return evidence


def _partial_output(value: object) -> bytes:
    if value is None:
        return b""
    if type(value) is bytes:
        return value
    if type(value) is str:
        return value.encode()
    return b""


def _bounded_outputs(stdout: bytes, stderr: bytes, maximum: int) -> tuple[bytes, bytes]:
    stdout_limit = min(len(stdout), maximum)
    bounded_stdout = stdout[:stdout_limit]
    remaining = maximum - len(bounded_stdout)
    return bounded_stdout, stderr[:remaining]


def _safe_file_segment(value: str) -> str:
    _require_stable_id(value, "evidence path identity")
    return _UNSAFE_FILE_CHARACTER_RE.sub("_", value)


def _location_ref(kind: LocationKind, relative_path: Path, description: str) -> LocationReference:
    return LocationReference(
        kind=kind,
        ref=relative_path.as_posix(),
        description=description,
    )


def _write_new(path: Path, content: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(content)
