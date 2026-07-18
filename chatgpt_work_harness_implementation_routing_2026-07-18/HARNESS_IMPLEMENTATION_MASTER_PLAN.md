# Long-Running Agent Harness — Merged Implementation Master Plan

**Date:** 18 July 2026  
**Status:** research complete; implementation not started  
**Immediate next owner:** Local Codex, tasks `C-101` and `C-102`  
**Hard gate:** no broad implementation before `ADR-001` and `G-ADR` pass

## Executive routing decision

```text
Uploaded/connected/cloud sources + reviewable artifacts are sufficient
    → ChatGPT Work web

A private local document, desktop application, or UI rendering is evidence
    → Local Work

Git, shell, tests, worktrees, typed state, App Server, recovery or executable proof is required
    → Local Codex
```

For this project, **Local Work has no mandatory critical-path task**. The current inputs are already uploaded, and the remaining local work is repository/runtime engineering. Sending it through Local Work first would be an additional ceremonial corridor between the door and the room.

## What is already complete

- **R-001 — Complete the 30-source OpenAI/Anthropic source matrix**: docs/research/source-matrix.md
- **R-002 — Complete the ten mandatory architecture comparisons**: docs/research/pattern-comparison.md
- **R-003 — Assess ChatGPT Work applicability and limits**: docs/research/chatgpt-work-applicability.md
- **R-004 — Validate and package the research phase**: validation-report.json, MANIFEST.sha256, chatgpt_work_harness_research_2026-07-18.zip
- **R-005 — Merge implementation TODOs, surface split, and model routing**: HARNESS_IMPLEMENTATION_MASTER_PLAN.md, harness_implementation_backlog.yaml, CURRENT_PRODUCT_DELTA_2026-07-18.md, WORK_CODEX_HANDOFF_TEMPLATE.yaml

## Critical path

```text
Research package PASS
→ local repository/runtime/App Server evidence
→ Work web evidence merge
→ Pro ADR-001 architecture freeze
→ Work web contract/schema bundle
→ Local Codex scaffold
→ state model → fake adapter → lifecycle → deterministic validation
→ workspace isolation → durable state/budgets/CLI
→ App Server adapter → recovery → security → integration
→ unit/integration/eval evidence
→ Work web final report
→ Pro fresh-context release review
→ Local Codex corrections and package
```

## Model and effort routing

| Route | Use here | Do not use for |
|---|---|---|
| **Sol High** | Default for research merges, specifications, routine multi-file implementation, validators, tests, docs, packaging, and ordinary fixes | Unresolved architecture or subtle state/security/recovery failures |
| **Sol Max / highest exposed Sol effort** | App Server protocol integration, crash recovery, idempotency, permission boundaries, path containment edge cases, persistent failures, and final multi-component integration | Long source lists, routine coding, test execution, ZIPs, or mere importance |
| **Sol Pro** | `P-101` ADR-001 and `P-701` fresh read-only release review; also conflict resolution when evidence remains materially inconsistent | Copying files, writing validators, lint fixes, manifests, routine scheduled monitoring |
| **Ultra** | Not on the v0 runtime path. At most, independent read-only research branches with one coordinator | Shared mutable implementation, serial bottlenecks, side effects, or an excuse to multiply agents |

**Important:** Pro is a distinct model route, not an effort level above Max. `max` is a reasoning effort where exposed; standard ChatGPT uses product labels such as Very High and Pro. This plan says “Max / highest exposed Sol effort” deliberately.

## Surface-owned queues

### ChatGPT Work web

| ID | Status | Model | Task | Depends on |
|---|---|---|---|---|
| `R-001` | DONE | Sol High | Complete the 30-source OpenAI/Anthropic source matrix | — |
| `R-002` | DONE | Sol High | Complete the ten mandatory architecture comparisons | R-001 |
| `R-003` | DONE | Sol High | Assess ChatGPT Work applicability and limits | R-001, R-002 |
| `R-004` | DONE | Sol High | Validate and package the research phase | R-001, R-002, R-003 |
| `R-005` | DONE | Sol High | Merge implementation TODOs, surface split, and model routing | R-001, R-002, R-003, R-004 |
| `W-101` | BLOCKED | Sol High | Merge Codex target-environment evidence into the research package | C-105 |
| `W-102` | BLOCKED | Sol High | Prepare the architecture decision evidence packet | W-101 |
| `W-201` | BLOCKED | Sol High | Write the ChatGPT Work loop adapter | G-ADR |
| `W-202` | BLOCKED | Sol High | Finalize the web/local Work/local Codex routing matrix | G-ADR |
| `W-203` | BLOCKED | Sol High | Define the generator/verifier protocol | G-ADR |
| `W-204` | BLOCKED | Sol High | Define the Work-to-Codex and Codex-to-Work handoff protocol | G-ADR |
| `W-205` | BLOCKED | Sol High | Design the Work goal contract schema | G-ADR |
| `W-206` | BLOCKED | Sol High | Design the Work loop-state schema | G-ADR |
| `W-207` | BLOCKED | Sol High | Design the verifier-result schema | W-203 |
| `W-208` | BLOCKED | Sol High | Design the capability-execution record | G-ADR |
| `W-209` | BLOCKED | Sol High | Create the human-readable Work acceptance cases | W-201, W-202, W-203, W-204 |
| `W-210` | BLOCKED | Sol High | Write the dated model/effort routing reference | G-ADR |
| `W-211` | BLOCKED | Sol High | Define web scheduled-task patterns for research and monitoring | W-201 |
| `W-212` | BLOCKED | Sol High | Prepare UPE runtime-layer migration notes without changing the stable core | W-201, W-202, W-210 |
| `W-701` | BLOCKED | Sol High | Synthesize the implementation evidence and draft the final report | C-604, C-605, C-606 |

