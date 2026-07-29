# Capability-readiness report Git-context repair

## Status

`IMPLEMENTED_LOCALLY_PENDING_PR_26_DELIVERY`

## Problem

PR #25 refreshed `UPE_5.6.0_to_5.6.1_capability_readiness_report_2026-07-19.html` with `repository.head` and `repository.branch` set to `unavailable`.

The updater currently converts any failed Git subprocess to the literal `unavailable`. Its freshness comparison then excludes the entire `repository` block, and the dedicated test accepts arbitrary repository values. The report can therefore pass `--check` after losing the SHA/branch that identifies its refresh context.

This does not invalidate review bound to the exact PR SHA/tree/diff. It does degrade the report's durable provenance.

## Root cause

- `scripts/update_capability_readiness_report.py::_git_value()` returns `unavailable` for every Git failure.
- `build_payload()` writes that sentinel into the tracked report.
- `_freshness_state()` excludes `repository` entirely.
- `test_repository_identity_is_refresh_context_not_freshness_state()` checks only that repository identity does not make capability state stale; it does not validate repository-context quality.

## Required repair

1. Keep repository identity outside capability-state freshness because committing the report necessarily changes HEAD.
2. Validate repository context separately rather than ignoring its quality.
3. Select refresh provenance in this order:
   1. observed local Git HEAD and branch;
   2. explicit validated `--repository-head` and `--repository-branch` values;
   3. previously embedded valid context, labeled `preserved`;
   4. otherwise fail the write instead of emitting `unavailable`.
4. Store an explicit context status:

```json
"repository": {
  "head": "<40-hex-sha>",
  "branch": "<branch>",
  "context_status": "observed | explicit | preserved"
}
```

5. Let post-commit `--check` continue ignoring expected SHA drift for capability freshness, but make it fail when repository context is missing, malformed, or `unavailable` unless a narrowly named diagnostic override is supplied.

## Acceptance tests

- Git available: exact observed SHA and branch are written with `context_status: observed`.
- Git unavailable plus valid existing context: existing values are retained and labeled `preserved`.
- Git unavailable plus valid explicit override: override is written and labeled `explicit`.
- Git unavailable plus no valid context: refresh exits non-zero and leaves the report unchanged.
- A non-40-hex SHA is rejected.
- Capability-state freshness remains independent of the commit created by refreshing the report.
- A tracked report containing `head: unavailable` or `branch: unavailable` fails the separate provenance check.

## Local implementation and verification

PR #26 now implements the repair in
`scripts/update_capability_readiness_report.py` and its dedicated tests:

- observed Git identity wins when both HEAD and branch are valid;
- a paired, validated explicit override is used only when Git is unavailable;
- previously valid embedded values are retained as `preserved`;
- missing or malformed provenance fails before the report write;
- `--check` validates provenance separately from capability freshness;
- `--allow-invalid-repository-context` is diagnostic-only and cannot authorize a write.

The report was regenerated with a validated explicit PR-head/branch context
because the uv subprocess could not read Git under the worktree ownership
boundary. The report tests, full repository suite, Ruff, mypy, schema,
reference, Work-specification, freshness and diff gates pass locally. These are
local PR #26 results until committed, pushed, reviewed and merged.

## Boundaries

- Do not change task completion derivation while repairing provenance.
- Do not make repository SHA part of the self-referential capability freshness payload.
- Do not claim the report itself proves C-502 live compatibility.
- Refresh the HTML and run the full report test set in the local repository before merging the repair.

## Related exact identities

- PR #25 head: `4d942ba6c07712d5fa8c147f4b2822ed64ba6a5a`
- PR #25 merge: `b20aa4304e61d12e6460e92fccb5b63d9560eb43`
- Reconciliation branch: `agent/reconcile-c501-c502`
