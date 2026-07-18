# Web Run 02 Report — Architecture Freeze

**Status:** PASS  
**Completed:** W-101, W-102, P-101, G-ADR  
**Date:** 2026-07-18

## Architecture decision

1. Windows-native trusted host is the active v0 runtime.
2. Codex App Server is the execution boundary, pinned to an exact installed version and schemas.
3. Raw App Server protocol remains inside the provider adapter.
4. SQLite + JSONL + evidence files + Git checkpoints are canonical state.
5. One Git worktree isolates each active task.
6. Deterministic validation governs completion.
7. Independent model evaluation is read-only and optional.
8. Credentials, budgets, approvals, audit and recovery remain host-owned.
9. v0 is single-agent and excludes scheduler/UI/issue-tracker/release automation.
10. A live App Server smoke test is required before the real adapter is called tested.

## Gate result

`gate-records/ADR-001-PASS.yaml`

The unexplained legacy-upstream merge remains a safety finding but does not block architecture. It tightens future approval enforcement. The target `Denys/UPE_v5.6#1` PR remains draft and unmerged.

## Next executable range

`W-201` through `W-210`: schemas, templates, prompts, security, evaluation and operations specifications.
