"""Focused C-409 CLI and secret-safe doctor tests."""

from __future__ import annotations

import io
import json
import platform
import sqlite3
import subprocess
from collections.abc import Mapping
from pathlib import Path, PureWindowsPath

import pytest

from harness.cli import (
    COMMAND_NAMES,
    MAX_PROBE_OUTPUT_BYTES,
    PROBE_READ_CHUNK_BYTES,
    CheckStatus,
    CommandRequest,
    CommandResponse,
    DoctorContext,
    ExitCode,
    ProbeResult,
    SubprocessProbe,
    create_parser,
    main,
    run_doctor,
)
from harness.config import (
    HarnessConfig,
    HarnessPaths,
    HostLimits,
    PolicySettings,
    ProviderAdapter,
    ProviderSettings,
    RetrySettings,
    ValidationSettings,
)


class ScriptedProbe:
    def __init__(self, results: Mapping[tuple[str, ...], ProbeResult] | None = None) -> None:
        self.results = dict(results or {})
        self.calls: list[tuple[tuple[str, ...], Path, float]] = []

    def run(
        self,
        args: tuple[str, ...],
        *,
        cwd: Path,
        timeout_seconds: float,
    ) -> ProbeResult:
        self.calls.append((args, cwd, timeout_seconds))
        default = (
            ProbeResult(returncode=0, stdout="codex-cli 0.144.3\n")
            if args == ("codex", "--version")
            else ProbeResult(returncode=0)
        )
        return self.results.get(args, default)


class TrackingStream(io.BytesIO):
    def __init__(self, value: bytes) -> None:
        super().__init__(value)
        self.read_sizes: list[int] = []

    def read(self, size: int | None = -1) -> bytes:
        if size is None or size <= 0:
            raise AssertionError("probe attempted an unbounded pipe read")
        self.read_sizes.append(size)
        return super().read(size)


class CompletedProcess:
    def __init__(self, stdout: bytes, stderr: bytes) -> None:
        self.stdout = TrackingStream(stdout)
        self.stderr = TrackingStream(stderr)
        self.killed = False

    def wait(self, timeout: float | None = None) -> int:
        return 0

    def kill(self) -> None:
        self.killed = True


class TimeoutProcess(CompletedProcess):
    def __init__(self) -> None:
        super().__init__(b"", b"")
        self.wait_calls = 0

    def wait(self, timeout: float | None = None) -> int:
        self.wait_calls += 1
        if self.wait_calls == 1:
            raise subprocess.TimeoutExpired("bounded-probe", 0.0 if timeout is None else timeout)
        return -9


class RecordingExecutor:
    def __init__(self, response: CommandResponse) -> None:
        self.response = response
        self.requests: list[CommandRequest] = []

    def execute(self, request: CommandRequest) -> CommandResponse:
        self.requests.append(request)
        return self.response


def _windows(path: Path) -> PureWindowsPath:
    return PureWindowsPath(str(path.resolve()))


def config_for(
    root: Path,
    *,
    adapter: ProviderAdapter = ProviderAdapter.FAKE,
    docker_enabled: bool = False,
) -> HarnessConfig:
    repository = root / "repository"
    worktrees = root / "worktrees"
    state = root / "state"
    repository.mkdir()
    worktrees.mkdir()
    state.mkdir()
    return HarnessConfig(
        paths=HarnessPaths(
            repository_root=_windows(repository),
            worktree_root=_windows(worktrees),
            host_state_root=_windows(state),
        ),
        provider=ProviderSettings(adapter=adapter),
        limits=HostLimits(max_iterations=3, max_elapsed_seconds=300),
        retry=RetrySettings(
            max_transient_retries=2,
            identical_failure_limit=2,
            no_progress_iteration_limit=2,
            initial_backoff_seconds=0.1,
            maximum_backoff_seconds=1.0,
            backoff_multiplier=2.0,
            jitter_ratio=0.0,
        ),
        validation=ValidationSettings(default_timeout_seconds=30.0, max_output_bytes=4096),
        policy=PolicySettings(docker_enabled=docker_enabled),
    )


