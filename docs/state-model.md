# Harness state model

## Authority and layers

This state model reflects code at `origin/main`
`c8370a53b2d1b5cdf4c5f448ad7aae9c34a412dd`, observed on 2026-07-27.
The canonical Python contracts are in [`state.py`](../src/harness/state.py);
the matching JSON schemas are
[`goal.schema.json`](../schemas/goal.schema.json),
[`task.schema.json`](../schemas/task.schema.json),
[`run-state.schema.json`](../schemas/run-state.schema.json),
[`event.schema.json`](../schemas/event.schema.json), and
[`config.schema.json`](../schemas/config.schema.json).

State is divided into four layers:

1. `Goal` defines mandatory done conditions, outputs, capabilities, action
   scope, budgets, and evidence expectations.
2. `Task` defines one bounded unit, dependencies, worktree, allowed/locked
   paths, criteria, validators, evidence paths, attempts, and operator next
   action.
3. `Run` holds the authoritative lifecycle, active task, budget, approval,
   checkpoint, stop, verdict, evidence, and event sequence.
4. `Event` records lifecycle transitions or normalized provider/validation/
   policy observations without becoming authority by itself.

All public records are frozen. Mappings are strict: unknown keys, type coercion,
naive timestamps, malformed stable IDs, duplicate references, and inconsistent
terminal fields are rejected.

## Task status

`TaskStatus` is distinct from the run lifecycle:

| Status | Meaning |
|---|---|
| `PLANNED` | Defined but not selectable |
| `READY` | Eligible for one iteration |
| `IN_PROGRESS` | Selected and executing |
| `VALIDATING` | Provider success occurred; evidence is being checked |
| `CHECKPOINTED` | Passing evidence was checkpointed |
| `COMPLETE` | Evidence paths exist and no next action remains |
| `BLOCKED` | Cannot continue; an explicit next action is required |
| `APPROVAL_REQUIRED` | A consequential boundary requires an explicit next action |
| `FAILED` | Terminal task failure with `last_failure` |
| `CANCELLED` | Task was cancelled |

One `execute_iteration` accepts one `READY` task, increments its attempt and the
run iteration once, and submits one provider turn. It does not schedule multiple
tasks or agents.

## Run lifecycle

The ordinary path is:

```text
CREATED
  -> INITIALIZING
  -> READY
  -> SELECTING_TASK
  -> EXECUTING
  -> VALIDATING
  -> [EVALUATING]
  -> CHECKPOINTING
  -> READY | COMPLETED
```

`EVALUATING` is optional. `VALIDATING -> CHECKPOINTING` is valid when
deterministic checks settle every mandatory criterion.

Every active state may stop as `BLOCKED`, `BUDGET_EXHAUSTED`,
`APPROVAL_REQUIRED`, `FAILED`, or `CANCELLED`. The normal completion path may
enter `COMPLETED` only from `CHECKPOINTING`.

| Stopped state | Allowed reason codes |
|---|---|
| `COMPLETED` | `COMPLETED` |
| `BLOCKED` | `BLOCKED`, `MISSING_DEPENDENCY`, `REPOSITORY_DIVERGENCE`, `UNSAFE_ACTION`, `REPEATED_NO_PROGRESS`, `REPEATED_INSUFFICIENT_EVIDENCE` |
| `BUDGET_EXHAUSTED` | `BUDGET_EXHAUSTED` |
| `APPROVAL_REQUIRED` | `APPROVAL_REQUIRED` |
| `FAILED` | `FAILED` |
| `CANCELLED` | `CANCELLED` |

`COMPLETED`, `FAILED`, and `CANCELLED` are final. `BLOCKED`,
`BUDGET_EXHAUSTED`, and `APPROVAL_REQUIRED` are classified as resumable stop
states, but current C-401 transition code gives all stopped states no outgoing
edge. Actual stopped-run resume and reconciliation are deferred to C-503; do
not mutate a stopped `Run` to imitate resume.

## Transition contract

`transition_run` returns one new immutable `Run`/`Event` pair and performs no
I/O. It enforces:

