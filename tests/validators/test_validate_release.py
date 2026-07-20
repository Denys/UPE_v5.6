"""CLI tests for release manifest and ZIP validation."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate_release.py"


def run_validator(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        capture_output=True,
        check=False,
        text=True,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_package(tmp_path: Path) -> tuple[Path, Path, Path]:
    package = tmp_path / "package"
    (package / "docs").mkdir(parents=True)
    (package / "README.md").write_text("Known limitations: test package.\n", encoding="utf-8")
    (package / "docs" / "guide.txt").write_text("guide\n", encoding="utf-8")
    entries = []
    for relative in ("README.md", "docs/guide.txt"):
        target = package / relative
        raw = target.read_bytes()
        entries.append(
            {
                "path": relative,
                "bytes": len(raw),
                "characters": len(raw.decode("utf-8")),
                "sha256": sha256(target),
            }
        )
    manifest = tmp_path / "MANIFEST.json"
    manifest.write_text(json.dumps({"files": entries}), encoding="utf-8")
    archive = tmp_path / "release.zip"
    with zipfile.ZipFile(archive, "w") as output:
        for relative in ("README.md", "docs/guide.txt"):
            output.write(package / relative, relative)
    return package, manifest, archive


def test_valid_package_manifest_and_archive_pass(tmp_path: Path) -> None:
    package, manifest, archive = make_package(tmp_path)

    result = run_validator(str(package), "--manifest", str(manifest), "--archive", str(archive))

    assert result.returncode == 0, result.stderr
    assert "PASS release validation: 2 file(s)" in result.stdout


def test_hash_mismatch_fails_nonzero_with_expected_and_actual_digest(tmp_path: Path) -> None:
    package, manifest, _ = make_package(tmp_path)
    (package / "README.md").write_text("changed\n", encoding="utf-8")

    result = run_validator(str(package), "--manifest", str(manifest))

    assert result.returncode == 1
    assert "hash mismatch: expected" in result.stderr
    assert "got" in result.stderr


def test_unlisted_package_file_fails_nonzero(tmp_path: Path) -> None:
    package, manifest, _ = make_package(tmp_path)
    (package / "unlisted.txt").write_text("not in manifest\n", encoding="utf-8")

    result = run_validator(str(package), "--manifest", str(manifest))

    assert result.returncode == 1
    assert "package contains unlisted file(s)" in result.stderr
    assert "unlisted.txt" in result.stderr


def test_unsafe_manifest_path_fails_nonzero(tmp_path: Path) -> None:
    package, manifest, _ = make_package(tmp_path)
    manifest.write_text(
        json.dumps({"files": [{"path": "../escape", "sha256": "0" * 64}]}),
        encoding="utf-8",
    )

    result = run_validator(str(package), "--manifest", str(manifest))

    assert result.returncode == 1
    assert "manifest entry '../escape' is unsafe" in result.stderr


def test_archive_traversal_member_fails_without_extraction(tmp_path: Path) -> None:
    package, manifest, archive = make_package(tmp_path)
    with zipfile.ZipFile(archive, "a") as output:
        output.writestr("../escape.txt", "unsafe")

    result = run_validator(str(package), "--manifest", str(manifest), "--archive", str(archive))

    assert result.returncode == 1
    assert "archive member '../escape.txt' is unsafe" in result.stderr
