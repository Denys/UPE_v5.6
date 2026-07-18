# Pattern Comparison — Long-Running Agent Harness

**Access date:** 2026-07-18  
**Status:** research recommendation, not implementation  
**Primary evidence IDs:** `OAI-01`–`OAI-21`, `ANT-22`–`ANT-30`

## Executive decision

Use **Codex App Server inside a trusted host-owned harness**. Keep durable run state and verification outside model conversation state. Start with one coding agent and deterministic validators. Use Work mode as the research, steering, review, and deliverable surface, while Codex/host owns repository mutation, process recovery, exact budgets, and protocol-level control.

This is not because Work is incapable of substantial execution. Current Work mode can run long multi-step tasks, use files/plugins/approved tools, work with local files on desktop, follow `/goal`, and run scheduled tasks. The boundary exists because strict software-harness invariants require inspectable state, recovery, validation, and versioned protocol behavior rather than a pleasant feeling that the thread looks continuous.

---

## 1. Codex App Server versus a custom Responses/Agents SDK loop

| Dimension | Codex App Server | Custom Responses/Agents SDK loop |
|---|---|---|
| Existing capability | Full Codex harness: thread/turn/item lifecycle, shell/file tools, skills/MCP, approvals, persistence, streamed events, auth/config. | Application owns model loop, tools, sessions, guardrails, handoffs, tracing, and sandbox client. |
| Integration cost | JSON-RPC-lite/JSONL client plus version compatibility. | More code and policy ownership; easier provider abstraction. |
| Risk | Protocol evolution and Codex dependence. | Reimplementing behavior Codex already solves; more failure and security surface. |
| Evidence | `OAI-02`–`OAI-05` | `OAI-14`–`OAI-21` |

**v0 choice:** Codex App Server adapter. Define an internal provider interface, but implement only Codex. Add an Agents SDK/Claude adapter later without changing Goal/Task/Run/Event, workspace, validator, or evaluator contracts.

**Work applicability:** use native Work/Goal behavior for non-repository research and artifacts. Do not embed App Server into Work merely to make an architecture diagram look industrious.

**Change trigger:** App Server cannot expose a required stable capability, or a representative cross-provider eval justifies the portability cost.

---

## 2. Host-owned harness versus harness inside the sandbox

| Dimension | Trusted host owns harness | Harness runs inside sandbox |
|---|---|---|
| Credentials/policy | Remain outside agent workspace. | Risk of broad credential inheritance and merged trust boundaries. |
| Recovery/audit | Host can reconcile process, state, Git, events, and validation. | Crash can destroy or obscure the controller and its evidence together. |
| Prototype speed | More interfaces to implement. | Faster proof of concept. |
| Evidence | `OAI-08`, `OAI-15`, `OAI-17`, `OAI-20` | `OAI-15` warns against this for durable deployments. |

**v0 choice:** host owns credentials, approval decisions, budgets, audit log, SQLite, external writes, and recovery. Agent receives only the assigned worktree and narrow runtime access.

**Work applicability:** Work desktop may use local files/apps with permission, but the Project/chat remains an operator and artifact surface. It does not become the secret or policy authority.

**Change trigger:** none expected for security-critical state; only execution mechanics may move to managed infrastructure.

---

## 3. Compaction versus explicit fresh-session handoff

| Dimension | Compaction | Fresh-session handoff |
|---|---|---|
| Strength | Preserves conversational continuity with lower token pressure. | Removes accumulated distraction and builder bias; forces explicit state. |
| Weakness | Can omit details and makes hidden state hard to audit. | Adds latency, orchestration, re-orientation, and possible loss of tacit context. |
| Evidence | `OAI-02`–`OAI-04` | `ANT-22`–`ANT-26` |

**v0 choice:** support both at different layers.

1. Allow Codex/App Server compaction within a live thread.
2. Persist canonical Goal/Task/Run/Event state, progress, decisions, blockers, Git checkpoint, and validator evidence outside the thread.
3. Resume the same thread when healthy.
4. Start a fresh worker/evaluator context after corruption, plateau, or explicit checkpoint boundaries.

**Work applicability:** same chat for related work; separate chats for independent tasks or fresh review. All meaningful handoffs land in files, not in a sentimental attachment to a long transcript.

**Change trigger:** evals show fresh resets harm coherence more than they improve reliability, or vice versa.

---

## 4. `AGENTS.md` versus skills versus hooks versus runtime configuration

