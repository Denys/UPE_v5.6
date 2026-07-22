"""Pure trusted-host command, path, network, environment, and redaction policy.

All decisions are deny-by-default and side-effect free.  Callers must provide
the environment and observed path/network facts explicitly; this module never
inherits the process environment, resolves DNS, starts a process, or touches a
filesystem.
"""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from ipaddress import ip_address
from pathlib import Path, PureWindowsPath
from urllib.parse import urlsplit

from harness.approvals import Decision
from harness.state import RedactionStatus
from harness.workspace import FilesystemIdentity, WorkspaceAssignment

_ENVIRONMENT_KEY = re.compile(r"[A-Z][A-Z0-9_]{0,127}\Z")
_HOST = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?\Z")
_SENSITIVE_KEY = re.compile(
    r"(?i)(?:authorization|cookie|credential|password|passwd|secret|token|api[-_]?key|private[-_]?key)"
)
_INTERPRETERS = frozenset(
    {
        "bash.exe",
        "cmd.exe",
        "node.exe",
        "powershell.exe",
        "pwsh.exe",
        "py.exe",
        "python.exe",
        "python3.exe",
        "sh.exe",
        "wscript.exe",
        "cscript.exe",
    }
)
_INTERPRETER_NAME = re.compile(
    r"(?i)(?:bash|bun|cmd|cscript|deno|fish|java|jshell|nodejs?|perl|php|"
    r"powershell|pwsh|py|pypy\d*|python(?:\d+(?:\.\d+)*)?|ruby|sh|wscript|zsh)\.exe\Z"
)
_RESERVED_NAMES = frozenset(
    {"AUX", "CLOCK$", "CON", "NUL", "PRN"}
    | {f"COM{index}" for index in range(1, 10)}
    | {f"LPT{index}" for index in range(1, 10)}
)
_SHELL_COMPOSITION = re.compile(r"[|&;<>`\r\n]|\$\(|\)\s*\{")
_VARIABLE_EXPANSION = re.compile(r"%[^%]+%|\$\{[^}]+\}|\$[A-Za-z_][A-Za-z0-9_]*")

_EMAIL = re.compile(r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![\w.-])")
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d .()/-]{6,}\d)(?!\w)")
_BEARER = re.compile(r"(?i)\b(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{6,}")
_SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b([A-Z0-9_-]*(?:authorization|cookie|credential|password|passwd|secret|token|"
    r"api[-_]?key|private[-_]?key)[A-Z0-9_-]*)"
    r"(\s*[:=]\s*)([^\r\n]*?)(?=(?:[\s,;&]+[A-Z][A-Z0-9_-]*\s*[:=])|[\r\n]|$)"
)
_TOKEN = re.compile(
    r"(?i)\b(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9_]{8,}|AKIA[0-9A-Z]{12,})\b"
)
_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b")
_PRIVATE_KEY = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"
)
_URL_USERINFO = re.compile(r"(?i)(https?://)([^/@\s:]+):([^/@\s]+)@")
_SECRET_CANARY = re.compile(r"C505_SECRET_CANARY_[A-Za-z0-9_-]+")

_MAX_ARGUMENTS = 64
_MAX_ARGUMENT_LENGTH = 4096
_MAX_ARGUMENT_VECTORS = 256
_MAX_ENVIRONMENT_VALUE = 32767


@dataclass(frozen=True, slots=True, kw_only=True)
class PermissionDecision:
    decision: Decision
    reason: str
    normalized_target: str | None = None

    def __post_init__(self) -> None:
        if type(self.decision) is not Decision:
            raise TypeError("PermissionDecision.decision must be Decision")
        _require_text(self.reason, "PermissionDecision.reason")
        if self.normalized_target is not None:
            _require_text(self.normalized_target, "PermissionDecision.normalized_target")

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOWED


