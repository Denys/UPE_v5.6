"""Immutable, dependency-free configuration contracts for the trusted host."""

from __future__ import annotations

import math
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import PureWindowsPath
from typing import Self, cast

__all__ = [
    "HarnessConfig",
    "HarnessPaths",
    "ProviderSettings",
    "HostLimits",
    "RetrySettings",
    "ValidationSettings",
    "PolicySettings",
    "ProviderAdapter",
    "InvalidConfigError",
]

_SCHEMA_VERSION = "1.0.0"
_MAX_PROVIDER_STRING_LENGTH = 256
_MAX_HOST_LENGTH = 253
_MAX_WINDOWS_PATH_LENGTH = 32_767
_WINDOWS_ABSOLUTE_PREFIX = re.compile(r"^[A-Za-z]:[\\/]")
_WINDOWS_SEPARATORS = re.compile(r"[\\/]")
_HOST_TOKEN = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)"
    r"(?:\.(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?))*$"
)
_RESERVED_WINDOWS_NAMES = {
    "aux",
    "con",
    "conin$",
    "conout$",
    "nul",
    "prn",
    *(f"com{index}" for index in range(1, 10)),
    *(f"lpt{index}" for index in range(1, 10)),
}


class InvalidConfigError(ValueError):
    """Raised when a configuration value violates the public contract."""


class ProviderAdapter(StrEnum):
    """Provider adapters supported by the v0 configuration surface."""

    FAKE = "fake"
    CODEX_APP_SERVER = "codex_app_server"


def _format_keys(keys: set[object]) -> str:
    return ", ".join(sorted(repr(key) for key in keys))


def _strict_mapping(
    value: object,
    *,
    location: str,
    expected_keys: frozenset[str],
) -> Mapping[object, object]:
    if not isinstance(value, Mapping):
        raise InvalidConfigError(f"{location} must be an object mapping")

    actual_keys = set(value.keys())
    missing = expected_keys - actual_keys
    unexpected = actual_keys - expected_keys
    if missing or unexpected:
        details: list[str] = []
        if missing:
            details.append(f"missing keys: {_format_keys(set(missing))}")
        if unexpected:
            details.append(f"unexpected keys: {_format_keys(unexpected)}")
        raise InvalidConfigError(f"{location} has {'; '.join(details)}")
    return value


def _strict_list(value: object, *, location: str) -> list[object]:
    if type(value) is not list:
        raise InvalidConfigError(f"{location} must be an array")
    return value


def _strict_string(value: object, *, location: str) -> str:
    if type(value) is not str:
        raise InvalidConfigError(f"{location} must be a string")
    return value


def _nonempty_string(value: object, *, location: str, maximum: int) -> str:
    result = _strict_string(value, location=location)
    if not result.strip():
        raise InvalidConfigError(f"{location} must not be empty or whitespace-only")
    if len(result) > maximum:
        raise InvalidConfigError(f"{location} must contain at most {maximum} characters")
    return result


def _optional_nonempty_string(value: object, *, location: str) -> str | None:
    if value is None:
        return None
    return _nonempty_string(value, location=location, maximum=_MAX_PROVIDER_STRING_LENGTH)


def _strict_bool(value: object, *, location: str) -> bool:
    if type(value) is not bool:
        raise InvalidConfigError(f"{location} must be a boolean")
    return value


def _strict_int(
    value: object,
    *,
    location: str,
    minimum: int,
) -> int:
    if type(value) is not int:
        raise InvalidConfigError(f"{location} must be an integer (booleans are not integers)")
    if value < minimum:
        raise InvalidConfigError(f"{location} must be at least {minimum}")
    return value


def _optional_nonnegative_int(value: object, *, location: str) -> int | None:
    if value is None:
        return None
    return _strict_int(value, location=location, minimum=0)


