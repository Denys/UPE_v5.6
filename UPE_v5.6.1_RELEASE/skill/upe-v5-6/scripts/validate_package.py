#!/usr/bin/env python3
"""Validate the complete UPE v5.6.1 release or extracted upe-v5-6 skill."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - explicit deployment dependency
    raise SystemExit("FAIL: PyYAML is required") from exc


MANIFEST = "MANIFEST.json"
KERNEL_MAX = 8000
PORTABLE_MAX = 6000

RELEASE_REQUIRED = [
    "01_UPE_v5.6.1_FULL_REFERENCE.md",
    "02_UPE_v5.6.1_PROJECT_INSTRUCTIONS_KERNEL.md",
    "03_UPE_v5.6.1_PORTABLE_KERNEL.md",
    "04_GPT_5.6_RUNTIME_PROFILE.md",
    "05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md",
    "06_SOURCE_MAP.md",
    "07_CHANGELOG_AND_MIGRATION.md",
    "08_EVAL_SUITE.md",
    "09_CAPABILITY_REGISTRY_TEMPLATE.yaml",
    "10_UPE_STATE_TEMPLATE.yaml",
    "11_VALIDATION_REPORT.md",
    "12_INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md",
    "README.md",
    "evals/acceptance_cases.yaml",
    "evals/terminal_audit_cases.yaml",
    MANIFEST,
]

SKILL_REQUIRED = [
    "SKILL.md",
    "agents/openai.yaml",
    "assets/capability_registry_template.yaml",
    "assets/evaluation_report_template.md",
    "assets/upe_state_template.yaml",
    "evals/acceptance_cases.yaml",
    "evals/terminal_audit_cases.yaml",
    "evals/terminal_audit_trigger_cases.csv",
    "evals/trigger_cases.csv",
    "references/CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md",
    "references/GPT_5.6_RUNTIME_PROFILE.md",
    "references/INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md",
    "references/SOURCE_MAP.md",
    "references/UPE_v5.6.1_FULL_REFERENCE.md",
    "references/UPE_v5.6.1_PORTABLE_KERNEL.md",
    "references/UPE_v5.6.1_PROJECT_INSTRUCTIONS_KERNEL.md",
    "scripts/validate_package.py",
]

RELEASE_TO_SKILL_COPIES = {
    "01_UPE_v5.6.1_FULL_REFERENCE.md": "references/UPE_v5.6.1_FULL_REFERENCE.md",
    "02_UPE_v5.6.1_PROJECT_INSTRUCTIONS_KERNEL.md": (
        "references/UPE_v5.6.1_PROJECT_INSTRUCTIONS_KERNEL.md"
    ),
    "03_UPE_v5.6.1_PORTABLE_KERNEL.md": "references/UPE_v5.6.1_PORTABLE_KERNEL.md",
    "04_GPT_5.6_RUNTIME_PROFILE.md": "references/GPT_5.6_RUNTIME_PROFILE.md",
    "05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md": (
        "references/CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md"
    ),
    "06_SOURCE_MAP.md": "references/SOURCE_MAP.md",
    "09_CAPABILITY_REGISTRY_TEMPLATE.yaml": "assets/capability_registry_template.yaml",
    "10_UPE_STATE_TEMPLATE.yaml": "assets/upe_state_template.yaml",
    "12_INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md": (
        "references/INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md"
    ),
    "evals/acceptance_cases.yaml": "evals/acceptance_cases.yaml",
    "evals/terminal_audit_cases.yaml": "evals/terminal_audit_cases.yaml",
}


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def safe_rel_path(value: str) -> bool:
    path = PurePosixPath(value)
    return (
        bool(value)
        and "\\" not in value
        and not path.is_absolute()
        and ".." not in path.parts
        and value == path.as_posix()
    )


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_hash(records: list[tuple[str, str]]) -> str:
    canonical = "".join(f"{digest}  {path}\n" for path, digest in records)
    return hashlib.sha256(canonical.encode()).hexdigest()


def payload_files(root: Path, errors: list[str]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            fail(errors, f"symlink not allowed: {relative}")
        elif path.is_file() and relative != MANIFEST:
            files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix().encode())


def extract_yaml_block(text: str, marker: str) -> Any:
    marker_at = text.index(marker)
    fence_at = text.index("```yaml", marker_at) + len("```yaml")
    end_at = text.index("```", fence_at)
    return yaml.safe_load(text[fence_at:end_at])


def key_paths(value: Any, prefix: str = "") -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            result.add(path)
            result.update(key_paths(child, path))
    elif isinstance(value, list) and value:
        path = f"{prefix}[]"
        result.add(path)
        result.update(key_paths(value[0], path))
    return result


def validate_skill_frontmatter(skill_md: Path, errors: list[str]) -> None:
    text = skill_md.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        fail(errors, "SKILL.md has no YAML front matter")
        return
    frontmatter = yaml.safe_load(match.group(1))
    if not isinstance(frontmatter, dict):
        fail(errors, "SKILL.md front matter is not a mapping")
        return
    if set(frontmatter) != {"name", "description"}:
        fail(errors, "SKILL.md front matter must contain only name and description")
    if frontmatter.get("name") != "upe-v5-6":
        fail(errors, "SKILL.md name must be upe-v5-6")
    description = frontmatter.get("description")
    if not isinstance(description, str) or "Do not trigger" not in description:
        fail(errors, "SKILL.md description lacks a non-trigger boundary")


def validate_csvs(skill_root: Path, errors: list[str]) -> None:
    skill_trigger = skill_root / "evals/trigger_cases.csv"
    with skill_trigger.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or set(rows[0]) != {"class", "prompt", "expected"}:
        fail(errors, "skill trigger_cases.csv has wrong header or no rows")

    terminal_trigger = skill_root / "evals/terminal_audit_trigger_cases.csv"
    with terminal_trigger.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or set(rows[0]) != {"id", "input", "expected", "reason"}:
        fail(errors, "terminal_audit_trigger_cases.csv has wrong header or no rows")
        return
    allowed = {"TRIGGER", "NO_TRIGGER", "PENDING_TRIGGER"}
    invalid = [row.get("id", "?") for row in rows if row.get("expected") not in allowed]
    if invalid:
        fail(errors, f"invalid terminal trigger expectations: {invalid}")


def validate_schema_parity(full_reference: Path, worker: Path, errors: list[str]) -> None:
    try:
        reference_schema = extract_yaml_block(
            full_reference.read_text(encoding="utf-8"),
            "### 23.4 Independent framework audit report",
        )
        worker_schema = extract_yaml_block(
            worker.read_text(encoding="utf-8"),
            "## Required audit output",
        )
    except (OSError, ValueError, yaml.YAMLError) as exc:
        fail(errors, f"could not extract audit schemas: {exc}")
        return
    reference_paths = key_paths(reference_schema)
    worker_paths = key_paths(worker_schema)
    if reference_paths != worker_paths:
        fail(
            errors,
            "audit schema key paths differ: "
            f"reference_only={sorted(reference_paths - worker_paths)} "
            f"worker_only={sorted(worker_paths - reference_paths)}",
        )
    else:
        print(f"PASS audit_schema_key_paths={len(reference_paths)}")


def validate_manifest(root: Path, errors: list[str]) -> None:
    manifest_path = root / MANIFEST
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid {MANIFEST}: {exc}")
        return

    declared_entries = manifest.get("files")
    if not isinstance(declared_entries, list):
        fail(errors, "MANIFEST.json must contain a files array")
        return

    declared: list[tuple[str, str]] = []
    seen: set[str] = set()
    for entry in declared_entries:
        if not isinstance(entry, dict):
            fail(errors, "manifest file entry is not an object")
            continue
        relative = entry.get("path")
        digest = entry.get("sha256")
        if not isinstance(relative, str) or not safe_rel_path(relative):
            fail(errors, f"unsafe manifest path: {relative!r}")
            continue
        if relative in seen:
            fail(errors, f"duplicate manifest path: {relative}")
        seen.add(relative)
        path = root / relative
        if not path.is_file():
            fail(errors, f"manifest path is missing: {relative}")
            continue
        if not isinstance(digest, str) or len(digest) != 64:
            fail(errors, f"invalid manifest digest: {relative}")
            continue
        raw = path.read_bytes()
        if entry.get("bytes") != len(raw):
            fail(errors, f"manifest byte count mismatch: {relative}")
        try:
            characters = len(raw.decode("utf-8"))
        except UnicodeDecodeError:
            characters = None
        if entry.get("characters") != characters:
            fail(errors, f"manifest character count mismatch: {relative}")
        declared.append((relative, digest))

    actual_paths = payload_files(root, errors)
    actual = [(path.relative_to(root).as_posix(), hash_file(path)) for path in actual_paths]
    if declared != actual:
        fail(errors, "manifest file set/order/hash records do not match payload")
    computed = package_hash(actual)
    if manifest.get("package_sha256") != computed:
        fail(errors, f"package_sha256 mismatch: computed {computed}")
    if manifest.get("manifest_excluded") != MANIFEST:
        fail(errors, f"manifest_excluded must be {MANIFEST}")
    print(f"PASS payload_files={len(actual)} package_sha256={computed}")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    errors: list[str] = []
    release_mode = (root / "01_UPE_v5.6.1_FULL_REFERENCE.md").is_file()
    skill_root = root / "skill/upe-v5-6" if release_mode else root

    required = list(RELEASE_REQUIRED) if release_mode else []
    required += (
        [f"skill/upe-v5-6/{path}" for path in SKILL_REQUIRED] if release_mode else SKILL_REQUIRED
    )
    for relative in required:
        if not (root / relative).is_file():
            fail(errors, f"missing required file: {relative}")

    kernel = (
        root / "02_UPE_v5.6.1_PROJECT_INSTRUCTIONS_KERNEL.md"
        if release_mode
        else root / "references/UPE_v5.6.1_PROJECT_INSTRUCTIONS_KERNEL.md"
    )
    portable = (
        root / "03_UPE_v5.6.1_PORTABLE_KERNEL.md"
        if release_mode
        else root / "references/UPE_v5.6.1_PORTABLE_KERNEL.md"
    )
    full_reference = (
        root / "01_UPE_v5.6.1_FULL_REFERENCE.md"
        if release_mode
        else root / "references/UPE_v5.6.1_FULL_REFERENCE.md"
    )
    worker = (
        root / "12_INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md"
        if release_mode
        else root / "references/INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md"
    )

    if kernel.is_file():
        characters = len(kernel.read_text(encoding="utf-8"))
        if characters >= KERNEL_MAX:
            fail(errors, f"active kernel has {characters} characters; must be <{KERNEL_MAX}")
        else:
            print(f"PASS kernel_characters={characters}")
    if portable.is_file():
        characters = len(portable.read_text(encoding="utf-8"))
        if characters > PORTABLE_MAX:
            fail(errors, f"portable kernel has {characters} characters; max={PORTABLE_MAX}")
        else:
            print(f"PASS portable_kernel_characters={characters}")

    for path in sorted(root.rglob("*.md")):
        fence_count = sum(
            line.startswith("```") for line in path.read_text(encoding="utf-8").splitlines()
        )
        if fence_count % 2:
            fail(errors, f"unbalanced Markdown fences: {path.relative_to(root)}")
    for path in sorted(root.rglob("*.yaml")):
        try:
            yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            fail(errors, f"invalid YAML {path.relative_to(root)}: {exc}")

    if (skill_root / "SKILL.md").is_file():
        validate_skill_frontmatter(skill_root / "SKILL.md", errors)
    if all((skill_root / path).is_file() for path in SKILL_REQUIRED):
        validate_csvs(skill_root, errors)
    if full_reference.is_file() and worker.is_file():
        validate_schema_parity(full_reference, worker, errors)

    if release_mode:
        for release_path, skill_path in RELEASE_TO_SKILL_COPIES.items():
            if (root / release_path).read_bytes() != (skill_root / skill_path).read_bytes():
                fail(errors, f"release/skill copy mismatch: {release_path} != {skill_path}")
        validate_manifest(root, errors)

    obsolete = ("upe-v5-6-" + "1-1", "UPE v5.6." + "2")
    for path in root.rglob("*"):
        if path.is_file() and path.suffix in {".md", ".yaml", ".json", ".csv", ".py"}:
            text = path.read_text(encoding="utf-8")
            for marker in obsolete:
                if marker in text:
                    fail(errors, f"obsolete marker {marker!r} in {path.relative_to(root)}")

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(f"PASS package_validation mode={'release' if release_mode else 'skill'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