def write_config(path: Path, config: HarnessConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config.to_dict()), encoding="utf-8")


def install_validator_markers(repository: Path) -> None:
    scripts = repository / "scripts"
    scripts.mkdir()
    (scripts / "validate_work_specifications.py").write_text("", encoding="utf-8")
    (scripts / "validate_references.py").write_text("", encoding="utf-8")


def check_map(context: DoctorContext) -> dict[str, tuple[CheckStatus, str]]:
    return {check.name: (check.status, check.summary) for check in run_doctor(context).checks}


def test_parser_declares_exact_c409_command_surface() -> None:
    parser = create_parser()
    minimal_arguments = {
        "init": ("init", "C:/repo"),
        "research": ("research",),
        "doctor": ("doctor",),
        "run": ("run", "--goal", "goal.yaml"),
        "status": ("status", "run.001"),
        "events": ("events", "run.001"),
        "resume": ("resume", "run.001"),
        "pause": ("pause", "run.001"),
        "cancel": ("cancel", "run.001"),
        "evaluate": ("evaluate", "run.001"),
        "cleanup": ("cleanup", "run.001"),
    }
    assert tuple(minimal_arguments) == COMMAND_NAMES
    for command, arguments in minimal_arguments.items():
        assert parser.parse_args(arguments).command == command


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (("init", "C:/repo"), (("path", "C:\\repo"),)),
        (("research",), ()),
        (("run", "--goal", "goal.yaml"), (("goal", "goal.yaml"),)),
        (("status", "run.001"), (("run_id", "run.001"),)),
        (("events", "run.001"), (("run_id", "run.001"),)),
        (("resume", "run.001"), (("run_id", "run.001"),)),
        (("pause", "run.001"), (("run_id", "run.001"),)),
        (("cancel", "run.001"), (("run_id", "run.001"),)),
        (("evaluate", "run.001"), (("run_id", "run.001"),)),
        (("cleanup", "run.001"), (("run_id", "run.001"),)),
    ],
)
def test_non_doctor_commands_dispatch_without_side_effects(
    tmp_path: Path, argv: tuple[str, ...], expected: tuple[tuple[str, str], ...]
) -> None:
    executor = RecordingExecutor(CommandResponse(exit_code=0, summary="accepted"))
    stdout = io.StringIO()
    assert main(argv, stdout=stdout, cwd=tmp_path, executor=executor) == ExitCode.OK
    assert stdout.getvalue() == "accepted\n"
    assert executor.requests[0].arguments == expected


def test_default_executor_fails_closed() -> None:
    stderr = io.StringIO()
    assert main(("status", "run.001"), stderr=stderr) == ExitCode.UNAVAILABLE
    assert "integrated runtime operation is not configured" in stderr.getvalue()


def test_doctor_passes_with_clean_injected_environment(tmp_path: Path) -> None:
    config = config_for(tmp_path)
    repository = Path(str(config.paths.repository_root))
    install_validator_markers(repository)
    config_path = tmp_path / "config.json"
    write_config(config_path, config)
    context = DoctorContext(
        cwd=repository,
        config_path=config_path,
        environment={},
        probe=ScriptedProbe(),
    )
    report = run_doctor(context)
    assert report.usable
    assert {check.name for check in report.checks} == {
        "runtime",
        "config",
        "codex",
        "app_server",
        "git",
        "repository",
        "worktrees",
        "validators",
        "sqlite",
        "permissions",
        "credentials",
    }
    assert check_map(context)["credentials"][0] is CheckStatus.SKIP