### ChatGPT Pro / Work

| ID | Status | Model | Task | Depends on |
|---|---|---|---|---|
| `P-101` | BLOCKED | Sol Pro | Freeze the v0 harness boundary in ADR-001 | W-102 |
| `P-701` | BLOCKED | Sol Pro | Perform a fresh-context read-only release review | W-701 |

### Local Work

| ID | Status | Model | Task | Depends on |
|---|---|---|---|---|
| `LW-001` | OPTIONAL | Sol High | Inspect private local non-repository documents when upload is inappropriate | — |
| `LW-002` | OPTIONAL | Sol High | Perform desktop application or visual/template QA | — |
| `LW-003` | OPTIONAL | Sol High | Demonstrate a desktop workflow for later skill design | — |

### Local Codex

| ID | Status | Model | Task | Depends on |
|---|---|---|---|---|
| `C-101` | READY | Sol High | Inspect the target repository and preserve unrelated local state | R-005 |
| `C-102` | READY | Sol High | Inventory the WSL2/Codex runtime and development dependencies | R-005 |
| `C-103` | PLANNED | Sol High | Capture the installed App Server protocol surface | C-102 |
| `C-104` | PLANNED | Sol High | Materialize the web research package in the target repository | C-101 |
| `C-105` | PLANNED | Sol High | Produce the Codex-to-Work environment handoff packet | C-101, C-102, C-103, C-104 |
| `C-301` | BLOCKED | Sol High | Re-inspect repository state immediately before edits | G-ADR, W-204, W-205, W-206, W-207, W-208 |
| `C-302` | BLOCKED | Sol High | Create the minimal Python/uv repository scaffold | C-301 |
| `C-303` | BLOCKED | Sol High | Materialize accepted research, ADR, schemas, templates, and prompts | C-302, W-209, W-210 |
| `C-304` | BLOCKED | Sol High | Create a short AGENTS.md map and repository operating README | C-302, C-303 |
| `C-305` | BLOCKED | Sol High | Create the fixture repository and deterministic baseline commands | C-302 |
| `C-306` | BLOCKED | Sol High | Create schema and package validators | C-303 |
| `C-401` | BLOCKED | Sol High | Implement typed Goal, Task, Run, Event, configuration, and lifecycle models | C-304, C-305, C-306 |
| `C-402` | BLOCKED | Sol High | Implement the provider adapter interface and fake adapter | C-401 |
| `C-403` | BLOCKED | Sol High | Implement the lifecycle/orchestrator against the fake adapter | C-402 |
| `C-404` | BLOCKED | Sol High | Implement deterministic validation and evidence records | C-403, C-305 |
| `C-405` | BLOCKED | Sol High | Implement workspace/worktree isolation and path containment | C-403, C-305 |
| `C-406` | BLOCKED | Sol High | Implement SQLite state persistence and append-only JSONL events | C-401, C-403 |
| `C-407` | BLOCKED | Sol High | Implement budgets, stop rules, retry/backoff, and no-progress detection | C-403, C-406 |
| `C-408` | BLOCKED | Sol High | Implement optional read-only model evaluator interface | C-404, W-203, W-207 |
| `C-409` | BLOCKED | Sol High | Implement the CLI and harness doctor | C-403, C-404, C-405, C-406, C-407 |
| `C-410` | BLOCKED | Sol High | Document threat model, state model, evaluation plan, and operations | C-401, C-404, C-405, C-406, C-407, C-409 |
| `C-501` | BLOCKED | Sol Max / highest exposed Sol effort | Implement the Codex App Server adapter | C-103, C-402, C-406, C-407 |
| `C-502` | BLOCKED | Sol High | Run a controlled Codex App Server smoke task | C-501, C-305, C-409 |
| `C-503` | BLOCKED | Sol Max / highest exposed Sol effort | Implement crash/restart and process-state reconciliation | C-406, C-501, C-502 |
| `C-504` | BLOCKED | Sol Max / highest exposed Sol effort | Implement checkpoint and partial-failure recovery | C-405, C-406, C-503 |
| `C-505` | BLOCKED | Sol Max / highest exposed Sol effort | Implement permissions, approval gates, command policy, and redaction | C-403, C-405, C-406, C-501 |
| `C-506` | BLOCKED | Sol Max / highest exposed Sol effort | Integrate state, workspace, validation, App Server, recovery, and security | C-409, C-501, C-503, C-504, C-505 |
| `C-601` | BLOCKED | Sol High | Complete unit-test coverage for all required behaviors | C-506 |
| `C-602` | BLOCKED | Sol High | Complete the ten required integration tests | C-506 |
| `C-603` | BLOCKED | Sol High | Create the six representative evaluation fixtures | C-506 |
| `C-604` | BLOCKED | Sol High | Run repeated model-dependent trials and record metrics | C-603, C-502 |
| `C-605` | BLOCKED | Sol High | Run the complete deterministic quality suite | C-601, C-602, C-603 |
| `C-606` | BLOCKED | Sol High | Run security, secret, malicious-instruction, and no-external-mutation checks | C-505, C-602, C-603 |
| `C-701` | BLOCKED | Sol High | Apply only accepted release-review corrections | P-701 |
| `C-702` | BLOCKED | Sol High | Rerun all deterministic tests after corrections | C-701 |
| `C-703` | BLOCKED | Sol High | Package the v0 artifacts, documentation, manifest, and archive | C-702 |
| `C-704` | APPROVAL | Sol High | Create a local Git commit for the accepted release candidate | C-703 |