@dataclass(frozen=True, slots=True, kw_only=True)
class EnvironmentFilter:
    values: tuple[tuple[str, str], ...]
    dropped_keys: tuple[str, ...]

    def __post_init__(self) -> None:
        if type(self.values) is not tuple or any(
            type(item) is not tuple
            or len(item) != 2
            or type(item[0]) is not str
            or type(item[1]) is not str
            for item in self.values
        ):
            raise TypeError("EnvironmentFilter.values must be string pairs")
        if type(self.dropped_keys) is not tuple or any(
            type(key) is not str for key in self.dropped_keys
        ):
            raise TypeError("EnvironmentFilter.dropped_keys must be a string tuple")


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandRule:
    executable: str
    argument_vectors: tuple[tuple[str, ...], ...]
    allow_interpreter: bool = False

    def __post_init__(self) -> None:
        _safe_absolute_windows_path(self.executable, "CommandRule.executable")
        if type(self.argument_vectors) is not tuple or not self.argument_vectors:
            raise ValueError("CommandRule.argument_vectors must be a non-empty tuple")
        if len(self.argument_vectors) > _MAX_ARGUMENT_VECTORS:
            raise ValueError("CommandRule.argument_vectors exceeds the policy limit")
        if type(self.allow_interpreter) is not bool:
            raise TypeError("CommandRule.allow_interpreter must be a boolean")
        for index, vector in enumerate(self.argument_vectors):
            _require_arguments(vector, f"CommandRule.argument_vectors[{index}]")
        if len(set(self.argument_vectors)) != len(self.argument_vectors):
            raise ValueError("CommandRule.argument_vectors must not contain duplicates")


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandPolicy:
    workspace: WorkspaceAssignment
    rules: tuple[CommandRule, ...]
    allowed_environment_keys: tuple[str, ...]
    maximum_timeout_seconds: float
    maximum_output_bytes: int

    def __post_init__(self) -> None:
        if type(self.workspace) is not WorkspaceAssignment:
            raise TypeError("CommandPolicy.workspace must be a WorkspaceAssignment")
        if type(self.rules) is not tuple:
            raise TypeError("CommandPolicy.rules must be a tuple")
        if any(type(rule) is not CommandRule for rule in self.rules):
            raise TypeError("CommandPolicy.rules must contain CommandRule values")
        if len({rule.executable.casefold() for rule in self.rules}) != len(self.rules):
            raise ValueError("CommandPolicy.rules must have unique executable identities")
        _require_environment_keys(self.allowed_environment_keys)
        if type(self.maximum_timeout_seconds) not in (int, float):
            raise TypeError("CommandPolicy.maximum_timeout_seconds must be numeric")
        if not 0 < float(self.maximum_timeout_seconds) <= 3600:
            raise ValueError("CommandPolicy.maximum_timeout_seconds must be in (0, 3600]")
        if (
            type(self.maximum_output_bytes) is not int
            or not 1 <= self.maximum_output_bytes <= 10**8
        ):
            raise ValueError("CommandPolicy.maximum_output_bytes must be in [1, 100000000]")


@dataclass(frozen=True, slots=True, kw_only=True)
class CommandRequest:
    executable: str
    arguments: tuple[str, ...]
    cwd: Path
    observed_workspace_identity: FilesystemIdentity
    observed_reparse_components: tuple[str, ...]
    timeout_seconds: float
    output_limit_bytes: int

    def __post_init__(self) -> None:
        _safe_absolute_windows_path(self.executable, "CommandRequest.executable")
        _require_arguments(self.arguments, "CommandRequest.arguments")
        if not isinstance(self.cwd, Path):
            raise TypeError("CommandRequest.cwd must be a Path")
        _safe_absolute_windows_path(str(self.cwd), "CommandRequest.cwd")
        if type(self.observed_workspace_identity) is not FilesystemIdentity:
            raise TypeError("CommandRequest.observed_workspace_identity must be FilesystemIdentity")
        if type(self.observed_reparse_components) is not tuple or any(
            type(item) is not str or not item for item in self.observed_reparse_components
        ):
            raise TypeError("CommandRequest.observed_reparse_components must be text tuple")
        if type(self.timeout_seconds) not in (int, float) or not 0 < float(self.timeout_seconds):
            raise ValueError("CommandRequest.timeout_seconds must be positive")
        if type(self.output_limit_bytes) is not int or self.output_limit_bytes < 1:
            raise ValueError("CommandRequest.output_limit_bytes must be positive")


