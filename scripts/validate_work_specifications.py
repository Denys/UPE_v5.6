#!/usr/bin/env python3
"""Deterministic validation for the W-201…W-210 specification bundle."""

from __future__ import annotations

import copy
import importlib.metadata
import json
import platform
import re
import sys
from pathlib import Path
from typing import Any

import yaml

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:  # pragma: no cover - reported as a validation failure
    Draft202012Validator = None  # type: ignore[assignment,misc]
    FormatChecker = None  # type: ignore[assignment,misc]


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "docs/work/CHATGPT_WORK_LOOP_ADAPTER.md",
    "docs/work/WEB_VS_LOCAL_ROUTING.md",
    "docs/work/GENERATOR_VERIFIER_PROTOCOL.md",
    "docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md",
    "docs/work/MODEL_EFFORT_ROUTING.md",
    "docs/work/SECURITY_THREAT_BOUNDARY.md",
    "docs/work/RECOVERY_EVALUATION_OPERATIONS.md",
    "schemas/handoff.schema.yaml",
    "schemas/goal_contract.schema.yaml",
    "schemas/work_loop_state.schema.yaml",
    "schemas/verifier_result.schema.yaml",
    "schemas/capability_execution_record.schema.yaml",
    "evals/work_loop_acceptance_cases.yaml",
    "validation/W-200-SPECIFICATION-ACCEPTANCE.yaml",
    "validation/W-200-CROSS-DOCUMENT-REVIEW.md",
    "handoffs/W-200-LOCAL-IMPLEMENTATION-BRIEF.md",
    "handoffs/W-200-SPECIFICATION-CHECKPOINT.yaml",
    "examples/specifications/local_implementation_goal.example.yaml",
)

SCHEMA_EXAMPLES = {
    "schemas/handoff.schema.yaml": "examples/specifications/handoff.example.yaml",
    "schemas/goal_contract.schema.yaml": "examples/specifications/goal_contract.example.yaml",
    "schemas/work_loop_state.schema.yaml": "examples/specifications/work_loop_state.example.yaml",
    "schemas/verifier_result.schema.yaml": "examples/specifications/verifier_result.example.yaml",
    "schemas/capability_execution_record.schema.yaml": "examples/specifications/capability_execution_record.example.yaml",
}

ADDITIONAL_SCHEMA_EXAMPLES = {
    "schemas/goal_contract.schema.yaml": (
        "examples/specifications/local_implementation_goal.example.yaml",
    ),
}

EXPECTED_TASK_OUTPUTS = {
    "W-201": ["docs/work/CHATGPT_WORK_LOOP_ADAPTER.md"],
    "W-202": ["docs/work/WEB_VS_LOCAL_ROUTING.md"],
    "W-203": ["docs/work/GENERATOR_VERIFIER_PROTOCOL.md"],
    "W-204": ["docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md", "schemas/handoff.schema.yaml"],
    "W-205": ["schemas/goal_contract.schema.yaml"],
    "W-206": ["schemas/work_loop_state.schema.yaml"],
    "W-207": ["schemas/verifier_result.schema.yaml"],
    "W-208": ["schemas/capability_execution_record.schema.yaml"],
    "W-209": ["evals/work_loop_acceptance_cases.yaml"],
    "W-210": ["docs/work/MODEL_EFFORT_ROUTING.md"],
}

TYPE_PATHS: dict[str, tuple[str | int, ...]] = {
    "schemas/handoff.schema.yaml": ("handoff_id",),
    "schemas/goal_contract.schema.yaml": ("goal_id",),
    "schemas/work_loop_state.schema.yaml": ("state_id",),
    "schemas/verifier_result.schema.yaml": ("result_id",),
    "schemas/capability_execution_record.schema.yaml": ("record_id",),
}

ENUM_PATHS: dict[str, tuple[str | int, ...]] = {
    "schemas/handoff.schema.yaml": ("direction",),
    "schemas/goal_contract.schema.yaml": ("tools", "required", 0, "required_action_scope"),
    "schemas/work_loop_state.schema.yaml": ("status",),
    "schemas/verifier_result.schema.yaml": ("overall_verdict",),
    "schemas/capability_execution_record.schema.yaml": ("surface", "kind"),
}