## Authoritative merged backlog

### 0-research

#### R-001 — Complete the 30-source OpenAI/Anthropic source matrix

- **Status:** DONE  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** none  
- **Scope:** Current-source research and evidence classification.
- **Outputs:** `docs/research/source-matrix.md`
- **Done evidence:** 30 primary source IDs; required fields present; exact repository refs recorded

#### R-002 — Complete the ten mandatory architecture comparisons

- **Status:** DONE  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** R-001  
- **Scope:** Compare App Server/custom loop, state, evaluators, isolation, tools, and hosting.
- **Outputs:** `docs/research/pattern-comparison.md`
- **Done evidence:** comparisons 1-10 present; recommended v0 boundary documented

#### R-003 — Assess ChatGPT Work applicability and limits

- **Status:** DONE  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** R-001, R-002  
- **Scope:** Separate Work-native knowledge work from host/Codex enforcement.
- **Outputs:** `docs/research/chatgpt-work-applicability.md`
- **Done evidence:** Work/native/adapted/host boundary recorded; known unknowns recorded

#### R-004 — Validate and package the research phase

- **Status:** DONE  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** R-001, R-002, R-003  
- **Scope:** Package research without claiming runtime implementation.
- **Outputs:** `validation-report.json`, `MANIFEST.sha256`, `chatgpt_work_harness_research_2026-07-18.zip`
- **Done evidence:** structural validation PASS; archive integrity PASS

#### R-005 — Merge implementation TODOs, surface split, and model routing

- **Status:** DONE  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** R-001, R-002, R-003, R-004  
- **Scope:** Create one authoritative backlog and derived surface queues; do not duplicate tasks.
- **Outputs:** `HARNESS_IMPLEMENTATION_MASTER_PLAN.md`, `harness_implementation_backlog.yaml`, `CURRENT_PRODUCT_DELTA_2026-07-18.md`, `WORK_CODEX_HANDOFF_TEMPLATE.yaml`
- **Done evidence:** unique task IDs; valid dependency graph; acceptance criteria mapped; ZIP integrity PASS

### 1-pre-adr-evidence

#### C-101 — Inspect the target repository and preserve unrelated local state

- **Status:** READY  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** R-005  
- **Scope:** Read-only repository orientation. Do not edit implementation files yet.
- **Outputs:** `docs/research/local-target-context.md`
- **Done evidence:** repository root/ref recorded; git status recorded; README/AGENTS/manifests inspected; unrelated changes preserved
- **Notes:** Stop BLOCKED if the current directory is not the intended repository or repository identity is ambiguous.

#### C-102 — Inventory the WSL2/Codex runtime and development dependencies

- **Status:** READY  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** R-005  
- **Scope:** Run bounded version/help/doctor checks. No broad implementation.
- **Outputs:** `docs/research/codex-runtime-observations.md`
- **Done evidence:** Python, uv, Git, worktree support and OS recorded; Codex desktop/CLI version recorded; App Server availability recorded; missing dependencies identified without exposing secrets
- **Escalation:** Use sol_max only if version/runtime evidence conflicts or App Server behavior is ambiguous.
- **Notes:** Current documented GPT-5.6 minimums to verify locally: desktop 26.707.30751; Codex CLI 0.144.0.

#### C-103 — Capture the installed App Server protocol surface

- **Status:** PLANNED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-102  
- **Scope:** Generate installed-version TypeScript/JSON schemas or record the exact blocker.
- **Outputs:** `docs/research/app-server-protocol-observations.md`, `docs/research/generated-app-server-schema/`
- **Done evidence:** initialize/help or schema generation observed; exact Codex version tied to generated schema; experimental fields labeled; no raw protocol assumptions leaked into architecture
- **Escalation:** Use sol_max only for protocol-version conflicts, event-order ambiguity, or undocumented behavior.

#### C-104 — Materialize the web research package in the target repository

- **Status:** PLANNED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-101  
- **Scope:** Copy accepted research artifacts into the repository. Do not start broad implementation.
- **Outputs:** `docs/research/source-matrix.md`, `docs/research/pattern-comparison.md`, `docs/research/chatgpt-work-applicability.md`, `docs/research/research-state.yaml`
- **Done evidence:** files copied without evidence-label rewrites; checksums compared; repository diff inspected

#### C-105 — Produce the Codex-to-Work environment handoff packet

- **Status:** PLANNED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-101, C-102, C-103, C-104  
- **Scope:** Return only evidence required for web merge and ADR.
- **Outputs:** `handoffs/CODEX_ENVIRONMENT_HANDOFF.yaml`, `handoffs/CODEX_ENVIRONMENT_EVIDENCE.md`
- **Done evidence:** exact commands and observed results recorded; repo/ref/version recorded; conflicts and unknowns explicit; no unsupported completion claim
- **Notes:** This is the immediate local deliverable. It is not the harness implementation.

### 2-architecture-gate

