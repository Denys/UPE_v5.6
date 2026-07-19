"""C-305 fixture initialization and baseline command checks."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = REPOSITORY_ROOT / "examples" / "fixture-repository"
GENERATED_OUTPUT = FIXTURE_ROOT / ".fixture-output"
GENERATED_REPOSITORY = GENERATED_OUTPUT / "repository"
OWNER_MARKER = FIXTURE_ROOT / ".fixture-output.owner"
OWNER_MARKER_VALUE = "upe-c305-fixture-output-v1\n"


def _git_bash() -> Path:
    git_executable = shutil.which("git")
    if git_executable is not None:
        git_directory = Path(git_executable).resolve().parent
        git_root = (
            git_directory.parent if git_directory.name.lower() in {"bin", "cmd"} else git_directory
        )
        candidate = git_root / "usr" / "bin" / "bash.exe"
        if candidate.is_file():
            return candidate
    standard_install = Path("C:/Program Files/Git/usr/bin/bash.exe")
    assert standard_install.is_file(), "Git Bash is required by the Windows-native fixture contract"
    return standard_install


def _run_script(name: str, *arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [_git_bash().as_posix(), f"scripts/{name}", *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _fixture_head() -> str:
    result = subprocess.run(
        ["git", "-C", str(GENERATED_REPOSITORY), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _create_junction(link: Path, target: Path) -> None:
    environment = os.environ.copy()
    environment.update({"C305_LINK": str(link), "C305_TARGET": str(target)})
    result = subprocess.run(
        [
            "powershell.exe",
            "-NoLogo",
            "-NoProfile",
            "-NonInteractive",
            "-Command",
            "$null = New-Item -ItemType Junction -Path $env:C305_LINK "
            "-Target $env:C305_TARGET -ErrorAction Stop",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    assert result.returncode == 0, result.stderr
    assert link.is_dir()


def _remove_junction(link: Path) -> None:
    assert link.is_dir()
    assert link.stat(follow_symlinks=False).st_file_attributes & 0x400
    link.rmdir()


def _assert_all_entrypoints_refuse(expected_error: str) -> None:
    for script_name in ("bootstrap.sh", "verify-fast.sh", "verify-full.sh"):
        result = _run_script(script_name)
        assert result.returncode == 2, (script_name, result.stdout, result.stderr)
        assert expected_error in result.stderr


def test_fixture_scripts_have_reproducible_and_adversarial_contracts() -> None:
    first_bootstrap = _run_script("bootstrap.sh")
    assert first_bootstrap.returncode == 0, first_bootstrap.stderr
    assert "fixture_bootstrap=PASS" in first_bootstrap.stdout
    first_head = _fixture_head()

    second_bootstrap = _run_script("bootstrap.sh")
    assert second_bootstrap.returncode == 0, second_bootstrap.stderr
    assert _fixture_head() == first_head
    assert not list((FIXTURE_ROOT / "seed").rglob(".git"))

    refused_bootstrap = _run_script("bootstrap.sh", "unexpected-argument")
    assert refused_bootstrap.returncode == 2
    assert "usage: scripts/bootstrap.sh" in refused_bootstrap.stderr
    assert _fixture_head() == first_head

    for script_name in ("verify-fast.sh", "verify-full.sh"):
        passing = _run_script(script_name)
        assert passing.returncode == 0, passing.stderr
        assert "=PASS" in passing.stdout
        assert "exit_code=0" in passing.stdout

        failing = _run_script(script_name, "--known-failure")
        assert failing.returncode == 1
        assert "=KNOWN_FAILURE" in failing.stdout
        assert "exit_code=1" in failing.stdout

    original_marker = OWNER_MARKER.read_text(encoding="utf-8")
    OWNER_MARKER.write_text("tampered-owner\n", encoding="utf-8")
    try:
        _assert_all_entrypoints_refuse("fixture owner marker is invalid")
        assert _fixture_head() == first_head
    finally:
        OWNER_MARKER.write_text(original_marker, encoding="utf-8")

    adversarial_root = FIXTURE_ROOT / ".fixture-adversarial-test"
    adversarial_root.mkdir(exist_ok=True)
    assert not (adversarial_root.stat().st_file_attributes & 0x400)
    marker_target = adversarial_root / "marker-target"
    output_target = adversarial_root / "output-target"
    repository_target = adversarial_root / "repository-target"
    for target in (marker_target, output_target, repository_target):
        target.mkdir(exist_ok=True)
        assert not (target.stat().st_file_attributes & 0x400)
        assert not list(target.iterdir())
    marker_sentinel = marker_target / "sentinel.txt"
    output_sentinel = output_target / "sentinel.txt"
    repository_sentinel = repository_target / "sentinel.txt"
    marker_sentinel.write_text("keep-marker-target\n", encoding="utf-8")
    output_sentinel.write_text("keep-output-target\n", encoding="utf-8")
    repository_sentinel.write_text("keep-repository-target\n", encoding="utf-8")

    marker_backup = GENERATED_OUTPUT / ".owner-marker.test-backup"
    OWNER_MARKER.replace(marker_backup)
    try:
        _create_junction(OWNER_MARKER, marker_target)
        try:
            _assert_all_entrypoints_refuse("owner marker path is a reparse point")
            assert marker_sentinel.read_text(encoding="utf-8") == "keep-marker-target\n"
        finally:
            if OWNER_MARKER.exists():
                _remove_junction(OWNER_MARKER)
    finally:
        marker_backup.replace(OWNER_MARKER)

    output_backup = FIXTURE_ROOT / ".fixture-output.test-backup"
    GENERATED_OUTPUT.replace(output_backup)
    try:
        _create_junction(GENERATED_OUTPUT, output_target)
        try:
            _assert_all_entrypoints_refuse("fixture output path is a reparse point")
            assert output_sentinel.read_text(encoding="utf-8") == "keep-output-target\n"
        finally:
            if GENERATED_OUTPUT.exists():
                _remove_junction(GENERATED_OUTPUT)
    finally:
        output_backup.replace(GENERATED_OUTPUT)

    repository_backup = GENERATED_OUTPUT / ".repository.test-backup"
    GENERATED_REPOSITORY.replace(repository_backup)
    try:
        _create_junction(GENERATED_REPOSITORY, repository_target)
        try:
            _assert_all_entrypoints_refuse("generated repository path is a reparse point")
            assert repository_sentinel.read_text(encoding="utf-8") == "keep-repository-target\n"
        finally:
            if GENERATED_REPOSITORY.exists():
                _remove_junction(GENERATED_REPOSITORY)
    finally:
        repository_backup.replace(GENERATED_REPOSITORY)

    final_bootstrap = _run_script("bootstrap.sh")
    assert final_bootstrap.returncode == 0, final_bootstrap.stderr
    assert _fixture_head() == first_head
    assert OWNER_MARKER.read_text(encoding="utf-8") == OWNER_MARKER_VALUE

    for sentinel in (marker_sentinel, output_sentinel, repository_sentinel):
        sentinel.unlink()
    for target in (marker_target, output_target, repository_target):
        target.rmdir()
    adversarial_root.rmdir()
