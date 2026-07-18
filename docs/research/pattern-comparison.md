# Pattern Comparison — Long-Running Agent Harness

**Access date:** 2026-07-18  
**Status:** research recommendation reconciled by ADR-001  
**Primary evidence IDs:** `OAI-01`–`OAI-21`, `ANT-22`–`ANT-30`

## Executive decision

Use **Codex App Server inside a trusted host-owned harness**. Keep durable run state and verification outside model conversation state. Start with one coding agent and deterministic validators. Use Work mode as the research, steering, review and deliverable surface, while Codex and the trusted host own repository mutation, process recovery, exact budgets and protocol-level control.

The current v0 target is Windows-native Codex. Earlier WSL2-first recommendations are preserved as historical research context and are superseded for active implementation by `docs/architecture/ADR-001-harness-boundary.md` and `docs/research/W-101-target-runtime-reconciliation.md`.

## 1. Codex App Server versus a custom Responses or Agents SDK loop

| Dimension | Codex App Server | Custom Responses or Agents SDK loop |
|---|---|---|
| Existing capability | Full Codex harness: thread, turn and item lifecycle, shell/file tools, skills/MCP, approvals, persistence, streamed events, authentication and configuration. | Application owns model loop, tools, sessions, guardrails, handoffs, tracing and sandbox client. |
| Integration cost | JSON-RPC-lite/JSONL client plus version compatibility. | More code and policy ownership; easier provider abstraction. |
| Risk | Protocol evolution and Codex dependence. | Reimplementing behavior Codex already solves; more failure and security surface. |
| Evidence | `OAI-02`–`OAI-05` | `OAI-14`–`OAI-21` |

**v0 choice:** Codex App Server adapter. Define an internal provider interface, but implement only Codex. Add another provider adapter later without changing Goal, Task, Run, Event, workspace, validator or evaluator contracts.

**Change trigger:** App Server cannot expose a mandatory control after direct smoke testing, or representative cross-provider evaluations justify the portability cost.

## 2. Host-owned harness versus harness inside the sandbox

| Dimension | Trusted host owns harness | Harness runs inside sandbox |
|---|---|---|
| Credentials and policy | Remain outside agent workspace. | Risk of broad credential inheritance and merged trust boundaries. |
| Recovery and audit | Host can reconcile process, state, Git, events, actions and validation. | Crash can destroy or obscure controller and evidence together. |
| Prototype speed | More interfaces to implement. | Faster proof of concept. |
| Evidence | `OAI-08`, `OAI-15`, `OAI-17`, `OAI-20` | `OAI-15` warns against this for durable deployments. |

**v0 choice:** host owns credentials, approval decisions, budgets, action journal, audit, SQLite, external writes and recovery. Agent receives only the assigned worktree and narrow runtime access.

## 3. Compaction versus explicit fresh-session handoff

| Dimension | Compaction | Fresh-session handoff |
|---|---|---|
| Strength | Preserves conversational continuity with lower token pressure. | Removes accumulated distraction and builder bias; forces explicit state. |
| Weakness | Can omit details and makes hidden state hard to audit. | Adds latency, re-orientation and possible loss of tacit context. |
| Evidence | `OAI-02`–`OAI-04` | `ANT-22`–`ANT-26` |

**v0 choice:** support both at different layers.

1. Allow Codex/App Server compaction within a live thread.
2. Persist canonical Goal, Task, Run and Event state, decisions, blockers, approval, action and validation evidence outside the thread.
3. Resume the same thread when healthy.
4. Start a fresh worker or evaluator context after corruption, plateau or explicit checkpoint boundaries.

## 4. `AGENTS.md` versus skills versus hooks versus runtime configuration

| Layer | Correct contents | Must not become | Work analogue |
|---|---|---|---|
| `AGENTS.md` | Short repository map, invariants, commands, architecture links and done definition. | Mutable progress log or encyclopedic reference. | Project Instructions for active UPE invariants; project files for detail. |
| Skill | Repeatable triggered procedure, templates, schemas, scripts and focused references. | Canonical run state or broad authorization. | Native Work skill selected explicitly where useful. |
| Hook | Deterministic lifecycle enforcement, validation, blocking and context injection. | Fuzzy policy or a substitute for sandboxing. | Use only when the local surface supports it; otherwise host policy and validators. |
| Runtime configuration | Model and effort, permissions, sandbox, provider, network and hooks. | Task facts, acceptance criteria or business-policy prose. | Desktop permissions and volatile capability profile. |

**v0 choice:** state each invariant once in the cheapest durable layer.

## 5. Deterministic tests versus model evaluator

| Dimension | Deterministic validator | Independent model evaluator |
|---|---|---|
| Best for | Tests, build, lint, types, schemas, paths, diffs, security rules and expected outputs. | Subjective quality, ambiguous intent, visual judgment and synthesis completeness. |
| Reliability | Repeatable and cheap when specification is expressible. | Nondeterministic and calibration-dependent. |
| Failure risk | Can miss qualities not encoded in tests. | Can accept persuasive summaries instead of inspecting outcomes. |
| Evidence | `OAI-01`, `OAI-19`, `OAI-20`, `ANT-24`, `ANT-27` | `ANT-23`, `ANT-24`, `ANT-27` |

