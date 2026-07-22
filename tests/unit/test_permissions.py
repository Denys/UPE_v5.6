from __future__ import annotations

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from harness.approvals import Decision
from harness.permissions import (
    CommandPolicy,
    CommandRequest,
    CommandRule,
    NetworkPolicy,
    NetworkRequest,
    NetworkRule,
    PathOperation,
    PathPolicy,
    PathRequest,
    evaluate_command,
    evaluate_network,
    evaluate_path,
    filter_environment,
    redact_payload,
)
from harness.state import RedactionStatus
from harness.workspace import FilesystemIdentity, GitStatus, WorkspaceAssignment

WORKSPACE = Path(r"C:\repo\worktrees\c505")
EXECUTABLE = r"C:\tools\uv.exe"


def assignment(*, workspace: Path = WORKSPACE) -> WorkspaceAssignment:
    return WorkspaceAssignment(
        task_id="C-505",
        workspace=workspace,
        root_identity=FilesystemIdentity(device=1, inode=10),
        workspace_identity=FilesystemIdentity(device=1, inode=11),
        git_head="a" * 40,
        git_branch="codex/c505-cloud-coordinator",
        owner_token="owner-token",
        observed_status=GitStatus(),
    )


def command_policy(
    *,
    rules: tuple[CommandRule, ...] | None = None,
    environment_keys: tuple[str, ...] = ("PATH", "TEMP"),
    workspace: Path = WORKSPACE,
) -> CommandPolicy:
    if rules is None:
        rules = (
            CommandRule(
                executable=EXECUTABLE,
                argument_vectors=(("run", "pytest", "-q"),),
            ),
        )
    return CommandPolicy(
        workspace=assignment(workspace=workspace),
        rules=rules,
        allowed_environment_keys=environment_keys,
        maximum_timeout_seconds=60,
        maximum_output_bytes=4096,
    )


def command_request(**changes: object) -> CommandRequest:
    values: dict[str, object] = {
        "executable": EXECUTABLE,
        "arguments": ("run", "pytest", "-q"),
        "cwd": WORKSPACE,
        "observed_workspace_identity": FilesystemIdentity(device=1, inode=11),
        "observed_reparse_components": (),
        "timeout_seconds": 30,
        "output_limit_bytes": 2048,
    }
    values.update(changes)
    return CommandRequest(**values)  # type: ignore[arg-type]


def network_rule() -> NetworkRule:
    return NetworkRule(
        scheme="https",
        host="api.example.test",
        port=443,
        purpose="read-source",
        resolved_destinations=("203.0.113.10",),
    )


def network_request(**changes: object) -> NetworkRequest:
    values: dict[str, object] = {
        "url": "https://api.example.test/v1/data",
        "purpose": "read-source",
        "resolved_destination": "203.0.113.10",
        "resolved_port": 443,
    }
    values.update(changes)
    return NetworkRequest(**values)  # type: ignore[arg-type]


def test_exact_structured_command_and_minimized_environment_are_allowed() -> None:
    decision, environment = evaluate_command(
        command_policy(),
        command_request(),
        environment={"PATH": r"C:\tools", "TEMP": r"C:\temp", "UNRELATED": "drop"},
    )

    assert decision.decision is Decision.ALLOWED
    assert environment.values == (("PATH", r"C:\tools"), ("TEMP", r"C:\temp"))
    assert environment.dropped_keys == ("UNRELATED",)


def test_default_deny_command_policy_runs_nothing() -> None:
    decision, environment = evaluate_command(
        command_policy(rules=()),
        command_request(),
        environment={},
    )

    assert decision.decision is Decision.FORBIDDEN
    assert environment.values == ()


@pytest.mark.parametrize(
    "changes",
    [
        {"executable": r"C:\tools\git.exe"},
        {"arguments": ("run", "pytest")},
        {"cwd": Path(r"C:\repo\worktrees\other")},
        {"timeout_seconds": 61},
        {"output_limit_bytes": 4097},
    ],
)
def test_command_scope_drift_is_forbidden(changes: dict[str, object]) -> None:
    decision, _ = evaluate_command(
        command_policy(),
        command_request(**changes),
        environment={},
    )

    assert decision.decision is Decision.FORBIDDEN


@pytest.mark.parametrize(
    "changes",
    [
        {"observed_workspace_identity": FilesystemIdentity(device=1, inode=99)},
        {"observed_reparse_components": (str(WORKSPACE),)},
    ],
)
def test_command_requires_fresh_workspace_identity_and_no_reparse(
    changes: dict[str, object],
) -> None:
    decision, _ = evaluate_command(
        command_policy(),
        command_request(**changes),
        environment={},
    )

    assert decision.decision is Decision.FORBIDDEN


