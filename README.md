# UPE v5.6 Long-Running Harness

This repository is building a minimal, resumable, independently verifiable software-engineering harness around a portable trusted-host contract and a Windows-native Codex App Server adapter.

## Current status

**Status date:** 2026-07-19

**Accepted baseline:** `main@d0fbfd56c6b533da62db3e4bea147496345b6c90`

**Architecture:** `ADR-001` accepted; `G-ADR = PASS`

**Specification phase:** `W-201` through `W-210` = `PASS`

**Specification adoption:** PR `#3` merged at `d0fbfd56c6b533da62db3e4bea147496345b6c90`

**Runtime implementation:** `C-301 = PASS`; `C-302 = TESTED_LOCALLY`

The W-200 specification acceptance gate is `PASS`. The user separately authorized
local implementation of `C-301` and `C-302`; that authorization does not include a
commit, push, PR, merge, release, deployment, visibility change, or other external
mutation.

## Minimal local scaffold

The current scaffold intentionally contains only package metadata, the importable
`harness` package root, one package-level test, and the reserved fixture-repository
boundary. State, adapters, orchestration, CLI, persistence, and recovery remain later
canonical tasks.

```powershell
uv sync --all-groups
uv run python -c "import harness; print(harness.__version__)"
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
```

## Authority and current-state sources

Use these in order after active instructions:

1. `Pasted markdown.md` — authoritative build brief.
2. `docs/architecture/ADR-001-harness-boundary.md` and `gate-records/ADR-001-PASS.yaml` — accepted architecture and gate.
3. `docs/research/research-state.yaml` — mutable current phase and recovery state.
4. `chatgpt_work_harness_implementation_routing_2026-07-18/harness_implementation_backlog.yaml` — canonical task definitions and dependencies.
5. `AGENTS.md` — repository operating rules.

The dated routing package, Run 01/02 prompts, archives, and C-101…C-105 handoffs are preserved point-in-time evidence. Their embedded status and next-action fields are historical; do not use them instead of `docs/research/research-state.yaml`.

## W-201…W-210 canonical mapping

| ID | Canonical task | Required output | Dependency |
|---|---|---|---|
| `W-201` | Write the ChatGPT Work loop adapter | `docs/work/CHATGPT_WORK_LOOP_ADAPTER.md` | `G-ADR` |
| `W-202` | Finalize the web/local Work/local Codex routing matrix | `docs/work/WEB_VS_LOCAL_ROUTING.md` | `G-ADR` |
| `W-203` | Define the generator/verifier protocol | `docs/work/GENERATOR_VERIFIER_PROTOCOL.md` | `G-ADR` |
| `W-204` | Define the Work-to-Codex and Codex-to-Work handoff protocol | `docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md`, `schemas/handoff.schema.yaml` | `G-ADR` |
| `W-205` | Design the Work goal contract schema | `schemas/goal_contract.schema.yaml` | `G-ADR` |
| `W-206` | Design the Work loop-state schema | `schemas/work_loop_state.schema.yaml` | `G-ADR` |
| `W-207` | Design the verifier-result schema | `schemas/verifier_result.schema.yaml` | `W-203` |
| `W-208` | Design the capability-execution record | `schemas/capability_execution_record.schema.yaml` | `G-ADR` |
| `W-209` | Create the human-readable Work acceptance cases | `evals/work_loop_acceptance_cases.yaml` | `W-201`…`W-204` |
| `W-210` | Write the dated model/effort routing reference | `docs/work/MODEL_EFFORT_ROUTING.md` | `G-ADR` |

Phase-level Web/Work artifacts also define the security/threat boundary, recovery/evaluation/operations contract, cross-document/static-validation gate, and the local implementation handoff. These are phase acceptance artifacts; no additional W-ID mapping is inferred beyond the canonical backlog.

## Runtime boundary

- Windows-native Codex is the current v0 target behind a provider-portable host contract.
- SQLite is authoritative lifecycle/action state; JSONL is a replayable audit mirror emitted through a transactional outbox.
- External actions use stable IDs, recorded approval scope, and reconciliation before retry.
- Routine checkpoints are host-managed patch snapshots; Git commits are separately authorized milestones.
- Deterministic validation precedes optional read-only model evaluation.
- v0 remains single-agent and fake-adapter-first.

`C-301` and `C-302` are complete on the local implementation worktree. The next
canonical task is `C-303`, which requires a new active task authorization. Publication
of the local scaffold requires separate commit/push/PR authorization.
