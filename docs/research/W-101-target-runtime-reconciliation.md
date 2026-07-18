# W-101 Target Runtime Reconciliation

**Status:** authoritative target-specific reconciliation  
**Reviewed:** 2026-07-18  
**Runtime target:** Windows-native Codex  
**Architecture authority:** `docs/architecture/ADR-001-harness-boundary.md`

## Purpose

The original research and build brief contain WSL2-first recommendations. Direct C-101 through C-105 evidence establishes Windows-native Codex as the actual target for v0. This record preserves the older research as historical evidence while preventing its runtime-specific conclusions from overriding the observed target or ADR-001.

## Precedence

For target-runtime decisions, use this order:

1. active user authorization and target constraints;
2. ADR-001 and its gate records;
3. this target-runtime reconciliation;
4. installed-version observations;
5. pre-target research recommendations.

Accordingly, the following statements are historical, not active v0 requirements:

- `docs/research/pattern-comparison.md`: WSL2 wording in comparison 10 and its consolidated diagram;
- `docs/research/chatgpt-work-applicability.md`: the sentence assigning the host harness to a trusted WSL2 host;
- `Pasted markdown.md`: the WSL2-first implementation recommendation.

They remain visible because evidence should not be rewritten merely because the target changed.

## Active target decision

- The architecture uses a portable trusted-host contract.
- Windows-native Codex is the current v0 execution surface.
- WSL2 is `NOT APPLICABLE` to the current target, but remains a possible later portability environment.
- Git worktrees are the default task-isolation mechanism.
- Docker is optional and evidence-triggered.
- Codex App Server is isolated behind a version-pinned adapter.
- The real adapter cannot be marked tested until an initialize/thread/turn/tool/approval/interrupt/reconnect smoke test passes.
- SQLite is authoritative state and emits JSONL through a transactional outbox.
- External actions use a durable action journal and reconciliation before retry.
- Routine checkpoints are host-managed patch snapshots; Git commits remain approval-gated.
- Work and App Server thread history remain supporting context.

## Safety reconciliation

The separately observed legacy-upstream merge is a safety incident, not project authorization. The target PR remains draft and unmerged. Commit, push, PR, merge, release, deployment, visibility changes, external messages, purchases and production mutation remain approval-gated.

The user's current instruction authorizes committing and pushing the reviewed architecture updates to `agent/windows-materialization-handoff-refresh`. It does not authorize merging the PR or modifying another branch.

## Review condition

Any future document that states WSL2 is the active v0 host conflicts with ADR-001 unless it explicitly identifies itself as historical or as a proposed portability extension.
