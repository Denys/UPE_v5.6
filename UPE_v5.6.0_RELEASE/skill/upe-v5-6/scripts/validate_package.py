#!/usr/bin/env python3
"""Validate the UPE v5.6.0 release or skill bundle."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

KERNEL_MIN = 7200
KERNEL_MAX = 8000
PORTABLE_MAX = 6000


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Cannot read {path}: {exc}") from exc


def validate_frontmatter(skill_md: Path, errors: list[str]) -> None:
    text = read(skill_md)
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        errors.append(f"{skill_md}: missing YAML front matter")
        return
    front = match.group(1)
    for key in ("name:", "description:"):
        if key not in front:
            errors.append(f"{skill_md}: missing {key[:-1]} in front matter")
    description = next((line.split(":", 1)[1].strip() for line in front.splitlines() if line.startswith("description:")), "")
    if len(description) < 80:
        errors.append(f"{skill_md}: description is too vague/short ({len(description)} chars)")
    if "Do not trigger" not in description:
        errors.append(f"{skill_md}: description lacks an explicit non-trigger boundary")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".", help="Release root or skill directory")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    errors: list[str] = []
    warnings: list[str] = []

    release_kernel = root / "02_UPE_v5.6.0_PROJECT_INSTRUCTIONS_KERNEL.md"
    portable = root / "03_UPE_v5.6.0_PORTABLE_KERNEL.md"
    skill_md = root / "skill" / "upe-v5-6" / "SKILL.md"

    if not release_kernel.exists() and (root / "SKILL.md").exists():
        skill_md = root / "SKILL.md"
        candidate_ref = root / "references" / "UPE_v5.6.0_PROJECT_INSTRUCTIONS_KERNEL.md"
        if candidate_ref.exists():
            release_kernel = candidate_ref
        portable = root / "references" / "UPE_v5.6.0_PORTABLE_KERNEL.md"

    required_release = [
        "01_UPE_v5.6.0_FULL_REFERENCE.md",
        "02_UPE_v5.6.0_PROJECT_INSTRUCTIONS_KERNEL.md",
        "03_UPE_v5.6.0_PORTABLE_KERNEL.md",
        "04_GPT_5.6_RUNTIME_PROFILE.md",
        "05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md",
        "06_SOURCE_MAP.md",
        "07_CHANGELOG_AND_MIGRATION.md",
        "09_CAPABILITY_REGISTRY_TEMPLATE.yaml",
        "10_UPE_STATE_TEMPLATE.yaml",
    ]
    if (root / "01_UPE_v5.6.0_FULL_REFERENCE.md").exists():
        for name in required_release:
            if not (root / name).exists():
                errors.append(f"missing release file: {name}")

    if release_kernel.exists():
        count = len(read(release_kernel))
        if count > KERNEL_MAX:
            errors.append(f"kernel is {count} chars; hard max is {KERNEL_MAX}")
        elif count < KERNEL_MIN:
            warnings.append(f"kernel is {count} chars; target minimum is {KERNEL_MIN}")
    else:
        errors.append("project kernel not found")

    if portable.exists():
        count = len(read(portable))
        if count > PORTABLE_MAX:
            errors.append(f"portable kernel is {count} chars; expected <= {PORTABLE_MAX}")

    if skill_md.exists():
        validate_frontmatter(skill_md, errors)
    else:
        errors.append("SKILL.md not found")

    for path in root.rglob("*.md"):
        text = read(path)
        if "UPE v4.3 —" in text and "migration" not in path.name.lower() and "changelog" not in path.name.lower():
            warnings.append(f"legacy active version marker in {path}")
        if "TODO" in text or "TBD" in text:
            warnings.append(f"unfinished marker in {path}")

    report = {
        "root": str(root),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "kernel_chars": len(read(release_kernel)) if release_kernel.exists() else None,
        "portable_chars": len(read(portable)) if portable.exists() else None,
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