| Layer | Correct contents | Must not become | Work analogue |
|---|---|---|---|
| `AGENTS.md` | Short repository map, invariants, commands, architecture links, done definition. | Mutable progress log or encyclopedic reference. | Project Instructions for the active UPE kernel; project files for detail. |
| Skill | Repeatable triggered procedure, templates, schemas, scripts, focused references. | Canonical run state or a dumping ground for all domain knowledge. | Native Work skill selected explicitly with `@` where useful. |
| Hook | Deterministic lifecycle enforcement, validation, blocking, context injection. | Fuzzy policy, broad autonomous authority, or a substitute for sandboxing. | Use only when that Work/local surface explicitly supports it; otherwise use permissions plus host/checklist validation. |
| Runtime config | Model/effort, permissions, sandbox, provider, network, hooks/rules, environment. | Task facts, acceptance criteria, or business policy prose. | Desktop permissions/settings; volatile capability profile. |

**Evidence:** `OAI-09`–`OAI-13`, `OAI-01`, local UPE layering files.

**v0 choice:** state each invariant once in the cheapest durable layer. This directly implements the UPE instruction-placement doctrine.

---

## 5. Deterministic tests versus model evaluator

| Dimension | Deterministic validator | Independent model evaluator |
|---|---|---|
| Best for | Tests, build, lint, types, schemas, paths, diffs, security rules, expected files/output. | Subjective quality, ambiguous intent, visual/design judgment, synthesis completeness. |
| Reliability | Repeatable and cheap when specification is expressible. | Nondeterministic and calibration-dependent. |
| Failure risk | Can miss qualities not encoded in tests. | Can accept persuasive summaries instead of inspecting outcomes. |
| Evidence | `OAI-01`, `OAI-19`, `OAI-20`, `ANT-24`, `ANT-27` | `ANT-23`, `ANT-24`, `ANT-27` |

**v0 choice:** deterministic first. Invoke a read-only independent evaluator only when mandatory criteria cannot be established deterministically. Evaluator returns `PASS`, `FAIL`, or `INSUFFICIENT_EVIDENCE` per criterion and cannot expand scope.

**Work applicability:** a fresh Work reviewer chat can grade a report/deck/research artifact from the actual sources. It must not rely only on the producing chat’s summary.

**Change trigger:** measured false-positive/false-negative rates on representative evals.

---

## 6. Single-agent iteration versus planner/generator/evaluator

| Dimension | Single agent + tools | Planner/generator/evaluator |
|---|---|---|
| Strength | Less context transfer, latency, cost, and coordination failure. | Useful separation near capability limits or for subjective quality loops. |
| Weakness | Builder can self-certify or drift on very long/ambiguous work. | Every boundary can lose context; evaluators can overfit or become redundant. |
| Evidence | `OAI-14`, `ANT-28`, supplemental OpenAI practical guide | `ANT-23`, `ANT-24`, `ANT-30` |

**v0 choice:** one coding agent, one coherent task per iteration, deterministic validation. Add an independent evaluator only when needed. Do not implement planner or multi-agent execution in v0.

**Work applicability:** use `/plan` only when the outcome is unclear; use separate research/review chats only for independent work or fresh judgment.

**Change trigger:** repeated single-agent failure caused by instruction/tool overload or separable independent workstreams, demonstrated by evals rather than enthusiasm.

---

## 7. Worktree isolation versus container isolation

| Dimension | Git worktree | Container/sandbox |
|---|---|---|
| Provides | Branch/filesystem separation, reversible diffs, low overhead. | Process, dependency, filesystem, and optional network isolation. |
| Does not provide | Strong protection from host processes, network, or secrets. | Automatically useful Git workflow or cheap startup. |
| Evidence | `OAI-01`, `OAI-06`–`OAI-08` | `OAI-15`, `OAI-20`, `ANT-29` |

**v0 choice:** worktree per task by default. Add Docker only for untrusted dependencies, destructive commands, conflicting environments, or tests requiring material process/filesystem isolation.

**Work applicability:** Work/Codex desktop scheduled tasks can use isolated worktrees for Git repositories. Parallel Work research chats should remain read-only or write to distinct artifacts.

**Change trigger:** threat model or reproducibility tests show worktrees are insufficient.

---

## 8. Durable file/database state versus conversation/thread state

