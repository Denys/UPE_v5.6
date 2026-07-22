"""Small, fail-closed command boundary and read-only harness doctor for C-409.

The CLI declares the v0 command surface without taking ownership of lifecycle,
recovery, evaluation, cleanup, or provider behavior.  Those operations are
dispatched through an injected ``CommandExecutor`` and are unavailable by
default until the integrated runtime supplies one.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sqlite3
import subprocess
import sys
import threading
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path, PureWindowsPath
from typing import BinaryIO, Protocol, TextIO, cast, runtime_checkable

from harness.config import HarnessConfig, InvalidConfigError, ProviderAdapter

COMMAND_NAMES = (
    "init",
    "research",
    "doctor",
    "run",
    "status",
    "events",
    "resume",
    "pause",
    "cancel",
    "evaluate",
    "cleanup",
)
DEFAULT_CONFIG_RELATIVE_PATH = Path(".harness") / "config.json"
MINIMUM_PYTHON = (3, 12)
DEFAULT_PROBE_TIMEOUT_SECONDS = 5.0
MAX_PROBE_OUTPUT_BYTES = 4096
PROBE_READ_CHUNK_BYTES = 1024
_VALIDATOR_SCRIPTS = (
    Path("scripts/validate_work_specifications.py"),
    Path("scripts/validate_references.py"),
)
_CREDENTIAL_ENVIRONMENT_NAMES = ("OPENAI_API_KEY", "CODEX_API_KEY")
_VERSION_TOKEN = re.compile(
    r"(?<![A-Za-z0-9])(?P<version>\d+\.\d+\.\d+(?:[-+][A-Za-z0-9.-]+)?)(?![A-Za-z0-9])"
)


class ExitCode(IntEnum):
    OK = 0
    USAGE = 2
    UNAVAILABLE = 69
    SOFTWARE = 70


class CheckStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    SKIP = "SKIP"


@dataclass(frozen=True, slots=True)
class ProbeResult:
    """Bounded process result used only to decide fixed diagnostic messages."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


