#!/usr/bin/env bash

set -euo pipefail

fail() {
  printf 'fixture bootstrap error: %s\n' "$1" >&2
  exit 2
}

if (( $# != 0 )); then
  fail "usage: scripts/bootstrap.sh"
fi

source_dir="$(cygpath -u "$(dirname -- "${BASH_SOURCE[0]}")")"
source "$source_dir/fixture-guard.sh"
script_dir="$(cd -- "$source_dir" && pwd -P)"
repo_root="$(cd -- "$script_dir/.." && pwd -P)"
fixture_root="$repo_root/examples/fixture-repository"
seed_root="$fixture_root/seed"
output_root="$fixture_root/.fixture-output"
output_repository="$output_root/repository"
owner_marker="$fixture_root/.fixture-output.owner"

[[ -d "$seed_root" ]] || fail "missing committed seed directory: $seed_root"
[[ ! -e "$seed_root/.git" ]] || fail "the committed seed must not contain Git metadata"

if ! fixture_guard_validate_layout \
  "$fixture_root" "$output_root" "$output_repository" "$owner_marker"; then
  fail "$FIXTURE_GUARD_ERROR"
fi

if [[ -e "$owner_marker" || -L "$owner_marker" ]]; then
  fixture_guard_require_owner "$owner_marker" || fail "$FIXTURE_GUARD_ERROR"
elif [[ -e "$output_root" || -L "$output_root" ]]; then
  fail "refusing to replace output without its adjacent owner marker"
fi

if [[ -e "$output_root" || -L "$output_root" ]]; then
  rm -rf -- "$output_root"
fi

printf '%s\n' "$FIXTURE_OWNER_MARKER_VALUE" > "$owner_marker"
mkdir -p -- "$output_repository"
cp -R -- "$seed_root/." "$output_repository/"

if ! fixture_guard_require_initialized \
  "$fixture_root" "$output_root" "$output_repository" "$owner_marker"; then
  fail "$FIXTURE_GUARD_ERROR"
fi

git -c init.templateDir= init --quiet --initial-branch=main "$output_repository"
git -C "$output_repository" config core.autocrlf false
git -C "$output_repository" config core.filemode false
git -C "$output_repository" config user.name "C-305 Fixture"
git -C "$output_repository" config user.email "fixture@example.invalid"
git -c core.attributesFile=/dev/null -C "$output_repository" add --all

GIT_AUTHOR_NAME="C-305 Fixture" \
GIT_AUTHOR_EMAIL="fixture@example.invalid" \
GIT_AUTHOR_DATE="2000-01-01T00:00:00Z" \
GIT_COMMITTER_NAME="C-305 Fixture" \
GIT_COMMITTER_EMAIL="fixture@example.invalid" \
GIT_COMMITTER_DATE="2000-01-01T00:00:00Z" \
  git -c core.hooksPath=/dev/null -c commit.gpgSign=false -C "$output_repository" \
  commit --quiet --no-gpg-sign --no-verify -m "Initialize deterministic C-305 fixture"

resolved_repository="$(cd -- "$output_repository" && pwd -P)"
git_toplevel="$(git -C "$output_repository" rev-parse --show-toplevel)"
resolved_toplevel="$(cd -- "$git_toplevel" && pwd -P)"
[[ "$resolved_toplevel" == "$resolved_repository" ]] \
  || fail "fixture Git root is not the exact generated repository"

fixture_head="$(git -C "$output_repository" rev-parse HEAD)"
[[ -z "$(git -C "$output_repository" status --porcelain=v1 --untracked-files=all)" ]] \
  || fail "new fixture repository is unexpectedly dirty"

printf 'fixture_bootstrap=PASS\n'
printf 'fixture_repository=%s\n' "$resolved_repository"
printf 'fixture_head=%s\n' "$fixture_head"