- one legal state edge;
- a new stable transition ID;
- a timestamp not earlier than `Run.updated_at`;
- one event-sequence increment;
- a state-appropriate structured stop reason;
- approval, checkpoint, verdict, and evidence invariants; and
- complete transition metadata only on lifecycle and terminal events.

[`LifecycleCoordinator`](../src/harness/lifecycle.py) derives transition
identities and requires a `LifecycleCommitter` to acknowledge the pair before
the next provider action.
[`HarnessOrchestrator`](../src/harness/orchestrator.py) commits
`INITIALIZING` before adapter startup and `EXECUTING` before turn submission.
It commits each normalized provider event before requesting the next event.

Provider events have provider-local IDs and sequence numbers. The orchestrator
assigns the canonical run-level `Event.event_seq`; provider output cannot
create lifecycle transition metadata.

## Completion and stop behavior

A provider `TURN_TERMINAL` success moves the run to `VALIDATING` and the task
to `VALIDATING`. It does not set `PASS`, checkpoint, complete the task, or
complete the run.

Finalization requires:

1. aggregate deterministic validation `PASS`;
2. optional evaluation evidence, if evaluation was requested;
3. an explicit checkpoint reference; and
4. explicit completion evidence references.

Passing evidence moves through `CHECKPOINTING` to either `READY` for another
task or `COMPLETED` for the goal. Missing or non-passing evidence is rejected.

Approval events stop at `APPROVAL_REQUIRED` with `REQUESTED`; the orchestrator
does not answer the provider or continue streaming. Expected provider failure
enters `FAILED`, interruption enters `BLOCKED`, and cancellation enters
`CANCELLED`. Adapter protocol/state errors fail; compatibility and transport
conditions are normalized to explicit blocked or failed outcomes.

## Persistence and event mirror

[`SQLiteStateStore`](../src/harness/state_store.py) is the authoritative
`LifecycleCommitter`. It creates:

- `metadata` for store schema identity;
- `runs` for the latest canonical run snapshot and hash; and
- `outbox` for each complete event, state/event hashes, delivery state, and
  unique run sequence/transition identity.

A successor run and its complete outbox row are written in one
`BEGIN IMMEDIATE` transaction. New histories start at sequence 1 and advance
exactly once. Exact duplicate delivery is idempotent only while the
authoritative run has not advanced; stale or conflicting replay fails closed.
Inline run JSON is limited to 256 KiB and event JSON to 64 KiB. Large payloads
must remain external and be referenced.

[`JsonlEventMirror`](../src/harness/events.py) scans the entire canonical UTF-8
JSONL file before append. It appends in committed outbox order, flushes and
fsyncs each line, then acknowledges the exact outbox row. A crash after fsync
and before acknowledgement is deduplicated on replay. A missing mirror can be
rebuilt from SQLite pending rows. A partial, noncanonical, duplicate, changed,
or conflicting mirror stops delivery; it is never used to invent state.

## State that exists but is not integrated

- [`budgets.py`](../src/harness/budgets.py) and
  [`retry_policy.py`](../src/harness/retry_policy.py) provide immutable policy
  decisions but are not wired into the orchestrator.
- [`approvals.py`](../src/harness/approvals.py) and
  [`permissions.py`](../src/harness/permissions.py) provide host decisions but
  are not wired into provider dispatch or persistence.
- SQLite currently persists Run/Event/outbox only. Broader Goal, Task,
  approval, action, and checkpoint tables are not implemented.
- Cross-process run locking, restart/reconnect, action reconciliation, and
  stopped-run resume are not implemented.
- The default CLI executor does not expose lifecycle state operations; see
  [`operations.md`](operations.md).

## Verification

The lifecycle and durability behavior is covered by:

- [`test_state.py`](../tests/unit/test_state.py);
- [`test_lifecycle.py`](../tests/unit/test_lifecycle.py);
- [`test_state_store.py`](../tests/unit/test_state_store.py); and
- [`test_events.py`](../tests/unit/test_events.py).

The accepted package evidence is
[`C-401-GATE.yaml`](../validation/C-401-GATE.yaml),
[`C-403-GATE.yaml`](../validation/C-403-GATE.yaml), and
[`C-406-GATE.yaml`](../validation/C-406-GATE.yaml).