@runtime_checkable
class ProcessProbe(Protocol):
    def run(
        self,
        args: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> ProbeResult:
        """Run one read-only, shell-free diagnostic command."""


class SubprocessProbe:
    """Windows-native bounded process probe with no shell or inherited stdin."""

    def run(
        self,
        args: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> ProbeResult:
        try:
            process = subprocess.Popen(
                list(args),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
            )
        except OSError:
            return ProbeResult(returncode=-1)

        if process.stdout is None or process.stderr is None:
            process.kill()
            return ProbeResult(returncode=-1)
        stdout = bytearray()
        stderr = bytearray()
        readers = (
            threading.Thread(
                target=_drain_bounded,
                args=(process.stdout, stdout),
                daemon=True,
            ),
            threading.Thread(
                target=_drain_bounded,
                args=(process.stderr, stderr),
                daemon=True,
            ),
        )
        for reader in readers:
            reader.start()
        timed_out = False
        try:
            returncode = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            try:
                process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                process.stdout.close()
                process.stderr.close()
        finally:
            for reader in readers:
                reader.join(timeout=5.0)
            process.stdout.close()
            process.stderr.close()
        return ProbeResult(
            returncode=-1 if timed_out else returncode,
            stdout=bytes(stdout).decode("utf-8", errors="replace"),
            stderr=bytes(stderr).decode("utf-8", errors="replace"),
        )


def _drain_bounded(stream: BinaryIO, destination: bytearray) -> None:
    """Drain a child pipe completely while retaining at most the configured bound."""

    try:
        while chunk := stream.read(PROBE_READ_CHUNK_BYTES):
            remaining = MAX_PROBE_OUTPUT_BYTES - len(destination)
            if remaining > 0:
                destination.extend(chunk[:remaining])
    except (OSError, ValueError):
        return


@dataclass(frozen=True, slots=True)
class DoctorCheck:
    name: str
    status: CheckStatus
    summary: str


@dataclass(frozen=True, slots=True)
class DoctorReport:
    checks: tuple[DoctorCheck, ...]

    @property
    def usable(self) -> bool:
        return all(check.status is not CheckStatus.FAIL for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        return {
            "usable": self.usable,
            "checks": [
                {"name": check.name, "status": check.status.value, "summary": check.summary}
                for check in self.checks
            ],
        }


@dataclass(frozen=True, slots=True)
class DoctorContext:
    cwd: Path
    config_path: Path
    environment: Mapping[str, str]
    probe: ProcessProbe
    timeout_seconds: float = DEFAULT_PROBE_TIMEOUT_SECONDS

    def __post_init__(self) -> None:
        if not isinstance(self.cwd, Path) or not isinstance(self.config_path, Path):
            raise TypeError("cwd and config_path must be pathlib.Path values")
        if not isinstance(self.environment, Mapping):
            raise TypeError("environment must be a mapping")
        if not isinstance(self.probe, ProcessProbe):
            raise TypeError("probe must implement ProcessProbe")
        if (
            type(self.timeout_seconds) not in (int, float)
            or isinstance(self.timeout_seconds, bool)
            or self.timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be positive")


@dataclass(frozen=True, slots=True)
class CommandRequest:
    command: str
    config_path: Path
    arguments: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class CommandResponse:
    exit_code: int
    summary: str


@runtime_checkable
class CommandExecutor(Protocol):
    def execute(self, request: CommandRequest) -> CommandResponse:
        """Execute one parsed non-doctor command through the integrated runtime."""


class UnavailableCommandExecutor:
    """Fail closed until C-506 supplies the integrated runtime operations."""

    def execute(self, request: CommandRequest) -> CommandResponse:
        return CommandResponse(
            exit_code=ExitCode.UNAVAILABLE,
            summary=(
                f"{request.command}: command boundary is available; "
                "integrated runtime operation is not configured"
            ),
        )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="harness")
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="credential-free harness config (default: .harness/config.json)",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="initialize a repository")
    init_parser.add_argument("path", type=Path)
    subparsers.add_parser("research", help="run the configured research boundary")

    doctor_parser = subparsers.add_parser("doctor", help="check the local environment safely")
    doctor_parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_PROBE_TIMEOUT_SECONDS,
        help="per-process diagnostic timeout in seconds",
    )

    run_parser = subparsers.add_parser("run", help="start a bounded run")
    run_parser.add_argument("--goal", type=Path, required=True)

    for name in ("status", "events", "resume", "pause", "cancel", "evaluate", "cleanup"):
        command_parser = subparsers.add_parser(name)
        command_parser.add_argument("run_id")
    return parser


def _load_config(path: Path) -> HarnessConfig | None:
    if not path.is_file():
        return None
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise InvalidConfigError("configuration file is not valid UTF-8 JSON") from exc
    if type(decoded) is not dict or any(type(key) is not str for key in decoded):
        raise InvalidConfigError("configuration must contain a JSON object")
    return HarnessConfig.from_dict(cast(dict[str, object], decoded))


def _local_path(path: PureWindowsPath) -> Path:
    return Path(str(path))


def _probe_check(
    context: DoctorContext,
    *,
    name: str,
    args: tuple[str, ...],
    cwd: Path,
    passed: str,
    failed: str,
) -> tuple[DoctorCheck, ProbeResult]:
    result = context.probe.run(
        args,
        cwd=cwd,
        timeout_seconds=float(context.timeout_seconds),
    )
    status = CheckStatus.PASS if result.returncode == 0 else CheckStatus.FAIL
    return DoctorCheck(name, status, passed if status is CheckStatus.PASS else failed), result


def _nearest_existing_parent(path: Path) -> Path | None:
    candidate = path.resolve(strict=False)
    while not candidate.exists():
        parent = candidate.parent
        if parent == candidate:
            return None
        candidate = parent
    return candidate


def _exact_version(result: ProbeResult) -> str | None:
    """Extract one sanitized version token without forwarding arbitrary process output."""

    match = _VERSION_TOKEN.search(f"{result.stdout}\n{result.stderr}")
    return None if match is None else match.group("version")


def _permission_check(repository: Path, state_path: Path) -> DoctorCheck:
    state_parent = _nearest_existing_parent(state_path)
    readable = repository.is_dir() and os.access(repository, os.R_OK)
    state_writable = state_parent is not None and os.access(state_parent, os.W_OK)
    if readable and state_writable:
        return DoctorCheck(
            "permissions",
            CheckStatus.PASS,
            "repository is readable and the host-state location is writable",
        )
    return DoctorCheck(
        "permissions",
        CheckStatus.FAIL,
        "required repository or host-state permissions are unavailable",
    )


def _sqlite_check(database_path: Path) -> DoctorCheck:
    resolved_path = database_path.resolve(strict=False)
    sqlite_identity = f"SQLite {sqlite3.sqlite_version} path {resolved_path}"
    if not resolved_path.exists():
        parent = _nearest_existing_parent(resolved_path)
        status = (
            CheckStatus.PASS
            if parent is not None and os.access(parent, os.W_OK)
            else CheckStatus.FAIL
        )
        summary = (
            f"{sqlite_identity} is creatable"
            if status is CheckStatus.PASS
            else f"{sqlite_identity} is not accessible"
        )
        return DoctorCheck("sqlite", status, summary)
    try:
        uri = resolved_path.as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True, timeout=1.0) as connection:
            row = connection.execute("PRAGMA quick_check").fetchone()
    except (OSError, sqlite3.Error, ValueError):
        return DoctorCheck("sqlite", CheckStatus.FAIL, f"{sqlite_identity} read check failed")
    if row is not None and row[0] == "ok":
        return DoctorCheck("sqlite", CheckStatus.PASS, f"{sqlite_identity} read check passed")
    return DoctorCheck("sqlite", CheckStatus.FAIL, f"{sqlite_identity} integrity check failed")


