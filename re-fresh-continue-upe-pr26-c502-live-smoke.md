# Session refresh - Continue UPE PR 26 and make C-502 attempt-002 executable

Continue in `C:\Users\denko\CodexWork\UPE_5.6_worktrees\pr26-reconcile-20260728`.
Goal of this Codex session: finish PR #26 as an executable, evidence-safe
precondition for the real C-502 attempt-002, without merging or starting the
live smoke unless separately authorized.

## Where things stand

- Repository: `Denys/UPE_v5.6`.
- Local branch: `codex/pr26-state-persistence-reconciliation-20260728`.
- Remote PR branch: `agent/reconcile-c501-c502`.
- Pull request: https://github.com/Denys/UPE_v5.6/pull/26
- Published functional/state checkpoint:
  `f13d197b9909b8f04fc214620573f29121d38ae2`.
- PR #25 is merged at `b20aa4304e61d12e6460e92fccb5b63d9560eb43`
  and fixes the unversioned App Server envelope framing.
- C-502 attempt-001 was a real Windows-native App Server 0.144.3 launch. It
  stopped at `initialize_response_parse` after 2.417 seconds because the old
  adapter required an invented `jsonrpc` member. It created no thread or turn.
- Attempt-001 evidence is immutable and remains in the retained historical
  worktree.
- PR #26 defines a complete attempt-002 contract for initialize, thread/turn,
  exact-scope approval, interrupt, same-thread reconnect, terminal correlation,
  fixture containment, validators and evidence.
- The readiness aggregator remediation is locally verified: a required task
  gate is applied after every completion source; missing, `FAIL` or
  `INSUFFICIENT_EVIDENCE` keeps C-502 incomplete. Targeted tests are 30/30 and
  the complete suite is 498/498.
- Critical open gap: PR #26 does not deliver an attempt-002 runner, validator or
  integration test. The uncommitted historical runner is happy-path-only,
  denies approvals and has no interrupt/reconnect scenario.
- No PR #26 merge and no attempt-002 live run are authorized or performed.

## Next steps

1. Inspect branch, HEAD, dirty state and recent history; re-run the smallest
   checks if the checkpoint is not clean.
2. Resolve the runner-delivery design before implementation:
   - recommended minimum: extend the PR #26 handoff and goal allowed paths so
     the post-merge C-502 branch may adapt, test and commit
     `scripts/run_c502_app_server_smoke.py`,
     `scripts/validate_c502_app_server_smoke.py` and
     `tests/integration/test_c502_app_server_smoke.py` before consuming the one
     live attempt;
   - alternative: implement and review the complete lifecycle tooling inside
     PR #26 before merge, at the cost of a much larger reconciliation PR;
   - reject an ephemeral external runner because it lacks reviewed repository
     provenance.
3. After the design is approved, update the bounded contracts and deterministic
   tests only. Do not run App Server yet.
4. Regenerate the readiness report, run the full local gate set, push the
   checkpoint and obtain a fresh exact-head review.
5. Request separate merge authorization. Only after PR #26 is merged into a
   fresh `origin/main` worktree may attempt-002 start.
6. During attempt-002, use exactly one App Server process, one thread, at most
   three turns and one fixture mutation; write the planned evidence/result/gate,
   and keep C-503 blocked unless every critical criterion passes.

## Files to open

- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\pr26-reconcile-20260728\docs\research\research-state.yaml`
  - canonical current state, recovery point and blockers.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\pr26-reconcile-20260728\validation\C-501-PR25-POST-MERGE-RECONCILIATION.yaml`
  - dated decision/review log, verification evidence and 2026-07-29 refresh checkpoint.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\pr26-reconcile-20260728\handoffs\C-502-BOUNDED-LIVE-SMOKE-RERUN-2026-07-28.yaml`
  - attempt-002 scope, allowed paths, lifecycle criteria and stop conditions.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\pr26-reconcile-20260728\handoffs\C-502-GOAL-CONTRACT-2026-07-28.yaml`
  - goal, approvals, budgets, evidence and completion contract.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\pr26-reconcile-20260728\scripts\update_capability_readiness_report.py`
  - readiness aggregation and required-gate finalization logic.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\pr26-reconcile-20260728\tests\test_capability_readiness_report.py`
  - regressions for missing/FAIL/INSUFFICIENT/PASS gate behavior.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\c502-app-server-smoke-20260727\agent\state\C-502-result.yaml`
  - immutable attempt-001 result and exact failure stage.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\c502-app-server-smoke-20260727\validation\C-502-GATE.yaml`
  - immutable attempt-001 acceptance verdict.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\c502-app-server-smoke-20260727\docs\research\app-server-smoke-observation.md`
  - evidence-labelled live launch observation.
- `C:\Users\denko\CodexWork\UPE_5.6_worktrees\c502-app-server-smoke-20260727\scripts\run_c502_app_server_smoke.py`
  - historical uncommitted runner; source material only, not an attempt-002 executor.

## Carried-over data

The latest reviewed remote head was
`ec7a552773fb5da160276cbe676b93f44051690e`. Review found one P1: a missing or
non-PASS C-502 gate could be bypassed by result, must-status, backlog or
downstream completion aggregation. The remediation was published at
`f13d197b9909b8f04fc214620573f29121d38ae2`; it derives required gates from
canonical handoff outputs and applies them after all completion sources. It
still requires a fresh exact-head review.