EXPECTED_ACCEPTANCE_COVERAGE = {
    "canonical_W_209": {
        "success",
        "failed_verification",
        "no_progress",
        "read_only_verifier",
        "scheduled_monitor",
        "mobile_web_local_fallback",
        "concurrent_write_prevention",
        "local_folder_assumption",
    },
    "additional_phase_requirements": {
        "injection",
        "approval",
        "path",
        "secret",
        "crash",
        "retry",
        "duplicate_actions",
        "unknown_evidence",
    },
}

MARKDOWN_FILES = tuple(path for path in REQUIRED_FILES if path.endswith(".md"))
MARKDOWN_LINK = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def construct_unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> Any:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    construct_unique_mapping,
)


def load_data(relative_path: str) -> Any:
    path = ROOT / relative_path
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    return yaml.load(text, Loader=UniqueKeyLoader)


def check_markdown_links(relative_path: str) -> list[str]:
    path = ROOT / relative_path
    errors: list[str] = []
    for raw_target in MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")):
        target = raw_target.strip().split(maxsplit=1)[0].strip("<>")
        if target.startswith(("#", "http://", "https://", "mailto:", "sandbox:")):
            continue
        target_path = target.split("#", 1)[0]
        if not target_path:
            continue
        resolved = (path.parent / target_path).resolve()
        if not resolved.is_relative_to(ROOT.resolve()):
            errors.append(f"{relative_path}: link escapes repository: {target}")
        elif not resolved.exists():
            errors.append(f"{relative_path}: missing local link target: {target}")
    return errors


def set_nested(instance: Any, path: tuple[str | int, ...], value: Any) -> None:
    target = instance
    for segment in path[:-1]:
        target = target[segment]
    target[path[-1]] = value


def resolve_local_reference(schema: Any, reference: str) -> bool:
    if not reference.startswith("#/"):
        return False
    target = schema
    for segment in reference[2:].split("/"):
        key = segment.replace("~1", "/").replace("~0", "~")
        if not isinstance(target, dict) or key not in target:
            return False
        target = target[key]
    return True


def iter_references(value: Any) -> list[str]:
    references: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$ref" and isinstance(item, str):
                references.append(item)
            references.extend(iter_references(item))
    elif isinstance(value, list):
        for item in value:
            references.extend(iter_references(item))
    return references


def iter_location_references(value: Any) -> list[dict[str, Any]]:
    references: list[dict[str, Any]] = []
    if isinstance(value, dict):
        if {"kind", "ref", "description"}.issubset(value):
            references.append(value)
        for item in value.values():
            references.extend(iter_location_references(item))
    elif isinstance(value, list):
        for item in value:
            references.extend(iter_location_references(item))
    return references


def path_is_covered(path: str, allowed: list[str]) -> bool:
    normalized_path = path.rstrip("/")
    return any(
        normalized_path == prefix.rstrip("/")
        or normalized_path.startswith(f"{prefix.rstrip('/')}/")
        for prefix in allowed
    )


