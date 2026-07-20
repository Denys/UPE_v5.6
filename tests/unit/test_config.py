"""Unit tests for the immutable trusted-host configuration contract."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields
from pathlib import Path, PureWindowsPath
from typing import Any, cast

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError, ValidationError

import harness.config as config_module
from harness.config import (
    HarnessConfig,
    HarnessPaths,
    HostLimits,
    InvalidConfigError,
    PolicySettings,
    ProviderAdapter,
    ProviderSettings,
    RetrySettings,
    ValidationSettings,
)

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "config.schema.json"


def make_paths() -> HarnessPaths:
    return HarnessPaths(
        repository_root=PureWindowsPath(r"C:\projects\target"),
        worktree_root=PureWindowsPath(r"D:\harness\worktrees"),
        host_state_root=PureWindowsPath(r"E:\harness\state"),
    )


def make_retry() -> RetrySettings:
    return RetrySettings(
        max_transient_retries=2,
        identical_failure_limit=2,
        no_progress_iteration_limit=3,
        initial_backoff_seconds=0.5,
        maximum_backoff_seconds=8.0,
        backoff_multiplier=2.0,
        jitter_ratio=0.25,
    )


def make_config() -> HarnessConfig:
    return HarnessConfig(
        paths=make_paths(),
        limits=HostLimits(max_iterations=20, max_elapsed_seconds=3600),
        retry=make_retry(),
        validation=ValidationSettings(
            default_timeout_seconds=120,
            max_output_bytes=1_048_576,
        ),
    )


def load_schema() -> dict[str, Any]:
    value: object = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return cast(dict[str, Any], value)


def nested_mapping(mapping: dict[str, object], key: str) -> dict[str, object]:
    value = mapping[key]
    assert isinstance(value, dict)
    return cast(dict[str, object], value)


def test_public_surface_is_explicit() -> None:
    assert config_module.__all__ == [
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


def test_safe_defaults_are_fully_materialized() -> None:
    config = make_config()

    assert config.schema_version == "1.0.0"
    assert config.provider == ProviderSettings(
        adapter=ProviderAdapter.FAKE,
        model=None,
        reasoning_effort=None,
    )
    assert config.policy == PolicySettings(
        network_enabled=False,
        allowed_hosts=(),
        docker_enabled=False,
    )
    assert config.limits.max_input_tokens is None
    assert config.limits.max_output_tokens is None
    assert config.limits.max_total_tokens is None
    assert config.limits.max_cost is None
    assert config.limits.max_external_actions == 0
    assert config.to_dict()["provider"] == {
        "adapter": "fake",
        "model": None,
        "reasoning_effort": None,
    }
    assert config.to_dict()["policy"] == {
        "network_enabled": False,
        "allowed_hosts": [],
        "docker_enabled": False,
    }


def test_models_are_frozen_and_materialized_collections_do_not_alias() -> None:
    config = make_config()

    with pytest.raises(FrozenInstanceError):
        config.policy.network_enabled = True  # type: ignore[misc]

    materialized = config.to_dict()
    policy = nested_mapping(materialized, "policy")
    hosts = policy["allowed_hosts"]
    assert isinstance(hosts, list)
    hosts.append("example.test")
    assert config.policy.allowed_hosts == ()


@pytest.mark.parametrize(
    ("section", "key", "value"),
    [
        ("limits", "max_iterations", 0),
        ("limits", "max_elapsed_seconds", -1),
        ("limits", "max_input_tokens", -1),
        ("limits", "max_output_tokens", -1),
        ("limits", "max_total_tokens", -1),
        ("limits", "max_cost", -0.01),
        ("limits", "max_external_actions", -1),
        ("retry", "max_transient_retries", -1),
        ("retry", "identical_failure_limit", 0),
        ("retry", "no_progress_iteration_limit", 0),
        ("retry", "initial_backoff_seconds", 0),
        ("retry", "maximum_backoff_seconds", 0.25),
        ("retry", "backoff_multiplier", 0.99),
        ("retry", "jitter_ratio", -0.01),
        ("retry", "jitter_ratio", 1.01),
        ("validation", "default_timeout_seconds", 0),
        ("validation", "max_output_bytes", 0),
    ],
)
def test_numeric_bounds_are_enforced(section: str, key: str, value: object) -> None:
    mapping = make_config().to_dict()
    nested_mapping(mapping, section)[key] = value

    with pytest.raises(InvalidConfigError):
        HarnessConfig.from_dict(mapping)


@pytest.mark.parametrize(
    ("section", "key"),
    [
        ("limits", "max_iterations"),
        ("limits", "max_elapsed_seconds"),
        ("limits", "max_input_tokens"),
        ("limits", "max_output_tokens"),
        ("limits", "max_total_tokens"),
        ("limits", "max_cost"),
        ("limits", "max_external_actions"),
        ("retry", "max_transient_retries"),
        ("retry", "identical_failure_limit"),
        ("retry", "no_progress_iteration_limit"),
        ("retry", "initial_backoff_seconds"),
        ("retry", "maximum_backoff_seconds"),
        ("retry", "backoff_multiplier"),
        ("retry", "jitter_ratio"),
        ("validation", "default_timeout_seconds"),
        ("validation", "max_output_bytes"),
    ],
)
def test_bool_is_never_accepted_as_an_integer_or_number(section: str, key: str) -> None:
    mapping = make_config().to_dict()
    nested_mapping(mapping, section)[key] = True

    with pytest.raises(InvalidConfigError, match="boolean|booleans"):
        HarnessConfig.from_dict(mapping)

    errors = list(Draft202012Validator(load_schema()).iter_errors(mapping))
    assert errors


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_nonfinite_numbers_are_rejected(value: float) -> None:
    mapping = make_config().to_dict()
    nested_mapping(mapping, "limits")["max_cost"] = value

    with pytest.raises(InvalidConfigError, match="finite"):
        HarnessConfig.from_dict(mapping)


@pytest.mark.parametrize(
    "candidate",
    [
        "",
        "   ",
        "relative\\repo",
        r"C:relative",
        r"C:\repo\..\escape",
        r"C:\repo\.\child",
        r"C:\repo\*.txt",
        r"C:\repo\[abc]",
        r"C:\%TEMP%\repo",
        r"C:\$env\repo",
        r"C:\~\repo",
        r"\\server\share\repo",
        r"\\?\C:\repo",
        r"\\.\C:\repo",
        r"C:\repo:stream",
        r"1:\repo",
        r"CC:\repo",
        r"C::\repo",
        r"C:\CON",
        r"C:\aux.txt",
        "C:\\repo\\trailing. ",
    ],
)
def test_unsafe_or_malformed_windows_paths_are_rejected(candidate: str) -> None:
    with pytest.raises(InvalidConfigError):
        HarnessPaths(
            repository_root=cast(PureWindowsPath, candidate),
            worktree_root=PureWindowsPath(r"D:\harness\worktrees"),
            host_state_root=PureWindowsPath(r"E:\harness\state"),
        )

    mapping = make_config().to_dict()
    nested_mapping(mapping, "paths")["repository_root"] = candidate
    assert list(Draft202012Validator(load_schema()).iter_errors(mapping))


def test_concrete_path_values_are_accepted_without_filesystem_inspection() -> None:
    paths = HarnessPaths(
        repository_root=cast(PureWindowsPath, Path(r"C:\missing\repository")),
        worktree_root=cast(PureWindowsPath, Path(r"D:\missing\worktrees")),
        host_state_root=cast(PureWindowsPath, Path(r"E:\missing\state")),
    )

    assert paths.repository_root == PureWindowsPath(r"C:\missing\repository")


@pytest.mark.parametrize(
    ("repository", "worktree", "state"),
    [
        (r"C:\root", r"C:\root", r"E:\state"),
        (r"C:\root", r"C:\root\child", r"E:\state"),
        (r"C:\root\child", r"C:\ROOT", r"E:\state"),
        (r"C:\repo", r"D:\work", r"D:\work\state"),
    ],
)
def test_paths_reject_case_insensitive_lexical_overlap(
    repository: str,
    worktree: str,
    state: str,
) -> None:
    with pytest.raises(InvalidConfigError, match="overlap or nest"):
        HarnessPaths(
            repository_root=cast(PureWindowsPath, repository),
            worktree_root=cast(PureWindowsPath, worktree),
            host_state_root=cast(PureWindowsPath, state),
        )


def test_host_state_derived_paths_are_lexical_children() -> None:
    paths = make_paths()

    assert paths.database_path == PureWindowsPath(r"E:\harness\state\harness.sqlite3")
    assert paths.events_path == PureWindowsPath(r"E:\harness\state\events")
    assert paths.checkpoints_path == PureWindowsPath(r"E:\harness\state\checkpoints")
    assert paths.artifacts_path == PureWindowsPath(r"E:\harness\state\artifacts")


def test_provider_adapter_and_optional_strings_round_trip() -> None:
    provider = ProviderSettings.from_dict(
        {
            "adapter": "codex_app_server",
            "model": "gpt-5.6",
            "reasoning_effort": "high",
        }
    )

    assert provider.adapter is ProviderAdapter.CODEX_APP_SERVER
    assert provider.to_dict() == {
        "adapter": "codex_app_server",
        "model": "gpt-5.6",
        "reasoning_effort": "high",
    }


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("adapter", "unknown"),
        ("model", ""),
        ("model", "   "),
        ("model", "m" * 257),
        ("reasoning_effort", ""),
        ("reasoning_effort", "r" * 257),
    ],
)
def test_invalid_provider_values_are_rejected(key: str, value: object) -> None:
    mapping: dict[str, object] = ProviderSettings().to_dict()
    mapping[key] = value

    with pytest.raises(InvalidConfigError):
        ProviderSettings.from_dict(mapping)


def test_provider_constructor_requires_enum_value() -> None:
    with pytest.raises(InvalidConfigError, match="ProviderAdapter"):
        ProviderSettings(adapter=cast(ProviderAdapter, "fake"))


def test_policy_is_fail_closed_by_default() -> None:
    policy = PolicySettings()

    assert policy.network_enabled is False
    assert policy.allowed_hosts == ()
    assert policy.docker_enabled is False

    with pytest.raises(InvalidConfigError, match="must be empty"):
        PolicySettings(allowed_hosts=("example.test",))


def test_policy_accepts_only_explicit_normalized_hosts_when_network_is_enabled() -> None:
    policy = PolicySettings(
        network_enabled=True,
        allowed_hosts=("api.openai.com", "localhost", "127.0.0.1"),
    )

    assert policy.allowed_hosts == ("api.openai.com", "localhost", "127.0.0.1")


@pytest.mark.parametrize(
    "host",
    [
        "",
        "*.example.test",
        "https://example.test",
        "user@example.test",
        "example.test:443",
        "example.test/path",
        "example.test\\path",
        "Example.test",
        "example_test",
        "-example.test",
        "example-.test",
        "example.test.",
    ],
)
def test_policy_rejects_ambiguous_or_unnormalized_hosts(host: str) -> None:
    with pytest.raises(InvalidConfigError):
        PolicySettings(network_enabled=True, allowed_hosts=(host,))

    mapping = make_config().to_dict()
    policy = nested_mapping(mapping, "policy")
    policy["network_enabled"] = True
    policy["allowed_hosts"] = [host]
    assert list(Draft202012Validator(load_schema()).iter_errors(mapping))


def test_policy_rejects_duplicate_hosts() -> None:
    with pytest.raises(InvalidConfigError, match="duplicates"):
        PolicySettings(
            network_enabled=True,
            allowed_hosts=("example.test", "example.test"),
        )


@pytest.mark.parametrize(
    ("location", "mutation"),
    [
        ("root-extra", "unexpected"),
        ("nested-extra", "unexpected"),
        ("missing-materialized-default", "model"),
    ],
)
def test_strict_mapping_rejects_extra_or_missing_keys(location: str, mutation: str) -> None:
    mapping = make_config().to_dict()
    if location == "root-extra":
        mapping[mutation] = True
    elif location == "nested-extra":
        nested_mapping(mapping, "provider")[mutation] = True
    else:
        del nested_mapping(mapping, "provider")[mutation]

    with pytest.raises(InvalidConfigError, match="keys"):
        HarnessConfig.from_dict(mapping)

    with pytest.raises(ValidationError):
        Draft202012Validator(load_schema()).validate(mapping)


def test_mapping_rejects_non_json_coercion() -> None:
    mapping = make_config().to_dict()
    nested_mapping(mapping, "paths")["repository_root"] = Path(r"C:\projects\target")

    with pytest.raises(InvalidConfigError, match="string"):
        HarnessConfig.from_dict(mapping)


def test_schema_is_valid_draft_2020_12_and_round_trips_with_model() -> None:
    schema = load_schema()
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:  # pragma: no cover - assertion context for schema regressions
        pytest.fail(f"invalid Draft 2020-12 schema: {exc.message}")

    mapping = make_config().to_dict()
    json_mapping: object = json.loads(json.dumps(mapping, allow_nan=False))
    assert isinstance(json_mapping, dict)
    decoded = cast(dict[str, object], json_mapping)
    Draft202012Validator(schema).validate(decoded)

    restored = HarnessConfig.from_dict(decoded)
    assert restored == make_config()
    assert restored.to_dict() == decoded


def test_schema_and_model_reject_disallowed_network_allowlist() -> None:
    mapping = make_config().to_dict()
    nested_mapping(mapping, "policy")["allowed_hosts"] = ["example.test"]

    with pytest.raises(InvalidConfigError, match="must be empty"):
        HarnessConfig.from_dict(mapping)
    with pytest.raises(ValidationError):
        Draft202012Validator(load_schema()).validate(mapping)


def test_schema_rejects_unsafe_path_and_host_syntax() -> None:
    schema = load_schema()
    mapping = make_config().to_dict()
    nested_mapping(mapping, "paths")["repository_root"] = r"C:\repo\..\escape"
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(mapping)

    mapping = make_config().to_dict()
    policy = nested_mapping(mapping, "policy")
    policy["network_enabled"] = True
    policy["allowed_hosts"] = ["https://example.test"]
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(mapping)


def test_config_contract_contains_no_secret_value_fields() -> None:
    prohibited = {
        "api_key",
        "credential",
        "credentials",
        "password",
        "secret",
        "access_token",
        "refresh_token",
    }
    model_field_names = {
        item.name
        for model in (
            HarnessConfig,
            HarnessPaths,
            ProviderSettings,
            HostLimits,
            RetrySettings,
            ValidationSettings,
            PolicySettings,
        )
        for item in fields(model)
    }
    assert model_field_names.isdisjoint(prohibited)

    def schema_property_names(value: object) -> set[str]:
        names: set[str] = set()
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "properties" and isinstance(child, dict):
                    names.update(str(name) for name in child)
                names.update(schema_property_names(child))
        elif isinstance(value, list):
            for child in value:
                names.update(schema_property_names(child))
        return names

    assert schema_property_names(load_schema()).isdisjoint(prohibited)


def test_non_mapping_root_is_rejected() -> None:
    with pytest.raises(InvalidConfigError, match="object mapping"):
        HarnessConfig.from_dict(cast(dict[str, object], []))
