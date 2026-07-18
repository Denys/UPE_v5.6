# ADR-001 Pro Review

**Reviewer route:** GPT-5.6 Sol Pro  
**Date:** 2026-07-18  
**Verdict:** PASS after targeted repair

## Scope

Fresh-context review of:

- C-101 through C-105 environment evidence;
- ADR-001 and evidence packet;
- `gate-records/ADR-001-PASS.yaml`;
- current draft PR scope and approval boundaries.

## Findings

### PASS

- Windows-native is correctly selected as the current v0 target while the host contract remains portable.
- Codex App Server is the narrowest credible Codex-native execution boundary.
- Provider-specific protocol remains isolated behind an adapter.
- Deterministic environmental validation precedes optional read-only model evaluation.
- Single-agent and fake-adapter-first constraints remain intact.
- The legacy-upstream merge is recorded as a safety incident and is not treated as authorization.

### Repaired before final PASS

1. **SQLite/JSONL crash consistency**

   The earlier ADR named both stores but did not define how a transition survives interruption between the two writes. ADR-001 now uses SQLite as authoritative state with a transactional outbox; JSONL is a replayable and deduplicated audit mirror.

2. **External action retry safety**

   The earlier ADR required idempotency but did not define recovery for an action whose remote result is unknown. ADR-001 now requires stable action IDs, recorded approval scope, provider idempotency keys where available, and reconciliation before retry.

3. **Checkpoint/commit authority**

   The earlier ADR used Git checkpoints while separately requiring approval for commits. ADR-001 now uses host-managed patch snapshots for routine checkpoints; Git commits remain explicit approval-gated milestones.

4. **App Server smoke-test coverage**

   The required live smoke test now includes tool events, approval flow and reconnect behavior in addition to initialize, thread, turn and interrupt.

## Residual non-blocking unknowns

- live App Server smoke test has not yet run;
- Python dependency compatibility awaits `pyproject.toml`;
- no CI checks are configured;
- legacy-upstream merge authorization history remains unknown;
- repository remains intentionally public.

These unknowns block later implementation or release claims, not the architecture decision.

## Final gate

`G-ADR = PASS`

Proceed to `W-201` through `W-210`. Do not merge, release or deploy without separate explicit authorization.