def _credential_check(config: HarnessConfig | None, context: DoctorContext) -> DoctorCheck:
    if config is None or config.provider.adapter is ProviderAdapter.FAKE:
        return DoctorCheck(
            "credentials",
            CheckStatus.SKIP,
            "provider credentials are not required for the selected boundary",
        )
    environment_available = any(
        bool(context.environment.get(name)) for name in _CREDENTIAL_ENVIRONMENT_NAMES
    )
    codex_home = context.environment.get("CODEX_HOME")
    auth_root = Path(codex_home) if codex_home else Path.home() / ".codex"
    auth_available = (auth_root / "auth.json").is_file()
    if environment_available or auth_available:
        return DoctorCheck(
            "credentials",
            CheckStatus.PASS,
            "a credential source is available; values were not inspected or displayed",
        )
    return DoctorCheck(
        "credentials",
        CheckStatus.FAIL,
        "required provider credentials are missing; no values were displayed",
    )


def run_doctor(context: DoctorContext) -> DoctorReport:
    """Run deterministic, bounded, read-only diagnostics in stable order."""

    checks: list[DoctorCheck] = []
    runtime_ok = sys.version_info >= MINIMUM_PYTHON
    runtime_version = platform.python_version()
    minimum_version = ".".join(str(part) for part in MINIMUM_PYTHON)
    checks.append(
        DoctorCheck(
            "runtime",
            CheckStatus.PASS if runtime_ok else CheckStatus.FAIL,
            (
                f"Python {runtime_version} satisfies minimum {minimum_version}"
                if runtime_ok
                else f"Python {runtime_version} is below minimum {minimum_version}"
            ),
        )
    )

    try:
        config = _load_config(context.config_path)
    except InvalidConfigError:
        config = None
        checks.append(
            DoctorCheck("config", CheckStatus.FAIL, "configuration is present but invalid")
        )
    else:
        checks.append(
            DoctorCheck(
                "config",
                CheckStatus.PASS if config is not None else CheckStatus.SKIP,
                (
                    "credential-free configuration is valid"
                    if config is not None
                    else "configuration is absent; current-directory defaults are in use"
                ),
            )
        )

    repository = _local_path(config.paths.repository_root) if config is not None else context.cwd
    database_path = (
        _local_path(config.paths.database_path)
        if config is not None
        else context.cwd / ".harness-state" / "harness.sqlite3"
    )

    codex_result = context.probe.run(
        ("codex", "--version"),
        cwd=context.cwd,
        timeout_seconds=float(context.timeout_seconds),
    )
    codex_version = _exact_version(codex_result) if codex_result.returncode == 0 else None
    checks.append(
        DoctorCheck(
            "codex",
            CheckStatus.PASS if codex_version is not None else CheckStatus.FAIL,
            (
                f"Codex {codex_version} is available"
                if codex_version is not None
                else "Codex exact version is unavailable"
            ),
        )
    )
    app_server_check, _ = _probe_check(
        context,
        name="app_server",
        args=("codex", "app-server", "--help"),
        cwd=context.cwd,
        passed=(
            f"Codex App Server is available through Codex {codex_version}"
            if codex_version is not None
            else "Codex App Server is available but the Codex version is unknown"
        ),
        failed="Codex App Server is unavailable",
    )
    if app_server_check.status is CheckStatus.PASS and codex_version is None:
        app_server_check = DoctorCheck(
            "app_server",
            CheckStatus.FAIL,
            "Codex App Server is available but the exact Codex version is unavailable",
        )
    checks.append(app_server_check)
    check, _ = _probe_check(
        context,
        name="git",
        args=("git", "--version"),
        cwd=repository,
        passed="Git command is available",
        failed="Git command is unavailable",
    )
    checks.append(check)

    repository_check, repository_result = _probe_check(
        context,
        name="repository",
        args=("git", "status", "--porcelain"),
        cwd=repository,
        passed="repository status is readable",
        failed="repository status is unavailable",
    )
    if repository_check.status is CheckStatus.PASS and repository_result.stdout.strip():
        repository_check = DoctorCheck(
            "repository",
            CheckStatus.FAIL,
            "repository has uncommitted changes",
        )
    elif repository_check.status is CheckStatus.PASS:
        repository_check = DoctorCheck(
            "repository",
            CheckStatus.PASS,
            "repository is clean",
        )
    checks.append(repository_check)

    check, _ = _probe_check(
        context,
        name="worktrees",
        args=("git", "worktree", "list", "--porcelain"),
        cwd=repository,
        passed="Git worktree support is available",
        failed="Git worktree support is unavailable",
    )
    checks.append(check)

    validator_check, _ = _probe_check(
        context,
        name="validators",
        args=("uv", "--version"),
        cwd=repository,
        passed="validator runtime is available",
        failed="validator runtime is unavailable",
    )
    if validator_check.status is CheckStatus.PASS:
        missing = [path for path in _VALIDATOR_SCRIPTS if not (repository / path).is_file()]
        if missing:
            validator_check = DoctorCheck(
                "validators",
                CheckStatus.FAIL,
                "one or more configured validator entry points are missing",
            )
        else:
            validator_check = DoctorCheck(
                "validators",
                CheckStatus.PASS,
                "validator runtime and configured entry points are available",
            )
    checks.append(validator_check)
    checks.append(_sqlite_check(database_path))
    checks.append(_permission_check(repository, database_path.parent))

    if config is not None and config.policy.docker_enabled:
        check, _ = _probe_check(
            context,
            name="docker",
            args=("docker", "version"),
            cwd=repository,
            passed="configured Docker runtime is available",
            failed="Docker is configured but unavailable",
        )
        checks.append(check)
    checks.append(_credential_check(config, context))
    return DoctorReport(tuple(checks))


