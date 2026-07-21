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
    assert tasks["C-405"]["status"] == "ready"
    assert tasks["C-406"]["status"] == "ready"
    assert tasks["C-404"]["dependency_mode"] == "satisfied"
    assert tasks["C-407"]["status"] == "blocked"
    assert tasks["C-407"]["dependency_mode"] == "sequential"
    assert tasks["C-407"]["incomplete_dependencies"] == ["C-406"]
    assert tasks["C-408"]["status"] == "ready"
    assert tasks["C-408"]["dependency_mode"] == "independent_now"
    assert tasks["C-408"]["incomplete_dependencies"] == []


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