def _finite_number(
    value: object,
    *,
    location: str,
    minimum: float,
    maximum: float | None = None,
) -> float:
    if type(value) not in (int, float):
        raise InvalidConfigError(f"{location} must be a finite number (booleans are not numbers)")
    numeric = cast(int | float, value)
    result = float(numeric)
    if not math.isfinite(result):
        raise InvalidConfigError(f"{location} must be finite")
    if result < minimum:
        raise InvalidConfigError(f"{location} must be at least {minimum:g}")
    if maximum is not None and result > maximum:
        raise InvalidConfigError(f"{location} must be at most {maximum:g}")
    return result


def _optional_nonnegative_number(value: object, *, location: str) -> int | float | None:
    if value is None:
        return None
    _finite_number(value, location=location, minimum=0.0)
    # Preserve an integer as an integer so materialized mappings remain lossless.
    return cast(int | float, value)


def _windows_path(value: str | os.PathLike[str], *, location: str) -> PureWindowsPath:
    try:
        raw_value = os.fspath(value)
    except TypeError as exc:
        raise InvalidConfigError(f"{location} must be a string or path value") from exc
    if type(raw_value) is not str:
        raise InvalidConfigError(f"{location} must resolve to a string path")

    if not raw_value or not raw_value.strip():
        raise InvalidConfigError(f"{location} must not be empty")
    if raw_value != raw_value.strip():
        raise InvalidConfigError(f"{location} must not have leading or trailing whitespace")
    if len(raw_value) > _MAX_WINDOWS_PATH_LENGTH:
        raise InvalidConfigError(
            f"{location} must contain at most {_MAX_WINDOWS_PATH_LENGTH} characters"
        )

    folded = raw_value.casefold()
    if raw_value.startswith(("\\\\", "//")):
        raise InvalidConfigError(f"{location} must not use a UNC or device namespace")
    if folded.startswith(("\\?\\", "\\.\\", "\\??\\", "/?/", "/./", "/??/")):
        raise InvalidConfigError(f"{location} must not use a device namespace")
    if _WINDOWS_ABSOLUTE_PREFIX.match(raw_value) is None:
        raise InvalidConfigError(
            f"{location} must be an absolute Windows drive path such as C:\\path"
        )

    remainder = raw_value[3:]
    if ":" in remainder:
        raise InvalidConfigError(f"{location} must not contain an alternate data stream")
    if any(character in raw_value for character in "%$~*?[]{}"):
        raise InvalidConfigError(
            f"{location} must not contain environment expansion or glob syntax"
        )
    if any(character in raw_value for character in '<>"|') or any(
        ord(character) < 32 for character in raw_value
    ):
        raise InvalidConfigError(f"{location} contains a character invalid in Windows paths")

    segments = [segment for segment in _WINDOWS_SEPARATORS.split(remainder) if segment]
    for segment in segments:
        if segment in {".", ".."}:
            raise InvalidConfigError(f"{location} must not contain traversal segments")
        if segment.endswith((" ", ".")):
            raise InvalidConfigError(
                f"{location} must not contain segments ending in a space or period"
            )
        device_stem = segment.split(".", 1)[0].casefold()
        if device_stem in _RESERVED_WINDOWS_NAMES:
            raise InvalidConfigError(f"{location} must not contain a reserved device name")

    result = PureWindowsPath(raw_value)
    if not result.is_absolute() or not result.drive or result.root not in {"\\", "/"}:
        raise InvalidConfigError(f"{location} must be an absolute Windows drive path")
    return result


def _validate_distinct_roots(paths: Mapping[str, PureWindowsPath]) -> None:
    items = tuple(paths.items())
    for index, (left_name, left_path) in enumerate(items):
        for right_name, right_path in items[index + 1 :]:
            if (
                left_path == right_path
                or left_path in right_path.parents
                or right_path in left_path.parents
            ):
                raise InvalidConfigError(
                    f"paths.{left_name} and paths.{right_name} must not overlap or nest"
                )