#### W-101 — Merge Codex target-environment evidence into the research package

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-105  
- **Scope:** Reconcile current official documentation with installed target behavior.
- **Outputs:** `docs/research/source-matrix.md (updated)`, `docs/research/pattern-comparison.md (updated)`, `docs/research/research-state.yaml (updated)`, `docs/research/environment-conflict-log.md`
- **Done evidence:** documented vs observed claims separated; stale claims corrected; critical UNKNOWNs resolved or retained
- **Escalation:** Escalate unresolved high-impact source/runtime conflicts to sol_pro in P-101.

#### W-102 — Prepare the architecture decision evidence packet

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** W-101  
- **Scope:** Prepare concise decision inputs; do not pre-ordain the conclusion.
- **Outputs:** `docs/architecture/ADR-001-evidence-packet.md`
- **Done evidence:** alternatives, tradeoffs, security implications and change triggers mapped; all active brief constraints represented

#### P-101 — Freeze the v0 harness boundary in ADR-001

- **Status:** BLOCKED  
- **Owner:** ChatGPT Pro / Work  
- **Model:** Sol Pro  
- **Critical path:** yes  
- **Dependencies:** W-102  
- **Scope:** Highest-value indivisible judgment: decide Work/host/Codex/state/evaluator/security boundary.
- **Outputs:** `docs/architecture/ADR-001-harness-boundary.md`
- **Done evidence:** minimum viable architecture selected; rejected alternatives explained; provider dependencies and failure boundaries explicit; security implications explicit; evidence that would justify a change recorded; no critical unresolved contradiction
- **Notes:** Pro is used here for coherent architecture judgment, not for file copying or YAML formatting.

#### G-ADR — Architecture gate: block broad implementation until ADR-001 passes

- **Status:** BLOCKED  
- **Owner:** Coordinator gate  
- **Model:** Deterministic gate  
- **Critical path:** yes  
- **Dependencies:** P-101  
- **Scope:** This gate is a hard dependency for every broad implementation task.
- **Outputs:** `gate-records/ADR-001-PASS.yaml`
- **Done evidence:** ADR exists; all required ADR sections present; critical constraints mapped; critical FAIL/UNKNOWN repaired or explicitly blocking

### 3-local-work-optional

#### LW-001 — Inspect private local non-repository documents when upload is inappropriate

- **Status:** OPTIONAL  
- **Owner:** Local Work  
- **Model:** Sol High  
- **Critical path:** no  
- **Dependencies:** none  
- **Scope:** Use only when a private local document materially affects the task.
- **Outputs:** `review artifact or local evidence note`
- **Done evidence:** only necessary files granted; no repository mutation performed

#### LW-002 — Perform desktop application or visual/template QA

- **Status:** OPTIONAL  
- **Owner:** Local Work  
- **Model:** Sol High  
- **Critical path:** no  
- **Dependencies:** none  
- **Scope:** Use for Word/Excel/PowerPoint/PDF/browser UI evidence, not Git/tests.
- **Outputs:** `visual QA report`, `screenshots/evidence when appropriate`
- **Done evidence:** rendered artifact inspected in the actual application; defects listed

#### LW-003 — Demonstrate a desktop workflow for later skill design

- **Status:** OPTIONAL  
- **Owner:** Local Work  
- **Model:** Sol High  
- **Critical path:** no  
- **Dependencies:** none  
- **Scope:** Use only when the workflow is easier to demonstrate than describe.
- **Outputs:** `workflow demonstration notes`
- **Done evidence:** steps and UI evidence captured; no autonomous external action

### 3-web-specification

#### W-201 — Write the ChatGPT Work loop adapter

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR  
- **Scope:** Work-native operator/research/deliverable layer, not host runtime state.
- **Outputs:** `docs/work/CHATGPT_WORK_LOOP_ADAPTER.md`
- **Done evidence:** goal, repair, eval, checkpoint, no-progress and escalation rules documented

#### W-202 — Finalize the web/local Work/local Codex routing matrix

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR  
- **Scope:** Choose surface before model. Web first unless local evidence/execution is required.
- **Outputs:** `docs/work/WEB_VS_LOCAL_ROUTING.md`
- **Done evidence:** every task class has one primary owner; fallback does not duplicate completed work; local Work remains narrow and non-repository

#### W-203 — Define the generator/verifier protocol

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR  
- **Scope:** Use separate evaluator only where deterministic checks cannot settle completion.
- **Outputs:** `docs/work/GENERATOR_VERIFIER_PROTOCOL.md`
- **Done evidence:** deterministic-first rule; read-only independent evaluator contract; PASS/FAIL/INSUFFICIENT_EVIDENCE schema; scope expansion forbidden
- **Escalation:** Use sol_pro for final review only if acceptance involves substantial subjective judgment.

#### W-204 — Define the Work-to-Codex and Codex-to-Work handoff protocol

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR  
- **Scope:** Make cross-surface state explicit and versionable.
- **Outputs:** `docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md`, `schemas/handoff.schema.yaml`
- **Done evidence:** authoritative inputs, scope, MUST IDs, outputs, evidence and approval fields required; no hidden conversation memory required for resume

#### W-205 — Design the Work goal contract schema

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR  
- **Scope:** Design schema; local Codex later validates and materializes code models.
- **Outputs:** `schemas/goal_contract.schema.yaml`
- **Done evidence:** objective, done conditions, constraints, tools, approvals, budget and outputs represented
- **Escalation:** Use sol_max_or_highest_exposed only if schema invariants conflict with runtime state semantics.

