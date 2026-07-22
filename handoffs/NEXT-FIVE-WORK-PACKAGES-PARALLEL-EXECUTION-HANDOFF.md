# Next Five Work Packages: Parallel Execution Handoff

## Current reconciliation — 2026-07-22

The five-run decision below is retained as historical execution evidence; its
original C-405/C-406/C-408 frontier has been completed. C-409 is now locally
accepted at `4d6392bec8bf6ade6e77b5651bd78006576a9180` and is in its serialized
reconciliation/delivery lane. Once adopted, the live ready frontier is `C-502`,
`C-410`, `W-211` and `W-212`.

C-505 is also locally accepted in a separate worktree, but it remains unmerged
and therefore appears as **in development**, not completed or recommended as
fresh work. Its coordinator must rebase and reconcile shared state/report files
after C-409 merges. No live App Server compatibility is claimed until C-502 runs.

## Decision

Start the next implementation wave in a **new coordinator chat**, with five
separate work-package runs. Classify the execution shape as **parallel runs**,
not one bundled change:

1. `C-406` — priority local run.
2. `C-405` — parallel local run.
3. `C-408` — parallel optional local run.
4. `W-211` — parallel Web specification run.
5. `W-212` — parallel Web specification run.

The current chat has already carried the C-404 implementation, report-hook
integration and report redesign. A fresh coordinator context reduces accidental
reuse of stale branch/evidence assumptions. Five dedicated chats are preferable
to one large multi-agent chat because each run needs a persistent isolated Git
identity and an independently reviewable handoff. If a single coordinator chat
uses subagents, run no more than the three local packages concurrently and keep
all Git integration in the coordinator.

## Start condition

Start only after the capability-readiness report enhancement containing this
handoff is merged. Each run must:

- fetch and branch from the then-current `origin/main`;
- re-read root `AGENTS.md` and the canonical backlog entry;
- confirm all declared dependencies are accepted by current result/gate/Git
  evidence;
- stop on material drift rather than inheriting the commit recorded in this
  handoff as a permanent base.

The user has granted standing implementation and GitHub-delivery authority for
bounded work packages. That does not authorize release, deployment, repository
visibility changes, destructive cleanup, unrelated external actions or mutation
of protected user-owned state.

## Live dependency frontier

| Priority | WP | Surface | Owned functional paths | Rough effort | Direct application |
|---:|---|---|---|---|---|
| 1 | `C-406` | Local Codex | `src/harness/state_store.py`, `src/harness/events.py`, `tests/unit/test_state_store.py`, `tests/unit/test_events.py` | 2–4 engineering days | Makes SQLite authoritative, emits replayable JSONL and unlocks `C-407`, `C-409`, `C-410` and the App Server path. |
| 2 | `C-405` | Local Codex | `src/harness/workspace.py`, `tests/unit/test_workspace.py` | 1.5–3 engineering days | Contains one task per workspace, rejects traversal/reparse escape and supplies containment for CLI/recovery/security work. |
| 3 | `C-408` | Local Codex | `src/harness/evaluation.py`, `tests/unit/test_evaluation.py` | 1–2 engineering days | Adds optional read-only judgment for irreducible criteria without overriding deterministic failure. |
| 4 | `W-211` | ChatGPT Work Web | `docs/work/SCHEDULED_TASK_PATTERNS.md` | 3–5 hours | Defines narrow web-only monitoring/research schedules; it is not the harness scheduler. |
| 5 | `W-212` | ChatGPT Work Web | `docs/work/UPE_V5_6_1_MIGRATION_NOTES.md` | 4–8 hours | Explains how volatile runtime behavior moves into dated adapters/skills/evals without changing the stable core. |

All five dependency sets are currently satisfied. Their declared outputs do not
overlap. They remain separate because their task contracts, acceptance evidence,
surface ownership and review risks differ.

## Shared-file ownership rule

Workers own only their functional paths plus unique task-specific evidence such
as `agent/state/<WP>-pre-edit-context.yaml`, `agent/state/<WP>-result.yaml` and
`validation/<WP>-GATE.yaml`.

Workers MUST NOT independently edit these shared integration paths:

- `AGENTS.md`;
- `docs/research/research-state.yaml`;
- `scripts/update_capability_readiness_report.py`;
- `tests/test_capability_readiness_report.py`;
- `UPE_5.6.0_to_5.6.1_capability_readiness_report_2026-07-19.html`.

The coordinator serializes those files into each WP branch after functional
review and immediately before that WP's pull request. This satisfies the
project-wide directive that every completed and merged WP refresh the report
without creating five conflicting report copies.

## Recommended execution topology

```text
Fresh coordinator chat
├─ Run A / worktree A: C-406  ─┐
├─ Run B / worktree B: C-405   ├─ coordinator review + serial integration
├─ Run C / worktree C: C-408   ┤  C-406 → C-405 → C-408 → W-211 → W-212
├─ Run D / Web chat: W-211     ┤
└─ Run E / Web chat: W-212   ──┘
```

