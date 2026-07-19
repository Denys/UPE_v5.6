"""CLI tests for deterministic Draft 2020-12 validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_schema.py"


def run_validator(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_accepted_examples_pass() -> None:
    result = run_validator()

    assert result.returncode == 0, result.stderr
    assert "PASS schema validation: 6 instance(s)" in result.stdout


@pytest.mark.parametrize(
    ("mutation", "expected_rule", "expected_detail"),
    [
        ("required", "required", "name"),
        ("type", "type", "string"),
        ("enum", "enum", "allowed"),
        ("additional", "additionalProperties", "unexpected"),
        ("format", "format", "uri"),
    ],
)
def test_invalid_examples_fail_nonzero_with_actionable_message(
    mutation: str, expected_rule: str, expected_detail: str
) -> None:
    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["name", "mode", "source"],
        "properties": {
            "name": {"type": "string"},
            "mode": {"enum": ["allowed"]},
            "source": {"type": "string", "format": "uri"},
        },
    }
    instance: dict[str, object] = {
        "name": "valid",
        "mode": "allowed",
        "source": "https://example.test/source",
    }
    if mutation == "required":
        del instance["name"]
    elif mutation == "type":
        instance["name"] = []
    elif mutation == "enum":
        instance["mode"] = "denied"
    elif mutation == "additional":
        instance["unexpected"] = True
    elif mutation == "format":
        instance["source"] = "not a URI"

    with tempfile.TemporaryDirectory(prefix="c306-schema-", dir=ROOT / ".pytest_cache") as tmp:
        tmp_path = Path(tmp)
        schema_path = tmp_path / "schema.json"
        instance_path = tmp_path / "instance.json"
        write_json(schema_path, schema)
        write_json(instance_path, instance)

        result = run_validator(
            "--root",
            str(tmp_path),
            "--schema",
            schema_path.name,
            "--instance",
            instance_path.name,
        )

    assert result.returncode == 1
    assert "FAIL schema validation" in result.stderr
    assert f"rule: {expected_rule}" in result.stderr
    assert expected_detail in result.stderr
