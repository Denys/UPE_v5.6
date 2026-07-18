# Next ChatGPT Work Task — Merge Local Evidence and Freeze ADR

Use this only after the local Codex handoff packet exists.

## Inputs

- `handoffs/CODEX_ENVIRONMENT_HANDOFF.yaml`
- `handoffs/CODEX_ENVIRONMENT_EVIDENCE.md`
- existing `docs/research/source-matrix.md`
- existing `docs/research/pattern-comparison.md`
- existing `docs/research/research-state.yaml`
- active build brief
- `CURRENT_PRODUCT_DELTA_2026-07-18.md`

## Stage 1 — Sol High

Complete `W-101` and `W-102`:

1. Merge direct target-environment observations without overwriting documented/observed/inferred labels.
2. Resolve source/version conflicts by authority and discriminating evidence.
3. Keep unresolved material facts as `UNKNOWN`.
4. Produce `docs/research/environment-conflict-log.md`.
5. Produce `docs/architecture/ADR-001-evidence-packet.md`.

## Stage 2 — GPT-5.6 Sol Pro

Complete `P-101` in a fresh context:

Create `docs/architecture/ADR-001-harness-boundary.md` and decide:

- Work versus host versus Codex ownership;
- Codex App Server versus custom Agents SDK/Responses loop;
- canonical durable state;
- worktree/workspace boundary;
- deterministic versus model evaluation;
- security and approval authority;
- failure/recovery boundaries;
- provider dependencies and migration path;
- evidence that would justify changing the architecture.

Return `PASS`, `FAIL`, or `INSUFFICIENT_EVIDENCE` for every required ADR section. Broad implementation remains blocked until `G-ADR` passes.