class PathOperation(StrEnum):
    READ = "READ"
    WRITE = "WRITE"
    CLEANUP = "CLEANUP"


@dataclass(frozen=True, slots=True, kw_only=True)
class PathPolicy:
    workspace: WorkspaceAssignment

    def __post_init__(self) -> None:
        if type(self.workspace) is not WorkspaceAssignment:
            raise TypeError("PathPolicy.workspace must be a WorkspaceAssignment")


@dataclass(frozen=True, slots=True, kw_only=True)
class PathRequest:
    workspace: Path
    observed_workspace_identity: FilesystemIdentity
    relative_path: str
    operation: PathOperation
    observed_reparse_components: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.workspace, Path):
            raise TypeError("PathRequest.workspace must be a Path")
        if type(self.observed_workspace_identity) is not FilesystemIdentity:
            raise TypeError("PathRequest.observed_workspace_identity must be FilesystemIdentity")
        if type(self.relative_path) is not str:
            raise TypeError("PathRequest.relative_path must be a string")
        if type(self.operation) is not PathOperation:
            raise TypeError("PathRequest.operation must be PathOperation")
        if type(self.observed_reparse_components) is not tuple or any(
            type(item) is not str or not item for item in self.observed_reparse_components
        ):
            raise TypeError("PathRequest.observed_reparse_components must be text tuple")


@dataclass(frozen=True, slots=True, kw_only=True)
class NetworkRule:
    scheme: str
    host: str
    port: int
    purpose: str
    resolved_destinations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.scheme not in {"http", "https"}:
            raise ValueError("NetworkRule.scheme must be http or https")
        _require_host(self.host, "NetworkRule.host")
        if self.host != self.host.casefold():
            raise ValueError("NetworkRule.host must be lowercase")
        _require_port(self.port, "NetworkRule.port")
        _require_text(self.purpose, "NetworkRule.purpose")
        if type(self.resolved_destinations) is not tuple or not self.resolved_destinations:
            raise ValueError("NetworkRule.resolved_destinations must be non-empty")
        for item in self.resolved_destinations:
            _require_host(item, "NetworkRule.resolved_destinations")
            if item != item.casefold():
                raise ValueError("NetworkRule.resolved_destinations must be lowercase")
        if len(set(self.resolved_destinations)) != len(self.resolved_destinations):
            raise ValueError("NetworkRule.resolved_destinations must be unique")


@dataclass(frozen=True, slots=True, kw_only=True)
class NetworkPolicy:
    rules: tuple[NetworkRule, ...] = ()

    def __post_init__(self) -> None:
        if type(self.rules) is not tuple or any(
            type(rule) is not NetworkRule for rule in self.rules
        ):
            raise TypeError("NetworkPolicy.rules must contain NetworkRule values")
        identities = tuple((rule.scheme, rule.host, rule.port, rule.purpose) for rule in self.rules)
        if len(set(identities)) != len(identities):
            raise ValueError("NetworkPolicy.rules must have unique scopes")


@dataclass(frozen=True, slots=True, kw_only=True)
class NetworkRequest:
    url: str
    purpose: str
    resolved_destination: str
    resolved_port: int
    redirect_url: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.url, "NetworkRequest.url")
        _require_text(self.purpose, "NetworkRequest.purpose")
        _require_host(self.resolved_destination, "NetworkRequest.resolved_destination")
        if self.resolved_destination != self.resolved_destination.casefold():
            raise ValueError("NetworkRequest.resolved_destination must be lowercase")
        _require_port(self.resolved_port, "NetworkRequest.resolved_port")
        if self.redirect_url is not None:
            _require_text(self.redirect_url, "NetworkRequest.redirect_url")


@dataclass(frozen=True, slots=True, kw_only=True)
class RedactionResult:
    value: object
    status: RedactionStatus

    def __post_init__(self) -> None:
        if type(self.status) is not RedactionStatus:
            raise TypeError("RedactionResult.status must be RedactionStatus")


