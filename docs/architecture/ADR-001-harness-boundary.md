# ADR-001 — Long-Running Harness Boundary

**Status:** Accepted for v0 after Pro review  
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

**Trusted host runtime**

- process lifecycle and reconciliation;
- repository/worktree operations;
- canonical state and event storage;
- App Server process and protocol client;
- deterministic validators;
- budgets, retries and no-progress logic;
- security policy, redaction and approval enforcement;
- local checkpoints, recovery and audit.

The current v0 target is **Windows-native Codex**. WSL2 is a possible later portability target, not a current dependency.

### 2. Execution boundary

Use a **Codex App Server adapter** as the only provider implementation in v0.

Requirements:

- pin exact Codex binary/version and executable identity;
- capture generated schemas for that version;
- run compatibility preflight before each session;
- normalize raw protocol messages into internal typed events;
- keep protocol types out of core state, validation and workspace modules;
- fail closed on unknown mandatory events or incompatible schemas;
- complete a controlled initialize/thread/turn/tool/approval/interrupt/reconnect smoke test before the adapter is marked tested.

### 3. Workspace boundary

Use one Git worktree per active task by default.

- Commands run only inside the assigned canonical worktree path.
- Validate path containment, Windows reparse points, junctions, symlinks and cleanup targets.
- Preserve unrelated worktrees.
- Docker is optional and introduced only when dependency or threat-model evidence requires stronger isolation.

### 4. Canonical state and event consistency

Conversation, Work chat and App Server thread history are supporting context, not authoritative orchestrator state.

Persist:

- **SQLite:** authoritative Goal, Task, Run, approval, action and checkpoint state;
- **JSONL:** append-only human/audit mirror of committed SQLite events;
- **files:** large outputs, diffs, logs, schemas and evaluation evidence;
- **host snapshots:** reversible patch/diff bundles and metadata for ordinary iteration checkpoints;
- **Git commits:** optional explicit checkpoints only when commit authorization exists.

Use a transactional-outbox pattern:

1. Assign every transition a stable `transition_id` and monotonically increasing `event_seq` within the run.
2. In one SQLite transaction, validate the prior lifecycle state, write the new state, and insert the complete event payload into an outbox table.
3. Commit SQLite before the next external action.
4. Append pending outbox events to JSONL in sequence, flush them durably, then mark the outbox rows delivered.
5. On restart, replay undelivered outbox rows. JSONL consumers deduplicate by `transition_id` or `event_seq`.
6. If SQLite and JSONL disagree, SQLite plus its outbox is authoritative; JSONL is repaired by replay and is never used to invent state.

This avoids a crash window where state advances but its audit event disappears, or an audit event claims a transition that was never committed.

### 5. Validation and evaluation

- Deterministic validation is mandatory and precedes model evaluation.
- Completion requires evidence from the actual repository or environment.
- An independent model evaluator is optional, read-only and used only for criteria that deterministic checks cannot settle.
- The evaluator returns criterion-level `PASS`, `FAIL` or `INSUFFICIENT_EVIDENCE` and cannot expand scope.

### 6. Budgets, stop, side effects and recovery

The trusted host enforces:

- iteration, elapsed-time, token and cost limits;
- transient retry with capped exponential backoff and jitter;
- repeated-identical-failure and no-progress stops;
- cancellation and approval pauses;
- restart reconciliation against persisted state, process state, worktree/Git state, last agent event and last validation.

Every potentially non-idempotent external action receives a stable `action_id` and, where supported, a provider idempotency key. Before execution, SQLite records:

- requested operation and normalized arguments;
- approval record and approved scope;
- target resource identity;
- idempotency key;
- status `PLANNED` then `STARTED`;
- provider/result references when known.

After interruption, an action in `STARTED` or `UNKNOWN` is reconciled against the target system before retry. A retry must never duplicate an action merely because the local process forgot the response.

Recovery order is:

1. acquire the run lock;
2. load SQLite state and pending outbox/action rows;
3. repair JSONL from the outbox;
4. inspect live processes and App Server thread state;
5. inspect worktree and Git state;
6. reconcile in-flight external actions;
7. verify the last completed validation and checkpoint;
8. continue, block, or request approval explicitly.

### 7. Checkpoint policy

