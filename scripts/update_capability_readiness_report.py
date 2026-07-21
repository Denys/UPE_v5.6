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


def _git_value(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip() if completed.returncode == 0 else "unavailable"


def build_payload(root: Path, *, refreshed_at: str | None = None) -> dict[str, Any]:
    backlog = _load_yaml(root / BACKLOG_PATH)
    state = _load_yaml(root / STATE_PATH)
    raw_tasks = backlog.get("tasks")
    if not isinstance(raw_tasks, list) or not all(isinstance(task, Mapping) for task in raw_tasks):
        raise ValueError("Canonical backlog does not contain a valid tasks list")
    tasks = [task for task in raw_tasks if isinstance(task, Mapping)]
    completed = _completed_task_ids(tasks, state, root)

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
                "outputs": [str(item) for item in task.get("outputs", [])],
                "completion_evidence": [str(item) for item in task.get("completion_evidence", [])],
            }
        )

    by_id = {task["id"]: task for task in rendered}
    for task in rendered:
        for dependency in task["dependencies"]:
            if dependency in by_id:
                by_id[dependency]["dependents"].append(task["id"])

    delivery_tasks = [task for task in rendered if task["critical_path"]]
    completed_delivery = sum(task["status"] == "complete" for task in delivery_tasks)
    status_counts = {
        status: sum(task["status"] == status for task in rendered)
        for status in ("complete", "ready", "blocked", "optional", "approval_required")
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
        "repository": {
            "head": _git_value(root, "rev-parse", "HEAD"),
            "branch": _git_value(root, "branch", "--show-current"),
        },
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


def _parse_args(arguments: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail when embedded state is stale")
    parser.add_argument("--quiet", action="store_true", help="suppress the summary line")
    parser.add_argument("--report", type=Path, help="override the report path")
    return parser.parse_args(arguments)


def main(arguments: list[str] | None = None) -> int:
    options = _parse_args(arguments if arguments is not None else sys.argv[1:])
    root = Path(__file__).resolve().parents[1]
    report = options.report or root / REPORT_NAME
    if not report.is_absolute():
        report = root / report
    html = report.read_bytes().decode("utf-8")
    existing = _embedded_payload(html)
    refreshed_at = str(existing.get("refreshed_at", "")) if options.check else None
    expected = build_payload(root, refreshed_at=refreshed_at)

    if options.check:
        if existing != expected:
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