def test_malformed_assigned_command_workspace_returns_forbidden() -> None:
    decision, _ = evaluate_command(
        command_policy(workspace=Path("relative")),
        command_request(),
        environment={},
    )

    assert decision.decision is Decision.FORBIDDEN
    assert decision.reason.startswith("command cwd or assigned workspace is malformed:")


@pytest.mark.parametrize(
    "arguments",
    [
        ("status; whoami",),
        ("status | more",),
        ("%USERPROFILE%",),
        ("$env:USERPROFILE",),
        ("token=C505_SECRET_CANARY_CMD",),
    ],
)
def test_shell_composition_expansion_and_secrets_are_rejected(
    arguments: tuple[str, ...],
) -> None:
    with pytest.raises(ValueError):
        CommandRule(executable=EXECUTABLE, argument_vectors=(arguments,))


@pytest.mark.parametrize(
    "executable",
    [r"C:\tools\python3.14.exe", r"C:\tools\python3.14", r"C:\tools\cmd"],
)
def test_interpreters_require_an_explicit_narrow_rule(executable: str) -> None:
    request = command_request(executable=executable, arguments=("-m", "pytest"))
    denied, _ = evaluate_command(
        command_policy(
            rules=(CommandRule(executable=executable, argument_vectors=(("-m", "pytest"),)),)
        ),
        request,
        environment={},
    )
    allowed, _ = evaluate_command(
        command_policy(
            rules=(
                CommandRule(
                    executable=executable,
                    argument_vectors=(("-m", "pytest"),),
                    allow_interpreter=True,
                ),
            )
        ),
        request,
        environment={},
    )

    assert denied.decision is Decision.FORBIDDEN
    assert allowed.decision is Decision.ALLOWED


@pytest.mark.parametrize(
    "arguments",
    [
        ("--password", "hunter2"),
        ("--token", "opaque-session-token"),
        ("--api-key", "abcdef"),
        ("/client-secret", "opaque-session-secret"),
    ],
)
def test_split_credential_flags_are_rejected(arguments: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="credential-bearing argument flag"):
        CommandRule(executable=EXECUTABLE, argument_vectors=(arguments,))


def test_command_arguments_and_environment_values_are_bounded() -> None:
    with pytest.raises(ValueError, match="too many"):
        CommandRule(
            executable=EXECUTABLE,
            argument_vectors=(tuple("arg" for _ in range(65)),),
        )
    with pytest.raises(TypeError, match="control-free"):
        CommandRule(
            executable=EXECUTABLE,
            argument_vectors=(("x" * 4097,),),
        )
    with pytest.raises(ValueError, match="bounded"):
        filter_environment(command_policy(), {"PATH": "x" * 32768})


def test_environment_never_inherits_unpassed_values_or_inline_credentials() -> None:
    filtered = filter_environment(command_policy(), {"PATH": r"C:\tools"})
    assert filtered.values == (("PATH", r"C:\tools"),)

    with pytest.raises(ValueError, match="credential"):
        filter_environment(command_policy(), {"PATH": "Bearer C505_SECRET_CANARY_ENV"})
    with pytest.raises(ValueError, match="credential-like"):
        command_policy(environment_keys=("API_TOKEN",))


@pytest.mark.parametrize("operation", [PathOperation.READ, PathOperation.WRITE])
def test_contained_child_path_is_allowed(operation: PathOperation) -> None:
    result = evaluate_path(
        PathPolicy(workspace=assignment()),
        PathRequest(
            workspace=WORKSPACE,
            observed_workspace_identity=FilesystemIdentity(device=1, inode=11),
            relative_path=r"src\harness\state.py",
            operation=operation,
        ),
    )

    assert result.decision is Decision.ALLOWED
    assert result.normalized_target == str(WORKSPACE / "src" / "harness" / "state.py")


@pytest.mark.parametrize(
    "relative_path",
    [
        r"..\other\secret.txt",
        r"C:\outside\secret.txt",
        r"\\server\share\secret.txt",
        r"file.txt:stream",
        r"\\?\C:\repo\file.txt",
        r"src\*.py",
        r"%TEMP%\file.txt",
        r"NUL.txt",
        r"folder.\file.txt",
        "src\\ok\nFORGED=1.txt",
        "src\\bad\tname.txt",
        'src\\bad"name.txt',
    ],
)
def test_windows_path_escape_classes_fail_closed(relative_path: str) -> None:
    result = evaluate_path(
        PathPolicy(workspace=assignment()),
        PathRequest(
            workspace=WORKSPACE,
            observed_workspace_identity=FilesystemIdentity(device=1, inode=11),
            relative_path=relative_path,
            operation=PathOperation.WRITE,
        ),
    )

    assert result.decision is Decision.FORBIDDEN