#### W-206 — Design the Work loop-state schema

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR  
- **Scope:** Compact project-level handoff state, not the host SQLite schema.
- **Outputs:** `schemas/work_loop_state.schema.yaml`
- **Done evidence:** status, iteration, evidence, failed checks, remaining, approvals and stop reason represented
- **Escalation:** Use sol_max_or_highest_exposed for subtle state/terminal-state conflicts.

#### W-207 — Design the verifier-result schema

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** W-203  
- **Scope:** Structured read-only evaluation result.
- **Outputs:** `schemas/verifier_result.schema.yaml`
- **Done evidence:** criterion-level verdicts; evidence references; smallest correction; release-blocking flag; insufficient-evidence state

#### W-208 — Design the capability-execution record

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR  
- **Scope:** Record actual exposure and action boundaries without inventing capabilities.
- **Outputs:** `schemas/capability_execution_record.schema.yaml`
- **Done evidence:** surface, capability, permission, validation, fallback and residual limits represented

#### W-209 — Create the human-readable Work acceptance cases

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** W-201, W-202, W-203, W-204  
- **Scope:** Acceptance cases for the Work-facing layer.
- **Outputs:** `evals/work_loop_acceptance_cases.yaml`
- **Done evidence:** success, failed verification, no-progress, read-only verifier, scheduled monitor, mobile/web/local fallback, concurrent-write prevention and local-folder assumption cases
- **Escalation:** Use sol_max_or_highest_exposed for adversarial case coverage and negative tests.

#### W-210 — Write the dated model/effort routing reference

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR  
- **Scope:** Separate model tier, effort, Pro, and orchestration controls.
- **Outputs:** `docs/work/MODEL_EFFORT_ROUTING.md`
- **Done evidence:** Sol High default; Max escalation triggers; Pro-specific tasks; surface-dependent naming caveat; Ultra deferred for v0 runtime

#### W-211 — Define web scheduled-task patterns for research and monitoring

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** no  
- **Dependencies:** W-201  
- **Scope:** Optional operational support. Not the v0 harness scheduler.
- **Outputs:** `docs/work/SCHEDULED_TASK_PATTERNS.md`
- **Done evidence:** web-only source monitoring examples; manual-run prerequisite; narrow permissions and stop/report rules; no local repo claim

#### W-212 — Prepare UPE runtime-layer migration notes without changing the stable core

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** no  
- **Dependencies:** W-201, W-202, W-210  
- **Scope:** Supporting UPE deployment note; not a harness v0 blocker.
- **Outputs:** `docs/work/UPE_V5_6_1_MIGRATION_NOTES.md`
- **Done evidence:** new volatile behavior placed in dated adapter/skill/evals; stable core unchanged unless ADR supplies explicit evidence
- **Escalation:** Use sol_pro for final core-vs-runtime placement review.

### 4-local-scaffold

#### C-301 — Re-inspect repository state immediately before edits

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** G-ADR, W-204, W-205, W-206, W-207, W-208  
- **Scope:** Mandatory pre-edit check. Do not assume C-101 is still current.
- **Outputs:** `agent/state/pre-edit-context.yaml`
- **Done evidence:** repo/ref/status recorded; unrelated changes preserved; smallest slice selected; tests and rollback path stated

#### C-302 — Create the minimal Python/uv repository scaffold

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-301  
- **Scope:** Python 3.12+, uv, pytest, ruff, and mypy/pyright. WSL2 first.
- **Outputs:** `pyproject.toml`, `src/harness/`, `tests/`, `examples/fixture-repository/`, `README.md`, `AGENTS.md`
- **Done evidence:** uv environment resolves; package imports; tree contains no empty speculative abstractions

#### C-303 — Materialize accepted research, ADR, schemas, templates, and prompts

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-302, W-209, W-210  
- **Scope:** Bring accepted web-owned artifacts into the versioned repository.
- **Outputs:** `docs/`, `schemas/`, `templates/`, `prompts/`
- **Done evidence:** content identity or intentional transformation recorded; internal references resolve

#### C-304 — Create a short AGENTS.md map and repository operating README

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-302, C-303  
- **Scope:** Do not turn AGENTS.md into a duplicate encyclopedia.
- **Outputs:** `AGENTS.md`, `README.md`
- **Done evidence:** AGENTS.md points to docs/scripts/tests; commands and invariants are concise; definition of done and prohibited actions explicit

#### C-305 — Create the fixture repository and deterministic baseline commands

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-302  
- **Scope:** Ground later lifecycle and recovery tests in an inspectable environment.
- **Outputs:** `examples/fixture-repository/`, `scripts/bootstrap.sh`, `scripts/verify-fast.sh`, `scripts/verify-full.sh`
- **Done evidence:** fixture initializes reproducibly; fast/full checks have known pass/fail behavior

#### C-306 — Create schema and package validators

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-303  
- **Scope:** Mechanical validation belongs to code, not model confidence.
- **Outputs:** `scripts/validate_schema.py`, `scripts/validate_release.py`, `scripts/validate_references.py`
- **Done evidence:** valid examples pass; invalid examples fail with actionable messages

### 5-core-harness