def main() -> int:
    errors: list[str] = []
    checks: dict[str, Any] = {}

    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    checks["required_files"] = {
        "status": "PASS" if not missing else "FAIL",
        "count": len(REQUIRED_FILES) - len(missing),
        "expected": len(REQUIRED_FILES),
        "missing": missing,
    }
    errors.extend(f"missing required file: {path}" for path in missing)

    parse_targets = sorted(
        {
            *SCHEMA_EXAMPLES,
            *SCHEMA_EXAMPLES.values(),
            *(path for paths in ADDITIONAL_SCHEMA_EXAMPLES.values() for path in paths),
            "docs/research/research-state.yaml",
            "evals/work_loop_acceptance_cases.yaml",
            "validation/W-200-SPECIFICATION-ACCEPTANCE.yaml",
            "handoffs/W-200-SPECIFICATION-CHECKPOINT.yaml",
            "chatgpt_work_harness_implementation_routing_2026-07-18/harness_implementation_backlog.yaml",
        }
    )
    parsed: dict[str, Any] = {}
    for relative_path in parse_targets:
        path = ROOT / relative_path
        if not path.is_file():
            errors.append(f"missing parse target: {relative_path}")
            continue
        try:
            parsed[relative_path] = load_data(relative_path)
        except Exception as exc:  # noqa: BLE001 - report every parser failure
            errors.append(f"{relative_path}: parse failed: {exc}")
    checks["yaml_json_parse"] = {
        "status": "PASS" if len(parsed) == len(parse_targets) else "FAIL",
        "count": len(parsed),
        "expected": len(parse_targets),
    }

    schema_results: dict[str, str] = {}
    additional_example_results: dict[str, str] = {}
    negative_results: dict[str, dict[str, str]] = {}
    reference_results: dict[str, dict[str, Any]] = {}
    schema_ids: list[str] = []
    if Draft202012Validator is None:
        errors.append("jsonschema is unavailable; install jsonschema>=4.18 for Draft 2020-12 validation")
    else:
        for schema_path, example_path in SCHEMA_EXAMPLES.items():
            if schema_path not in parsed or example_path not in parsed:
                continue
            try:
                schema = parsed[schema_path]
                Draft202012Validator.check_schema(schema)
                validator = Draft202012Validator(schema, format_checker=FormatChecker())
                instance_errors = sorted(validator.iter_errors(parsed[example_path]), key=lambda item: list(item.path))
                if instance_errors:
                    detail = "; ".join(
                        f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}"
                        for item in instance_errors
                    )
                    raise ValueError(detail)

                schema_id = schema.get("$id")
                if not isinstance(schema_id, str) or not schema_id:
                    raise ValueError("schema has no non-empty $id")
                schema_ids.append(schema_id)

                references = iter_references(schema)
                invalid_references = sorted(
                    reference for reference in references if not resolve_local_reference(schema, reference)
                )
                reference_results[schema_path] = {
                    "status": "PASS" if not invalid_references else "FAIL",
                    "count": len(references),
                    "invalid": invalid_references,
                }
                if invalid_references:
                    raise ValueError(f"unresolved or non-local references: {invalid_references}")

                negative_instances: dict[str, Any] = {}
                required_instance = copy.deepcopy(parsed[example_path])
                required_instance.pop(schema["required"][0], None)
                negative_instances["required_field"] = required_instance

                type_instance = copy.deepcopy(parsed[example_path])
                set_nested(type_instance, TYPE_PATHS[schema_path], [])
                negative_instances["type"] = type_instance

                enum_instance = copy.deepcopy(parsed[example_path])
                set_nested(enum_instance, ENUM_PATHS[schema_path], "__INVALID_ENUM__")
                negative_instances["enum_or_const"] = enum_instance

                additional_instance = copy.deepcopy(parsed[example_path])
                additional_instance["__unexpected_property__"] = True
                negative_instances["additional_property"] = additional_instance

                if schema_path == "schemas/handoff.schema.yaml":
                    unsafe_path = copy.deepcopy(parsed[example_path])
                    unsafe_path["scope"]["allowed_paths"][0] = "../escape"
                    negative_instances["unsafe_relative_path"] = unsafe_path

                    bad_aggregate = copy.deepcopy(parsed[example_path])
                    bad_aggregate["verification"]["criteria"][0]["verdict"] = "FAIL"
                    bad_aggregate["verification"]["criteria"][0]["smallest_correction"] = "Repair it."
                    negative_instances["pass_with_failed_criterion"] = bad_aggregate

                    missing_action_approval = copy.deepcopy(parsed[example_path])
                    missing_action_approval["external_actions"].append(
                        {
                            "action_id": "ACT-negative",
                            "operation": "COMMIT",
                            "target": "Denys/UPE_v5.6",
                            "status": "PLANNED",
                            "approval_id": None,
                            "idempotency_key": None,
                            "result_ref": None,
                        }
                    )
                    negative_instances["external_action_without_approval"] = missing_action_approval

                if schema_path == "schemas/verifier_result.schema.yaml":
                    bad_aggregate = copy.deepcopy(parsed[example_path])
                    bad_aggregate["criteria"][0]["verdict"] = "INSUFFICIENT_EVIDENCE"
                    bad_aggregate["criteria"][0]["missing_evidence"] = ["Missing artifact."]
                    bad_aggregate["criteria"][0]["smallest_correction"] = {
                        "action": "Supply the artifact.",
                        "owner": "GENERATOR",
                        "target_refs": [],
                        "verification": "Re-run the deterministic validator.",
                    }
                    bad_aggregate["criteria"][0]["release_blocking"] = True
                    bad_aggregate["release_blocking"] = True
                    negative_instances["pass_with_insufficient_criterion"] = bad_aggregate

                if schema_path == "schemas/capability_execution_record.schema.yaml":
                    unauthorized_effect = copy.deepcopy(parsed[example_path])
                    unauthorized_effect["permission"].update(
                        {
                            "action_scope": "WRITE",
                            "state": "AUTHORIZED",
                            "approval_required": False,
                            "authorization_ref": None,
                            "enforcement_owner": "TRUSTED_HOST",
                        }
                    )
                    unauthorized_effect["action_boundary"]["side_effect_owner"] = "TRUSTED_HOST"
                    unauthorized_effect["execution"]["action_id"] = "action.negative"
                    unauthorized_effect["execution"]["side_effects"] = [
                        {
                            "effect_id": "effect.negative",
                            "action": "Write",
                            "target": "repository",
                            "occurred": True,
                            "authorization_required": True,
                            "result_ref": None,
                        }
                    ]
                    negative_instances["occurred_effect_without_authorization_ref"] = unauthorized_effect

                negative_results[schema_path] = {}
                for case_name, negative_instance in negative_instances.items():
                    rejected = bool(list(validator.iter_errors(negative_instance)))
                    negative_results[schema_path][case_name] = "PASS" if rejected else "FAIL"
                    if not rejected:
                        raise ValueError(f"negative case was accepted: {case_name}")
                schema_results[schema_path] = "PASS"
            except Exception as exc:  # noqa: BLE001 - aggregate validation failures
                schema_results[schema_path] = "FAIL"
                errors.append(f"{schema_path} / {example_path}: {exc}")
        for schema_path, example_paths in ADDITIONAL_SCHEMA_EXAMPLES.items():
            if schema_path not in parsed:
                continue
            validator = Draft202012Validator(parsed[schema_path], format_checker=FormatChecker())
            for example_path in example_paths:
                key = f"{schema_path} / {example_path}"
                if example_path not in parsed:
                    additional_example_results[key] = "FAIL"
                    continue
                instance_errors = sorted(
                    validator.iter_errors(parsed[example_path]), key=lambda item: list(item.path)
                )
                if instance_errors:
                    detail = "; ".join(
                        f"{'.'.join(map(str, item.path)) or '<root>'}: {item.message}"
                        for item in instance_errors
                    )
                    additional_example_results[key] = "FAIL"
                    errors.append(f"{key}: {detail}")
                else:
                    additional_example_results[key] = "PASS"
    checks["json_schema_2020_12"] = {
        "status": "PASS"
        if len(schema_results) == len(SCHEMA_EXAMPLES)
        and set(schema_results.values()) == {"PASS"}
        and len(additional_example_results)
        == sum(len(paths) for paths in ADDITIONAL_SCHEMA_EXAMPLES.values())
        and set(additional_example_results.values()) == {"PASS"}
        else "FAIL",
        "results": schema_results,
        "additional_examples": additional_example_results,
    }
    duplicate_ids = sorted({schema_id for schema_id in schema_ids if schema_ids.count(schema_id) > 1})
    checks["schema_local_references_and_ids"] = {
        "status": "PASS"
        if len(reference_results) == len(SCHEMA_EXAMPLES) and not duplicate_ids
        else "FAIL",
        "results": reference_results,
        "duplicate_ids": duplicate_ids,
    }
    if duplicate_ids:
        errors.append(f"duplicate schema $id values: {duplicate_ids}")
    checks["negative_schema_cases"] = {
        "status": "PASS"
        if len(negative_results) == len(SCHEMA_EXAMPLES)
        and all(set(results.values()) == {"PASS"} for results in negative_results.values())
        else "FAIL",
        "results": negative_results,
    }

    link_errors: list[str] = []
    for relative_path in MARKDOWN_FILES:
        if (ROOT / relative_path).is_file():
            link_errors.extend(check_markdown_links(relative_path))
    checks["markdown_local_links"] = {
        "status": "PASS" if not link_errors else "FAIL",
        "files_checked": sum((ROOT / path).is_file() for path in MARKDOWN_FILES),
        "errors": link_errors,
    }
    errors.extend(link_errors)

    canonical_ids = set(EXPECTED_TASK_OUTPUTS)
    readme = (ROOT / "README.md").read_text(encoding="utf-8") if (ROOT / "README.md").is_file() else ""
    missing_ids = sorted(task_id for task_id in canonical_ids if task_id not in readme)
    backlog_path = "chatgpt_work_harness_implementation_routing_2026-07-18/harness_implementation_backlog.yaml"
    backlog_tasks = {
        task["id"]: task
        for task in parsed.get(backlog_path, {}).get("tasks", [])
        if task.get("id") in canonical_ids
    }
    mapping_errors: list[str] = []
    for task_id, expected_outputs in EXPECTED_TASK_OUTPUTS.items():
        task = backlog_tasks.get(task_id)
        if task is None:
            mapping_errors.append(f"canonical backlog is missing {task_id}")
            continue
        if task.get("surface") != "chatgpt_work_web":
            mapping_errors.append(f"{task_id}: expected chatgpt_work_web, got {task.get('surface')!r}")
        if task.get("outputs") != expected_outputs:
            mapping_errors.append(
                f"{task_id}: expected outputs {expected_outputs!r}, got {task.get('outputs')!r}"
            )
        exact_title = task.get("title")
        if not isinstance(exact_title, str) or f"| `{task_id}` | {exact_title} |" not in readme:
            mapping_errors.append(f"README does not preserve the canonical title for {task_id}: {exact_title!r}")
    checks["canonical_task_mapping"] = {
        "status": "PASS" if not missing_ids and not mapping_errors else "FAIL",
        "missing_ids": missing_ids,
        "mapping_errors": mapping_errors,
    }
    errors.extend(f"README missing canonical task ID: {task_id}" for task_id in missing_ids)
    errors.extend(mapping_errors)

    acceptance = parsed.get("evals/work_loop_acceptance_cases.yaml", {})
    cases = acceptance.get("cases", [])
    case_ids = [case.get("id") for case in cases]
    coverage = acceptance.get("coverage", {})
    coverage_errors: list[str] = []
    if len(case_ids) != len(set(case_ids)):
        coverage_errors.append("acceptance case IDs are not unique")
    for case in cases:
        if not case.get("oracle") or not case.get("forbidden_outcomes"):
            coverage_errors.append(f"{case.get('id')}: missing oracle or forbidden outcomes")
    for group, expected_keys in EXPECTED_ACCEPTANCE_COVERAGE.items():
        actual = coverage.get(group, {})
        if set(actual) != expected_keys:
            coverage_errors.append(
                f"coverage.{group}: expected {sorted(expected_keys)}, got {sorted(actual)}"
            )
        missing_case_refs = sorted(set(actual.values()) - set(case_ids))
        if missing_case_refs:
            coverage_errors.append(f"coverage.{group}: missing case IDs {missing_case_refs}")
    checks["acceptance_case_coverage"] = {
        "status": "PASS" if not coverage_errors else "FAIL",
        "case_count": len(cases),
        "errors": coverage_errors,
    }
    errors.extend(coverage_errors)

    example_reference_errors: list[str] = []
    for example_path in SCHEMA_EXAMPLES.values():
        for reference in iter_location_references(parsed.get(example_path, {})):
            if reference.get("kind") not in {"REPOSITORY_PATH", "ARTIFACT_PATH", "COMMAND_RESULT"}:
                continue
            target = str(reference.get("ref", "")).split("#", 1)[0]
            if not target or not (ROOT / target).exists():
                example_reference_errors.append(
                    f"{example_path}: unresolved {reference.get('kind')} reference {reference.get('ref')!r}"
                )
    checks["example_repository_references"] = {
        "status": "PASS" if not example_reference_errors else "FAIL",
        "errors": example_reference_errors,
    }
    errors.extend(example_reference_errors)

    goal = parsed.get("examples/specifications/goal_contract.example.yaml", {})
    loop_state = parsed.get("examples/specifications/work_loop_state.example.yaml", {})
    verifier = parsed.get("examples/specifications/verifier_result.example.yaml", {})
    capability = parsed.get("examples/specifications/capability_execution_record.example.yaml", {})
    handoff = parsed.get("examples/specifications/handoff.example.yaml", {})
    alignment_errors: list[str] = []
    goal_id = goal.get("goal_id")
    aligned_goal_ids = {
        "work_loop_state": loop_state.get("goal_id"),
        "verifier_result": verifier.get("goal_id"),
        "capability_record": capability.get("goal_id"),
    }
    for record_name, aligned_goal_id in aligned_goal_ids.items():
        if aligned_goal_id != goal_id:
            alignment_errors.append(
                f"{record_name}: goal_id {aligned_goal_id!r} does not match {goal_id!r}"
            )

    expected_goal_ref = "examples/specifications/goal_contract.example.yaml"
    goal_refs = {
        "work_loop_state": loop_state.get("goal_contract_ref", {}).get("ref"),
        "verifier_result": verifier.get("goal_contract_ref", {}).get("ref"),
    }
    for record_name, goal_ref in goal_refs.items():
        if goal_ref != expected_goal_ref:
            alignment_errors.append(
                f"{record_name}: goal_contract_ref {goal_ref!r} does not match {expected_goal_ref!r}"
            )

    completed_ids = {item.get("id") for item in loop_state.get("completed", [])}
    if loop_state.get("status") == "COMPLETED" and completed_ids != canonical_ids:
        alignment_errors.append(
            f"completed work-loop state has task IDs {sorted(completed_ids)}, expected {sorted(canonical_ids)}"
        )

    allowed_files = [item.get("ref", "") for item in goal.get("scope", {}).get("allowed_files", [])]
    for task_id, outputs in EXPECTED_TASK_OUTPUTS.items():
        for output in outputs:
            if not path_is_covered(output, allowed_files):
                alignment_errors.append(f"goal scope does not cover {task_id} output {output}")

    task = handoff.get("task", {})
    if task.get("task_id") != "C-301":
        alignment_errors.append(f"handoff task is {task.get('task_id')!r}, expected canonical C-301")
    implementation_goal_path = "examples/specifications/local_implementation_goal.example.yaml"
    implementation_goal = parsed.get(implementation_goal_path, {})
    if task.get("goal_id") != implementation_goal.get("goal_id"):
        alignment_errors.append(
            f"handoff goal_id {task.get('goal_id')!r} does not match implementation goal "
            f"{implementation_goal.get('goal_id')!r}"
        )
    if task.get("goal_contract_ref", {}).get("ref") != implementation_goal_path:
        alignment_errors.append(
            f"handoff goal_contract_ref does not identify {implementation_goal_path}"
        )
    still_required = set(handoff.get("approvals", {}).get("still_required", []))
    pending_records = {
        record.get("action")
        for record in handoff.get("approvals", {}).get("records", [])
        if record.get("status") in {"REQUIRED", "REQUESTED"}
    }
    if not still_required.issubset(pending_records):
        alignment_errors.append(
            f"handoff still_required actions lack scoped pending records: {sorted(still_required - pending_records)}"
        )

    output_ids = {item.get("output_id") for item in handoff.get("outputs", [])}
    evidence_ids = {item.get("evidence_id") for item in handoff.get("evidence", [])}
    approval_ids = {item.get("approval_id") for item in handoff.get("approvals", {}).get("records", [])}
    for requirement in handoff.get("must_requirements", []):
        missing_outputs = set(requirement.get("output_refs", [])) - output_ids
        missing_evidence = set(requirement.get("evidence_refs", [])) - evidence_ids
        if missing_outputs or missing_evidence:
            alignment_errors.append(
                f"handoff {requirement.get('must_id')}: unresolved output/evidence refs "
                f"{sorted(missing_outputs | missing_evidence)}"
            )
    for action in handoff.get("external_actions", []):
        if action.get("approval_id") not in approval_ids:
            alignment_errors.append(
                f"handoff {action.get('action_id')}: unresolved approval {action.get('approval_id')!r}"
            )

    checks["cross_contract_examples"] = {
        "status": "PASS" if not alignment_errors else "FAIL",
        "errors": alignment_errors,
    }
    errors.extend(alignment_errors)

    result = {
        "schema_version": "1.0",
        "gate": "W-200-SPECIFICATION",
        "status": "PASS" if not errors else "FAIL",
        "runtime": {
            "python": platform.python_version(),
            "PyYAML": importlib.metadata.version("PyYAML"),
            "jsonschema": importlib.metadata.version("jsonschema")
            if Draft202012Validator is not None
            else None,
        },
        "checks": checks,
        "errors": errors,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