def test_workspace_identity_reparse_and_cleanup_require_stronger_boundaries() -> None:
    policy = PathPolicy(workspace=assignment())
    wrong_workspace = evaluate_path(
        policy,
        PathRequest(
            workspace=Path(r"C:\repo\worktrees\sibling"),
            observed_workspace_identity=FilesystemIdentity(device=1, inode=11),
            relative_path="file.txt",
            operation=PathOperation.WRITE,
        ),
    )
    reparse = evaluate_path(
        policy,
        PathRequest(
            workspace=WORKSPACE,
            observed_workspace_identity=FilesystemIdentity(device=1, inode=11),
            relative_path="file.txt",
            operation=PathOperation.WRITE,
            observed_reparse_components=(r"C:\repo\worktrees\c505\link",),
        ),
    )
    cleanup = evaluate_path(
        policy,
        PathRequest(
            workspace=WORKSPACE,
            observed_workspace_identity=FilesystemIdentity(device=1, inode=11),
            relative_path="file.txt",
            operation=PathOperation.CLEANUP,
        ),
    )

    assert wrong_workspace.decision is Decision.FORBIDDEN
    assert reparse.decision is Decision.FORBIDDEN
    assert cleanup.decision is Decision.FORBIDDEN


@pytest.mark.parametrize(
    "malformed_workspace",
    [Path("relative"), Path(r"\\server\share"), Path(r"\rooted")],
)
def test_malformed_request_workspace_returns_forbidden(malformed_workspace: Path) -> None:
    result = evaluate_path(
        PathPolicy(workspace=assignment()),
        PathRequest(
            workspace=malformed_workspace,
            observed_workspace_identity=FilesystemIdentity(device=1, inode=11),
            relative_path="file.txt",
            operation=PathOperation.READ,
        ),
    )

    assert result.decision is Decision.FORBIDDEN
    assert result.reason.startswith("path workspace is malformed:")


def test_path_requires_fresh_workspace_identity() -> None:
    result = evaluate_path(
        PathPolicy(workspace=assignment()),
        PathRequest(
            workspace=WORKSPACE,
            observed_workspace_identity=FilesystemIdentity(device=1, inode=99),
            relative_path="file.txt",
            operation=PathOperation.READ,
        ),
    )

    assert result.decision is Decision.FORBIDDEN
    assert result.reason == "path workspace filesystem identity changed after assignment"


def test_network_is_default_deny_and_exact_rule_allows_one_destination() -> None:
    denied = evaluate_network(NetworkPolicy(), network_request())
    allowed = evaluate_network(NetworkPolicy(rules=(network_rule(),)), network_request())

    assert denied.decision is Decision.FORBIDDEN
    assert allowed.decision is Decision.ALLOWED
    assert allowed.normalized_target == "https://api.example.test:443"


@pytest.mark.parametrize(
    "changes",
    [
        {"purpose": "write-source"},
        {"resolved_destination": "203.0.113.11"},
        {"resolved_port": 444},
        {"redirect_url": "https://api.example.test/other"},
        {"url": "https://user:password@api.example.test/v1/data"},
        {"url": "https://api.example.test/v1/data#fragment"},
        {"url": "https://api.example.test/v1/data?token=C505_SECRET_CANARY_URL"},
        {"url": "https://api.example.test\\@evil.test/v1/data"},
        {"url": "not-a-url"},
    ],
)
def test_network_scope_drift_redirects_and_credentials_are_forbidden(
    changes: dict[str, object],
) -> None:
    result = evaluate_network(
        NetworkPolicy(rules=(network_rule(),)),
        network_request(**changes),
    )

    assert result.decision is Decision.FORBIDDEN


def test_malformed_hostname_is_rejected_before_policy_use() -> None:
    with pytest.raises(ValueError, match="hostname"):
        NetworkRule(
            scheme="https",
            host="api..example.test",
            port=443,
            purpose="read-source",
            resolved_destinations=("203.0.113.10",),
        )
    with pytest.raises(ValueError, match="valid IP"):
        NetworkRule(
            scheme="https",
            host="api.example.test",
            port=443,
            purpose="read-source",
            resolved_destinations=("999.0.0.1",),
        )