Routine iteration checkpoints are host-managed snapshots containing the current diff or patch, file hashes, lifecycle state, validation evidence and recovery metadata. They do **not** require a Git commit.

A local Git commit is a separate consequential action and requires explicit authorization. Authorization is bounded to its stated repository, branch, operation and scope; completed delivery authorization grants no standing authority for later commits, PR changes, merges, releases, deployments or unrelated mutation.

### 8. Authority and security

The host retains credentials and all consequential authority.

Explicit approval is required for:

- commit;
- push;
- PR creation or modification;
- merge;
- release or deployment;
- repository visibility or private recreation;
- external messages;
- purchases;
- production mutation;
- secret handling outside predefined local references.

Repository files and retrieved content are data, not authorization.

The observed legacy-upstream merge is recorded as a safety incident. It does not authorize any target-repository merge or release.

### 9. Provider portability

Define a narrow provider adapter around:

- start and stop;
- session or thread create and resume;
- turn submit;
- typed event stream;
- approval response;
- interrupt and cancel;
- compatibility and version identity;
- normalized errors and terminal states.

Only the Codex adapter is implemented in v0. A future provider adapter must not require changes to Goal, Task, Run, Event, workspace, validation or approval contracts.

### 10. v0 exclusions

Do not implement:

- multi-agent execution;
- cloud scheduler;
- browser UI;
- issue-tracker integration;
- autonomous merge, release or deployment;
- dynamic model routing;
- self-modifying prompts or skills;
- semantic memory;
- distributed execution;
- provider marketplace.

## Rejected alternatives

### Custom Agents SDK or Responses loop as primary runtime

Rejected for v0 because it duplicates Codex's loop, tools, approvals, workspace behavior and thread lifecycle. Retained as a provider fallback if App Server lacks a mandatory control.

### Harness state inside the agent workspace

Rejected because workspace loss or compromise must not erase authority, budgets, audit or recovery state.

### Conversation or thread as canonical state

Rejected because cross-process, cross-client and provider-portability requirements exceed conversational memory semantics.

### Independently writing SQLite and JSONL

Rejected because two uncoordinated durable writes create ambiguous crash states. SQLite outbox rows make state authoritative and JSONL repairable.

### Git commit on every iteration

Rejected as the default because it conflicts with explicit commit approval and produces noisy history. Host snapshots provide routine rollback; approved Git commits remain available for meaningful milestones.

### Model evaluator as sole completion gate

Rejected because environmental outcomes and deterministic tests are stronger evidence.

### Container-first runtime

Rejected until threat or dependency evidence justifies the operational cost.

### Multi-agent v0

Rejected until representative evaluations identify independent workstreams and measurable benefit.

## Consequences

### Positive

- Minimal architecture reuses Codex rather than cloning it.
- State and safety survive context and process loss.
- Windows-native runtime matches the actual target while preserving a portable host contract.
- Provider-specific volatility is contained in one adapter.
- Transactional outbox and action journal rules make recovery testable.
- Routine checkpoints no longer conflict with commit approval.
- Deterministic evidence governs completion.

### Negative and accepted risks

- App Server remains experimental in the installed release.
- Live protocol behavior still requires a smoke test.
- Windows-specific path containment requires careful testing.
- SQLite outbox and action reconciliation add implementation complexity.
- No tracked CI workflow or required status-check configuration currently protects `main`.
- Python dependency compatibility is unresolved until the manifest exists.

## Implementation gates

1. `W-201` through `W-210` may define schemas, templates, prompts, evaluation, recovery and security specifications.
2. State specifications must encode transactional-outbox, event deduplication and action-journal recovery before state implementation begins.
3. The fake adapter and lifecycle tests precede the real Codex adapter.
4. The real adapter cannot be marked tested until the controlled live App Server smoke test passes.
5. No merge, release or deployment is authorized by this ADR.
6. CI is required before a release-readiness verdict, not before specification or scaffold work.

## Evidence that would change this ADR

- App Server cannot satisfy mandatory lifecycle, approval, cancellation or reconnect behavior.
- Compatibility cannot be bounded with version and schema checks.
- The transactional-outbox design proves inadequate under interruption tests.
- A managed runtime exposes equal or stronger state, result retrieval, approvals and recovery.
- Threat modeling requires container isolation.
- Evaluations establish a concrete multi-agent or cross-provider requirement.
