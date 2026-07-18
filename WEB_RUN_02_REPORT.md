# Web Run 02 Report — Architecture Freeze and Pro Review

**Status:** PASS  
**Completed:** W-101, W-102, P-101, G-ADR, Pro fresh-context review  
**Date:** 2026-07-18

## Architecture decision

1. A portable trusted-host contract owns orchestration; Windows-native Codex is the current v0 target.
2. Codex App Server is the execution boundary, pinned to an exact installed binary and generated schemas.
3. Raw App Server protocol remains inside the provider adapter.
4. SQLite is authoritative lifecycle and action state.
5. JSONL is an append-only audit mirror emitted through a transactional outbox and repaired by replay.
6. Routine checkpoints are host-managed patch snapshots; Git commits remain explicit approval-gated actions.
7. One Git worktree isolates each active task.
8. Deterministic validation governs completion; independent model evaluation is read-only and optional.
9. Credentials, budgets, approvals, action idempotency, audit and recovery remain host-owned.
10. v0 is single-agent and excludes scheduler, UI, issue-tracker and release automation.
11. A live initialize/thread/turn/tool/approval/interrupt/reconnect App Server smoke test is required before the real adapter is called tested.

## Pro review corrections

The fresh-context review found and repaired two architecture ambiguities:

- independent SQLite and JSONL writes had no crash-consistency rule;
- routine Git checkpoints conflicted with the explicit commit-approval boundary.

ADR-001 now requires a SQLite transactional outbox, JSONL replay/deduplication, an external-action journal with reconciliation before retry, and host-managed patch snapshots for ordinary checkpoints.

## Gate result

`gate-records/ADR-001-PASS.yaml` remains `PASS` at schema version `1.1`.

The unexplained legacy-upstream merge remains a safety finding but does not block architecture. It tightens future approval enforcement. The target `Denys/UPE_v5.6#1` PR remains draft and unmerged.

## Delivery state

The reviewed ADR and gate updates are committed and pushed to:

`agent/windows-materialization-handoff-refresh`

Temporary `TEMP_DO_NOT_USE*` files have been removed from the branch.

## Next executable range

`W-201` through `W-210`: schemas, templates, prompts, state/recovery contracts, security, evaluation and operations specifications.

Do not merge, release or deploy without separate explicit authorization.