#### C-401 — Implement typed Goal, Task, Run, Event, configuration, and lifecycle models

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-304, C-305, C-306  
- **Scope:** State model first. No provider calls.
- **Outputs:** `src/harness/state.py`, `src/harness/config.py`, `schemas/*.schema.json`, `tests/unit/test_state.py`, `tests/unit/test_config.py`
- **Done evidence:** valid transitions pass; invalid transitions fail; schemas round-trip; terminal states and reasons explicit
- **Escalation:** Use sol_max_or_highest_exposed only if transition/recovery invariants conflict.

#### C-402 — Implement the provider adapter interface and fake adapter

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-401  
- **Scope:** Test orchestration without model calls. Implement no second real provider.
- **Outputs:** `src/harness/adapters/base.py`, `src/harness/adapters/fake.py`, `tests/unit/test_fake_adapter.py`
- **Done evidence:** scripted success, failure, interruption and approval events reproducible

#### C-403 — Implement the lifecycle/orchestrator against the fake adapter

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-402  
- **Scope:** Drive CREATED through CHECKPOINTING/READY and explicit terminal states.
- **Outputs:** `src/harness/orchestrator.py`, `src/harness/lifecycle.py`, `tests/unit/test_lifecycle.py`
- **Done evidence:** one coherent task per iteration; transition persisted before external action; reasoned stop states emitted; worker message alone cannot complete a task
- **Escalation:** Use sol_max_or_highest_exposed for subtle event ordering or re-entrancy.

#### C-404 — Implement deterministic validation and evidence records

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-403, C-305  
- **Scope:** Deterministic layer is primary and precedes model evaluation.
- **Outputs:** `src/harness/validation.py`, `tests/unit/test_validation.py`
- **Done evidence:** validator commands scoped; outputs stored by reference; task completion requires passing evidence; timeouts/errors normalized

#### C-405 — Implement workspace/worktree isolation and path containment

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-403, C-305  
- **Scope:** Git worktree or scoped workspace manager without broad host access.
- **Outputs:** `src/harness/workspace.py`, `tests/unit/test_workspace.py`
- **Done evidence:** one task maps to one contained workspace; path traversal rejected; unrelated worktrees cannot be removed; dirty state handled safely
- **Escalation:** Use sol_max_or_highest_exposed for containment, symlink, Windows/WSL path, or cleanup edge cases.

#### C-406 — Implement SQLite state persistence and append-only JSONL events

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-401, C-403  
- **Scope:** Conversation history is not canonical state.
- **Outputs:** `src/harness/state_store.py`, `src/harness/events.py`, `tests/unit/test_state_store.py`, `tests/unit/test_events.py`
- **Done evidence:** transactional writes; large outputs referenced not embedded; events replayable enough for recovery; redaction marker supported
- **Escalation:** Use sol_max_or_highest_exposed if replay, transaction, or concurrency semantics become subtle.

#### C-407 — Implement budgets, stop rules, retry/backoff, and no-progress detection

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-403, C-406  
- **Scope:** Exact bounds owned by host code.
- **Outputs:** `src/harness/budgets.py`, `src/harness/retry_policy.py`, `tests/unit/test_budgets.py`, `tests/unit/test_retry_policy.py`
- **Done evidence:** iteration/time/token-cost limits enforced; jittered bounded backoff; identical-failure and no-progress stops; non-idempotent retry blocked
- **Escalation:** Use sol_max_or_highest_exposed when idempotency and side effects interact.

#### C-408 — Implement optional read-only model evaluator interface

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-404, W-203, W-207  
- **Scope:** Optional second layer only for irreducible judgment.
- **Outputs:** `src/harness/evaluation.py`, `tests/unit/test_evaluation.py`
- **Done evidence:** not invoked when deterministic checks suffice; no write access; PASS/FAIL/INSUFFICIENT_EVIDENCE preserved; criteria cannot be rewritten
- **Escalation:** Use sol_max_or_highest_exposed for multi-grader aggregation or difficult evidence calibration.

#### C-409 — Implement the CLI and harness doctor

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-403, C-404, C-405, C-406, C-407  
- **Scope:** Small explicit CLI. Missing credentials reported without values.
- **Outputs:** `src/harness/cli.py`, `tests/unit/test_cli.py`
- **Done evidence:** init/research/doctor/run/status/events/resume/pause/cancel/evaluate/cleanup commands exist; doctor checks runtime/Codex/Git/worktrees/validators/SQLite/permissions safely

#### C-410 — Document threat model, state model, evaluation plan, and operations

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-401, C-404, C-405, C-406, C-407, C-409  
- **Scope:** Documentation follows working code and exact tests, not imagined capabilities.
- **Outputs:** `docs/threat-model.md`, `docs/state-model.md`, `docs/evaluation-plan.md`, `docs/operations.md`
- **Done evidence:** setup, operation, recovery, approvals and limitations match implementation

### 6-app-server-recovery-security

#### C-501 — Implement the Codex App Server adapter

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol Max / highest exposed Sol effort  
- **Critical path:** yes  
- **Dependencies:** C-103, C-402, C-406, C-407  
- **Scope:** Keep raw protocol messages inside the adapter boundary.
- **Outputs:** `src/harness/adapters/codex_app_server.py`, `tests/unit/test_codex_adapter.py`
- **Done evidence:** startup/shutdown; initialize handshake; thread start/resume; turn submission; streamed event translation; approvals/cancel; terminal detection; error normalization; protocol version compatibility
- **Notes:** Max is justified by protocol evolution, event ordering, reconnectability, and approval semantics.

