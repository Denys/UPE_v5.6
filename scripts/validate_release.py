#!/usr/bin/env python3
"""Validate a release directory, checksum manifest, and optional ZIP without extraction."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SHA256 = re.compile(r"^[A-Fa-f0-9]{64}$")
MANIFEST_LINE = re.compile(r"^([A-Fa-f0-9]{64})  (.+)$")


@dataclass(frozen=True)
class ManifestEntry:
    path: str
    sha256: str
    byte_count: int | None = None
    character_count: int | None = None


def safe_package_path(value: str) -> str | None:
    """Return an explanation for unsafe or platform-dependent manifest paths."""

    if not value:
        return "path is empty"
    if "\\" in value:
        return "path must use forward slashes"
    if value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        return "path must be package-relative, not absolute"
    if "\x00" in value:
        return "path contains a NUL byte"
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return "path contains an empty, current-directory, or parent-directory segment"
    if any(":" in part for part in parts):
        return "path contains a colon (drive or alternate-data-stream syntax)"
    if PurePosixPath(value).is_absolute():
        return "path must be package-relative"
    return None


def _parse_nonnegative_int(value: Any, field: str, path: str, errors: list[str]) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        errors.append(f"manifest entry {path!r}: {field} must be a non-negative integer")
        return None
    return int(value)


def parse_json_manifest(path: Path) -> tuple[list[ManifestEntry], list[str]]:
    errors: list[str] = []
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"{path}: cannot parse JSON manifest: {exc}"]
    raw_entries = document.get("files") if isinstance(document, dict) else None
    if not isinstance(raw_entries, list):
        return [], [f"{path}: JSON manifest must contain a files array"]

    entries: list[ManifestEntry] = []
    for index, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            errors.append(f"{path}: files[{index}] must be an object")
            continue
        entry_path = raw_entry.get("path")
        digest = raw_entry.get("sha256")
        if not isinstance(entry_path, str) or not entry_path:
            errors.append(f"{path}: files[{index}].path must be a non-empty string")
            continue
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            errors.append(f"manifest entry {entry_path!r}: sha256 must be exactly 64 hex digits")
            continue
        entries.append(
            ManifestEntry(
                path=entry_path,
                sha256=digest.lower(),
                byte_count=_parse_nonnegative_int(
                    raw_entry.get("bytes"), "bytes", entry_path, errors
                ),
                character_count=_parse_nonnegative_int(
                    raw_entry.get("characters"), "characters", entry_path, errors
                ),
            )
        )
    return entries, errors


def parse_sha256_manifest(path: Path) -> tuple[list[ManifestEntry], list[str]]:
    errors: list[str] = []
    entries: list[ManifestEntry] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return [], [f"{path}: cannot read checksum manifest: {exc}"]
    for line_number, line in enumerate(lines, start=1):
        if not line:
            continue
        match = MANIFEST_LINE.fullmatch(line)
        if not match:
            errors.append(
                f"{path}:{line_number}: expected '<64 hex sha256><two spaces><relative path>'"
            )
            continue
        entries.append(ManifestEntry(path=match.group(2), sha256=match.group(1).lower()))
    return entries, errors


def parse_manifest(path: Path) -> tuple[list[ManifestEntry], list[str]]:
    if path.suffix.lower() == ".json":
        return parse_json_manifest(path)
    return parse_sha256_manifest(path)


def _candidate_payloads(raw: bytes, normalize_text_eol: bool) -> Iterable[tuple[bytes, str]]:
    yield raw, "raw bytes"
    if normalize_text_eol and b"\x00" not in raw:
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            return
        normalized = raw.replace(b"\r\n", b"\n")
        if normalized != raw:
            yield normalized, "UTF-8 text with CRLF normalized to LF"


def _matching_payload(
    raw: bytes, expected_sha256: str, normalize_text_eol: bool
) -> tuple[bytes | None, str | None]:
    for payload, label in _candidate_payloads(raw, normalize_text_eol):
        if hashlib.sha256(payload).hexdigest() == expected_sha256:
            return payload, label
    return None, None


def validate_entries(
    root: Path,
    manifest_path: Path,
    entries: Sequence[ManifestEntry],
    normalize_text_eol: bool,
    archive_path: Path | None,
) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    root_resolved = root.resolve()
    for entry in entries:
        unsafe_reason = safe_package_path(entry.path)
        if unsafe_reason:
            errors.append(f"manifest entry {entry.path!r} is unsafe: {unsafe_reason}")
            continue
        if entry.path in seen:
            errors.append(f"manifest contains duplicate path {entry.path!r}")
            continue
        seen.add(entry.path)

        target = (root_resolved / entry.path).resolve()
        if not target.is_relative_to(root_resolved):
            errors.append(f"manifest entry {entry.path!r} escapes package root")
            continue
        if not target.is_file():
            errors.append(f"manifest entry {entry.path!r} does not identify an existing file")
            continue
        raw = target.read_bytes()
        matched, matched_as = _matching_payload(raw, entry.sha256, normalize_text_eol)
        if matched is None:
            actual = hashlib.sha256(raw).hexdigest()
            errors.append(
                f"manifest entry {entry.path!r} hash mismatch: expected {entry.sha256}, "
                f"got {actual}"
            )
            continue
        if entry.byte_count is not None and len(matched) != entry.byte_count:
            errors.append(
                f"manifest entry {entry.path!r} byte count mismatch: expected "
                f"{entry.byte_count}, got {len(matched)} ({matched_as})"
            )
        if entry.character_count is not None:
            try:
                actual_characters = len(matched.decode("utf-8"))
            except UnicodeDecodeError:
                errors.append(
                    f"manifest entry {entry.path!r} declares characters but is not UTF-8 text"
                )
            else:
                if actual_characters != entry.character_count:
                    errors.append(
                        f"manifest entry {entry.path!r} character count mismatch: expected "
                        f"{entry.character_count}, got {actual_characters} ({matched_as})"
                    )

    excluded: set[Path] = set()
    for candidate in (manifest_path, archive_path):
        if candidate is None:
            continue
        resolved = candidate.resolve()
        if resolved.is_relative_to(root_resolved):
            excluded.add(resolved)
    actual_files: set[str] = set()
    for path in root_resolved.rglob("*"):
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved in excluded:
            continue
        relative = path.relative_to(root_resolved).as_posix()
        if not resolved.is_relative_to(root_resolved):
            errors.append(f"package file {relative!r} resolves outside package root")
            continue
        actual_files.add(relative)
    missing_from_manifest = sorted(actual_files - seen)
    if missing_from_manifest:
        errors.append(f"package contains unlisted file(s): {missing_from_manifest!r}")
    return errors


def validate_archive(
    archive_path: Path,
    entries: Sequence[ManifestEntry],
    prefix: str,
) -> list[str]:
    errors: list[str] = []
    normalized_prefix = prefix.strip("/")
    if normalized_prefix and safe_package_path(normalized_prefix):
        return [f"archive prefix {prefix!r} is unsafe"]
    prefix_text = f"{normalized_prefix}/" if normalized_prefix else ""
    expected = {f"{prefix_text}{entry.path}": entry.sha256 for entry in entries}

    try:
        with zipfile.ZipFile(archive_path) as archive:
            bad_member = archive.testzip()
            if bad_member is not None:
                errors.append(f"archive CRC check failed for {bad_member!r}")
            files: dict[str, zipfile.ZipInfo] = {}
            for member in archive.infolist():
                if member.is_dir():
                    continue
                unsafe_reason = safe_package_path(member.filename)
                if unsafe_reason:
                    errors.append(f"archive member {member.filename!r} is unsafe: {unsafe_reason}")
                    continue
                if member.filename in files:
                    errors.append(f"archive contains duplicate member {member.filename!r}")
                    continue
                files[member.filename] = member
            missing = sorted(set(expected) - set(files))
            unlisted = sorted(set(files) - set(expected))
            if missing:
                errors.append(f"archive is missing manifest member(s): {missing!r}")
            if unlisted:
                errors.append(f"archive contains unlisted member(s): {unlisted!r}")
            for member_name in sorted(set(expected) & set(files)):
                actual = hashlib.sha256(archive.read(files[member_name])).hexdigest()
                if actual != expected[member_name]:
                    errors.append(
                        f"archive member {member_name!r} hash mismatch: expected "
                        f"{expected[member_name]}, got {actual}"
                    )
    except (OSError, zipfile.BadZipFile) as exc:
        errors.append(f"{archive_path}: cannot read ZIP archive: {exc}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("package_root", type=Path, help="Directory containing packaged files.")
    parser.add_argument(
        "--manifest",
        type=Path,
        required=True,
        help="SHA-256 text manifest or JSON manifest with a files array.",
    )
    parser.add_argument("--archive", type=Path, help="Optional ZIP that must match the manifest.")
    parser.add_argument(
        "--archive-prefix",
        default="",
        help="Optional top-level ZIP path before each manifest path.",
    )
    parser.add_argument(
        "--normalize-text-eol",
        action="store_true",
        help="Also accept UTF-8 hashes/metrics after CRLF-to-LF normalization.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.package_root.resolve()
    manifest_path = args.manifest.resolve()
    archive_path = args.archive.resolve() if args.archive else None
    errors: list[str] = []

    if not root.is_dir():
        errors.append(f"{root}: package root is not a directory")
    if not manifest_path.is_file():
        errors.append(f"{manifest_path}: manifest file does not exist")
    if archive_path is not None and not archive_path.is_file():
        errors.append(f"{archive_path}: archive file does not exist")

    entries: list[ManifestEntry] = []
    if not errors:
        entries, manifest_errors = parse_manifest(manifest_path)
        errors.extend(manifest_errors)
        if not entries:
            errors.append(f"{manifest_path}: manifest has no valid file entries")

    if entries and root.is_dir():
        errors.extend(
            validate_entries(root, manifest_path, entries, args.normalize_text_eol, archive_path)
        )
    if entries and archive_path is not None and archive_path.is_file():
        errors.extend(validate_archive(archive_path, entries, args.archive_prefix))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL release validation: {len(errors)} error(s)", file=sys.stderr)
        return 1

    archive_summary = f", archive={archive_path}" if archive_path else ""
    print(f"PASS release validation: {len(entries)} file(s){archive_summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
