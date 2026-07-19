#!/usr/bin/env bash

set -euo pipefail

fail() {
  printf 'fixture fast verification error: %s\n' "$1" >&2
  exit 2
}

mode="pass"
if (( $# == 1 )) && [[ "$1" == "--known-failure" ]]; then
  mode="known-failure"
elif (( $# != 0 )); then
  fail "usage: scripts/verify-fast.sh [--known-failure]"
fi

source_dir="$(cygpath -u "$(dirname -- "${BASH_SOURCE[0]}")")"
source "$source_dir/fixture-guard.sh"
script_dir="$(cd -- "$source_dir" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
fixture_root="$repo_root/examples/fixture-repository"
output_root="$fixture_root/.fixture-output"
fixture_repository="$output_root/repository"
owner_marker="$fixture_root/.fixture-output.owner"

if ! fixture_guard_require_initialized \
  "$fixture_root" "$output_root" "$fixture_repository" "$owner_marker"; then
  fail "$FIXTURE_GUARD_ERROR"
fi
[[ -d "$fixture_repository/.git" ]] || fail "generated fixture Git repository is missing"
command -v py >/dev/null 2>&1 || fail "Windows Python launcher 'py' is unavailable"

resolved_repository="$(cd -- "$fixture_repository" && pwd -P)"
git_toplevel="$(git -C "$fixture_repository" rev-parse --show-toplevel)"
resolved_toplevel="$(cd -- "$git_toplevel" && pwd -P)"
[[ "$resolved_toplevel" == "$resolved_repository" ]] \
  || fail "fixture Git root is not the exact generated repository"
[[ "$(git -C "$fixture_repository" symbolic-ref --short HEAD)" == "main" ]] \
  || fail "fixture must use the main branch"

set +e
if [[ "$mode" == "known-failure" ]]; then
  (cd -- "$fixture_repository" && py -3 fixture_math.py --known-failure)
else
  (cd -- "$fixture_repository" && py -3 fixture_math.py --self-check)
fi
verification_status=$?
set -e

if [[ "$mode" == "known-failure" ]]; then
  if (( verification_status != 1 )); then
    fail "known failure returned $verification_status instead of 1"
  fi
  printf 'fixture_verify_fast=KNOWN_FAILURE\n'
  printf 'exit_code=1\n'
  exit 1
fi

if (( verification_status != 0 )); then
  printf 'fixture_verify_fast=FAIL\n' >&2
  printf 'exit_code=%s\n' "$verification_status" >&2
  exit "$verification_status"
fi

printf 'fixture_verify_fast=PASS\n'
printf 'exit_code=0\n'