#### C-502 — Run a controlled Codex App Server smoke task

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-501, C-305, C-409  
- **Scope:** One narrow happy-path smoke run; do not call the harness production-ready.
- **Outputs:** `evals/results/app-server-smoke/`, `docs/research/app-server-smoke-observation.md`
- **Done evidence:** fixture-only change observed; events recorded; validator evidence recorded; no external mutation

#### C-503 — Implement crash/restart and process-state reconciliation

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol Max / highest exposed Sol effort  
- **Critical path:** yes  
- **Dependencies:** C-406, C-501, C-502  
- **Scope:** Crash-safe resume is a core Max task.
- **Outputs:** `src/harness/recovery.py`, `tests/integration/test_restart_recovery.py`
- **Done evidence:** persisted state, process state, worktree, Git, last event and validation reconciled; ambiguous executing state eliminated

#### C-504 — Implement checkpoint and partial-failure recovery

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol Max / highest exposed Sol effort  
- **Critical path:** yes  
- **Dependencies:** C-405, C-406, C-503  
- **Scope:** Use patch/archive/checkpoint metadata by default. Local Git commits remain approval-gated.
- **Outputs:** `src/harness/checkpoint.py`, `tests/integration/test_checkpoint_recovery.py`
- **Done evidence:** previous stable checkpoint preserved; interrupted checkpoint cannot corrupt state; rollback path proven without unauthorized commit

#### C-505 — Implement permissions, approval gates, command policy, and redaction

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol Max / highest exposed Sol effort  
- **Critical path:** yes  
- **Dependencies:** C-403, C-405, C-406, C-501  
- **Scope:** Security boundary is host-owned and adjacent to action.
- **Outputs:** `src/harness/approvals.py`, `src/harness/permissions.py`, `tests/unit/test_approvals.py`, `tests/unit/test_permissions.py`
- **Done evidence:** external/destructive/financial/secret/production action transitions to APPROVAL_REQUIRED; workspace credentials remain narrow; paths/commands/network checked; secrets and personal data redacted from logs
- **Notes:** No push, PR, merge, release, deployment, message, purchase, or production mutation by default.

#### C-506 — Integrate state, workspace, validation, App Server, recovery, and security

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol Max / highest exposed Sol effort  
- **Critical path:** yes  
- **Dependencies:** C-409, C-501, C-503, C-504, C-505  
- **Scope:** Final multi-component integration. This is where Max earns its keep.
- **Outputs:** `integrated v0 harness candidate`
- **Done evidence:** critical invariants hold across module boundaries; no duplicate controller state; failure states remain explicit; full fixture path runnable

### 7-tests-evals

#### C-601 — Complete unit-test coverage for all required behaviors

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-506  
- **Scope:** Tests should accompany each slice; this task closes gaps.
- **Outputs:** `tests/unit/`
- **Done evidence:** state transitions, schemas, budgets, retry, no-progress, approvals, redaction, task selection, path containment and adapter errors covered

#### C-602 — Complete the ten required integration tests

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-506  
- **Scope:** Prove init, workspace, fake edits, validation, resume, checkpoint recovery, budgets, approvals, evaluator, cleanup.
- **Outputs:** `tests/integration/`
- **Done evidence:** all ten brief-specified integration scenarios pass

#### C-603 — Create the six representative evaluation fixtures

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-506  
- **Scope:** Representative model-dependent trials, not decorative demos.
- **Outputs:** `tests/evals/`, `evals/cases/`
- **Done evidence:** passing change, test repair, ambiguous requirement, non-progress, malicious repository instruction and forbidden external action represented

#### C-604 — Run repeated model-dependent trials and record metrics

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-603, C-502  
- **Scope:** Use enough trials to expose failure modes; keep costs bounded.
- **Outputs:** `evals/results/trial-summary.json`, `evals/results/trial-details.jsonl`
- **Done evidence:** pass rate, iterations, elapsed time, tool calls and reviewer corrections recorded
- **Escalation:** Use sol_max_or_highest_exposed only to diagnose persistent failures, not to conceal a weak harness.

#### C-605 — Run the complete deterministic quality suite

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-601, C-602, C-603  
- **Scope:** Tool output, not prose, determines these results.
- **Outputs:** `validation/full-suite-report.json`
- **Done evidence:** pytest PASS; ruff PASS; mypy or pyright PASS; schema checks PASS; package/reference checks PASS

#### C-606 — Run security, secret, malicious-instruction, and no-external-mutation checks

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-505, C-602, C-603  
- **Scope:** Release-blocking security evidence.
- **Outputs:** `validation/security-report.json`
- **Done evidence:** no secret in fixtures/logs; malicious repo instruction treated as data; forbidden action blocked; no push/PR/deploy/external mutation observed
- **Escalation:** Use sol_max_or_highest_exposed for unexplained policy bypass or path/credential edge cases.

### 8-release

#### W-701 — Synthesize the implementation evidence and draft the final report

- **Status:** BLOCKED  
- **Owner:** ChatGPT Work web  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-604, C-605, C-606  
- **Scope:** Answer-first evidence synthesis. Preserve planned/implemented/tested/blocked/unverified labels.
- **Outputs:** `FINAL_IMPLEMENTATION_REPORT.md`, `release-evidence-index.yaml`
- **Done evidence:** architecture, sources, exact versions, files, commands, tests, smoke behavior, security, assumptions, deferred features and failure modes covered