Functional work may overlap in elapsed time. Pull requests and shared-state
refreshes are intentionally serialized. Prefer merging `C-406` first because it
has the widest downstream unlock; merging it makes `C-407` ready.

Expected elapsed time:

- five isolated runs in parallel: roughly 2–4 engineering days, plus serial
  review/integration;
- the same work strictly sequentially: about 5.4–10.6 engineering days, plus
  integration.

These are planning ranges, not commitments. They exclude CI queue, review and
unexpected contract repairs.

## Coordinator workflow

For each WP, in the merge order above:

1. Reverify `origin/main`, worktree status, protected artifacts, stash and the
   separate dirty `UPE_5.6_pr1_fix` worktree.
2. Review the worker's exact owned-path diff and task-specific evidence.
3. Rebase or recreate the integration branch from current `origin/main`; never
   force-push or overwrite another run.
4. Run focused tests, then the warranted integrated/full repository gate.
5. Update mutable current state and run:

   ```powershell
   uv run python scripts/update_capability_readiness_report.py
   uv run pytest -q tests/test_capability_readiness_report.py
   uv run python scripts/update_capability_readiness_report.py --check
   ```

6. Confirm the generated “Next suggested implementation run” card reflects the
   new dependency graph and that report light/dark/details interactions remain
   healthy if the report shell changed.
7. Stage only the WP's functional paths, unique result/gate records and the
   coordinator-owned shared refresh. Commit, push, open and merge one PR.
8. Fast-forward primary `main`, run the post-merge report check, then move to the
   next already-finished worker branch.

## Per-run contracts

### Run A — C-406

Read the canonical `C-406` entry, `ADR-001`, C-401/C-403 result and gates,
`docs/work/RECOVERY_EVALUATION_OPERATIONS.md`, and current state/lifecycle code.

Required behavior:

- SQLite is authoritative state;
- state/event writes use a transactional outbox boundary;
- JSONL is append-only and replayable enough for recovery;
- large values remain referenced, not embedded;
- redaction markers are representable;
- persistence happens before the next external action.

Do not add retries/budgets (`C-407`), worktree containment (`C-405`), CLI
(`C-409`), real App Server behavior (`C-501`) or recovery policy beyond the
storage ports needed by C-406.

### Run B — C-405

Read the canonical `C-405` entry, `ADR-001`, C-305/C-403 evidence and
`docs/work/SECURITY_THREAT_BOUNDARY.md`.

Required behavior:

- one task maps to one exact contained workspace;
- traversal, symlink/junction/reparse and root-identity escapes fail closed;
- unrelated worktrees cannot be removed;
- dirty state is detected and handled without data loss;
- cleanup targets are explicitly resolved and verified.

Do not add persistence, CLI/doctor, recovery orchestration or broad host cleanup.

### Run C — C-408

Read the canonical `C-408` entry, W-203/W-207, C-404 result/gate and
`src/harness/validation.py`.

Required behavior:

- evaluator is optional and read-only;
- deterministic checks remain primary and deterministic failure cannot be
  overridden;
- criteria cannot be rewritten or expanded;
- `PASS | FAIL | INSUFFICIENT_EVIDENCE` semantics remain exact;
- no evaluator call occurs when deterministic evidence is sufficient.

Do not add a real provider, prompt routing, persistence, retries or CLI behavior.

### Run D — W-211

Read W-201, W-202 and the canonical W-211 entry. Produce only
`docs/work/SCHEDULED_TASK_PATTERNS.md` with web-only research/monitoring examples,
manual-run prerequisites, narrow permission requirements and explicit stop/report
rules. State clearly that this is not the v0 harness scheduler and proves no local
repository execution.

### Run E — W-212

Read W-201, W-202, W-210, the UPE v5.6.0 full reference and the canonical W-212
entry. Produce only `docs/work/UPE_V5_6_1_MIGRATION_NOTES.md`. Keep the stable
core unchanged; place volatile runtime behavior in dated adapters, skills or
evaluations and record the naming boundary between “harness v0” and planned UPE
v5.6.1.

## Worker handoff format

Each worker returns:

- branch/worktree/base and exact HEAD;
- dependency evidence inspected;
- files changed;
- behavior implemented and explicit exclusions;
- focused and regression commands with exact results;
- result/gate paths and hashes;
- unresolved risks;
- one recommended coordinator action.

Do not let a worker merge, alter shared report/current-state files, delete a
worktree or clean protected files.

## Stop conditions

Stop the affected run if:

- current `origin/main` or accepted dependency evidence materially diverges;
- a task requires another WP's owned functional path;
- output ownership overlaps another active run;
- a required semantic cannot be tested deterministically;
- protected untracked files, the named recovery stash or the dirty
  `UPE_5.6_pr1_fix` worktree would be modified;
- completion would require release, deployment, visibility change, destructive
  cleanup or unrelated external authority.

Other independent runs may continue when one run stops, but the coordinator must
record the blocker before integrating downstream work.
