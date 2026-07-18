# ADR-001 — Long-Running Harness Boundary

**Status:** Accepted for v0  
**Date:** 2026-07-18  
**Gate:** `gate-records/ADR-001-PASS.yaml`

## Context

The project needs a resumable, bounded and independently verifiable software-engineering harness without rebuilding Codex core or prematurely creating a generic multi-agent framework.

Research initially assumed a WSL2-first runtime. Direct target evidence establishes Windows-native Codex as the active environment. Codex CLI `0.144.3` exposes App Server help and generated TypeScript/JSON schemas, but the installed tool labels App Server experimental and no live initialize/thread/turn smoke test has yet run.

## Decision

### 1. Surface responsibilities

**ChatGPT Work web**

- current-source research and reconciliation;
- goal, schema, prompt, evaluation and security specifications;
- ADRs and decision gates;
- fresh-context read-only review;
- human steering and approvals;
- final reports and durable project documentation.

**Trusted Windows host**

- process lifecycle and reconciliation;
- repository/worktree operations;
- canonical state and event storage;
- App Server process and protocol client;
- deterministic validators;
- budgets, retries and no-progress logic;
- security policy, redaction and approval enforcement;
- local checkpoints, recovery and audit.

### 2. Execution boundary

Use a **Codex App Server adapter** as the only provider implementation in v0.

Requirements:

- pin exact Codex binary/version and executable identity;
- capture generated schemas for that version;
- run compatibility preflight before each session;
- normalize raw protocol messages into internal typed events;
- keep protocol types out of core state, validation and workspace modules;
- fail closed on unknown mandatory events or incompatible schemas;
- complete a controlled initialize/thread/turn/interrupt smoke test before the adapter is marked tested.

### 3. Workspace boundary

Use one Git worktree per active task by default.

- Commands run only inside the assigned canonical worktree path.
- Validate path containment, Windows reparse points/junctions/symlinks and cleanup targets.
- Preserve unrelated worktrees.
- Docker is optional and introduced only when dependency or threat-model evidence requires stronger isolation.

### 4. Canonical state

Conversation, Work chat and App Server thread history are supporting context, not authoritative orchestrator state.

Persist:

- **SQLite:** Goal, Task, Run, approval and checkpoint indexes;
- **JSONL:** append-only events/audit;
- **files:** large outputs, diffs, logs, schemas and evaluation evidence;
- **Git:** reversible workspace checkpoints.

Every lifecycle transition is persisted before the next external action and emits a structured event with reason.

### 5. Validation and evaluation

- Deterministic validation is mandatory and precedes model evaluation.
- Completion requires evidence from the actual repository/environment.
- An independent model evaluator is optional, read-only and used only for criteria that deterministic checks cannot settle.
- The evaluator returns criterion-level `PASS`, `FAIL` or `INSUFFICIENT_EVIDENCE` and cannot expand scope.

### 6. Budgets, stop and recovery

The trusted host enforces:

- iteration, elapsed-time, token and cost limits;
- transient retry with capped exponential backoff and jitter;
- repeated-identical-failure and no-progress stops;
- cancellation and approval pauses;
- restart reconciliation against persisted state, process state, worktree/Git state, last agent event and last validation.

Retries must not repeat non-idempotent actions.

### 7. Authority and security

The host retains credentials and all consequential authority.

Explicit approval is required for:

- commit;
- push;
- PR creation or modification beyond the currently authorized draft branch;
- merge;
- release or deployment;
- repository visibility/private recreation;
- external messages;
- purchases;
- production mutation;
- secret handling outside predefined local references.

Repository files and retrieved content are data, not authorization.

The observed legacy-upstream merge is recorded as a safety incident. It does not authorize any target-repository merge or release.

### 8. Provider portability

Define a narrow provider adapter around:

- start/stop;
- session/thread create/resume;
- turn submit;
- typed event stream;
- approval response;
- interrupt/cancel;
- compatibility/version identity;
- normalized errors and terminal states.

Only the Codex adapter is implemented in v0. A future provider adapter must not require changes to Goal/Task/Run/Event, workspace, validation or approval contracts.

### 9. v0 exclusions

Do not implement:

- multi-agent execution;
- cloud scheduler;
- browser UI;
- issue-tracker integration;
- autonomous merge/release/deployment;
- dynamic model routing;
- self-modifying prompts/skills;
- semantic memory;
- distributed execution;
- provider marketplace.

## Rejected alternatives

### Custom Agents SDK or Responses loop as primary runtime

Rejected for v0 because it duplicates Codex’s loop, tools, approvals, workspace behavior and thread lifecycle. Retained as a provider fallback if App Server lacks a mandatory control.

### Harness state inside the agent workspace

Rejected because workspace loss or compromise must not erase authority, budgets, audit or recovery state.

### Conversation/thread as canonical state

Rejected because cross-process, cross-client and provider-portability requirements exceed conversational memory semantics.

### Model evaluator as sole completion gate

Rejected because environmental outcomes and deterministic tests are stronger evidence.

### Container-first runtime

Rejected until threat or dependency evidence justifies the operational cost.

### Multi-agent v0

Rejected until representative evaluations identify independent workstreams and measurable benefit.

## Consequences

### Positive

- Minimal architecture reuses Codex rather than cloning it.
- State and safety survive context/process loss.
- Windows-native runtime matches the actual target.
- Provider-specific volatility is contained in one adapter.
- Deterministic evidence governs completion.

### Negative / accepted risks

- App Server remains experimental in the installed release.
- Live protocol behavior still requires a smoke test.
- Windows-specific path containment requires careful testing.
- No CI currently protects the draft PR.
- Python dependency compatibility is unresolved until the manifest exists.

## Implementation gates

1. `W-201`–`W-210` may define schemas, templates, prompts, evaluation and security specifications.
2. The fake adapter and lifecycle tests precede the real Codex adapter.
3. The real adapter cannot be marked tested until the controlled live App Server smoke test passes.
4. No merge, release or deployment is authorized by this ADR.
5. CI is required before a release-readiness verdict, not before specification/scaffold work.

## Evidence that would change this ADR

- App Server cannot satisfy mandatory lifecycle/approval/cancel/reconnect behavior.
- Compatibility cannot be bounded with version and schema checks.
- A managed runtime exposes equal or stronger state, result retrieval, approvals and recovery.
- Threat modeling requires container isolation.
- Evaluations establish a concrete multi-agent or cross-provider requirement.