| Dimension | Durable structured state | Conversation/thread state |
|---|---|---|
| Strength | Inspectable, queryable, recoverable, provider-portable, testable. | Rich local context and convenient continuation. |
| Weakness | Requires schema/migrations and careful synchronization. | Hidden, compacted, provider-bound, and insufficient for process/Git reconciliation. |
| Evidence | Active build brief, `OAI-08`, `OAI-16`, `ANT-22`–`ANT-26` | `OAI-03`, `OAI-04`, current Work Projects/chats docs |

**v0 choice:** SQLite for indexed Goal/Task/Run state, JSONL for append-only events, files for large outputs/evidence, and Git for workspace checkpoints. Thread IDs are references inside run state, not the run itself.

**Work applicability:** Projects preserve shared sources/instructions; each distinct outcome gets its own chat. A compact `research-state.yaml` and deliverable files remain canonical across chats/surfaces.

**Change trigger:** a managed runtime exposes equivalent inspectable state, recovery, export, and idempotency guarantees.

---

## 9. Direct tool exposure versus code-mediated tool access

| Dimension | Direct narrow tools | Code-mediated stage |
|---|---|---|
| Best for | One/few calls with judgment between calls, native citations/artifacts, approvals. | Predictable filtering, joining, ranking, dedupe, aggregation, validation, or side-effect centralization. |
| Risk | Too many overlapping tools increase selection errors and context. | Code can hide evidence or expand authority if poorly bounded. |
| Evidence | `OAI-02`, `OAI-12`–`OAI-15`, local capability scan | `OAI-14`, `OAI-19`, `ANT-28` |

**v0 choice:** expose the narrowest useful tools. Use deterministic code for bounded data reduction and validation. Treat MCP server security as its own boundary; the shell sandbox does not magically secure an MCP tool.

**Work applicability:** use native web/file/plugin tools when they provide source-linked results. Use code/data execution for reproducible aggregation, never to launder unsupported claims into a CSV.

**Change trigger:** measured tool-selection errors, context overhead, or repeated transformations dominate the stage.

---

## 10. Local orchestration versus managed/cloud execution

| Dimension | Local WSL2 host | Managed/cloud surface |
|---|---|---|
| Strength | Exact repository, local tools, inspectable processes/state, custom recovery. | Continues without a local terminal, easier access/sharing/scheduling. |
| Weakness | Machine/runtime maintenance and uptime. | Product limits, opaque lifecycle, reduced local-folder persistence, provider dependency. |
| Evidence | Active brief, `OAI-03`–`OAI-08`, `OAI-15`, current Work/Scheduled docs | Work web, Codex cloud, Workspace Agents API |

**v0 choice:** WSL2 Ubuntu trusted host for the coding harness. Use Work cloud for research and deliverables; use Work desktop for approved local everyday-work tasks. Add managed scheduling only after the workflow passes local evals.

**Current blocker for Workspace Agents API as a harness backend:** it durably accepts triggers and supports idempotency keys, but currently returns no public run ID and does not expose the agent response through the API. That is useful for fire-and-forget triggers, not for strict run reconciliation.

**Change trigger:** managed execution exposes the required state, result retrieval, approvals, isolation, budgets, and audit semantics at acceptable cost.

---

## Consolidated v0 recommendation

```text
ChatGPT Work Project
  - active UPE kernel in Project Instructions
  - source files, runtime profile, source map, and research state
  - long-running research/deliverables and fresh-context review
  - skills/plugins for tested repeatable workflows
  - user steering and approval
           |
           | versioned goal/evidence/decision artifacts
           v
Trusted WSL2 host orchestrator
  - Codex App Server adapter pinned to tested version
  - one task per worktree
  - SQLite run/task state + JSONL events
  - deterministic validation first
  - optional read-only evaluator
  - budgets, retry/idempotency, approvals, recovery
           |
           | evidence, diffs, validation, reports
           v
ChatGPT Work
  - synthesis, review, decisions, documentation, operating reports
```

## What would justify changing this decision

1. App Server lacks a mandatory stable control after direct smoke testing.
2. Work or a managed runtime exposes inspectable run IDs, result retrieval, durable structured state, reconciliation, and equivalent security controls.
3. Representative evals show a planner/evaluator or multi-agent topology materially improves pass rate enough to justify its cost and failure surface.
4. Container isolation becomes mandatory under the threat model.
5. Cross-provider execution becomes a real requirement rather than a tasteful rectangle in an architecture diagram.