def filter_environment(
    policy: CommandPolicy, environment: Mapping[object, object]
) -> EnvironmentFilter:
    """Return only explicitly allowlisted non-credential keys from passed data."""

    if type(policy) is not CommandPolicy:
        raise TypeError("policy must be CommandPolicy")
    if not isinstance(environment, Mapping):
        raise TypeError("environment must be an explicitly passed mapping")
    allowed = set(policy.allowed_environment_keys)
    retained: list[tuple[str, str]] = []
    dropped: list[str] = []
    for raw_key, raw_value in environment.items():
        if type(raw_key) is not str or type(raw_value) is not str:
            raise TypeError("environment keys and values must be strings")
        if _ENVIRONMENT_KEY.fullmatch(raw_key) is None:
            raise ValueError("environment keys must be normalized uppercase identifiers")
        if raw_key not in allowed:
            dropped.append(raw_key)
            continue
        if "\x00" in raw_value or len(raw_value) > _MAX_ENVIRONMENT_VALUE:
            raise ValueError("environment values must be bounded and NUL-free")
        if _contains_secret(raw_value):
            raise ValueError("environment values must not contain inline credentials")
        retained.append((raw_key, raw_value))
    retained.sort()
    dropped.sort()
    return EnvironmentFilter(values=tuple(retained), dropped_keys=tuple(dropped))


def evaluate_command(
    policy: object,
    request: object,
    *,
    environment: Mapping[object, object],
) -> tuple[PermissionDecision, EnvironmentFilter]:
    """Evaluate one exact argv request without invoking a shell or process."""

    empty_environment = EnvironmentFilter(values=(), dropped_keys=())
    if type(policy) is not CommandPolicy or type(request) is not CommandRequest:
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN,
                reason="command policy or request is malformed",
            ),
            empty_environment,
        )
    try:
        filtered = filter_environment(policy, environment)
    except (TypeError, ValueError):
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN,
                reason="command environment is malformed",
            ),
            empty_environment,
        )
    if _path_key(request.cwd) != _path_key(policy.workspace.workspace):
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN,
                reason="command cwd is not the exact assigned workspace",
            ),
            filtered,
        )
    if request.observed_reparse_components:
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN,
                reason="command cwd contains an observed reparse component",
            ),
            filtered,
        )
    if request.observed_workspace_identity != policy.workspace.workspace_identity:
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN,
                reason="command cwd filesystem identity changed after assignment",
            ),
            filtered,
        )
    if request.timeout_seconds > policy.maximum_timeout_seconds:
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN, reason="command timeout exceeds policy"
            ),
            filtered,
        )
    if request.output_limit_bytes > policy.maximum_output_bytes:
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN,
                reason="command output limit exceeds policy",
            ),
            filtered,
        )
    matching = [
        rule for rule in policy.rules if rule.executable.casefold() == request.executable.casefold()
    ]
    if len(matching) != 1:
        return (
            PermissionDecision(decision=Decision.FORBIDDEN, reason="executable is not allowlisted"),
            filtered,
        )
    rule = matching[0]
    executable_name = PureWindowsPath(request.executable).name.casefold()
    if (
        executable_name in _INTERPRETERS or _INTERPRETER_NAME.fullmatch(executable_name) is not None
    ) and not rule.allow_interpreter:
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN,
                reason="arbitrary interpreter execution is not permitted",
            ),
            filtered,
        )
    if request.arguments not in rule.argument_vectors:
        return (
            PermissionDecision(
                decision=Decision.FORBIDDEN,
                reason="argument vector is not exactly allowlisted",
            ),
            filtered,
        )
    return (
        PermissionDecision(
            decision=Decision.ALLOWED,
            reason="structured command matches the exact host rule",
            normalized_target=request.executable,
        ),
        filtered,
    )