def test_doctor_reports_sanitized_exact_versions_and_sqlite_path(tmp_path: Path) -> None:
    config = config_for(tmp_path)
    repository = Path(str(config.paths.repository_root))
    install_validator_markers(repository)
    config_path = tmp_path / "config.json"
    write_config(config_path, config)
    secret = "must-not-appear"
    checks = check_map(
        DoctorContext(
            cwd=repository,
            config_path=config_path,
            environment={},
            probe=ScriptedProbe(
                {
                    ("codex", "--version"): ProbeResult(
                        0, stdout=f"codex-cli 0.144.3 token={secret}\n"
                    )
                }
            ),
        )
    )
    assert checks["runtime"] == (
        CheckStatus.PASS,
        f"Python {platform.python_version()} satisfies minimum 3.12",
    )
    assert checks["codex"] == (CheckStatus.PASS, "Codex 0.144.3 is available")
    assert checks["app_server"] == (
        CheckStatus.PASS,
        "Codex App Server is available through Codex 0.144.3",
    )
    sqlite_summary = checks["sqlite"][1]
    assert f"SQLite {sqlite3.sqlite_version}" in sqlite_summary
    assert str(Path(str(config.paths.database_path)).resolve(strict=False)) in sqlite_summary
    assert secret not in "\n".join(summary for _, summary in checks.values())


def test_doctor_reports_dirty_repository_without_echoing_git_output(tmp_path: Path) -> None:
    config = config_for(tmp_path)
    repository = Path(str(config.paths.repository_root))
    install_validator_markers(repository)
    config_path = tmp_path / "config.json"
    write_config(config_path, config)
    secret = "OPENAI_API_KEY=super-secret-value"
    probe = ScriptedProbe(
        {("git", "status", "--porcelain"): ProbeResult(0, stdout=f"?? {secret}\n")}
    )
    stdout = io.StringIO()
    code = main(
        ("--config", str(config_path), "doctor"),
        stdout=stdout,
        cwd=repository,
        environment={"OPENAI_API_KEY": "super-secret-value"},
        probe=probe,
    )
    assert code == ExitCode.UNAVAILABLE
    assert "FAIL repository: repository has uncommitted changes" in stdout.getvalue()
    assert "super-secret" not in stdout.getvalue()


