# ADR-001 Evidence Packet

**Decision:** Minimum v0 harness boundary  
**Date:** 2026-07-18  
**Inputs:** 30-source research package, C-101–C-105 local handoff, installed App Server schemas, current official-source refresh.

## Executive finding

Select a **Windows-native trusted-host orchestrator** around a **version-pinned Codex App Server adapter**. Keep orchestration state, approvals, budgets, audit and recovery outside the agent workspace. Use deterministic validation first and a read-only model evaluator only for residual semantic criteria. Keep v0 single-agent.

## 1. Codex App Server vs custom Responses/Agents SDK loop

### App Server

**Evidence**

- Official OpenAI architecture exposes Codex core threads through bidirectional JSON-RPC-lite/JSONL.
- It supports thread lifecycle/persistence, streamed item events, server-initiated approval requests and generated client schemas.
- Installed Codex CLI `0.144.3` generated 1,873 non-directory schema files across default/experimental bundles; all 604 JSON files parse.
- A live handshake was not yet attempted.

**Benefits**

- Reuses Codex’s tool loop, sandbox/config/auth behavior, thread persistence and event model.
- Matches the intended Codex-native requirement.
- Keeps provider-specific protocol isolated behind one adapter.

**Costs / risks**

- Installed surface is labeled experimental.
- Event ordering and reconnect behavior still require a controlled smoke test.
- Version compatibility must be managed explicitly.

### Custom Agents SDK / Responses loop

**Benefits**

- Greater control over loop semantics.
- Agents SDK offers sessions, sandbox agents, approvals, tracing and durable-workflow integrations.

**Costs**

- Reimplements Codex-specific tool, workspace, configuration and event behavior already available through App Server.
- Expands scope and test burden before v0 proves value.

**Decision:** App Server. Pin the binary and generated schemas; isolate raw protocol; keep an adapter fallback path.

## 2. Trusted-host orchestrator vs harness inside sandbox

| Choice | Strength | Failure |
|---|---|---|
| Trusted host | Owns credentials, approvals, state, budgets, audit, process reconciliation and workspace policy | Requires disciplined path/command policy |
| Inside sandbox | Strongly local execution context | Cannot safely own host credentials, authoritative state or recovery after sandbox loss |

**Decision:** trusted host. Agent workspaces receive only the minimum scoped capabilities.

## 3. Durable handoff vs conversation/thread state

App Server threads and Work chats are useful context, but neither is a sufficient cross-surface system of record. Canonical state must survive client replacement, thread loss, process restart and provider migration.

**Decision:** SQLite for indexed Goal/Task/Run state, JSONL for append-only events, files for large evidence, Git for reversible workspace checkpoints.

## 4. Deterministic validation vs independent model evaluator

Deterministic checks are reproducible and should establish all executable criteria. Model evaluation is appropriate only when semantics, design or judgment cannot be fully encoded.

**Decision:** validator first. Evaluator is read-only, criterion-level, evidence-facing and returns `PASS | FAIL | INSUFFICIENT_EVIDENCE`.

## 5. Worktree vs container isolation

| Mechanism | v0 role |
|---|---|
| Git worktree | Default task isolation and diff/checkpoint surface on Windows |
| Container/Docker | Optional only when threat model or dependency conflicts materially require it |

**Decision:** worktree first; do not make Docker a prerequisite without evidence.

## 6. Host-owned authority

The host owns:

- provider/business credentials;
- approval decisions;
- state and event persistence;
- time/iteration/token/cost budgets;
- command/network/path policy;
- external-write authorization;
- audit and redaction.

The unexplained legacy-upstream merge demonstrates why project files cannot self-authorize commits, pushes, merges or releases.

## 7. Provider portability

Core contracts must not contain raw App Server messages. The adapter translates provider events into internal typed events such as:

- session/thread opened;
- turn started/completed;
- tool proposed/started/completed;
- approval requested/resolved;
- output delta;
- usage/rate-limit update;
- interruption/cancellation;
- normalized error.

A future Agents SDK or Claude adapter may replace the provider layer without changing Goal/Task/Run/Event, validation or workspace contracts.

## 8. Single-agent v0 vs multi-agent

Research supports multi-agent execution only for independently verifiable workstreams. v0’s actual bottleneck is unproven.

**Decision:** one worker session per task. Defer planner/generator/evaluator topologies and parallel workers until representative evaluations show a measurable need.

## Security implications

- Windows-native paths require canonicalization, junction/symlink/reparse-point checks and worktree containment tests.
- App Server compatibility failure stops before execution.
- No secret values enter model-visible state or committed fixtures.
- Commit, push, PR, merge, release, deployment, visibility change, external messages, purchases and production mutations require explicit approval.
- Target PR remains draft; ADR acceptance does not authorize merge.

## Migration triggers

Revisit the decision when:

1. the live App Server smoke test lacks a mandatory lifecycle/control;
2. protocol compatibility cannot be bounded by version/schema checks;
3. a managed runtime exposes equivalent inspectable state, approvals, recovery and results;
4. container isolation becomes mandatory;
5. cross-provider execution becomes an evaluated requirement;
6. multi-agent evaluations materially outperform single-agent v0.