**v0 choice:** deterministic first. Invoke a read-only independent evaluator only when mandatory criteria cannot be established deterministically. Evaluator returns `PASS`, `FAIL` or `INSUFFICIENT_EVIDENCE` per criterion and cannot expand scope.

## 6. Single-agent iteration versus planner, generator and evaluator

| Dimension | Single agent and tools | Planner, generator and evaluator |
|---|---|---|
| Strength | Less context transfer, latency, cost and coordination failure. | Useful separation near capability limits or for subjective quality loops. |
| Weakness | Builder can self-certify or drift on very long or ambiguous work. | Every boundary can lose context; evaluators can overfit or become redundant. |
| Evidence | `OAI-14`, `ANT-28` | `ANT-23`, `ANT-24`, `ANT-30` |

**v0 choice:** one coding agent, one coherent task per iteration, deterministic validation. Add an independent evaluator only where required. Do not implement planner or multi-agent execution in v0.

## 7. Worktree isolation versus container isolation

| Dimension | Git worktree | Container or sandbox |
|---|---|---|
| Provides | Branch and filesystem separation, reversible diffs and low overhead. | Process, dependency, filesystem and optional network isolation. |
| Does not provide | Strong protection from host processes, network or secrets. | Automatically useful Git workflow or cheap startup. |
| Evidence | `OAI-01`, `OAI-06`–`OAI-08` | `OAI-15`, `OAI-20`, `ANT-29` |

**v0 choice:** worktree per task by default. Add Docker only for untrusted dependencies, destructive commands, conflicting environments or tests requiring material process or filesystem isolation.

## 8. Durable structured state versus conversation or thread state

| Dimension | Durable structured state | Conversation or thread state |
|---|---|---|
| Strength | Inspectable, queryable, recoverable, provider-portable and testable. | Rich local context and convenient continuation. |
| Weakness | Requires schema, migrations and synchronization. | Hidden, compacted, provider-bound and insufficient for process or Git reconciliation. |
| Evidence | Active build brief, `OAI-08`, `OAI-16`, `ANT-22`–`ANT-26` | `OAI-03`, `OAI-04`, current Work Projects documentation |

**v0 choice:** SQLite is authoritative Goal, Task, Run, approval and action state. Each transition writes an event outbox row in the same SQLite transaction. JSONL is an append-only audit mirror repaired by replay and deduplicated by stable event identity. Files hold large evidence. Routine rollback uses host-managed patch snapshots; Git commits are approval-gated milestones.

## 9. Direct tool exposure versus code-mediated tool access

| Dimension | Direct narrow tools | Code-mediated stage |
|---|---|---|
| Best for | One or few calls with judgment between calls, native citations, artifacts and approvals. | Predictable filtering, joining, ranking, deduplication, aggregation, validation or side-effect centralization. |
| Risk | Too many overlapping tools increase selection errors and context. | Code can hide evidence or expand authority if poorly bounded. |
| Evidence | `OAI-02`, `OAI-12`–`OAI-15` | `OAI-14`, `OAI-19`, `ANT-28` |

**v0 choice:** expose the narrowest useful tools. Use deterministic code for bounded data reduction and validation. Treat MCP security as its own boundary.

## 10. Local trusted-host execution versus managed or cloud execution

| Dimension | Local trusted host | Managed or cloud surface |
|---|---|---|
| Strength | Exact repository, local tools, inspectable processes and state, custom recovery. | Continues without a local terminal, easier access, sharing and scheduling. |
| Weakness | Machine and runtime maintenance. | Product limits, opaque lifecycle, reduced local-folder persistence and provider dependency. |
| Evidence | Active brief, `OAI-03`–`OAI-08`, `OAI-15` | Work web, Codex cloud and managed agent surfaces |

**v0 choice:** trusted host for coding orchestration, with Windows-native Codex as the current target. Work cloud owns research, specifications, gates, review and deliverables. Add managed scheduling only after the workflow passes local evaluations and exposes adequate state, results, approvals and audit.

## Consolidated v0 recommendation

```text
ChatGPT Work Project
  - active UPE kernel and project sources
  - research, reconciliation, specifications, ADRs and fresh review
  - user steering and approvals
           |
           | versioned goal, evidence and decision artifacts
           v
Trusted host orchestrator
  - current target: Windows-native Codex
  - version-pinned Codex App Server adapter
  - one task per worktree
  - SQLite authoritative state and transactional outbox
  - JSONL replayable audit mirror
  - durable external-action journal
  - host-managed patch checkpoints
  - deterministic validation first
  - optional read-only evaluator
  - budgets, approvals and recovery
           |
           | evidence, diffs, validation and reports
           v
ChatGPT Work
  - synthesis, review, decisions, documentation and operating reports
```

## What would justify changing this decision

1. App Server lacks a mandatory control after direct smoke testing.
2. Protocol compatibility cannot be bounded with version and schema checks.
3. Interruption tests invalidate the transactional-outbox or action-reconciliation design.
4. Work or a managed runtime exposes inspectable run IDs, result retrieval, durable state, reconciliation and equivalent security controls.
5. Representative evaluations show a planner, evaluator or multi-agent topology materially improves pass rate enough to justify its cost and failure surface.
6. Container isolation becomes mandatory under the threat model.
7. Cross-provider execution becomes an evaluated requirement.
