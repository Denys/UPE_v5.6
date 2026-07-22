from __future__ import annotations

import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "UPE_5.6.0_to_5.6.1_capability_readiness_report_2026-07-19.html"
UPDATER = ROOT / "scripts/update_capability_readiness_report.py"
PROJECT_INSTRUCTIONS = ROOT / "AGENTS.md"


def _payload() -> dict[str, object]:
    html = REPORT.read_text(encoding="utf-8")
    match = re.search(
        r'<script type="application/json" id="upe-task-state">\s*(.*?)\s*</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    value = json.loads(match.group(1))
    assert isinstance(value, dict)
    return value


def test_capability_readiness_report_state_is_current() -> None:
    completed = subprocess.run(
        [sys.executable, str(UPDATER), "--check", "--quiet"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr


def test_repository_identity_is_refresh_context_not_freshness_state(tmp_path: Path) -> None:
    embedded = _payload()
    changed = deepcopy(embedded)
    changed["repository"] = {
        "head": "0" * 40,
        "branch": "codex/post-refresh-commit",
    }
    html = REPORT.read_text(encoding="utf-8")
    replacement = (
        '<script type="application/json" id="upe-task-state">\n'
        f"{json.dumps(changed, ensure_ascii=False, indent=2)}\n"
        "</script>"
    )
    changed_html, count = re.subn(
        r'<script type="application/json" id="upe-task-state">.*?</script>',
        replacement,
        html,
        count=1,
        flags=re.DOTALL,
    )
    assert count == 1
    temporary_report = tmp_path / REPORT.name
    temporary_report.write_text(changed_html, encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(UPDATER),
            "--check",
            "--quiet",
            "--report",
            str(temporary_report),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr


def test_capability_readiness_report_exposes_current_dependency_frontier() -> None:
    payload = _payload()
    tasks_value = payload["tasks"]
    assert isinstance(tasks_value, list)
    tasks = {task["id"]: task for task in tasks_value if isinstance(task, dict)}

    assert tasks["C-403"]["status"] == "complete"
    assert tasks["C-404"]["status"] == "complete"
    assert tasks["C-405"]["status"] == "complete"
    assert tasks["C-406"]["status"] == "complete"
    assert tasks["C-404"]["dependency_mode"] == "satisfied"
    assert tasks["C-407"]["status"] == "complete"
    assert tasks["C-407"]["dependency_mode"] == "satisfied"
    assert tasks["C-407"]["incomplete_dependencies"] == []
    assert tasks["C-408"]["status"] == "complete"
    assert tasks["C-408"]["dependency_mode"] == "satisfied"
    assert tasks["C-408"]["incomplete_dependencies"] == []
    assert tasks["C-409"]["status"] == "ready"
    assert tasks["C-409"]["dependency_mode"] == "independent_now"
    assert tasks["C-409"]["incomplete_dependencies"] == []
    assert tasks["C-501"]["status"] == "complete"
    assert tasks["C-501"]["dependency_mode"] == "satisfied"
    assert tasks["C-501"]["incomplete_dependencies"] == []
    assert tasks["C-505"]["status"] == "complete"
    assert tasks["C-505"]["dependency_mode"] == "satisfied"
    assert tasks["C-505"]["incomplete_dependencies"] == []


def test_visible_report_narrative_matches_current_frontier() -> None:
    html = REPORT.read_text(encoding="utf-8")

    assert "C‑301…C‑408 plus C‑501 and C‑505 are implemented and tested locally" in html
    assert "W‑211, W‑212 and C‑409 can now start independently" in html
    assert "C‑501 schema-bound Codex App Server adapter" in html
    assert "C‑301…C‑404 are implemented and tested" not in html


def test_capability_readiness_report_labels_surface_and_model_requirements() -> None:
    payload = _payload()
    tasks_value = payload["tasks"]
    assert isinstance(tasks_value, list)
    tasks = {task["id"]: task for task in tasks_value if isinstance(task, dict)}

    assert tasks["C-404"]["surface_label"] == "Local required"
    assert tasks["C-404"]["model_label"] == "High"
    assert tasks["C-501"]["model_label"] == "Max"
    assert tasks["P-101"]["surface_label"] == "Web · Pro required"
    assert tasks["P-101"]["model_label"] == "Pro"
    assert tasks["W-211"]["surface_label"] == "Web allowed"


def test_capability_readiness_report_explains_origin_application_and_planning() -> None:
    payload = _payload()
    tasks_value = payload["tasks"]
    assert isinstance(tasks_value, list)
    tasks = {task["id"]: task for task in tasks_value if isinstance(task, dict)}

    for task in tasks.values():
        assert isinstance(task["application"], str) and task["application"]
        origins = task["origin_documents"]
        assert isinstance(origins, list) and origins
        assert origins[0]["path"].endswith("harness_implementation_backlog.yaml")
        for origin in origins:
            assert (ROOT / origin["path"]).is_file()

    expected_estimates = {
        "W-211": "3–5 hours",
        "W-212": "4–8 hours",
        "C-409": "1–2 engineering days",
    }
    for task_id, estimate in expected_estimates.items():
        planning = tasks[task_id]["planning"]
        assert planning["estimate"] == estimate
        assert planning["parallelizable_now"] is True
        assert planning["confidence"] == "rough"

    assert tasks["C-407"]["planning"]["estimate"] is None
    assert tasks["C-407"]["planning"]["parallelizable_now"] is False
    assert tasks["C-409"]["planning"]["blocked_by"] == []
    assert tasks["C-505"]["planning"]["blocked_by"] == []
    assert tasks["C-501"]["planning"]["estimate"] is None
    assert tasks["C-505"]["planning"]["estimate"] is None
    assert tasks["C-505"]["planning"]["parallelizable_now"] is False
    assert tasks["C-404"]["planning"]["estimate"] is None
    assert tasks["C-405"]["planning"]["estimate"] is None
    assert tasks["C-406"]["planning"]["estimate"] is None
    assert tasks["C-408"]["planning"]["estimate"] is None


def test_capability_readiness_report_has_theme_and_click_details_ui() -> None:
    html = REPORT.read_text(encoding="utf-8")

    assert 'id="theme-toggle"' in html
    assert 'id="task-detail-dialog"' in html
    assert 'id="task-detail-origin"' in html
    assert 'id="task-detail-application"' in html
    assert 'id="task-detail-planning"' in html
    assert 'id="next-run-card"' in html
    assert 'id="next-run-classification"' in html
    assert 'id="next-run-runs"' in html
    assert "showModal()" in html
    assert "Click for full details" in html


def test_capability_readiness_report_generates_next_parallel_run() -> None:
    payload = _payload()
    recommendation = payload["next_suggested_run"]
    assert isinstance(recommendation, dict)

    assert recommendation["classification"] == "parallel_runs"
    assert recommendation["classification_label"] == "Parallel runs"
    assert recommendation["bundle_allowed"] is False
    assert recommendation["task_ids"] == ["C-409", "W-211", "W-212"]
    assert [run["task_ids"] for run in recommendation["runs"]] == [
        ["C-409"],
        ["W-211"],
        ["W-212"],
    ]
    assert "C-502 waits on C-409" in recommendation["blockers"]
    assert "shared" in recommendation["scope_collision_warning"].lower()
    assert recommendation["elapsed_comparison"]["parallel"] == (
        "1–2 engineering days plus serial integration"
    )
    assert recommendation["elapsed_comparison"]["sequential"] == (
        "about 1.9–3.6 engineering days plus integration"
    )
    assert (ROOT / recommendation["handoff"]["path"]).is_file()


def test_project_instructions_require_report_refresh_for_every_merged_wp() -> None:
    instructions = PROJECT_INSTRUCTIONS.read_text(encoding="utf-8")

    assert "## Mandatory merged-WP report directive" in instructions
    assert "Every work package that becomes both completed and merged MUST update" in instructions
    assert "scripts/update_capability_readiness_report.py" in instructions
    assert "One coordinator serializes those files" in instructions