def test_recursive_redaction_covers_success_error_nested_bytes_and_pii() -> None:
    payload = {
        "authorization": "Bearer C505_SECRET_CANARY_HEADER",
        "nested": [
            "email person@example.test phone +41 79 123 45 67",
            {"url": "https://user:pass@example.test/path?token=C505_SECRET_CANARY_URL"},
        ],
        "binary": b"C505_SECRET_CANARY_BYTES",
        "error": RuntimeError("password=C505_SECRET_CANARY_ERROR correlation=trace-123"),
        "correlation_id": "trace-123",
        "person@example.test": "mapping-key-pii",
        "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature123",
        "pem": ("-----BEGIN PRIVATE KEY-----\nC505_SECRET_CANARY_PEM\n-----END PRIVATE KEY-----"),
    }

    result = redact_payload(payload)
    rendered = repr(result.value)

    assert result.status is RedactionStatus.REDACTED
    assert "C505_SECRET_CANARY" not in rendered
    assert "person@example.test" not in rendered
    assert "+41 79 123 45 67" not in rendered
    assert "trace-123" in rendered
    assert "RuntimeError" in rendered
    assert "person@example.test" not in rendered
    assert "eyJhbGci" not in rendered
    assert "BEGIN PRIVATE KEY" not in rendered


def test_flat_text_redaction_covers_prefixed_credential_assignments() -> None:
    result = redact_payload("MY_PASSWORD=hunter2 AWS_SECRET_ACCESS_KEY=access-key-value")
    rendered = str(result.value)

    assert result.status is RedactionStatus.REDACTED
    assert "hunter2" not in rendered
    assert "access-key-value" not in rendered
    assert "MY_PASSWORD=<REDACTED:SECRET>" in rendered
    assert "AWS_SECRET_ACCESS_KEY=<REDACTED:SECRET>" in rendered


def test_assignment_redaction_consumes_quoted_values_with_separators() -> None:
    result = redact_payload('MY_PASSWORD="abc def,ghi;still-secret" CORRELATION_ID=trace-123')
    rendered = str(result.value)

    assert result.status is RedactionStatus.REDACTED
    assert "abc" not in rendered
    assert "def" not in rendered
    assert "ghi" not in rendered
    assert "still-secret" not in rendered
    assert "CORRELATION_ID=trace-123" in rendered


@pytest.mark.parametrize(
    ("payload", "secret", "safe_context"),
    [
        ('{"api_key":"opaque-session","status":"ok"}', "opaque-session", '"status":"ok"'),
        ("'password': 'hunter2'\nstatus: ok", "hunter2", "status: ok"),
    ],
)
def test_assignment_redaction_covers_quoted_serialized_keys(
    payload: str,
    secret: str,
    safe_context: str,
) -> None:
    result = redact_payload(payload)
    rendered = str(result.value)

    assert result.status is RedactionStatus.REDACTED
    assert secret not in rendered
    assert safe_context in rendered


@pytest.mark.parametrize("scheme", ["Bearer", "Basic"])
def test_authorization_header_redacts_opaque_secret_before_assignment(
    scheme: str,
) -> None:
    result = redact_payload(f"Authorization: {scheme} opaque-session-token")
    rendered = str(result.value)

    assert result.status is RedactionStatus.REDACTED
    assert "opaque-session-token" not in rendered


@pytest.mark.parametrize(
    "url",
    ["https://opaque-token@localhost/repo", "ssh://opaque-token@internal/repo"],
)
def test_url_userinfo_redacts_username_only_credentials(url: str) -> None:
    result = redact_payload(url)
    rendered = str(result.value)

    assert result.status is RedactionStatus.REDACTED
    assert "opaque-token" not in rendered
    assert "<REDACTED:USERINFO>@" in rendered


def test_safe_payload_is_preserved_without_false_redaction_marker() -> None:
    payload = {"status": "PASS", "count": 2, "refs": ("artifact-1",)}
    result = redact_payload(payload)

    assert result.status is RedactionStatus.NOT_REQUIRED
    assert result.value == payload


def test_cycles_depth_and_unsupported_types_fail_closed() -> None:
    cyclic: list[object] = []
    cyclic.append(cyclic)
    cycle_result = redact_payload(cyclic)

    deep: object = "safe"
    for _ in range(40):
        deep = [deep]
    depth_result = redact_payload(deep)
    unsupported_result = redact_payload(object())

    assert cycle_result.status is RedactionStatus.REDACTED
    assert "<REDACTED:CYCLE>" in repr(cycle_result.value)
    assert "<REDACTED:MAX_DEPTH>" in repr(depth_result.value)
    assert "<REDACTED:UNSUPPORTED_TYPE:object>" == unsupported_result.value


def test_policy_records_are_immutable() -> None:
    policy = command_policy()
    with pytest.raises(FrozenInstanceError):
        policy.maximum_output_bytes = 1  # type: ignore[misc]