def evaluate_path(policy: object, request: object) -> PermissionDecision:
    """Make a lexical/read-only child-path decision anchored to a C-405 assignment."""

    if type(policy) is not PathPolicy or type(request) is not PathRequest:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="path policy or request is malformed",
        )
    try:
        request_workspace_key = _path_key(request.workspace)
        policy_workspace_key = _path_key(policy.workspace.workspace)
    except (TypeError, ValueError) as exc:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason=f"path workspace is malformed: {exc}",
        )
    if request_workspace_key != policy_workspace_key:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="path workspace is not the exact C-405 assignment",
        )
    if request.observed_workspace_identity != policy.workspace.workspace_identity:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="path workspace filesystem identity changed after assignment",
        )
    if request.operation is PathOperation.CLEANUP:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="cleanup requires WorkspaceManager target revalidation and separate approval",
        )
    if request.observed_reparse_components:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="path contains an observed symlink, junction, or reparse component",
        )
    try:
        parts = _safe_relative_windows_path(request.relative_path)
    except (TypeError, ValueError) as exc:
        return PermissionDecision(decision=Decision.FORBIDDEN, reason=f"unsafe path: {exc}")
    target = policy.workspace.workspace.joinpath(*parts)
    if not _path_key(target).startswith(f"{policy_workspace_key}\\"):
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="path does not remain within the assigned workspace",
        )
    return PermissionDecision(
        decision=Decision.ALLOWED,
        reason="path is an exact lexical child of the assigned workspace",
        normalized_target=str(target),
    )


def evaluate_network(policy: object, request: object) -> PermissionDecision:
    """Allow one exact documented destination; DNS and redirects are caller supplied."""

    if type(policy) is not NetworkPolicy or type(request) is not NetworkRequest:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="network policy or request is malformed",
        )
    if request.redirect_url is not None:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="redirects are denied; submit the final destination for a new decision",
        )
    try:
        parsed = urlsplit(request.url)
        port = parsed.port
    except ValueError:
        return PermissionDecision(decision=Decision.FORBIDDEN, reason="network URL is malformed")
    if not parsed.scheme or not parsed.netloc or parsed.hostname is None:
        return PermissionDecision(decision=Decision.FORBIDDEN, reason="network URL is not absolute")
    if "\\" in request.url or any(ord(character) < 32 for character in request.url):
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="network URL contains an unsafe separator or control character",
        )
    if parsed.username is not None or parsed.password is not None:
        return PermissionDecision(
            decision=Decision.FORBIDDEN, reason="network URL contains userinfo"
        )
    if parsed.fragment:
        return PermissionDecision(
            decision=Decision.FORBIDDEN, reason="network URL contains a fragment"
        )
    if _contains_secret(request.url):
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="network URL contains inline credential material",
        )
    effective_port = port
    if effective_port is None:
        effective_port = {"http": 80, "https": 443}.get(parsed.scheme.casefold())
    matches = [
        rule
        for rule in policy.rules
        if rule.scheme == parsed.scheme.casefold()
        and rule.host == parsed.hostname.casefold()
        and rule.port == effective_port
        and rule.purpose == request.purpose
    ]
    if len(matches) != 1:
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="network scheme, host, port, or purpose is not allowlisted",
        )
    rule = matches[0]
    if request.resolved_port != rule.port or request.resolved_destination not in set(
        rule.resolved_destinations
    ):
        return PermissionDecision(
            decision=Decision.FORBIDDEN,
            reason="resolved network destination drifted from policy",
        )
    return PermissionDecision(
        decision=Decision.ALLOWED,
        reason="network request matches the exact documented destination and purpose",
        normalized_target=f"{rule.scheme}://{rule.host}:{rule.port}",
    )


def redact_payload(payload: object) -> RedactionResult:
    """Recursively redact secret/PII carriers before persistence or model transfer."""

    value, changed = _redact(payload, sensitive_context=False, depth=0, active=set())
    return RedactionResult(
        value=value,
        status=RedactionStatus.REDACTED if changed else RedactionStatus.NOT_REQUIRED,
    )


