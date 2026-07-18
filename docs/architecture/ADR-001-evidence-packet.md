# ADR-001 Evidence Packet

**Decision:** Minimum v0 harness boundary  
**Date:** 2026-07-18  
**Inputs:** 30-source research package, C-101–C-105 local handoff, installed App Server schemas, current official-source refresh, and Pro fresh-context review.

## Executive finding

Select a **trusted-host orchestrator**, with **Windows-native Codex as the current v0 target**, around a **version-pinned Codex App Server adapter**. Keep orchestration state, approvals, budgets, audit and recovery outside the agent workspace. Use deterministic validation first and a read-only model evaluator only for residual semantic criteria. Keep v0 single-agent.

## 1. Codex App Server versus custom Responses/Agents SDK loop

### App Server

**Evidence**

- Official OpenAI architecture exposes Codex core threads through bidirectional JSON-RPC-lite/JSONL.
- It supports thread lifecycle and persistence, streamed item events, server-initiated approval requests and generated client schemas.
- Installed Codex CLI `0.144.3` generated 1,873 non-directory schema files across default and experimental bundles; all 604 JSON files parse.
- A live lifecycle handshake has not yet been attempted.

**Benefits**

- Reuses Codex's tool loop, sandbox, configuration, authentication, thread persistence and event model.
- Matches the Codex-native requirement.
- Keeps provider-specific protocol isolated behind one adapter.

**Costs and risks**

- Installed surface is labeled experimental.
- Event ordering, approval, interruption and reconnect behavior still require a controlled smoke test.
- Version compatibility must be managed explicitly.

### Custom Agents SDK or Responses loop

**Benefits**

- Greater control over loop semantics.
- Agents SDK offers sessions, sandbox agents, approvals, tracing and durable-workflow integrations.

**Costs**

- Reimplements Codex-specific tool, workspace, configuration and event behavior already available through App Server.
- Expands scope and test burden before v0 proves value.

**Decision:** App Server. Pin the binary and generated schemas, isolate raw protocol, and keep an adapter fallback path.

## 2. Trusted-host orchestrator versus harness inside sandbox

| Choice | Strength | Failure |
|---|---|---|
| Trusted host | Owns credentials, approvals, state, budgets, audit, process reconciliation and workspace policy | Requires disciplined path, command and action policy |
| Inside sandbox | Strongly local execution context | Cannot safely own host credentials, authoritative state or recovery after sandbox loss |

**Decision:** trusted host. Agent workspaces receive only minimum scoped capabilities.

## 3. Durable state consistency

App Server threads and Work chats are useful context, but neither is a sufficient cross-surface system of record. Canonical state must survive client replacement, thread loss, process restart and provider migration.

**Decision:**

- SQLite is authoritative Goal, Task, Run, approval, action and checkpoint state.
- Lifecycle transitions write state and an event outbox row in one SQLite transaction.
- JSONL is a replayable, deduplicated audit mirror, not an independent state authority.
- Files store large evidence.
- Routine checkpoints are host-managed patch snapshots.
- Git commits are optional approval-gated milestones.

This resolves the two critical ambiguities found during Pro review: dual-write crash consistency and the conflict between automatic checkpoints and commit approval.

## 4. External action recovery

Every potentially non-idempotent action receives a stable action ID and a recorded approval scope. The host stores planned, started, completed or unknown state and provider references. After interruption, unknown actions are reconciled against the target system before retry.

**Decision:** never repeat a side effect merely because the local process did not receive its response.

## 5. Deterministic validation versus independent model evaluator

Deterministic checks are reproducible and should establish all executable criteria. Model evaluation is appropriate only when semantics, design or judgment cannot be fully encoded.

**Decision:** validator first. Evaluator is read-only, criterion-level, evidence-facing and returns `PASS | FAIL | INSUFFICIENT_EVIDENCE`.

## 6. Worktree versus container isolation

| Mechanism | v0 role |
|---|---|
| Git worktree | Default task isolation and diff surface on Windows |
| Container or Docker | Optional only when threat model or dependency conflicts materially require it |

**Decision:** worktree first; do not make Docker a prerequisite without evidence.

## 7. Host-owned authority

The host owns:

- provider and business credentials;
- approval decisions;
- state, outbox, action journal and event persistence;
- time, iteration, token and cost budgets;
- command, network and path policy;
- external-write authorization;
- audit and redaction.

The unexplained legacy-upstream merge demonstrates why project files cannot self-authorize commits, pushes, merges or releases.

## 8. Provider portability

Core contracts must not contain raw App Server messages. The adapter translates provider events into internal typed events such as:

- session or thread opened;
- turn started or completed;
- tool proposed, started or completed;
- approval requested or resolved;
- output delta;
- usage or rate-limit update;
- interruption or cancellation;
- normalized error.

A future Agents SDK or Claude adapter may replace the provider layer without changing Goal, Task, Run, Event, validation, workspace or approval contracts.

## 9. Single-agent v0 versus multi-agent

Research supports multi-agent execution only for independently verifiable workstreams. v0's actual bottleneck is unproven.

**Decision:** one worker session per task. Defer planner, generator/evaluator topologies and parallel workers until representative evaluations show a measurable need.

## Security implications

- Windows-native paths require canonicalization, junction, symlink, reparse-point and worktree-containment tests.
- App Server compatibility failure stops before execution.
- No secret values enter model-visible state or committed fixtures.
- Commit, push, PR, merge, release, deployment, visibility change, external messages, purchases and production mutations require explicit approval.
- Target PR remains draft; ADR acceptance does not authorize merge.

## Migration triggers

Revisit the decision when:

1. the live App Server smoke test lacks a mandatory lifecycle or control;
2. protocol compatibility cannot be bounded by version and schema checks;
3. transactional-outbox or action-reconciliation tests expose an unrecoverable ambiguity;
4. a managed runtime exposes equivalent inspectable state, approvals, recovery and results;
5. container isolation becomes mandatory;
6. cross-provider execution becomes an evaluated requirement;
7. multi-agent evaluations materially outperform single-agent v0.
