"""Refresh the embedded UPE delivery state in the capability readiness report."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

REPORT_NAME = "UPE_5.6.0_to_5.6.1_capability_readiness_report_2026-07-19.html"
BACKLOG_PATH = (
    Path("chatgpt_work_harness_implementation_routing_2026-07-18")
    / "harness_implementation_backlog.yaml"
)
STATE_PATH = Path("docs/research/research-state.yaml")
START_MARKER = "<!-- UPE_TASK_STATE:START -->"
END_MARKER = "<!-- UPE_TASK_STATE:END -->"
TASK_ID_PATTERN = re.compile(r"\b(?:[A-Z]+-\d{3}|G-ADR)\b")
RANGE_PATTERN = re.compile(r"\b([A-Z]+)-(\d{3})-\1-(\d{3})\b")

SUCCESS_WORDS = ("PASS", "MERGED", "COMPLETE", "ACCEPTED", "DONE", "TESTED_LOCALLY")
FAILURE_WORDS = ("FAIL", "BLOCKED", "UNKNOWN", "PENDING", "REJECTED")

STATUS_ALIASES: Mapping[str, tuple[str, ...]] = {
    "research_matrix": ("R-001",),
    "pattern_comparison": ("R-002",),
    "local_environment_handoff": ("C-105",),
    "architecture_evidence_packet": ("W-102",),
    "adr_001": ("P-101",),
    "adr_gate": ("G-ADR",),
}

SURFACE_LABELS: Mapping[str, str] = {
    "chatgpt_work_web": "Web allowed",
    "chatgpt_pro_web": "Web · Pro required",
    "chatgpt_work_desktop": "Desktop optional",
    "local_codex": "Local required",
    "coordinator": "Deterministic gate",
    "none": "Deferred",
}

MODEL_LABELS: Mapping[str, str] = {
    "sol_high": "High",
    "sol_max_or_highest_exposed": "Max",
    "sol_pro": "Pro",
    "deterministic_gate": "Gate",
    "not_applicable": "N/A",
}

PHASE_LABELS: Mapping[str, str] = {
    "0-research": "Research",
    "1-pre-adr-evidence": "Environment evidence",
    "2-architecture-gate": "Architecture gate",
    "3-web-specification": "Web specification",
    "4-local-scaffold": "Local foundation",
    "5-core-harness": "Core harness",
    "6-app-server-recovery-security": "App Server + recovery",
    "7-tests-evals": "Tests + evaluations",
    "8-release": "Release evidence",
}

SOURCE_LABELS: Mapping[str, str] = {
    str(BACKLOG_PATH).replace("\\", "/"): "Canonical implementation backlog",
    "Pasted markdown.md": "Authoritative build brief",
    "docs/architecture/ADR-001-harness-boundary.md": "Accepted harness boundary",
    "docs/research/app-server-protocol-observations.md": "Observed App Server protocol",
    "docs/work/CHATGPT_WORK_LOOP_ADAPTER.md": "Work loop adapter specification",
    "docs/work/GENERATOR_VERIFIER_PROTOCOL.md": "Generator/verifier protocol",
    "docs/work/MODEL_EFFORT_ROUTING.md": "Model and effort routing",
    "docs/work/RECOVERY_EVALUATION_OPERATIONS.md": "Recovery, evaluation, and operations",
    "docs/work/SECURITY_THREAT_BOUNDARY.md": "Security and containment boundary",
    "docs/work/WEB_VS_LOCAL_ROUTING.md": "Web/local execution routing",
    "docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md": "Work/Codex handoff protocol",
    "evals/work_loop_acceptance_cases.yaml": "Work-loop acceptance cases",
    "handoffs/NEXT-FIVE-WORK-PACKAGES-PARALLEL-EXECUTION-HANDOFF.md": (
        "Next-five parallel execution handoff"
    ),
    "handoffs/W-200-LOCAL-IMPLEMENTATION-BRIEF.md": "Accepted local implementation brief",
    "schemas/capability_execution_record.schema.yaml": "Capability execution record schema",
    "schemas/goal_contract.schema.yaml": "Goal contract schema",
    "schemas/handoff.schema.yaml": "Handoff schema",
    "schemas/verifier_result.schema.yaml": "Verifier result schema",
    "schemas/work_loop_state.schema.yaml": "Work loop-state schema",
    "UPE_v5.6.0_RELEASE/01_UPE_v5.6.0_FULL_REFERENCE.md": "UPE v5.6.0 full reference",
    "UPE_v5.6.0_RELEASE/07_CHANGELOG_AND_MIGRATION.md": "UPE changelog and migration",
    "UPE_v5.6.0_RELEASE/08_EVAL_SUITE.md": "UPE evaluation suite",
}

PHASE_DESIGN_SOURCES: Mapping[str, tuple[str, ...]] = {
    "0-research": ("Pasted markdown.md",),
    "1-pre-adr-evidence": ("Pasted markdown.md",),
    "2-architecture-gate": ("docs/architecture/ADR-001-harness-boundary.md",),
    "3-web-specification": ("handoffs/W-200-LOCAL-IMPLEMENTATION-BRIEF.md",),
    "4-local-scaffold": (
        "docs/architecture/ADR-001-harness-boundary.md",
        "handoffs/W-200-LOCAL-IMPLEMENTATION-BRIEF.md",
    ),
    "5-core-harness": (
        "docs/architecture/ADR-001-harness-boundary.md",
        "handoffs/W-200-LOCAL-IMPLEMENTATION-BRIEF.md",
    ),
    "6-app-server-recovery-security": (
        "docs/research/app-server-protocol-observations.md",
        "docs/work/RECOVERY_EVALUATION_OPERATIONS.md",
        "docs/work/SECURITY_THREAT_BOUNDARY.md",
    ),
    "7-tests-evals": (
        "docs/work/GENERATOR_VERIFIER_PROTOCOL.md",
        "evals/work_loop_acceptance_cases.yaml",
    ),
    "8-release": (
        "UPE_v5.6.0_RELEASE/07_CHANGELOG_AND_MIGRATION.md",
        "UPE_v5.6.0_RELEASE/08_EVAL_SUITE.md",
    ),
}

TASK_DESIGN_SOURCES: Mapping[str, tuple[str, ...]] = {
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
    "W-211": (
        "docs/work/CHATGPT_WORK_LOOP_ADAPTER.md",
        "docs/work/WEB_VS_LOCAL_ROUTING.md",
    ),
    "W-212": (
        "docs/work/CHATGPT_WORK_LOOP_ADAPTER.md",
        "docs/work/WEB_VS_LOCAL_ROUTING.md",
        "docs/work/MODEL_EFFORT_ROUTING.md",
        "UPE_v5.6.0_RELEASE/01_UPE_v5.6.0_FULL_REFERENCE.md",
    ),
    "C-405": (
        "docs/work/SECURITY_THREAT_BOUNDARY.md",
        "docs/architecture/ADR-001-harness-boundary.md",
    ),
    "C-406": (
        "docs/work/RECOVERY_EVALUATION_OPERATIONS.md",
        "docs/architecture/ADR-001-harness-boundary.md",
    ),
    "C-407": (
        "docs/work/RECOVERY_EVALUATION_OPERATIONS.md",
        "docs/work/CHATGPT_WORK_LOOP_ADAPTER.md",
    ),
    "C-408": (
        "docs/work/GENERATOR_VERIFIER_PROTOCOL.md",
        "schemas/verifier_result.schema.yaml",
    ),
    "C-409": (
        "docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md",
        "docs/work/RECOVERY_EVALUATION_OPERATIONS.md",
    ),
    "C-501": ("docs/research/app-server-protocol-observations.md",),
    "C-505": (
        "docs/work/SECURITY_THREAT_BOUNDARY.md",
        "docs/architecture/ADR-001-harness-boundary.md",
    ),
}

READY_EFFORT_ESTIMATES: Mapping[str, str] = {
    "W-211": "3–5 hours",
    "W-212": "4–8 hours",
    "C-405": "1.5–3 engineering days",
    "C-406": "2–4 engineering days",
    "C-408": "1–2 engineering days",
}

READY_EFFORT_HOURS: Mapping[str, tuple[float, float]] = {
    "W-211": (3.0, 5.0),
    "W-212": (4.0, 8.0),
    "C-405": (12.0, 24.0),
    "C-406": (16.0, 32.0),
    "C-408": (8.0, 16.0),
}


def _load_yaml(path: Path) -> Mapping[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"Expected a YAML mapping in {path}")
    return value


def _successful(value: object) -> bool:
    normalized = str(value).strip().upper()
    return any(word in normalized for word in SUCCESS_WORDS) and not any(
        word in normalized for word in FAILURE_WORDS
    )


def _task_ids_from_text(value: str) -> set[str]:
    ids = set(TASK_ID_PATTERN.findall(value.upper()))
    for prefix, first_text, last_text in RANGE_PATTERN.findall(value.upper()):
        first = int(first_text)
        last = int(last_text)
        if first <= last and last - first <= 50:
            ids.update(f"{prefix}-{number:03d}" for number in range(first, last + 1))
    return ids


def _status_values(value: object) -> Iterable[object]:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if str(key).lower() in {"status", "verdict", "result", "state"}:
                yield nested
            yield from _status_values(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _status_values(nested)


def _evidence_is_successful(path: Path) -> bool:
    try:
        data = _load_yaml(path)
    except (OSError, ValueError, yaml.YAMLError):
        return False
    return any(_successful(value) for value in _status_values(data))


def _evidence_task_ids(root: Path) -> set[str]:
    paths = [
        *sorted((root / "agent/state").glob("*result*.yaml")),
        *sorted((root / "validation").glob("*GATE*.yaml")),
        *sorted((root / "gate-records").glob("*.yaml")),
    ]
    completed: set[str] = set()
    for path in paths:
        if not _evidence_is_successful(path):
            continue
        completed.update(_task_ids_from_text(path.name))
        try:
            data = _load_yaml(path)
        except (OSError, ValueError, yaml.YAMLError):
            continue
        task_record = data.get("task")
        if isinstance(task_record, Mapping):
            declared_id = task_record.get("id")
            if declared_id is not None:
                completed.update(_task_ids_from_text(str(declared_id)))
        for key in ("task_id", "task_ids"):
            declared = data.get(key)
            if isinstance(declared, list):
                for item in declared:
                    completed.update(_task_ids_from_text(str(item)))
            elif declared is not None:
                completed.update(_task_ids_from_text(str(declared)))
    return completed


def _normalize_state_key(value: object) -> str:
    return str(value).strip().upper().replace("_", "-")


def _active_development_states(state: Mapping[str, Any]) -> dict[str, str]:
    upe_state = state.get("upe_state", {})
    if not isinstance(upe_state, Mapping):
        return {}
    active = upe_state.get("active_development", {})
    if not isinstance(active, Mapping):
        return {}

    states: dict[str, str] = {}
    for raw_task_id, record in active.items():
        raw_state = record.get("state", "") if isinstance(record, Mapping) else record
        states[_normalize_state_key(raw_task_id)] = _normalize_state_key(raw_state)
    return states


def _completed_task_ids(
    tasks: list[Mapping[str, Any]], state: Mapping[str, Any], root: Path
) -> set[str]:
    task_ids = {str(task["id"]) for task in tasks}
    completed = {str(task["id"]) for task in tasks if str(task.get("status", "")).lower() == "done"}
    must_status = state.get("upe_state", {}).get("must_status", {})
    if isinstance(must_status, Mapping):
        for raw_key, value in must_status.items():
            if not _successful(value):
                continue
            key = _normalize_state_key(raw_key)
            if key in task_ids:
                completed.add(key)
            completed.update(STATUS_ALIASES.get(str(raw_key), ()))

    completed.update(_evidence_task_ids(root) & task_ids)

    # Accepted downstream evidence proves that its canonical prerequisites were met.
    task_by_id = {str(task["id"]): task for task in tasks}
    pending = list(completed)
    while pending:
        task_id = pending.pop()
        task = task_by_id.get(task_id)
        if task is None:
            continue
        for dependency in task.get("dependencies", []):
            dependency_id = str(dependency)
            if dependency_id not in completed and dependency_id in task_by_id:
                completed.add(dependency_id)
                pending.append(dependency_id)
    return completed


def _git_value(root: Path, *arguments: str) -> str | None:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    value = completed.stdout.strip()
    return value if completed.returncode == 0 and value else None


def _repository_commit_exists(root: Path, head: str) -> bool:
    completed = subprocess.run(
        ["git", "cat-file", "-e", f"{head}^{{commit}}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def _valid_repository_head(head: object) -> bool:
    return isinstance(head, str) and re.fullmatch(r"[0-9a-f]{40}", head) is not None


def _valid_repository_values(head: object, branch: object) -> bool:
    return (
        _valid_repository_head(head)
        and isinstance(branch, str)
        and bool(branch)
        and branch != "unavailable"
        and not any(character.isspace() or ord(character) < 32 for character in branch)
    )


def _valid_repository_context(value: object) -> bool:
    return (
        isinstance(value, Mapping)
        and _valid_repository_values(value.get("head"), value.get("branch"))
        and value.get("context_status") in {"observed", "explicit", "preserved"}
    )


def _repository_context(
    root: Path,
    *,
    explicit_head: str | None,
    explicit_branch: str | None,
    previous: object,
) -> dict[str, str]:
    observed_head = _git_value(root, "rev-parse", "HEAD")
    observed_branch = _git_value(root, "branch", "--show-current")
    if _valid_repository_values(observed_head, observed_branch):
        return {
            "head": str(observed_head),
            "branch": str(observed_branch),
            "context_status": "observed",
        }

    if explicit_head is not None or explicit_branch is not None:
        if not _valid_repository_values(explicit_head, explicit_branch):
            raise ValueError("repository overrides require a 40-hex head and a non-empty branch")
        return {
            "head": str(explicit_head),
            "branch": str(explicit_branch),
            "context_status": "explicit",
        }

    if isinstance(previous, Mapping) and _valid_repository_values(
        previous.get("head"), previous.get("branch")
    ):
        return {
            "head": str(previous["head"]),
            "branch": str(previous["branch"]),
            "context_status": "preserved",
        }

    raise ValueError(
        "repository provenance is unavailable; no observed, explicit, or preserved context exists"
    )


def _origin_documents(task: Mapping[str, Any]) -> list[dict[str, str]]:
    task_id = str(task["id"])
    phase = str(task.get("phase", "unknown"))
    canonical_path = str(BACKLOG_PATH).replace("\\", "/")
    paths = [
        canonical_path,
        *TASK_DESIGN_SOURCES.get(task_id, PHASE_DESIGN_SOURCES.get(phase, ())),
    ]
    unique_paths = list(dict.fromkeys(paths))
    return [
        {
            "label": SOURCE_LABELS.get(path, Path(path).name),
            "path": path,
            "role": "Canonical task definition" if index == 0 else "Accepted design basis",
        }
        for index, path in enumerate(unique_paths)
    ]


def _rough_estimate(task: Mapping[str, Any]) -> str:
    task_id = str(task["id"])
    if task_id in READY_EFFORT_ESTIMATES:
        return READY_EFFORT_ESTIMATES[task_id]

    phase = str(task.get("phase", "unknown"))
    surface = str(task.get("surface", "none"))
    model_route = str(task.get("model_route", "not_applicable"))
    output_count = len(task.get("outputs", []))
    if surface.startswith("chatgpt_") or phase in {"0-research", "3-web-specification"}:
        return "4–8 hours"
    if model_route == "sol_max_or_highest_exposed":
        return "3–5 engineering days"
    if phase == "5-core-harness":
        return "2–4 engineering days" if output_count >= 3 else "1–2 engineering days"
    if phase == "6-app-server-recovery-security":
        return "2–4 engineering days"
    if phase == "7-tests-evals":
        return "1–3 engineering days"
    if phase == "8-release":
        return "1–2 engineering days"
    return "0.5–1 engineering day"


def _rough_hours(task: Mapping[str, Any]) -> tuple[float, float]:
    task_id = str(task["id"])
    if task_id in READY_EFFORT_HOURS:
        return READY_EFFORT_HOURS[task_id]

    phase = str(task.get("phase", "unknown"))
    surface = str(task.get("surface", "none"))
    model_route = str(task.get("model_route", "not_applicable"))
    output_count = len(task.get("outputs", []))
    if surface.startswith("chatgpt_") or phase in {"0-research", "3-web-specification"}:
        return (4.0, 8.0)
    if model_route == "sol_max_or_highest_exposed":
        return (24.0, 40.0)
    if phase == "5-core-harness":
        return (16.0, 32.0) if output_count >= 3 else (8.0, 16.0)
    if phase == "6-app-server-recovery-security":
        return (16.0, 32.0)
    if phase == "7-tests-evals":
        return (8.0, 24.0)
    if phase == "8-release":
        return (8.0, 16.0)
    return (4.0, 8.0)


def _planning(
    task: Mapping[str, Any],
    *,
    status: str,
    dependency_mode: str,
    incomplete_dependencies: list[str],
) -> dict[str, object]:
    if status == "complete":
        return {
            "estimate": None,
            "estimate_hours": None,
            "confidence": "not_applicable",
            "basis": "Completed work is not assigned a retrospective estimate.",
            "parallelizable_now": False,
            "parallel_note": "Already complete.",
            "blocked_by": [],
        }

    if status == "in_development":
        return {
            "estimate": None,
            "estimate_hours": None,
            "confidence": "not_applicable",
            "basis": "Locally accepted work is pending serialized repository delivery.",
            "parallelizable_now": False,
            "parallel_note": "In development; not a fresh-work recommendation.",
            "blocked_by": [],
        }

    parallelizable_now = dependency_mode == "independent_now" and not incomplete_dependencies
    if parallelizable_now:
        parallel_note = (
            "Can start from the current accepted baseline in an isolated branch/worktree; "
            "shared report and current-state bookkeeping must be integrated serially."
        )
    else:
        parallel_note = (
            f"Starts after {', '.join(incomplete_dependencies)}."
            if incomplete_dependencies
            else "Not selected for the current parallel frontier."
        )
    minimum_hours, maximum_hours = _rough_hours(task)
    return {
        "estimate": _rough_estimate(task),
        "estimate_hours": {"minimum": minimum_hours, "maximum": maximum_hours},
        "confidence": "rough",
        "basis": (
            "Planning range derived from surface, model route, output count, and escalation "
            "risk; excludes review, CI queue, and merge latency."
        ),
        "parallelizable_now": parallelizable_now,
        "parallel_note": parallel_note,
        "blocked_by": incomplete_dependencies,
    }


def _application(task: Mapping[str, Any], by_id: Mapping[str, Mapping[str, Any]]) -> str:
    scope = str(task.get("description", "No scope description recorded.")).rstrip(".")
    outputs = [str(item) for item in task.get("outputs", [])]
    dependents = [str(item) for item in task.get("dependents", [])]
    parts = [f"Operational effect: {scope}."]
    if outputs:
        output_summary = " · ".join(outputs[:3])
        suffix = f" · +{len(outputs) - 3} more" if len(outputs) > 3 else ""
        parts.append(f"Produces {output_summary}{suffix}.")
    if dependents:
        enabled = []
        for task_id in dependents[:5]:
            dependent = by_id.get(task_id)
            title = str(dependent.get("title")) if dependent is not None else task_id
            enabled.append(f"{task_id} ({title})")
        suffix = f" and {len(dependents) - 5} more" if len(dependents) > 5 else ""
        parts.append(f"Directly enables {', '.join(enabled)}{suffix}.")
    else:
        parts.append("No direct downstream package is recorded in the visible v0 route.")
    return " ".join(parts)


def _transitive_dependent_count(task_id: str, by_id: Mapping[str, Mapping[str, Any]]) -> int:
    seen: set[str] = set()
    pending = [str(item) for item in by_id[task_id].get("dependents", [])]
    while pending:
        dependent_id = pending.pop()
        if dependent_id in seen or dependent_id not in by_id:
            continue
        seen.add(dependent_id)
        pending.extend(str(item) for item in by_id[dependent_id].get("dependents", []))
    return len(seen)


def _format_engineering_days(minimum_hours: float, maximum_hours: float) -> str:
    minimum_days = minimum_hours / 8.0
    maximum_days = maximum_hours / 8.0
    if minimum_days.is_integer() and maximum_days.is_integer():
        return f"{int(minimum_days)}–{int(maximum_days)} engineering days"
    return f"{minimum_days:.1f}–{maximum_days:.1f} engineering days"


def _next_suggested_run(rendered: list[dict[str, Any]]) -> dict[str, object]:
    by_id = {str(task["id"]): task for task in rendered}
    ready = [
        task
        for task in rendered
        if task["status"] == "ready" and bool(task["planning"]["parallelizable_now"])
    ]
    ready.sort(
        key=lambda task: (
            -_transitive_dependent_count(str(task["id"]), by_id),
            -len(task["dependents"]),
            -int(bool(task["critical_path"])),
            int(task["order"]),
        )
    )

    output_owners: dict[str, list[str]] = {}
    for task in ready:
        for output in task["outputs"]:
            output_owners.setdefault(str(output), []).append(str(task["id"]))
    collisions = {output: owners for output, owners in output_owners.items() if len(owners) > 1}

    if len(ready) > 1 and not collisions:
        classification = "parallel_runs"
        classification_label = "Parallel runs"
    elif ready:
        classification = "sequential_runs"
        classification_label = "Sequential runs"
    else:
        classification = "sequential_runs"
        classification_label = "Sequential runs"

    task_ids = [str(task["id"]) for task in ready]
    runs = [
        {
            "label": f"Run {index}",
            "task_ids": [str(task["id"])],
            "surface": str(task["surface_label"]),
            "estimate": task["planning"]["estimate"],
            "application": str(task["application"]),
        }
        for index, task in enumerate(ready, start=1)
    ]

    blockers = [
        f"{task['id']} waits on {', '.join(task['incomplete_dependencies'])}"
        for task in rendered
        if task["status"] == "blocked"
        and any(dependency in task_ids for dependency in task["incomplete_dependencies"])
    ][:6]

    effort_ranges = [
        task["planning"]["estimate_hours"]
        for task in ready
        if isinstance(task["planning"]["estimate_hours"], Mapping)
    ]
    if effort_ranges:
        parallel_minimum = max(float(item["minimum"]) for item in effort_ranges)
        parallel_maximum = max(float(item["maximum"]) for item in effort_ranges)
        sequential_minimum = sum(float(item["minimum"]) for item in effort_ranges)
        sequential_maximum = sum(float(item["maximum"]) for item in effort_ranges)
        parallel_elapsed = (
            f"{_format_engineering_days(parallel_minimum, parallel_maximum)} "
            "plus serial integration"
        )
        sequential_elapsed = (
            f"about {_format_engineering_days(sequential_minimum, sequential_maximum)} "
            "plus integration"
        )
    else:
        parallel_elapsed = "No dependency-satisfied package is currently estimable."
        sequential_elapsed = parallel_elapsed

    if collisions:
        collision_text = "; ".join(
            f"{output}: {', '.join(owners)}" for output, owners in collisions.items()
        )
        scope_warning = f"Declared output collision requires serialization: {collision_text}."
    else:
        scope_warning = (
            "Declared task outputs do not collide, but shared AGENTS.md, mutable current-state "
            "records, result-frontier assertions, and the readiness report belong to one serial "
            "integration lane. Do not bundle independent work packages into one change."
        )

    if ready:
        lead = str(ready[0]["id"])
        rationale = (
            f"{len(ready)} packages have satisfied dependencies and disjoint declared outputs. "
            f"Start each as an isolated run; prioritize {lead} because it has the widest "
            "transitive downstream unlock in the live graph."
        )
    else:
        rationale = "No package is dependency-satisfied; complete the listed blockers first."

    return {
        "title": "Next suggested implementation run",
        "classification": classification,
        "classification_label": classification_label,
        "bundle_allowed": False,
        "task_ids": task_ids,
        "runs": runs,
        "rationale": rationale,
        "blockers": blockers,
        "scope_collisions": collisions,
        "scope_collision_warning": scope_warning,
        "elapsed_comparison": {
            "parallel": parallel_elapsed,
            "sequential": sequential_elapsed,
        },
        "handoff": {
            "label": "Live parallel execution handoff",
            "path": "handoffs/NEXT-FIVE-WORK-PACKAGES-PARALLEL-EXECUTION-HANDOFF.md",
        },
    }


def build_payload(
    root: Path,
    *,
    repository_context: Mapping[str, str],
    refreshed_at: str | None = None,
) -> dict[str, Any]:
    backlog = _load_yaml(root / BACKLOG_PATH)
    state = _load_yaml(root / STATE_PATH)
    raw_tasks = backlog.get("tasks")
    if not isinstance(raw_tasks, list) or not all(isinstance(task, Mapping) for task in raw_tasks):
        raise ValueError("Canonical backlog does not contain a valid tasks list")
    tasks = [task for task in raw_tasks if isinstance(task, Mapping)]
    completed = _completed_task_ids(tasks, state, root)
    active_states = _active_development_states(state)

    visible_tasks = [
        task
        for task in tasks
        if str(task.get("phase")) not in {"9-deferred", "3-local-work-optional"}
    ]
    visible_ids = {str(task["id"]) for task in visible_tasks}
    rendered: list[dict[str, Any]] = []
    for order, task in enumerate(visible_tasks):
        task_id = str(task["id"])
        dependencies = [str(item) for item in task.get("dependencies", [])]
        incomplete_dependencies = [item for item in dependencies if item not in completed]
        canonical_status = str(task.get("status", "planned")).lower()
        if task_id in completed:
            status = "complete"
            dependency_mode = "satisfied"
        elif active_states.get(task_id) == "LOCALLY-ACCEPTED-UNMERGED":
            status = "in_development"
            dependency_mode = "in_progress"
        elif canonical_status == "optional":
            status = "optional"
            dependency_mode = "independent" if not incomplete_dependencies else "sequential"
        elif canonical_status == "approval_required" and not incomplete_dependencies:
            status = "approval_required"
            dependency_mode = "independent_now"
        elif not incomplete_dependencies:
            status = "ready"
            dependency_mode = "independent_now"
        else:
            status = "blocked"
            dependency_mode = "sequential"

        surface = str(task.get("surface", "none"))
        model_route = str(task.get("model_route", "not_applicable"))
        rendered.append(
            {
                "id": task_id,
                "order": order,
                "title": str(task.get("title", task_id)),
                "phase": str(task.get("phase", "unknown")),
                "phase_label": PHASE_LABELS.get(str(task.get("phase")), str(task.get("phase"))),
                "status": status,
                "surface": surface,
                "surface_label": SURFACE_LABELS.get(surface, surface.replace("_", " ")),
                "model_route": model_route,
                "model_label": MODEL_LABELS.get(model_route, model_route),
                "dependency_mode": dependency_mode,
                "dependencies": dependencies,
                "incomplete_dependencies": incomplete_dependencies,
                "dependents": [],
                "critical_path": bool(task.get("critical_path", False)),
                "description": str(task.get("scope", "No scope description recorded.")),
                "application": "",
                "origin_documents": _origin_documents(task),
                "outputs": [str(item) for item in task.get("outputs", [])],
                "completion_evidence": [str(item) for item in task.get("completion_evidence", [])],
                "planning": _planning(
                    task,
                    status=status,
                    dependency_mode=dependency_mode,
                    incomplete_dependencies=incomplete_dependencies,
                ),
            }
        )

    by_id = {task["id"]: task for task in rendered}
    for task in rendered:
        for dependency in task["dependencies"]:
            if dependency in by_id:
                by_id[dependency]["dependents"].append(task["id"])
    for task in rendered:
        task["application"] = _application(task, by_id)

    delivery_tasks = [task for task in rendered if task["critical_path"]]
    completed_delivery = sum(task["status"] == "complete" for task in delivery_tasks)
    status_counts = {
        status: sum(task["status"] == status for task in rendered)
        for status in (
            "complete",
            "in_development",
            "ready",
            "blocked",
            "optional",
            "approval_required",
        )
    }
    model_counts = {
        model: sum(
            task["model_label"] == model and task["status"] != "complete" for task in rendered
        )
        for model in ("High", "Max", "Pro")
    }
    surface_counts = {
        surface: sum(
            task["surface_label"] == surface and task["status"] != "complete" for task in rendered
        )
        for surface in ("Web allowed", "Web · Pro required", "Local required")
    }

    return {
        "schema_version": "1.0",
        "refreshed_at": refreshed_at or datetime.now().astimezone().isoformat(timespec="seconds"),
        "repository": dict(repository_context),
        "summary": {
            "visible_tasks": len(rendered),
            "delivery_tasks": len(delivery_tasks),
            "completed_delivery": completed_delivery,
            "progress_percent": round(100 * completed_delivery / len(delivery_tasks))
            if delivery_tasks
            else 0,
            "deferred_post_v0": sum(str(task.get("phase")) == "9-deferred" for task in tasks),
            "status_counts": status_counts,
            "model_counts_remaining": model_counts,
            "surface_counts_remaining": surface_counts,
        },
        "tasks": rendered,
        "next_suggested_run": _next_suggested_run(rendered),
        "sources": {
            "backlog": str(BACKLOG_PATH).replace("\\", "/"),
            "state": str(STATE_PATH).replace("\\", "/"),
            "evidence": [
                "agent/state/*result*.yaml",
                "validation/*GATE*.yaml",
                "gate-records/*.yaml",
            ],
        },
        "notes": [
            (
                "Backlog status fields are historical; completion is derived from "
                "accepted current-state and gate/result evidence."
            ),
            (
                "Web tasks can prepare specifications and reviews, but only Local "
                "Codex tasks may inspect or mutate repository state."
            ),
            (
                "The v5.6.1 name remains a report framing for the repository's "
                "harness v0 line until formally ratified."
            ),
        ],
        "visible_task_ids": sorted(visible_ids),
    }


def _embedded_payload(html: str) -> dict[str, Any]:
    pattern = re.compile(
        re.escape(START_MARKER)
        + r"\s*<script[^>]*id=[\"']upe-task-state[\"'][^>]*>(.*?)</script>\s*"
        + re.escape(END_MARKER),
        re.DOTALL,
    )
    match = pattern.search(html)
    if match is None:
        raise ValueError("Report is missing the UPE task-state markers")
    value = json.loads(match.group(1))
    if not isinstance(value, dict):
        raise ValueError("Embedded UPE task state is not a JSON object")
    return value


def _replace_payload(html: str, payload: Mapping[str, Any]) -> str:
    newline = "\r\n" if "\r\n" in html else "\n"
    serialized = json.dumps(payload, ensure_ascii=False, indent=2).replace("<", "\\u003c")
    serialized = serialized.replace("\n", newline)
    replacement = (
        f"{START_MARKER}{newline}"
        f'<script type="application/json" id="upe-task-state">{newline}'
        f"{serialized}{newline}"
        f"</script>{newline}{END_MARKER}"
    )
    pattern = re.compile(re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER), re.DOTALL)
    updated, count = pattern.subn(replacement, html, count=1)
    if count != 1:
        raise ValueError("Report must contain exactly one replaceable UPE task-state block")
    return updated


def _freshness_state(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return state that can remain stable after the tracked report is committed.

    Repository branch and HEAD identify the context in which the report was
    refreshed.  They are intentionally excluded from freshness comparison:
    committing or merging the tracked report necessarily changes that identity
    without changing any capability or dependency evidence.
    """

    return {key: value for key, value in payload.items() if key != "repository"}