#### P-701 — Perform a fresh-context read-only release review

- **Status:** BLOCKED  
- **Owner:** ChatGPT Pro / Work  
- **Model:** Sol Pro  
- **Critical path:** yes  
- **Dependencies:** W-701  
- **Scope:** Second and final primary Pro use: adversarial whole-system judgment.
- **Outputs:** `PRO_RELEASE_REVIEW.yaml`
- **Done evidence:** every acceptance criterion graded PASS/FAIL/INSUFFICIENT_EVIDENCE; smallest correction specified; release blockers explicit

#### C-701 — Apply only accepted release-review corrections

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** P-701  
- **Scope:** Use Max only for a correction involving state/recovery/security/protocol invariants.
- **Outputs:** `corrected release candidate`, `correction-log.yaml`
- **Done evidence:** each change maps to an accepted finding; unrelated structure preserved
- **Escalation:** Escalate narrowly to sol_max_or_highest_exposed when the correction matches Max criteria.

#### C-702 — Rerun all deterministic tests after corrections

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-701  
- **Scope:** No release on stale pre-correction evidence.
- **Outputs:** `validation/final-validation-report.json`
- **Done evidence:** all critical deterministic gates PASS; remaining UNKNOWNs explicit

#### C-703 — Package the v0 artifacts, documentation, manifest, and archive

- **Status:** BLOCKED  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** yes  
- **Dependencies:** C-702  
- **Scope:** Packaging is mechanical and does not deserve Pro.
- **Outputs:** `release/`, `MANIFEST.sha256`, `agent-harness-v0.zip`
- **Done evidence:** archive extracts; checksums match; known limitations present

#### C-704 — Create a local Git commit for the accepted release candidate

- **Status:** APPROVAL  
- **Owner:** Local Codex  
- **Model:** Sol High  
- **Critical path:** no  
- **Dependencies:** C-703  
- **Scope:** Do not commit until explicitly authorized. Never push or open a PR under this plan.
- **Outputs:** `local commit hash`
- **Done evidence:** explicit user authorization recorded; diff reviewed; commit local only

## v0 acceptance mapping

| ID | Acceptance criterion | Evidence-producing tasks |
|---|---|---|
| `AC-01` | `uv run harness doctor` reports a usable environment | `C-409`, `C-605` |
| `AC-02` | `uv run harness init examples/fixture-repository` creates valid config/state | `C-305`, `C-409`, `C-602` |
| `AC-03` | One fixture task completes through the fake adapter | `C-402`, `C-403`, `C-602` |
| `AC-04` | The same run can be interrupted and resumed | `C-503`, `C-602` |
| `AC-05` | Codex App Server adapter completes a controlled smoke task | `C-501`, `C-502` |
| `AC-06` | State survives process restart | `C-406`, `C-503`, `C-602` |
| `AC-07` | Every completed task has validator evidence | `C-404`, `C-403`, `C-602` |
| `AC-08` | External/destructive operations require approval | `C-505`, `C-602`, `C-606` |
| `AC-09` | Tests, lint and type checks pass | `C-605`, `C-702` |
| `AC-10` | Setup, operation, recovery and limitations are documented | `C-410`, `W-701`, `C-703` |
| `AC-11` | No secret appears in committed fixtures or logs | `C-505`, `C-606` |
| `AC-12` | No push, PR, deployment or external mutation is performed | `C-505`, `C-606`, `P-701` |

## Approval and action boundary

- A local commit is **not authorized** by this plan. `C-704` remains approval-gated.
- Push, pull request, merge, release, deployment, external messages, purchases, and production mutation are excluded.
- The trusted host owns credentials, approvals, budgets, state, audit, and external-write authorization.
- Agent workspaces receive only the paths and capabilities required for the assigned task.
- A retry must not duplicate a non-idempotent action.

## Explicitly deferred from v0

- `D-001` — Multi-agent runtime execution
- `D-002` — Cloud scheduler for the harness
- `D-003` — Browser or web control UI
- `D-004` — Issue-tracker integration
- `D-005` — Autonomous PR merge or release
- `D-006` — Production deployment
- `D-007` — Dynamic model routing
- `D-008` — Self-modifying prompts or skills
- `D-009` — Persistent semantic memory
- `D-010` — Provider marketplace or distributed execution

## Immediate execution instruction

Run `NEXT_LOCAL_CODEX_PROMPT.md` in the intended WSL2 repository. Return the two handoff files to Work web. Do not begin harness implementation before the ADR gate. This ordering is not excessive caution; it is the one thing preventing “minimal v0” from becoming a lovingly typed generic framework before anyone has verified that App Server starts.

## Package files

- `HARNESS_IMPLEMENTATION_MASTER_PLAN.md` — human-readable authoritative plan
- `harness_implementation_backlog.yaml` — machine-readable source of truth
- `CURRENT_PRODUCT_DELTA_2026-07-18.md` — dated Work/Codex/model corrections
- `WORK_CODEX_HANDOFF_TEMPLATE.yaml` — bidirectional cross-surface contract
- `NEXT_LOCAL_CODEX_PROMPT.md` — immediate local evidence task
- `NEXT_WEB_WORK_PROMPT.md` — merge and ADR task after local handoff
- `validation-report.json` — structural checks actually run
- `MANIFEST.sha256` — file integrity