def _redact(
    value: object,
    *,
    sensitive_context: bool,
    depth: int,
    active: set[int],
) -> tuple[object, bool]:
    if sensitive_context:
        return "<REDACTED:SECRET>", True
    if depth > 32:
        return "<REDACTED:MAX_DEPTH>", True
    if value is None or type(value) in (bool, int, float):
        return value, False
    if type(value) is str:
        return _redact_text(value)
    if type(value) is bytes:
        return b"<REDACTED:BYTES>", True
    if isinstance(value, BaseException):
        message, changed = _redact_text(str(value))
        return {"error_type": type(value).__name__, "message": message}, changed
    if isinstance(value, Mapping):
        identity = id(value)
        if identity in active:
            return "<REDACTED:CYCLE>", True
        if any(type(key) is not str for key in value):
            return "<REDACTED:UNSUPPORTED_MAPPING>", True
        active.add(identity)
        result: dict[str, object] = {}
        changed = False
        try:
            for index, (key, item) in enumerate(value.items()):
                assert type(key) is str
                redacted_key, key_changed = _redact_text(key)
                output_key = f"<REDACTED:KEY:{index}>" if key_changed else redacted_key
                redacted, item_changed = _redact(
                    item,
                    sensitive_context=_SENSITIVE_KEY.search(key) is not None,
                    depth=depth + 1,
                    active=active,
                )
                result[output_key] = redacted
                changed = changed or key_changed or item_changed
        finally:
            active.remove(identity)
        return result, changed
    if type(value) is tuple:
        identity = id(value)
        if identity in active:
            return "<REDACTED:CYCLE>", True
        active.add(identity)
        try:
            items = tuple(
                _redact(
                    item,
                    sensitive_context=False,
                    depth=depth + 1,
                    active=active,
                )
                for item in value
            )
        finally:
            active.remove(identity)
        return tuple(item for item, _ in items), any(changed for _, changed in items)
    if type(value) is list:
        identity = id(value)
        if identity in active:
            return "<REDACTED:CYCLE>", True
        active.add(identity)
        try:
            items = tuple(
                _redact(
                    item,
                    sensitive_context=False,
                    depth=depth + 1,
                    active=active,
                )
                for item in value
            )
        finally:
            active.remove(identity)
        return [item for item, _ in items], any(changed for _, changed in items)
    if isinstance(value, Sequence):
        return "<REDACTED:UNSUPPORTED_SEQUENCE>", True
    return f"<REDACTED:UNSUPPORTED_TYPE:{type(value).__name__}>", True


def _redact_text(value: str) -> tuple[str, bool]:
    redacted = value
    redacted = _URL_USERINFO.sub(r"\1<REDACTED:USERINFO>@", redacted)
    redacted = _BEARER.sub("Bearer <REDACTED:SECRET>", redacted)
    redacted = _SECRET_ASSIGNMENT.sub(r"\1\2<REDACTED:SECRET>", redacted)
    redacted = _TOKEN.sub("<REDACTED:SECRET>", redacted)
    redacted = _JWT.sub("<REDACTED:SECRET>", redacted)
    redacted = _PRIVATE_KEY.sub("<REDACTED:SECRET>", redacted)
    redacted = _SECRET_CANARY.sub("<REDACTED:SECRET>", redacted)
    redacted = _EMAIL.sub("<REDACTED:EMAIL>", redacted)
    redacted = _PHONE.sub("<REDACTED:PHONE>", redacted)
    return redacted, redacted != value


def _require_text(value: object, location: str) -> None:
    if type(value) is not str:
        raise TypeError(f"{location} must be a string")
    if not value or value != value.strip() or "\x00" in value or len(value) > 8192:
        raise ValueError(f"{location} must be normalized non-empty NUL-free text")


def _require_arguments(value: object, location: str) -> None:
    if type(value) is not tuple:
        raise TypeError(f"{location} must be a tuple")
    if len(value) > _MAX_ARGUMENTS:
        raise ValueError(f"{location} contains too many arguments")
    for argument in value:
        if type(argument) is not str or "\x00" in argument or len(argument) > _MAX_ARGUMENT_LENGTH:
            raise TypeError(f"{location} must contain NUL-free strings")
        if _SHELL_COMPOSITION.search(argument) or _VARIABLE_EXPANSION.search(argument):
            raise ValueError(f"{location} contains shell composition or variable expansion")
        if _contains_secret(argument):
            raise ValueError(f"{location} contains inline credential material")


def _require_environment_keys(keys: object) -> None:
    if type(keys) is not tuple:
        raise TypeError("CommandPolicy.allowed_environment_keys must be a tuple")
    for key in keys:
        if type(key) is not str or _ENVIRONMENT_KEY.fullmatch(key) is None:
            raise ValueError("allowed environment keys must be uppercase identifiers")
        if _SENSITIVE_KEY.search(key):
            raise ValueError("credential-like environment keys cannot be broadly inherited")
    if len(set(keys)) != len(keys):
        raise ValueError("allowed environment keys must be unique")


