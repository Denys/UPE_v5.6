from __future__ import annotations

import importlib.util
import json
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "UPE_5.6.0_to_5.6.1_capability_readiness_report_2026-07-19.html"
UPDATER = ROOT / "scripts/update_capability_readiness_report.py"
PROJECT_INSTRUCTIONS = ROOT / "AGENTS.md"


def _updater_module() -> Any:
    spec = importlib.util.spec_from_file_location("upe_capability_updater_test", UPDATER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def _temporary_report(tmp_path: Path, payload: dict[str, object]) -> Path:
    html = REPORT.read_text(encoding="utf-8")
    replacement = (
        '<script type="application/json" id="upe-task-state">\n'
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
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
    return temporary_report


def _check_report(report: Path, *extra_arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(UPDATER),
            "--check",
            "--quiet",
            "--report",
            str(report),
            *extra_arguments,
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


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
    repository = embedded["repository"]
    assert isinstance(repository, dict)
    changed["repository"] = {
        "head": repository["head"],
        "branch": "codex/post-refresh-commit",
        "context_status": "observed",
    }
    completed = _check_report(_temporary_report(tmp_path, changed))

    assert completed.returncode == 0, completed.stderr


def test_repository_identity_rejects_nonexistent_commit_when_git_is_available(
    tmp_path: Path,
) -> None:
    embedded = _payload()
    changed = deepcopy(embedded)
    changed["repository"] = {
        "head": "0" * 40,
        "branch": "codex/fabricated-context",
        "context_status": "observed",
    }
    temporary_report = _temporary_report(tmp_path, changed)
    module = _updater_module()

    with (
        patch.object(module, "_git_value", side_effect=["3" * 40, "main"]),
        patch.object(module, "_repository_commit_exists", return_value=False),
    ):
        result = module.main(["--check", "--quiet", "--report", str(temporary_report)])

    assert result == 1


def test_repository_identity_rejects_nonexistent_commit_in_detached_checkout(
    tmp_path: Path,
) -> None:
    embedded = _payload()
    changed = deepcopy(embedded)
    changed["repository"] = {
        "head": "0" * 40,
        "branch": "codex/fabricated-context",
        "context_status": "observed",
    }
    temporary_report = _temporary_report(tmp_path, changed)
    module = _updater_module()

    with (
        patch.object(module, "_git_value", side_effect=["3" * 40, None]),
        patch.object(module, "_repository_commit_exists", return_value=False),
    ):
        result = module.main(["--check", "--quiet", "--report", str(temporary_report)])

    assert result == 1


def test_repository_check_accepts_unreachable_source_when_report_is_in_head(
    tmp_path: Path,
) -> None:
    embedded = _payload()
    temporary_report = _temporary_report(tmp_path, embedded)
    module = _updater_module()

    with (
        patch.object(
            module,
            "_git_value",
            side_effect=["3" * 40, "3" * 40, None],
        ),
        patch.object(module, "_repository_commit_exists", return_value=False),
        patch.object(module, "_report_matches_head", return_value=True),
    ):
        result = module.main(["--check", "--quiet", "--report", str(temporary_report)])

    assert result == 0


def test_repository_refresh_rejects_nonexistent_explicit_head_before_write(
    tmp_path: Path,
) -> None:
    temporary_report = _temporary_report(tmp_path, _payload())
    before = temporary_report.read_bytes()
    module = _updater_module()

    with (
        patch.object(module, "_git_value", side_effect=["3" * 40, "3" * 40, None]),
        patch.object(module, "_repository_commit_exists", return_value=False),
    ):
        result = module.main(
            [
                "--quiet",
                "--report",
                str(temporary_report),
                "--repository-head",
                "0" * 40,
                "--repository-branch",
                "codex/fabricated-context",
            ]
        )

    assert result == 1
    assert temporary_report.read_bytes() == before


def test_repository_refresh_rejects_nonexistent_preserved_head_before_write(
    tmp_path: Path,
) -> None:
    temporary_report = _temporary_report(tmp_path, _payload())
    before = temporary_report.read_bytes()
    module = _updater_module()

    with (
        patch.object(module, "_git_value", side_effect=["3" * 40, "3" * 40, None]),
        patch.object(module, "_repository_commit_exists", return_value=False),
    ):
        result = module.main(["--quiet", "--report", str(temporary_report)])

    assert result == 1
    assert temporary_report.read_bytes() == before


def test_repository_identity_fails_closed_when_provenance_is_invalid(tmp_path: Path) -> None:
    embedded = _payload()
    changed = deepcopy(embedded)
    changed["repository"] = {
        "head": "unavailable",
        "branch": "unavailable",
        "context_status": "observed",
    }

    completed = _check_report(_temporary_report(tmp_path, changed))

    assert completed.returncode == 1
    assert "repository provenance is invalid" in completed.stderr


def test_invalid_repository_context_override_is_diagnostic_only(tmp_path: Path) -> None:
    embedded = _payload()
    changed = deepcopy(embedded)
    changed["repository"] = {
        "head": "unavailable",
        "branch": "unavailable",
    }

    completed = _check_report(
        _temporary_report(tmp_path, changed),
        "--allow-invalid-repository-context",
    )

    assert completed.returncode == 0, completed.stderr


def test_repository_context_uses_explicit_then_preserved_when_git_is_unavailable() -> None:
    module = _updater_module()
    resolver = module._repository_context

    with patch.object(module, "_git_value", side_effect=["3" * 40, "main"]):
        observed = resolver(
            ROOT,
            explicit_head="1" * 40,
            explicit_branch="codex/ignored-explicit-context",
            previous={"head": "2" * 40, "branch": "preserved"},
        )

    with patch.object(module, "_git_value", return_value=None):
        explicit = resolver(
            ROOT,
            explicit_head="1" * 40,
            explicit_branch="codex/explicit-context",
            previous=None,
        )
        preserved = resolver(
            ROOT,
            explicit_head=None,
            explicit_branch=None,
            previous={"head": "2" * 40, "branch": "main"},
        )
        with pytest.raises(ValueError, match="repository provenance is unavailable"):
            resolver(
                ROOT,
                explicit_head=None,
                explicit_branch=None,
                previous={"head": "unavailable", "branch": "unavailable"},
            )

    assert observed == {
        "head": "3" * 40,
        "branch": "main",
        "context_status": "observed",
    }
    assert explicit["context_status"] == "explicit"
    assert preserved == {
        "head": "2" * 40,
        "branch": "main",
        "context_status": "preserved",
    }


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
    assert tasks["C-409"]["status"] == "complete"
    assert tasks["C-409"]["dependency_mode"] == "satisfied"
    assert tasks["C-409"]["incomplete_dependencies"] == []
    assert tasks["C-410"]["status"] == "complete"
    assert tasks["C-410"]["dependency_mode"] == "satisfied"
    assert tasks["C-410"]["incomplete_dependencies"] == []
    assert tasks["C-501"]["status"] == "complete"
    assert tasks["C-501"]["dependency_mode"] == "satisfied"
    assert tasks["C-501"]["incomplete_dependencies"] == []
    assert tasks["C-502"]["status"] == "blocked"
    assert tasks["C-502"]["dependency_mode"] == "sequential"
    assert tasks["C-502"]["incomplete_dependencies"] == []
    assert tasks["C-502"]["execution_gate"] == "PR_26_merged_and_exact_head_reviewed"
    assert tasks["C-505"]["status"] == "complete"
    assert tasks["C-505"]["dependency_mode"] == "satisfied"
    assert tasks["C-505"]["incomplete_dependencies"] == []


def test_execution_gate_is_derived_from_persisted_field_not_state_label() -> None:
    module = _updater_module()
    backlog = module._load_yaml(ROOT / module.BACKLOG_PATH)
    state = deepcopy(module._load_yaml(ROOT / module.STATE_PATH))
    c502 = state["upe_state"]["active_development"]["C-502"]
    c502["state"] = "RENAMED_AUTHORIZATION_STATE"

    original_load_yaml = module._load_yaml

    def load_with_renamed_state(path: Path) -> dict[str, Any]:
        if path == ROOT / module.BACKLOG_PATH:
            return cast(dict[str, Any], backlog)
        if path == ROOT / module.STATE_PATH:
            return cast(dict[str, Any], state)
        return cast(dict[str, Any], original_load_yaml(path))

    with patch.object(module, "_load_yaml", side_effect=load_with_renamed_state):
        payload = module.build_payload(
            ROOT,
            repository_context={
                "head": "1" * 40,
                "branch": "codex/execution-gate-regression",
                "context_status": "explicit",
            },
            refreshed_at="2026-07-28T00:00:00+00:00",
        )

    tasks_value = payload["tasks"]
    assert isinstance(tasks_value, list)
    tasks = {task["id"]: task for task in tasks_value if isinstance(task, dict)}
    assert tasks["C-502"]["status"] == "blocked"
    assert tasks["C-502"]["execution_gate"] == "PR_26_merged_and_exact_head_reviewed"
    assert tasks["C-502"]["planning"]["parallelizable_now"] is False


@pytest.mark.parametrize("overall", ["FAIL", "INSUFFICIENT_EVIDENCE"])
def test_partial_pass_does_not_complete_failed_evidence(overall: str) -> None:
    module = _updater_module()
    evidence = {
        "status": overall,
        "criteria": [
            {"id": "contract", "verdict": "PASS"},
            {"id": "live-smoke", "verdict": overall},
        ],
    }

    with patch.object(module, "_load_yaml", return_value=evidence):
        assert module._evidence_is_successful(Path("validation/C-502-GATE.yaml")) is False


@pytest.mark.parametrize(
    ("gate_status", "expected_complete"),
    [
        ("FAIL", False),
        ("INSUFFICIENT_EVIDENCE", False),
        ("PASS", True),
    ],
)
def test_authoritative_gate_controls_result_completion(
    tmp_path: Path, gate_status: str, expected_complete: bool
) -> None:
    module = _updater_module()
    result_path = tmp_path / "agent/state/C-502-result.yaml"
    gate_path = tmp_path / "validation/C-502-GATE.yaml"
    (tmp_path / "gate-records").mkdir()
    result_path.parent.mkdir(parents=True)
    gate_path.parent.mkdir()
    result_path.write_text("status: PASS\n", encoding="utf-8")
    gate_path.write_text(f"status: {gate_status}\n", encoding="utf-8")

    completed = module._evidence_task_ids(tmp_path)

    assert ("C-502" in completed) is expected_complete


@pytest.mark.parametrize(
    ("gate_status", "expected_complete"),
    [
        (None, False),
        ("FAIL", False),
        ("INSUFFICIENT_EVIDENCE", False),
        ("PASS", True),
    ],
)
def test_required_gate_is_applied_after_every_completion_source(
    tmp_path: Path, gate_status: str | None, expected_complete: bool
) -> None:
    module = _updater_module()
    handoff_path = tmp_path / "handoffs/C-502.yaml"
    result_path = tmp_path / "agent/state/C-502-result.yaml"
    gate_path = tmp_path / "validation/C-502-GATE.yaml"
    (tmp_path / "gate-records").mkdir()
    handoff_path.parent.mkdir()
    result_path.parent.mkdir(parents=True)
    gate_path.parent.mkdir()
    handoff_path.write_text(
        "outputs:\n  - output_id: OUT-C502-gate\n    location: validation/C-502-GATE.yaml\n",
        encoding="utf-8",
    )
    result_path.write_text("status: PASS\n", encoding="utf-8")
    if gate_status is not None:
        gate_path.write_text(f"status: {gate_status}\n", encoding="utf-8")
    state = {
        "upe_state": {
            "active_development": {
                "C-502": {
                    "state": "ATTEMPT_COMPLETE",
                    "handoff": "handoffs/C-502.yaml",
                }
            },
            "must_status": {"C-502": "PASS"},
        }
    }
    tasks = [{"id": "C-502", "status": "done", "dependencies": []}]

    completed = module._completed_task_ids(tasks, state, tmp_path)

    assert ("C-502" in completed) is expected_complete


def test_c501_next_actions_preserve_c502_execution_gate() -> None:
    for relative_path in ("agent/state/C-501-result.yaml", "validation/C-501-GATE.yaml"):
        record = (ROOT / relative_path).read_text(encoding="utf-8")
        assert "next_action_gate: PR_26_merged_and_exact_head_reviewed" in record
        assert "Only after PR 26 is merged and its exact reviewed content is present" in record


def test_c502_handoff_resolves_mutable_inputs_from_post_merge_main() -> None:
    handoff = (ROOT / "handoffs/C-502-BOUNDED-LIVE-SMOKE-RERUN-2026-07-28.yaml").read_text(
        encoding="utf-8"
    )
    authoritative_inputs = handoff.split("authoritative_inputs:\n", 1)[1].split("\nscope:\n", 1)[0]

    assert "agent/reconcile-c501-c502@79589b4d37526da84485a7321764fd38ea4688cb" not in (
        authoritative_inputs
    )
    assert (
        authoritative_inputs.count(
            "version_or_ref: post-merge-main@contains-PR-26-reviewed-content"
        )
        == 5
    )
    assert "without\n      requiring feature-branch SHA ancestry after a squash merge" in handoff


def test_visible_report_narrative_matches_current_frontier() -> None:
    html = REPORT.read_text(encoding="utf-8")

    assert "C‑301…C‑410 plus C‑501 and C‑505 are implemented and tested locally" in html
    assert "C‑502 is authorized but remains blocked until PR #26 integration" in html
    assert "C‑502 can now start independently alongside W‑211 and W‑212" not in html
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
    }
    for task_id, estimate in expected_estimates.items():
        planning = tasks[task_id]["planning"]
        assert planning["estimate"] == estimate
        assert planning["parallelizable_now"] is True
        assert planning["confidence"] == "rough"

    c502_planning = tasks["C-502"]["planning"]
    assert c502_planning["estimate"] == "2–4 engineering days"
    assert c502_planning["parallelizable_now"] is False
    assert c502_planning["blocked_by"] == ["PR_26_merged_and_exact_head_reviewed"]
    assert c502_planning["parallel_note"] == (
        "Blocked by execution gate PR_26_merged_and_exact_head_reviewed."
    )

    assert tasks["C-407"]["planning"]["estimate"] is None
    assert tasks["C-407"]["planning"]["parallelizable_now"] is False
    assert tasks["C-409"]["planning"]["estimate"] is None
    assert tasks["C-409"]["planning"]["blocked_by"] == []
    assert tasks["C-505"]["planning"]["estimate"] is None
    assert tasks["C-505"]["planning"]["parallelizable_now"] is False
    assert tasks["C-505"]["planning"]["blocked_by"] == []
    assert tasks["C-501"]["planning"]["estimate"] is None
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
    assert "const taskStatusLabel = task => task.execution_gate" in html
    assert '"Blocked by execution gate"' in html
    assert "const taskWaitingOn = task => task.execution_gate" in html
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
    assert recommendation["task_ids"] == ["W-211", "W-212"]
    assert [run["task_ids"] for run in recommendation["runs"]] == [
        ["W-211"],
        ["W-212"],
    ]
    assert "C-502 waits on PR_26_merged_and_exact_head_reviewed" in recommendation["blockers"]
    assert "shared" in recommendation["scope_collision_warning"].lower()
    assert recommendation["elapsed_comparison"]["parallel"] == (
        "0.5–1.0 engineering days plus serial integration"
    )
    assert recommendation["elapsed_comparison"]["sequential"] == (
        "about 0.9–1.6 engineering days plus integration"
    )
    assert (ROOT / recommendation["handoff"]["path"]).is_file()


def test_project_instructions_require_report_refresh_for_every_merged_wp() -> None:
    instructions = PROJECT_INSTRUCTIONS.read_text(encoding="utf-8")

    assert "## Mandatory merged-WP report directive" in instructions
    assert "Every work package that becomes both completed and merged MUST update" in instructions
    assert "scripts/update_capability_readiness_report.py" in instructions
    assert "One coordinator serializes those files" in instructions


def test_project_instructions_require_verified_state_persistence() -> None:
    instructions = PROJECT_INSTRUCTIONS.read_text(encoding="utf-8")

    assert "## Mandatory engineering state persistence" in instructions
    assert "docs/research/research-state.yaml" in instructions
    assert "agent/state/" in instructions
    assert "docs/architecture/" in instructions
    assert "Preserve prior attempts and hashes" in instructions
    assert "run its parser/reference/freshness checks" in instructions
    assert "STATUS: INCOMPLETE — state persistence missing" in instructions
    assert "commit, push, PR modification, merge" in instructions