def _command_arguments(namespace: argparse.Namespace) -> tuple[tuple[str, str], ...]:
    if namespace.command == "init":
        return (("path", str(namespace.path)),)
    if namespace.command == "run":
        return (("goal", str(namespace.goal)),)
    run_commands = {"status", "events", "resume", "pause", "cancel", "evaluate", "cleanup"}
    if namespace.command in run_commands:
        return (("run_id", cast(str, namespace.run_id)),)
    return ()


def _write_doctor(report: DoctorReport, stream: TextIO, *, json_output: bool) -> None:
    if json_output:
        stream.write(json.dumps(report.to_dict(), sort_keys=True) + "\n")
        return
    for check in report.checks:
        stream.write(f"{check.status.value} {check.name}: {check.summary}\n")
    stream.write("USABLE\n" if report.usable else "UNUSABLE\n")


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    cwd: Path | None = None,
    environment: Mapping[str, str] | None = None,
    probe: ProcessProbe | None = None,
    executor: CommandExecutor | None = None,
) -> int:
    """Parse and dispatch one CLI command; injectable dependencies keep tests offline."""

    output = stdout if stdout is not None else sys.stdout
    error = stderr if stderr is not None else sys.stderr
    working_directory = (cwd if cwd is not None else Path.cwd()).resolve(strict=False)
    parser = create_parser()
    try:
        namespace = parser.parse_args(argv)
    except SystemExit as exc:
        return cast(int, exc.code)

    config_path = (
        namespace.config.resolve(strict=False)
        if namespace.config is not None
        else working_directory / DEFAULT_CONFIG_RELATIVE_PATH
    )
    if namespace.command == "doctor":
        try:
            context = DoctorContext(
                cwd=working_directory,
                config_path=config_path,
                environment=environment if environment is not None else os.environ,
                probe=probe if probe is not None else SubprocessProbe(),
                timeout_seconds=namespace.timeout,
            )
            report = run_doctor(context)
        except (OSError, TypeError, ValueError):
            error.write("doctor: internal diagnostic setup failed\n")
            return ExitCode.SOFTWARE
        _write_doctor(report, output, json_output=namespace.json)
        return ExitCode.OK if report.usable else ExitCode.UNAVAILABLE

    selected_executor = executor if executor is not None else UnavailableCommandExecutor()
    request = CommandRequest(
        command=cast(str, namespace.command),
        config_path=config_path,
        arguments=_command_arguments(namespace),
    )
    try:
        response = selected_executor.execute(request)
    except Exception:
        error.write(f"{request.command}: runtime operation failed\n")
        return ExitCode.SOFTWARE
    destination = output if response.exit_code == ExitCode.OK else error
    if namespace.json:
        destination.write(
            json.dumps(
                {
                    "command": request.command,
                    "exit_code": int(response.exit_code),
                    "summary": response.summary,
                },
                sort_keys=True,
            )
            + "\n"
        )
    else:
        destination.write(response.summary + "\n")
    return int(response.exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