def test_doctor_reports_missing_codex_app_server_and_git(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    install_validator_markers(repository)
    probe = ScriptedProbe(
        {
            ("codex", "--version"): ProbeResult(-1),
            ("codex", "app-server", "--help"): ProbeResult(-1),
            ("git", "--version"): ProbeResult(-1),
            ("git", "status", "--porcelain"): ProbeResult(-1),
            ("git", "worktree", "list", "--porcelain"): ProbeResult(-1),
        }
    )
    checks = check_map(
        DoctorContext(
            cwd=repository,
            config_path=tmp_path / "missing.json",
            environment={},
            probe=probe,
        )
    )
    assert checks["codex"][0] is CheckStatus.FAIL
    assert checks["app_server"][0] is CheckStatus.FAIL
    assert checks["git"][0] is CheckStatus.FAIL
    assert checks["repository"][0] is CheckStatus.FAIL
    assert checks["worktrees"][0] is CheckStatus.FAIL


def test_doctor_checks_docker_only_when_configured(tmp_path: Path) -> None:
    config = config_for(tmp_path, docker_enabled=True)
    repository = Path(str(config.paths.repository_root))
    install_validator_markers(repository)
    config_path = tmp_path / "config.json"
    write_config(config_path, config)
    probe = ScriptedProbe({("docker", "version"): ProbeResult(-1)})
    checks = check_map(
        DoctorContext(
            cwd=repository,
            config_path=config_path,
            environment={},
            probe=probe,
        )
    )
    assert checks["docker"][0] is CheckStatus.FAIL
    assert ("docker", "version") in [call[0] for call in probe.calls]


def test_codex_credentials_are_presence_only_and_secret_safe(tmp_path: Path) -> None:
    config = config_for(tmp_path, adapter=ProviderAdapter.CODEX_APP_SERVER)
    repository = Path(str(config.paths.repository_root))
    install_validator_markers(repository)
    config_path = tmp_path / "config.json"
    write_config(config_path, config)
    value = "sk-test-do-not-print"
    context = DoctorContext(
        cwd=repository,
        config_path=config_path,
        environment={"OPENAI_API_KEY": value},
        probe=ScriptedProbe(),
    )
    status, summary = check_map(context)["credentials"]
    assert status is CheckStatus.PASS
    assert value not in summary


def test_missing_codex_credentials_fail_without_values(tmp_path: Path) -> None:
    config = config_for(tmp_path, adapter=ProviderAdapter.CODEX_APP_SERVER)
    repository = Path(str(config.paths.repository_root))
    install_validator_markers(repository)
    config_path = tmp_path / "config.json"
    write_config(config_path, config)
    status, summary = check_map(
        DoctorContext(
            cwd=repository,
            config_path=config_path,
            environment={"CODEX_HOME": str(tmp_path / "empty-codex-home")},
            probe=ScriptedProbe(),
        )
    )["credentials"]
    assert status is CheckStatus.FAIL
    assert "no values were displayed" in summary


def test_existing_sqlite_database_is_opened_read_only(tmp_path: Path) -> None:
    config = config_for(tmp_path)
    repository = Path(str(config.paths.repository_root))
    install_validator_markers(repository)
    database = Path(str(config.paths.database_path))
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE marker(value TEXT)")
        connection.execute("INSERT INTO marker(value) VALUES('unchanged')")
    before = database.read_bytes()
    config_path = tmp_path / "config.json"
    write_config(config_path, config)
    checks = check_map(
        DoctorContext(
            cwd=repository,
            config_path=config_path,
            environment={},
            probe=ScriptedProbe(),
        )
    )
    assert checks["sqlite"][0] is CheckStatus.PASS
    assert database.read_bytes() == before


def test_invalid_config_is_reported_without_parser_details(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text('{"credential": "secret-value"}', encoding="utf-8")
    repository = tmp_path / "repository"
    repository.mkdir()
    install_validator_markers(repository)
    stdout = io.StringIO()
    main(
        ("--config", str(config_path), "doctor"),
        stdout=stdout,
        cwd=repository,
        environment={},
        probe=ScriptedProbe(),
    )
    assert "FAIL config: configuration is present but invalid" in stdout.getvalue()
    assert "secret-value" not in stdout.getvalue()


def test_doctor_json_output_is_deterministic_and_contains_no_raw_probe_output(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    install_validator_markers(repository)
    probe = ScriptedProbe(
        {("codex", "--version"): ProbeResult(0, stdout="codex-cli 0.144.3 token=secret")}
    )
    stdout = io.StringIO()
    assert (
        main(
            ("--json", "doctor"),
            stdout=stdout,
            cwd=repository,
            environment={},
            probe=probe,
        )
        == ExitCode.OK
    )
    decoded = json.loads(stdout.getvalue())
    assert decoded["usable"] is True
    assert "secret" not in stdout.getvalue()


def test_doctor_probes_are_bounded_and_shell_free_by_contract(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    install_validator_markers(repository)
    probe = ScriptedProbe()
    run_doctor(
        DoctorContext(
            cwd=repository,
            config_path=tmp_path / "missing.json",
            environment={},
            probe=probe,
            timeout_seconds=1.25,
        )
    )
    assert probe.calls
    assert all(timeout == 1.25 for _, _, timeout in probe.calls)
    assert all(isinstance(args, tuple) for args, _, _ in probe.calls)


def test_subprocess_probe_bounds_capture_before_retention(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"x" * (MAX_PROBE_OUTPUT_BYTES * 20)
    process = CompletedProcess(payload, payload.replace(b"x", b"y"))
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: process)
    result = SubprocessProbe().run(
        ("bounded-probe",),
        cwd=tmp_path,
        timeout_seconds=30.0,
    )
    assert result.returncode == 0
    assert len(result.stdout.encode()) == MAX_PROBE_OUTPUT_BYTES
    assert len(result.stderr.encode()) == MAX_PROBE_OUTPUT_BYTES
    assert process.stdout.read_sizes
    assert process.stderr.read_sizes
    assert max(process.stdout.read_sizes) == PROBE_READ_CHUNK_BYTES
    assert max(process.stderr.read_sizes) == PROBE_READ_CHUNK_BYTES


def test_subprocess_probe_kills_a_timed_out_child(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    process = TimeoutProcess()
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: process)
    result = SubprocessProbe().run(
        ("bounded-probe",),
        cwd=tmp_path,
        timeout_seconds=0.01,
    )
    assert result.returncode == -1
    assert process.killed
    assert process.wait_calls == 2
