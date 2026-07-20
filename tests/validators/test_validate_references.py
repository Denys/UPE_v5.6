"""CLI tests for local-reference and cross-record validation."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_references.py"
ACCEPTED_EXAMPLES = ROOT / "examples" / "specifications"


def run_validator(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def replace_once(path: Path, old: str, new: str) -> None:
    original = path.read_text(encoding="utf-8")
    assert old in original
    path.write_text(original.replace(old, new, 1), encoding="utf-8")


def test_accepted_references_and_identities_pass() -> None:
    result = run_validator()

    assert result.returncode == 0, result.stderr
    assert "PASS reference validation" in result.stdout


@pytest.mark.parametrize(
    ("filename", "old", "new", "expected"),
    [
        (
            "goal_contract.example.yaml",
            "ref: docs/work/",
            "ref: ../outside",
            "is unsafe",
        ),
        (
            "capability_execution_record.example.yaml",
            "ref: https://github.com/Denys/UPE_v5.6",
            "ref: not a URI",
            "not a valid absolute URI",
        ),
        (
            "capability_execution_record.example.yaml",
            "ref: chatgpt_work_harness_implementation_routing_2026-07-18/"
            "harness_implementation_backlog.yaml",
            "ref: missing/target.yaml",
            "does not exist",
        ),
        (
            "capability_execution_record.example.yaml",
            "goal_id: goal.w200.specification",
            "goal_id: goal.wrong",
            "does not match goal_contract.example.yaml goal_id",
        ),
        (
            "capability_execution_record.example.yaml",
            "run_id: run.w200.2026-07-19",
            "run_id: run.wrong",
            "does not match work-loop run_id",
        ),
    ],
)
def test_invalid_reference_or_identity_fails_nonzero(
    filename: str, old: str, new: str, expected: str, tmp_path: Path
) -> None:
    examples = tmp_path / "specifications"
    shutil.copytree(ACCEPTED_EXAMPLES, examples)
    replace_once(examples / filename, old, new)

    result = run_validator("--root", str(ROOT), "--examples-dir", str(examples))

    assert result.returncode == 1
    assert "FAIL reference validation" in result.stderr
    assert expected in result.stderr