def _safe_absolute_windows_path(value: object, location: str) -> PureWindowsPath:
    if type(value) is not str or not value or "\x00" in value:
        raise ValueError(f"{location} must be a non-empty NUL-free string")
    normalized = value.replace("/", "\\")
    lowered = normalized.casefold()
    if lowered.startswith(("\\\\?\\", "\\\\.\\", "\\??\\")):
        raise ValueError(f"{location} uses a device namespace")
    pure = PureWindowsPath(normalized)
    if not pure.is_absolute() or not re.fullmatch(r"[A-Za-z]:", pure.drive):
        raise ValueError(f"{location} must be an absolute drive-local Windows path")
    if any(character in value for character in "*?[]"):
        raise ValueError(f"{location} contains glob syntax")
    if "%" in value or "$" in value or ":" in normalized[2:]:
        raise ValueError(f"{location} contains expansion or alternate data stream syntax")
    _validate_path_parts(tuple(pure.parts[1:]), location)
    return pure


def _safe_relative_windows_path(value: str) -> tuple[str, ...]:
    if not value or "\x00" in value:
        raise ValueError("relative path must be non-empty and NUL-free")
    normalized = value.replace("/", "\\")
    if normalized.casefold().startswith(("\\\\?\\", "\\\\.\\", "\\??\\")):
        raise ValueError("device namespace")
    pure = PureWindowsPath(normalized)
    if pure.is_absolute() or pure.drive or normalized.startswith("\\"):
        raise ValueError("absolute or UNC path")
    if any(character in value for character in "*?[]"):
        raise ValueError("glob syntax")
    if "%" in value or "$" in value or ":" in normalized:
        raise ValueError("expansion or alternate data stream syntax")
    parts = tuple(part for part in pure.parts if part)
    _validate_path_parts(parts, "relative path")
    if not parts or parts == (".",):
        raise ValueError("path must identify a child")
    return parts


def _validate_path_parts(parts: tuple[str, ...], location: str) -> None:
    for part in parts:
        if part in {".", ".."}:
            raise ValueError(f"{location} contains traversal")
        if part.endswith((" ", ".")):
            raise ValueError(f"{location} contains trailing dot or space")
        if part.split(".", maxsplit=1)[0].upper() in _RESERVED_NAMES:
            raise ValueError(f"{location} contains a reserved device name")


def _path_key(path: Path) -> str:
    return str(_safe_absolute_windows_path(str(path), "path")).casefold().rstrip("\\")


def _require_host(value: object, location: str) -> None:
    if type(value) is not str or _HOST.fullmatch(value) is None:
        raise ValueError(f"{location} must be a normalized hostname or address")
    labels = value.split(".")
    if all(label.isdigit() for label in labels):
        try:
            ip_address(value)
        except ValueError as exc:
            raise ValueError(f"{location} must be a valid IP address") from exc
        return
    label_pattern = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\Z")
    if any(label_pattern.fullmatch(label) is None for label in labels):
        raise ValueError(f"{location} must be a normalized hostname or address")


def _require_port(value: object, location: str) -> None:
    if type(value) is not int or not 1 <= value <= 65535:
        raise ValueError(f"{location} must be an integer port")


def _contains_secret(value: str) -> bool:
    return any(
        pattern.search(value) is not None
        for pattern in (
            _URL_USERINFO,
            _SECRET_ASSIGNMENT,
            _BEARER,
            _TOKEN,
            _JWT,
            _PRIVATE_KEY,
            _SECRET_CANARY,
        )
    )


__all__ = [
    "CommandPolicy",
    "CommandRequest",
    "CommandRule",
    "EnvironmentFilter",
    "NetworkPolicy",
    "NetworkRequest",
    "NetworkRule",
    "PathOperation",
    "PathPolicy",
    "PathRequest",
    "PermissionDecision",
    "RedactionResult",
    "evaluate_command",
    "evaluate_network",
    "evaluate_path",
    "filter_environment",
    "redact_payload",
]