@dataclass(frozen=True, slots=True, kw_only=True)
class HarnessPaths:
    """Lexically validated, mutually isolated Windows roots."""

    repository_root: PureWindowsPath
    worktree_root: PureWindowsPath
    host_state_root: PureWindowsPath

    def __post_init__(self) -> None:
        repository = _windows_path(self.repository_root, location="paths.repository_root")
        worktree = _windows_path(self.worktree_root, location="paths.worktree_root")
        host_state = _windows_path(self.host_state_root, location="paths.host_state_root")
        _validate_distinct_roots(
            {
                "repository_root": repository,
                "worktree_root": worktree,
                "host_state_root": host_state,
            }
        )
        object.__setattr__(self, "repository_root", repository)
        object.__setattr__(self, "worktree_root", worktree)
        object.__setattr__(self, "host_state_root", host_state)

    @property
    def database_path(self) -> PureWindowsPath:
        return self.host_state_root / "harness.sqlite3"

    @property
    def events_path(self) -> PureWindowsPath:
        return self.host_state_root / "events"

    @property
    def checkpoints_path(self) -> PureWindowsPath:
        return self.host_state_root / "checkpoints"

    @property
    def artifacts_path(self) -> PureWindowsPath:
        return self.host_state_root / "artifacts"

    def to_dict(self) -> dict[str, object]:
        return {
            "repository_root": str(self.repository_root),
            "worktree_root": str(self.worktree_root),
            "host_state_root": str(self.host_state_root),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> Self:
        data = _strict_mapping(
            value,
            location="paths",
            expected_keys=frozenset({"repository_root", "worktree_root", "host_state_root"}),
        )
        return cls(
            repository_root=_windows_path(
                _strict_string(data["repository_root"], location="paths.repository_root"),
                location="paths.repository_root",
            ),
            worktree_root=_windows_path(
                _strict_string(data["worktree_root"], location="paths.worktree_root"),
                location="paths.worktree_root",
            ),
            host_state_root=_windows_path(
                _strict_string(data["host_state_root"], location="paths.host_state_root"),
                location="paths.host_state_root",
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderSettings:
    """Provider selection without credentials or provider protocol details."""

    adapter: ProviderAdapter = ProviderAdapter.FAKE
    model: str | None = None
    reasoning_effort: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.adapter, ProviderAdapter):
            raise InvalidConfigError("provider.adapter must be a ProviderAdapter value")
        _optional_nonempty_string(self.model, location="provider.model")
        _optional_nonempty_string(
            self.reasoning_effort,
            location="provider.reasoning_effort",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "adapter": self.adapter.value,
            "model": self.model,
            "reasoning_effort": self.reasoning_effort,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> Self:
        data = _strict_mapping(
            value,
            location="provider",
            expected_keys=frozenset({"adapter", "model", "reasoning_effort"}),
        )
        raw_adapter = _strict_string(data["adapter"], location="provider.adapter")
        try:
            adapter = ProviderAdapter(raw_adapter)
        except ValueError as exc:
            allowed = ", ".join(repr(item.value) for item in ProviderAdapter)
            raise InvalidConfigError(f"provider.adapter must be one of: {allowed}") from exc
        return cls(
            adapter=adapter,
            model=_optional_nonempty_string(data["model"], location="provider.model"),
            reasoning_effort=_optional_nonempty_string(
                data["reasoning_effort"],
                location="provider.reasoning_effort",
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class HostLimits:
    """Hard host-enforced iteration, time, token, cost, and action limits."""

    max_iterations: int
    max_elapsed_seconds: int
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    max_total_tokens: int | None = None
    max_cost: int | float | None = None
    max_external_actions: int = 0

    def __post_init__(self) -> None:
        _strict_int(self.max_iterations, location="limits.max_iterations", minimum=1)
        _strict_int(
            self.max_elapsed_seconds,
            location="limits.max_elapsed_seconds",
            minimum=1,
        )
        _optional_nonnegative_int(
            self.max_input_tokens,
            location="limits.max_input_tokens",
        )
        _optional_nonnegative_int(
            self.max_output_tokens,
            location="limits.max_output_tokens",
        )
        _optional_nonnegative_int(
            self.max_total_tokens,
            location="limits.max_total_tokens",
        )
        _optional_nonnegative_number(self.max_cost, location="limits.max_cost")
        _strict_int(
            self.max_external_actions,
            location="limits.max_external_actions",
            minimum=0,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "max_iterations": self.max_iterations,
            "max_elapsed_seconds": self.max_elapsed_seconds,
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "max_total_tokens": self.max_total_tokens,
            "max_cost": self.max_cost,
            "max_external_actions": self.max_external_actions,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> Self:
        data = _strict_mapping(
            value,
            location="limits",
            expected_keys=frozenset(
                {
                    "max_iterations",
                    "max_elapsed_seconds",
                    "max_input_tokens",
                    "max_output_tokens",
                    "max_total_tokens",
                    "max_cost",
                    "max_external_actions",
                }
            ),
        )
        return cls(
            max_iterations=_strict_int(
                data["max_iterations"],
                location="limits.max_iterations",
                minimum=1,
            ),
            max_elapsed_seconds=_strict_int(
                data["max_elapsed_seconds"],
                location="limits.max_elapsed_seconds",
                minimum=1,
            ),
            max_input_tokens=_optional_nonnegative_int(
                data["max_input_tokens"],
                location="limits.max_input_tokens",
            ),
            max_output_tokens=_optional_nonnegative_int(
                data["max_output_tokens"],
                location="limits.max_output_tokens",
            ),
            max_total_tokens=_optional_nonnegative_int(
                data["max_total_tokens"],
                location="limits.max_total_tokens",
            ),
            max_cost=_optional_nonnegative_number(
                data["max_cost"],
                location="limits.max_cost",
            ),
            max_external_actions=_strict_int(
                data["max_external_actions"],
                location="limits.max_external_actions",
                minimum=0,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class RetrySettings:
    """Finite retry, repeated-failure, no-progress, and backoff settings."""

    max_transient_retries: int
    identical_failure_limit: int
    no_progress_iteration_limit: int
    initial_backoff_seconds: float
    maximum_backoff_seconds: float
    backoff_multiplier: float
    jitter_ratio: float

    def __post_init__(self) -> None:
        _strict_int(
            self.max_transient_retries,
            location="retry.max_transient_retries",
            minimum=0,
        )
        _strict_int(
            self.identical_failure_limit,
            location="retry.identical_failure_limit",
            minimum=1,
        )
        _strict_int(
            self.no_progress_iteration_limit,
            location="retry.no_progress_iteration_limit",
            minimum=1,
        )
        initial = _finite_number(
            self.initial_backoff_seconds,
            location="retry.initial_backoff_seconds",
            minimum=0.0,
        )
        if initial == 0:
            raise InvalidConfigError("retry.initial_backoff_seconds must be greater than 0")
        maximum = _finite_number(
            self.maximum_backoff_seconds,
            location="retry.maximum_backoff_seconds",
            minimum=initial,
        )
        multiplier = _finite_number(
            self.backoff_multiplier,
            location="retry.backoff_multiplier",
            minimum=1.0,
        )
        jitter = _finite_number(
            self.jitter_ratio,
            location="retry.jitter_ratio",
            minimum=0.0,
            maximum=1.0,
        )
        object.__setattr__(self, "initial_backoff_seconds", initial)
        object.__setattr__(self, "maximum_backoff_seconds", maximum)
        object.__setattr__(self, "backoff_multiplier", multiplier)
        object.__setattr__(self, "jitter_ratio", jitter)

    def to_dict(self) -> dict[str, object]:
        return {
            "max_transient_retries": self.max_transient_retries,
            "identical_failure_limit": self.identical_failure_limit,
            "no_progress_iteration_limit": self.no_progress_iteration_limit,
            "initial_backoff_seconds": self.initial_backoff_seconds,
            "maximum_backoff_seconds": self.maximum_backoff_seconds,
            "backoff_multiplier": self.backoff_multiplier,
            "jitter_ratio": self.jitter_ratio,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> Self:
        data = _strict_mapping(
            value,
            location="retry",
            expected_keys=frozenset(
                {
                    "max_transient_retries",
                    "identical_failure_limit",
                    "no_progress_iteration_limit",
                    "initial_backoff_seconds",
                    "maximum_backoff_seconds",
                    "backoff_multiplier",
                    "jitter_ratio",
                }
            ),
        )
        return cls(
            max_transient_retries=_strict_int(
                data["max_transient_retries"],
                location="retry.max_transient_retries",
                minimum=0,
            ),
            identical_failure_limit=_strict_int(
                data["identical_failure_limit"],
                location="retry.identical_failure_limit",
                minimum=1,
            ),
            no_progress_iteration_limit=_strict_int(
                data["no_progress_iteration_limit"],
                location="retry.no_progress_iteration_limit",
                minimum=1,
            ),
            initial_backoff_seconds=_finite_number(
                data["initial_backoff_seconds"],
                location="retry.initial_backoff_seconds",
                minimum=0.0,
            ),
            maximum_backoff_seconds=_finite_number(
                data["maximum_backoff_seconds"],
                location="retry.maximum_backoff_seconds",
                minimum=0.0,
            ),
            backoff_multiplier=_finite_number(
                data["backoff_multiplier"],
                location="retry.backoff_multiplier",
                minimum=1.0,
            ),
            jitter_ratio=_finite_number(
                data["jitter_ratio"],
                location="retry.jitter_ratio",
                minimum=0.0,
                maximum=1.0,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ValidationSettings:
    """Bounds applied to deterministic validator processes and captured output."""

    default_timeout_seconds: float
    max_output_bytes: int

    def __post_init__(self) -> None:
        timeout = _finite_number(
            self.default_timeout_seconds,
            location="validation.default_timeout_seconds",
            minimum=0.0,
        )
        if timeout == 0:
            raise InvalidConfigError("validation.default_timeout_seconds must be greater than 0")
        _strict_int(
            self.max_output_bytes,
            location="validation.max_output_bytes",
            minimum=1,
        )
        object.__setattr__(self, "default_timeout_seconds", timeout)

    def to_dict(self) -> dict[str, object]:
        return {
            "default_timeout_seconds": self.default_timeout_seconds,
            "max_output_bytes": self.max_output_bytes,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> Self:
        data = _strict_mapping(
            value,
            location="validation",
            expected_keys=frozenset({"default_timeout_seconds", "max_output_bytes"}),
        )
        return cls(
            default_timeout_seconds=_finite_number(
                data["default_timeout_seconds"],
                location="validation.default_timeout_seconds",
                minimum=0.0,
            ),
            max_output_bytes=_strict_int(
                data["max_output_bytes"],
                location="validation.max_output_bytes",
                minimum=1,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class PolicySettings:
    """Fail-closed external capability policy without secret values."""

    network_enabled: bool = False
    allowed_hosts: tuple[str, ...] = ()
    docker_enabled: bool = False

    def __post_init__(self) -> None:
        _strict_bool(self.network_enabled, location="policy.network_enabled")
        _strict_bool(self.docker_enabled, location="policy.docker_enabled")
        if type(self.allowed_hosts) is not tuple:
            raise InvalidConfigError("policy.allowed_hosts must be an immutable tuple")

        seen: set[str] = set()
        normalized_hosts: list[str] = []
        for index, host in enumerate(self.allowed_hosts):
            location = f"policy.allowed_hosts[{index}]"
            checked = _nonempty_string(host, location=location, maximum=_MAX_HOST_LENGTH)
            normalized = checked.casefold()
            if checked != normalized:
                raise InvalidConfigError(f"{location} must already be normalized lowercase ASCII")
            if _HOST_TOKEN.fullmatch(checked) is None:
                raise InvalidConfigError(
                    f"{location} must be an explicit hostname without URL, credentials, "
                    "port, path, or wildcard syntax"
                )
            if normalized in seen:
                raise InvalidConfigError(
                    "policy.allowed_hosts must not contain case-insensitive duplicates"
                )
            seen.add(normalized)
            normalized_hosts.append(normalized)

        if not self.network_enabled and normalized_hosts:
            raise InvalidConfigError(
                "policy.allowed_hosts must be empty when policy.network_enabled is false"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "network_enabled": self.network_enabled,
            "allowed_hosts": list(self.allowed_hosts),
            "docker_enabled": self.docker_enabled,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> Self:
        data = _strict_mapping(
            value,
            location="policy",
            expected_keys=frozenset({"network_enabled", "allowed_hosts", "docker_enabled"}),
        )
        raw_hosts = _strict_list(data["allowed_hosts"], location="policy.allowed_hosts")
        hosts = tuple(
            _nonempty_string(
                host,
                location=f"policy.allowed_hosts[{index}]",
                maximum=_MAX_HOST_LENGTH,
            )
            for index, host in enumerate(raw_hosts)
        )
        return cls(
            network_enabled=_strict_bool(
                data["network_enabled"],
                location="policy.network_enabled",
            ),
            allowed_hosts=hosts,
            docker_enabled=_strict_bool(
                data["docker_enabled"],
                location="policy.docker_enabled",
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class HarnessConfig:
    """Fully materialized v1 trusted-host configuration."""

    paths: HarnessPaths
    limits: HostLimits
    retry: RetrySettings
    validation: ValidationSettings
    schema_version: str = _SCHEMA_VERSION
    provider: ProviderSettings = field(default_factory=ProviderSettings)
    policy: PolicySettings = field(default_factory=PolicySettings)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not str or self.schema_version != _SCHEMA_VERSION:
            raise InvalidConfigError(f"schema_version must equal {_SCHEMA_VERSION!r}")
        if not isinstance(self.paths, HarnessPaths):
            raise InvalidConfigError("paths must be a HarnessPaths value")
        if not isinstance(self.provider, ProviderSettings):
            raise InvalidConfigError("provider must be a ProviderSettings value")
        if not isinstance(self.limits, HostLimits):
            raise InvalidConfigError("limits must be a HostLimits value")
        if not isinstance(self.retry, RetrySettings):
            raise InvalidConfigError("retry must be a RetrySettings value")
        if not isinstance(self.validation, ValidationSettings):
            raise InvalidConfigError("validation must be a ValidationSettings value")
        if not isinstance(self.policy, PolicySettings):
            raise InvalidConfigError("policy must be a PolicySettings value")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "paths": self.paths.to_dict(),
            "provider": self.provider.to_dict(),
            "limits": self.limits.to_dict(),
            "retry": self.retry.to_dict(),
            "validation": self.validation.to_dict(),
            "policy": self.policy.to_dict(),
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> Self:
        data = _strict_mapping(
            value,
            location="config",
            expected_keys=frozenset(
                {
                    "schema_version",
                    "paths",
                    "provider",
                    "limits",
                    "retry",
                    "validation",
                    "policy",
                }
            ),
        )
        schema_version = _strict_string(data["schema_version"], location="schema_version")
        if schema_version != _SCHEMA_VERSION:
            raise InvalidConfigError(f"schema_version must equal {_SCHEMA_VERSION!r}")
        return cls(
            schema_version=schema_version,
            paths=HarnessPaths.from_dict(cast(Mapping[str, object], data["paths"])),
            provider=ProviderSettings.from_dict(cast(Mapping[str, object], data["provider"])),
            limits=HostLimits.from_dict(cast(Mapping[str, object], data["limits"])),
            retry=RetrySettings.from_dict(cast(Mapping[str, object], data["retry"])),
            validation=ValidationSettings.from_dict(cast(Mapping[str, object], data["validation"])),
            policy=PolicySettings.from_dict(cast(Mapping[str, object], data["policy"])),
        )