def _parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when embedded state is stale")
    parser.add_argument("--quiet", action="store_true", help="suppress the summary line")
    parser.add_argument("--report", type=Path, help="override the report path")
    parser.add_argument(
        "--repository-head",
        help="validated 40-hex repository head used only when local Git is unavailable",
    )
    parser.add_argument(
        "--repository-branch",
        help="repository branch paired with --repository-head",
    )
    parser.add_argument(
        "--allow-invalid-repository-context",
        action="store_true",
        help="diagnostic-only: ignore invalid embedded provenance during --check",
    )
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    options = _parse_args(arguments if arguments is not None else sys.argv[1:])
    root = Path(__file__).resolve().parents[1]
    report = options.report or root / REPORT_NAME
    if not report.is_absolute():
        report = root / report
    html = report.read_bytes().decode("utf-8")
    existing = _embedded_payload(html)
    existing_repository = existing.get("repository")
    if (
        options.check
        and not options.allow_invalid_repository_context
        and not _valid_repository_context(existing_repository)
    ):
        print(
            "FAIL capability readiness report repository provenance is invalid",
            file=sys.stderr,
        )
        return 1
    observed_head = _git_value(root, "rev-parse", "HEAD")
    if (
        options.check
        and not options.allow_invalid_repository_context
        and _valid_repository_head(observed_head)
        and isinstance(existing_repository, Mapping)
        and not _repository_commit_exists(root, str(existing_repository["head"]))
    ):
        print(
            "FAIL capability readiness report repository head does not resolve to a commit",
            file=sys.stderr,
        )
        return 1
    if options.allow_invalid_repository_context and not options.check:
        print(
            "FAIL --allow-invalid-repository-context is diagnostic-only and requires --check",
            file=sys.stderr,
        )
        return 1
    try:
        repository_context = _repository_context(
            root,
            explicit_head=options.repository_head,
            explicit_branch=options.repository_branch,
            previous=existing_repository,
        )
    except ValueError as error:
        if not (options.check and options.allow_invalid_repository_context):
            print(f"FAIL {error}", file=sys.stderr)
            return 1
        repository_context = (
            dict(existing_repository) if isinstance(existing_repository, Mapping) else {}
        )
    refreshed_at = str(existing.get("refreshed_at", "")) if options.check else None
    expected = build_payload(
        root,
        repository_context=repository_context,
        refreshed_at=refreshed_at,
    )

    if options.check:
        if _freshness_state(existing) != _freshness_state(expected):
            print(
                "FAIL capability readiness report is stale; run "
                "`uv run python scripts/update_capability_readiness_report.py`",
                file=sys.stderr,
            )
            return 1
        if not options.quiet:
            print("PASS capability readiness report state is current")
        return 0

    updated = _replace_payload(html, expected)
    report.write_bytes(updated.encode("utf-8"))
    if not options.quiet:
        summary = expected["summary"]
        print(
            "PASS refreshed capability readiness report: "
            f"{summary['completed_delivery']}/{summary['delivery_tasks']} "
            "critical-path tasks complete; "
            f"{summary['status_counts']['ready']} ready now"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
