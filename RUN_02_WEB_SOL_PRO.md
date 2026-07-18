# Run 02 — Web Work architecture freeze

**Surface:** ChatGPT Work on the web, inside the UPE project  
**Model:** GPT-5.6 Sol Pro  
**Effort:** Pro model route, not a Sol reasoning-effort label  
**Why Pro:** This run combines evidence reconciliation, architecture trade-offs, security boundaries and the final indivisible ADR decision.

## Goal

Consume the Local Codex handoff from Run 01 and complete:

- `W-101` — merge target-environment evidence;
- `W-102` — prepare the architecture evidence packet;
- `P-101` — freeze the v0 boundary in `ADR-001`;
- `G-ADR` — issue a deterministic pass or block record.

Do not begin implementation or produce the post-ADR schema/specification bundle in this run.

## Required inputs

1. `handoffs/CODEX_ENVIRONMENT_HANDOFF.yaml`
2. `handoffs/CODEX_ENVIRONMENT_EVIDENCE.md`
3. `chatgpt_work_harness_research_2026-07-18.zip`
4. `chatgpt_work_harness_implementation_routing_2026-07-18.zip`
5. `Pasted markdown.md`
6. UPE v5.6.0:
   - full reference;
   - GPT-5.6 runtime profile;
   - capability/plugin opportunity scan;
   - source map;
   - capability registry template.
7. `AGENTS.md` from the next-runs package as repository operating context, not as architecture evidence.

## Evidence rules

For every material claim, distinguish:

- `Documented`: supported by current official documentation;
- `Observed`: recorded from the installed target environment;
- `Inference`: reasoned from documented and observed evidence;
- `Recommendation`: selected design choice;
- `Unknown`: unresolved and potentially blocking.

Installed behavior wins for compatibility with the installed runtime. Official documentation wins for intended semantics unless direct observation disproves applicability. An unresolved conflict must remain visible; do not massage sources into ceremonial agreement.

## Required work

### W-101 — Merge environment evidence

Update or create:

- `docs/research/source-matrix.md`
- `docs/research/pattern-comparison.md`
- `docs/research/research-state.yaml`
- `docs/research/environment-conflict-log.md`

Requirements:

- separate documented and observed claims;
- tie observations to exact repo/Codex/App Server versions;
- correct stale assumptions;
- preserve experimental/unsupported labels;
- resolve critical unknowns where evidence permits;
- retain unresolved critical unknowns explicitly.

### W-102 — Build the architecture evidence packet

Create:

- `docs/architecture/ADR-001-evidence-packet.md`

It must compare at minimum:

1. Codex App Server versus a custom Responses/Agents SDK loop;
2. trusted-host orchestration versus harness inside the sandbox;
3. explicit durable handoff versus conversation/thread state;
4. deterministic validation versus independent model evaluation;
5. Git worktrees versus container isolation;
6. host-owned credentials, budgets, approvals and audit;
7. provider-portable internal contracts versus Codex-specific adapter behavior;
8. v0 single-agent scope versus deferred multi-agent orchestration.

For each alternative provide:

- evidence;
- benefits;
- costs;
- failure boundary;
- security implications;
- portability implications;
- what future evidence would justify changing the choice.

### P-101 — Freeze ADR-001

Create:

- `docs/architecture/ADR-001-harness-boundary.md`

The ADR must decide:

- Work web responsibilities;
- trusted-host responsibilities;
- Codex App Server adapter boundary;
- workspace/worktree boundary;
- canonical durable state;
- deterministic validator boundary;
- optional read-only evaluator boundary;
- budget and stop controller;
- event/audit log;
- approval and credential ownership;
- provider portability;
- v0 exclusions.

The selected v0 should remain the minimum viable system:

```text
Trusted host orchestrator
  + Codex App Server adapter
  + workspace/worktree manager
  + SQLite state
  + JSONL events
  + deterministic validator
  + optional read-only evaluator
  + budget/stop controller
```

Change this only when the merged evidence demonstrates a material incompatibility.

### G-ADR — Apply the architecture gate

Create exactly one of:

- `gate-records/ADR-001-PASS.yaml`
- `gate-records/ADR-001-BLOCKED.yaml`

A PASS record requires:

- ADR exists;
- all mandatory ADR sections exist;
- every active build-brief invariant maps to an ADR location;
- provider dependencies and failure boundaries are explicit;
- security and approval boundaries are explicit;
- no critical contradiction remains unresolved;
- deferred features remain deferred.

A BLOCKED record must list the exact missing evidence and the smallest next evidence-gathering run. Do not produce a polite pseudo-pass with critical UNKNOWNs hidden in prose, humanity already invented committee minutes for that.

## Forbidden

- no repository implementation;
- no scaffold;
- no state models or schemas beyond the gate record;
- no fake or real adapter;
- no hooks or plugin package;
- no commit, push, PR, merge, release, deployment or external mutation;
- no expansion into multi-agent runtime, scheduler, UI, issue tracker or self-modification.

## Final response

Return:

1. architecture decision in no more than ten bullets;
2. `PASS` or `BLOCKED`;
3. all files created or updated;
4. unresolved `UNKNOWN`s;
5. next executable backlog range:
   - on PASS: `W-201` through `W-210`;
   - on BLOCKED: the exact bounded evidence task only.
