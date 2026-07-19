#!/usr/bin/env python3
"""Validate local references and identities in the accepted specification records."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlsplit

import yaml
from validate_schema import load_data

SCHEMA_NAMES = (
    "capability_execution_record.schema.yaml",
    "goal_contract.schema.yaml",
    "handoff.schema.yaml",
    "verifier_result.schema.yaml",
    "work_loop_state.schema.yaml",
)
EXAMPLE_NAMES = (
    "capability_execution_record.example.yaml",
    "goal_contract.example.yaml",
    "handoff.example.yaml",
    "local_implementation_goal.example.yaml",
    "verifier_result.example.yaml",
    "work_loop_state.example.yaml",
)
CANONICAL_TASK_IDS = {f"W-{number}" for number in range(201, 211)}
EXPECTED_TASK_OUTPUTS: Mapping[str, tuple[str, ...]] = {
    "W-201": ("docs/work/CHATGPT_WORK_LOOP_ADAPTER.md",),
    "W-202": ("docs/work/WEB_VS_LOCAL_ROUTING.md",),
    "W-203": ("docs/work/GENERATOR_VERIFIER_PROTOCOL.md",),
    "W-204": ("docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md", "schemas/handoff.schema.yaml"),
    "W-205": ("schemas/goal_contract.schema.yaml",),
    "W-206": ("schemas/work_loop_state.schema.yaml",),
    "W-207": ("schemas/verifier_result.schema.yaml",),
    "W-208": ("schemas/capability_execution_record.schema.yaml",),
    "W-209": ("evals/work_loop_acceptance_cases.yaml",),
    "W-210": ("docs/work/MODEL_EFFORT_ROUTING.md",),
}
LOCAL_REFERENCE_KINDS = {"REPOSITORY_PATH", "ARTIFACT_PATH", "COMMAND_RESULT"}
URI_REFERENCE_KINDS = {"URI", "PULL_REQUEST"}
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")
COMMIT = re.compile(r"^[A-Fa-f0-9]{7,64}$")


def iter_mappings(value: Any) -> Iterator[dict[str, Any]]:
    """Yield mappings recursively without treating scalar values as records."""

    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from iter_mappings(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_mappings(item)


def iter_schema_references(value: Any) -> Iterator[str]:
    for mapping in iter_mappings(value):
        reference = mapping.get("$ref")
        if isinstance(reference, str):
            yield reference


def resolve_json_pointer(document: Any, reference: str) -> bool:
    """Resolve a local RFC 6901 fragment used by the accepted schemas."""

    if not reference.startswith("#/"):
        return False
    target = document
    for raw_segment in reference[2:].split("/"):
        segment = raw_segment.replace("~1", "/").replace("~0", "~")
        if not isinstance(target, dict) or segment not in target:
            return False
        target = target[segment]
    return True


def safe_relative_path(reference: str) -> str | None:
    """Return an explanation when a package/repository path is not portable and relative."""

    path_part = reference.split("#", 1)[0]
    if not path_part:
        return "path is empty"
    if "\\" in path_part:
        return "path must use forward slashes"
    if path_part.startswith("/") or re.match(r"^[A-Za-z]:", path_part):
        return "path must be repository-relative, not absolute"
    if "\x00" in path_part:
        return "path contains a NUL byte"
    parts = path_part.split("/")
    checked_parts = parts[:-1] if path_part.endswith("/") else parts
    if any(part in {"", ".", ".."} for part in checked_parts):
        return "path contains an empty, current-directory, or parent-directory segment"
    if any(":" in part for part in parts):
        return "path contains a colon (drive or alternate-data-stream syntax)"
    if PurePosixPath(path_part).is_absolute():
        return "path must be repository-relative"
    return None


def valid_absolute_uri(reference: str) -> bool:
    if any(character.isspace() for character in reference):
        return False
    parsed = urlsplit(reference)
    if not parsed.scheme or not SCHEME.fullmatch(parsed.scheme):
        return False
    if parsed.scheme.lower() in {"http", "https"} and not parsed.netloc:
        return False
    return True


def _display(source: Path, root: Path) -> str:
    try:
        return source.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(source)


def validate_location_reference(reference: dict[str, Any], source: Path, root: Path) -> list[str]:
    errors: list[str] = []
    source_name = _display(source, root)
    kind = reference.get("kind")
    value = reference.get("ref")
    if not isinstance(kind, str) or not isinstance(value, str) or not value:
        return [f"{source_name}: location reference requires non-empty string kind and ref"]

    if kind in LOCAL_REFERENCE_KINDS:
        unsafe_reason = safe_relative_path(value)
        if unsafe_reason:
            errors.append(f"{source_name}: {kind} ref {value!r} is unsafe: {unsafe_reason}")
        else:
            target_text = value.split("#", 1)[0].rstrip("/")
            target = (root / target_text).resolve()
            if not target.is_relative_to(root.resolve()):
                errors.append(f"{source_name}: {kind} ref {value!r} escapes repository root")
            elif not target.exists():
                errors.append(f"{source_name}: {kind} ref {value!r} does not exist")
    elif kind in URI_REFERENCE_KINDS and not valid_absolute_uri(value):
        errors.append(f"{source_name}: {kind} ref {value!r} is not a valid absolute URI")
    elif kind == "GIT_COMMIT" and not COMMIT.fullmatch(value):
        errors.append(f"{source_name}: GIT_COMMIT ref {value!r} is not a 7-64 digit hex ID")
    return errors


def path_is_covered(path: str, allowed: Sequence[str]) -> bool:
    normalized_path = path.rstrip("/")
    return any(
        normalized_path == prefix.rstrip("/")
        or normalized_path.startswith(f"{prefix.rstrip('/')}/")
        for prefix in allowed
    )


def validate_cross_record_identities(records: Mapping[str, Any]) -> list[str]:
    """Check identities and reference keys that JSON Schema cannot compare across files."""

    errors: list[str] = []
    goal = records["goal_contract.example.yaml"]
    loop = records["work_loop_state.example.yaml"]
    verifier = records["verifier_result.example.yaml"]
    capability = records["capability_execution_record.example.yaml"]
    handoff = records["handoff.example.yaml"]
    local_goal = records["local_implementation_goal.example.yaml"]

    goal_id = goal.get("goal_id")
    for record_name, record in (
        ("work_loop_state.example.yaml", loop),
        ("verifier_result.example.yaml", verifier),
        ("capability_execution_record.example.yaml", capability),
    ):
        if record.get("goal_id") != goal_id:
            errors.append(
                f"{record_name}: goal_id {record.get('goal_id')!r} does not match "
                f"goal_contract.example.yaml goal_id {goal_id!r}"
            )

    if capability.get("run_id") != loop.get("run_id"):
        errors.append(
            "capability_execution_record.example.yaml: run_id "
            f"{capability.get('run_id')!r} does not match work-loop run_id {loop.get('run_id')!r}"
        )

    expected_goal_ref = "examples/specifications/goal_contract.example.yaml"
    for record_name, record in (
        ("work_loop_state.example.yaml", loop),
        ("verifier_result.example.yaml", verifier),
    ):
        actual_ref = record.get("goal_contract_ref", {}).get("ref")
        if actual_ref != expected_goal_ref:
            errors.append(
                f"{record_name}: goal_contract_ref {actual_ref!r} does not identify "
                f"{expected_goal_ref!r}"
            )

    completed_ids = {item.get("id") for item in loop.get("completed", [])}
    if loop.get("status") == "COMPLETED" and completed_ids != CANONICAL_TASK_IDS:
        errors.append(
            "work_loop_state.example.yaml: COMPLETED record task IDs are "
            f"{sorted(completed_ids, key=str)!r}; expected {sorted(CANONICAL_TASK_IDS)!r}"
        )
    if capability.get("task_id") not in completed_ids:
        errors.append(
            "capability_execution_record.example.yaml: task_id "
            f"{capability.get('task_id')!r} is not present in work-loop completed IDs"
        )

    allowed_files = [item.get("ref", "") for item in goal.get("scope", {}).get("allowed_files", [])]
    for task_id, outputs in EXPECTED_TASK_OUTPUTS.items():
        for output in outputs:
            if not path_is_covered(output, allowed_files):
                errors.append(
                    f"goal_contract.example.yaml: scope does not cover {task_id} output {output}"
                )

    task = handoff.get("task", {})
    if task.get("task_id") != "C-301":
        errors.append(f"handoff.example.yaml: task_id {task.get('task_id')!r} does not match C-301")
    if task.get("goal_id") != local_goal.get("goal_id"):
        errors.append(
            f"handoff.example.yaml: task goal_id {task.get('goal_id')!r} does not match "
            f"local implementation goal_id {local_goal.get('goal_id')!r}"
        )
    expected_local_goal_ref = "examples/specifications/local_implementation_goal.example.yaml"
    if task.get("goal_contract_ref", {}).get("ref") != expected_local_goal_ref:
        errors.append(
            f"handoff.example.yaml: task goal_contract_ref must identify {expected_local_goal_ref}"
        )

    pending = {
        item.get("action")
        for item in handoff.get("approvals", {}).get("records", [])
        if item.get("status") in {"REQUIRED", "REQUESTED"}
    }
    still_required = set(handoff.get("approvals", {}).get("still_required", []))
    if not still_required.issubset(pending):
        errors.append(
            "handoff.example.yaml: still_required actions lack pending approval records: "
            f"{sorted(still_required - pending)!r}"
        )

    output_ids = {item.get("output_id") for item in handoff.get("outputs", [])}
    evidence_ids = {item.get("evidence_id") for item in handoff.get("evidence", [])}
    approval_ids = {
        item.get("approval_id") for item in handoff.get("approvals", {}).get("records", [])
    }
    for requirement in handoff.get("must_requirements", []):
        missing_outputs = set(requirement.get("output_refs", [])) - output_ids
        missing_evidence = set(requirement.get("evidence_refs", [])) - evidence_ids
        if missing_outputs or missing_evidence:
            requirement_id = requirement.get("must_id")
            errors.append(
                f"handoff.example.yaml: {requirement_id} has unresolved output/evidence "
                f"IDs {sorted(missing_outputs | missing_evidence, key=str)!r}"
            )
    for action in handoff.get("external_actions", []):
        approval_id = action.get("approval_id")
        if approval_id not in approval_ids:
            errors.append(
                f"handoff.example.yaml: action {action.get('action_id')!r} references missing "
                f"approval_id {approval_id!r}"
            )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root used for schemas and local target resolution.",
    )
    parser.add_argument(
        "--examples-dir",
        type=Path,
        help=(
            "Directory containing the six accepted example filenames "
            "(default: ROOT/examples/specifications)."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()
    examples_dir = (
        args.examples_dir.resolve() if args.examples_dir else root / "examples" / "specifications"
    )
    errors: list[str] = []

    schemas: dict[str, Any] = {}
    schema_ids: dict[str, str] = {}
    for name in SCHEMA_NAMES:
        path = root / "schemas" / name
        try:
            schema = load_data(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{_display(path, root)}: cannot parse schema: {exc}")
            continue
        schemas[name] = schema
        schema_id = schema.get("$id") if isinstance(schema, dict) else None
        if not isinstance(schema_id, str) or not schema_id:
            errors.append(f"schemas/{name}: missing non-empty $id")
        elif schema_id in schema_ids:
            errors.append(
                f"schemas/{name}: duplicate $id {schema_id!r} also used by {schema_ids[schema_id]}"
            )
        else:
            schema_ids[schema_id] = name
        for reference in iter_schema_references(schema):
            if not resolve_json_pointer(schema, reference):
                errors.append(
                    f"schemas/{name}: $ref {reference!r} must be a resolvable local JSON Pointer"
                )

    records: dict[str, Any] = {}
    for name in EXAMPLE_NAMES:
        path = examples_dir / name
        try:
            records[name] = load_data(path)
        except (OSError, ValueError, yaml.YAMLError) as exc:
            errors.append(f"{_display(path, root)}: cannot parse example: {exc}")
            continue
        for mapping in iter_mappings(records[name]):
            if {"kind", "ref", "description"}.issubset(mapping):
                errors.extend(validate_location_reference(mapping, path, root))

    if set(records) == set(EXAMPLE_NAMES):
        errors.extend(validate_cross_record_identities(records))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL reference validation: {len(errors)} error(s)", file=sys.stderr)
        return 1

    reference_count = sum(
        1
        for record in records.values()
        for mapping in iter_mappings(record)
        if {"kind", "ref", "description"}.issubset(mapping)
    )
    schema_reference_count = sum(
        1 for schema in schemas.values() for _ in iter_schema_references(schema)
    )
    print(
        "PASS reference validation: "
        f"{reference_count} location reference(s), {schema_reference_count} schema reference(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
