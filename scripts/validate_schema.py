#!/usr/bin/env python3
"""Validate the accepted specification examples with JSON Schema Draft 2020-12."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

DEFAULT_SCHEMA_EXAMPLES: Mapping[str, tuple[str, ...]] = {
    "schemas/capability_execution_record.schema.yaml": (
        "examples/specifications/capability_execution_record.example.yaml",
    ),
    "schemas/goal_contract.schema.yaml": (
        "examples/specifications/goal_contract.example.yaml",
        "examples/specifications/local_implementation_goal.example.yaml",
    ),
    "schemas/handoff.schema.yaml": ("examples/specifications/handoff.example.yaml",),
    "schemas/verifier_result.schema.yaml": (
        "examples/specifications/verifier_result.example.yaml",
    ),
    "schemas/work_loop_state.schema.yaml": (
        "examples/specifications/work_loop_state.example.yaml",
    ),
}


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_data(path: Path) -> Any:
    """Load JSON or YAML while rejecting duplicate YAML keys."""

    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return yaml.load(text, Loader=UniqueKeyLoader)


def display_path(path: Sequence[object]) -> str:
    """Render a jsonschema path in an unambiguous JSONPath-like form."""

    rendered = "$"
    for part in path:
        if isinstance(part, int):
            rendered += f"[{part}]"
        elif str(part).isidentifier():
            rendered += f".{part}"
        else:
            rendered += f"[{part!r}]"
    return rendered


def format_validation_error(error: ValidationError) -> str:
    """Return a deterministic, actionable validation failure."""

    location = display_path(list(error.absolute_path))
    rule = error.validator or "schema"
    return f"{location}: {error.message} (rule: {rule})"


def _resolve(root: Path, supplied: str) -> Path:
    candidate = Path(supplied)
    if not candidate.is_absolute():
        candidate = root / candidate
    return candidate.resolve()


def validate_pair(schema_path: Path, instance_path: Path) -> list[str]:
    """Validate one schema/instance pair and return all deterministic errors."""

    errors: list[str] = []
    try:
        schema = load_data(schema_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"{schema_path}: cannot parse schema: {exc}"]

    if not isinstance(schema, dict):
        return [f"{schema_path}: schema root must be an object"]

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        return [f"{schema_path}: invalid Draft 2020-12 schema: {exc.message}"]

    try:
        instance = load_data(instance_path)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [f"{instance_path}: cannot parse instance: {exc}"]

    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    validation_errors = sorted(
        validator.iter_errors(instance),
        key=lambda item: (tuple(str(part) for part in item.absolute_path), item.message),
    )
    errors.extend(
        f"{instance_path} against {schema_path}: {format_validation_error(error)}"
        for error in validation_errors
    )
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root used to resolve relative paths (default: script parent).",
    )
    parser.add_argument("--schema", help="Schema path for an explicit validation run.")
    parser.add_argument(
        "--instance",
        action="append",
        default=[],
        help="Instance path for --schema; repeat to validate multiple instances.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.root.resolve()

    if bool(args.schema) != bool(args.instance):
        build_parser().error("--schema and at least one --instance must be supplied together")

    pairs: list[tuple[Path, Path]] = []
    if args.schema:
        schema_path = _resolve(root, args.schema)
        pairs.extend((schema_path, _resolve(root, item)) for item in args.instance)
    else:
        for schema, instances in DEFAULT_SCHEMA_EXAMPLES.items():
            pairs.extend((_resolve(root, schema), _resolve(root, item)) for item in instances)

    errors: list[str] = []
    for schema_path, instance_path in pairs:
        if not schema_path.is_file():
            errors.append(f"{schema_path}: schema file does not exist")
            continue
        if not instance_path.is_file():
            errors.append(f"{instance_path}: instance file does not exist")
            continue
        errors.extend(validate_pair(schema_path, instance_path))

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"FAIL schema validation: {len(errors)} error(s)", file=sys.stderr)
        return 1

    print(f"PASS schema validation: {len(pairs)} instance(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
