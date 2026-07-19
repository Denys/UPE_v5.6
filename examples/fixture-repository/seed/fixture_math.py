"""Small deterministic target used by harness lifecycle tests."""

from __future__ import annotations

import argparse


def classify_number(value: int) -> str:
    """Classify the behavior implemented by the initial fixture baseline."""
    if value > 0:
        return "positive"
    return "non-positive"


def _run_self_check() -> int:
    observed = (classify_number(2), classify_number(0))
    expected = ("positive", "non-positive")
    if observed != expected:
        print(f"baseline mismatch: expected {expected!r}, observed {observed!r}")
        return 1
    print("fixture baseline self-check passed")
    return 0


def _run_known_failure() -> int:
    observed = classify_number(-1)
    expected = "negative"
    if observed != expected:
        print(f"known failure: expected {expected!r}, observed {observed!r}")
        return 1
    print("known failure has been repaired")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--self-check", action="store_true")
    mode.add_argument("--known-failure", action="store_true")
    args = parser.parse_args()
    if args.known_failure:
        return _run_known_failure()
    return _run_self_check()


if __name__ == "__main__":
    raise SystemExit(main())
