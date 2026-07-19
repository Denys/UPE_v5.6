# Recovery, Evaluation, and Operations Specification

**Phase:** W-201…W-210 web specification  
**Artifact class:** cross-cutting phase specification; no separate canonical backlog W-ID  
**Date:** 2026-07-19  
**Runtime status:** specified, not implemented or locally tested

## Operating objective

The trusted Windows host must execute one bounded task at a time, persist each lifecycle transition before the next external action, recover from interruption without guessing, and mark completion only from validation evidence. ChatGPT Work supplies accepted goals, specifications, handoffs, review, and human steering; it is not the canonical process or action-state database.

## Lifecycle contract

The runtime implements the accepted lifecycle from `Pasted markdown.md`:

```text
CREATED -> INITIALIZING -> READY -> SELECTING_TASK -> EXECUTING
        -> VALIDATING -> EVALUATING -> CHECKPOINTING -> READY

terminal/interrupted:
COMPLETED | BLOCKED | BUDGET_EXHAUSTED | APPROVAL_REQUIRED | FAILED | CANCELLED
```

Every transition must have a stable `transition_id`, monotonically increasing run-local `event_seq`, prior state, next state, reason, run/task identity, timestamp, evidence references, and redaction status. The state transition and complete outbox event are committed in one SQLite transaction before the next external action.

`COMPLETED` is legal only when all mandatory criteria have passing evidence. A generator message, model confidence, aggregate score, or missing validator output is not completion evidence.

## Persistence and checkpoint ordering

1. Acquire the run lock and validate the expected prior lifecycle state.
2. In one SQLite transaction, write the new state and its complete outbox event.
3. Commit SQLite before the next external action.
4. Deliver pending outbox rows to append-only JSONL in `event_seq` order, flush durably, then mark them delivered.
5. Deduplicate JSONL consumers by `transition_id` or `event_seq`.
6. Store large logs, diffs, schemas, and evaluation output as content-addressed or hashed files and reference them from state.
7. Create a host-managed checkpoint containing patch/diff, file hashes, lifecycle state, validation evidence, and recovery metadata.
8. Preserve the previous stable checkpoint until the new checkpoint is verified.

SQLite plus its outbox is authoritative if JSONL differs. JSONL is repaired by replay and never invents state. Routine checkpoints are not Git commits; a commit remains separately approval-gated.

## External-action journal

Before dispatch, persist:

- stable `action_id` and run/task identity;
- operation class and normalized arguments;
- exact target identity;
- matching approval record and approved scope;
- provider idempotency key where supported;
- status `PLANNED`, followed by `STARTED` before the call;
- attempt number and timestamps.

After dispatch, store provider/result references and one of `SUCCEEDED`, `FAILED`, or `UNKNOWN`. An interrupted `STARTED` or `UNKNOWN` action must be reconciled against the target system before retry. If reconciliation cannot prove whether the effect occurred, remain `UNKNOWN` and block or request human resolution; never generate a new identity and blindly repeat it.

## Restart and recovery procedure

Recovery follows ADR-001 in this order:

1. Acquire the exclusive run lock; refuse concurrent recovery or execution.
2. Load SQLite lifecycle state, pending outbox rows, approvals, and action-journal rows.
3. Repair JSONL from the outbox and verify sequence continuity.
4. Inspect live process identity and App Server thread/session state using the version-pinned adapter.
5. Inspect assigned worktree identity, filesystem containment, Git HEAD, index, and dirty state.
6. Reconcile every in-flight external action before any retry.
7. Verify the last completed validation and stable checkpoint against recorded hashes.
8. Choose exactly one outcome: continue from the proven next transition, `BLOCKED`, `APPROVAL_REQUIRED`, `FAILED`, or `CANCELLED`.

Conversation or App Server thread history may help reconstruct context but cannot override persisted state. An ambiguous `EXECUTING`, `STARTED`, file, process, or remote-action condition blocks until reconciled.

## Retry and no-progress policy

Classify failures before retry:

| Class | Response |
|---|---|
| Transient provider/network/process failure | Capped exponential backoff with jitter, finite attempts, elapsed-time and budget checks |
| Deterministic validation failure | Produce the smallest evidence-linked repair; do not retry unchanged |
| Permanent dependency/version/policy failure | Stop `BLOCKED` with exact evidence and prerequisite |
| Approval-required operation | Persist request and stop `APPROVAL_REQUIRED` |
| Non-idempotent or unknown external outcome | Reconcile by `action_id`/target; never blind-retry |
| Repeated identical failure or no measurable progress | Stop at configured threshold and preserve the last stable checkpoint |

No-progress comparison uses stable signals such as failure category/signature, validator results, artifact/diff hashes, satisfied criteria, and remaining delta. Paraphrased prose is not progress. Budgets for iterations, elapsed time, tokens, cost, and retries are enforced by host code, not advisory prompt text.

## Evaluation contract

### Layer 1 — deterministic

Run every applicable mechanical check first:

- unit and integration tests;
- build, lint, and type checks;
- JSON/YAML and JSON Schema validation;
- repository, reference, filesystem, and path-containment invariants;
- expected-output and diff constraints;
- secret, redaction, policy, and static-security scans;
- browser/UI tests only when UI behavior is in scope.

Each result records command or validator identity, version, cwd/scope, start/end, exit/result status, normalized error, output/evidence path, artifact hash, and redaction state. Timeouts and unavailable validators are explicit errors or UNKNOWN evidence, not passes.

### Layer 2 — independent model verifier

Invoke only for an accepted criterion that deterministic checks cannot settle. The verifier receives the frozen goal/criterion and concise primary evidence, inspects the actual artifact where practical, has no write or external-action capability, and returns criterion-level `PASS`, `FAIL`, or `INSUFFICIENT_EVIDENCE` plus evidence references and the smallest correction.

It cannot add criteria, expand scope, authorize actions, edit the artifact, or override a deterministic failure. `INSUFFICIENT_EVIDENCE` remains blocking for a mandatory criterion. Repeated insufficiency triggers a stop rather than evaluator shopping.

### Gate evaluation

Before phase or run completion evaluate:

1. **Contract and coverage:** every MUST and deliverable maps to an output and done condition.
2. **Evidence and integrity:** facts, files, transforms, tests, links, code, and artifacts have appropriate inspected evidence.
3. **Feasibility, safety, and delivery:** capabilities and permissions were real; actions were authorized and serialized; output is usable and complete.

The W-200 phase acceptance/checkpoint record uses `PASS | FAIL | UNKNOWN`; critical FAIL requires repair and critical UNKNOWN requires evidence or an explicitly partial phase result. New run, criterion, verifier, and handoff verification records use `PASS | FAIL | INSUFFICIENT_EVIDENCE` (plus `NOT_EVALUATED` only where the lifecycle schema permits it). Scores and votes cannot override a blocker.

At a schema boundary, W-200 phase `UNKNOWN` may be translated to `INSUFFICIENT_EVIDENCE` only explicitly and with the missing evidence preserved; neither may become PASS by translation.

## Operational commands and expected behavior

The local implementation supplies the brief's CLI without implying that it exists yet:

| Command | Required behavior |
|---|---|
| `harness doctor` | Report runtime, exact Codex/App Server, Git/worktree support, validators, SQLite path, permissions, and missing credential references without values |
| `harness init PATH` | Resolve and record canonical repository/workspace identity; create valid configuration/state without escaping PATH |
| `harness research` | Run or record the bounded research phase without mutating unrelated state |
| `harness run --goal goal.yaml` | Validate goal, acquire lock, select one ready task, and enter the persisted lifecycle |
| `harness status RUN_ID` | Read canonical state and surface explicit pending approvals, blockers, budgets, and evidence |
| `harness events RUN_ID` | Show the redacted ordered audit mirror and identify sequence gaps |
| `harness resume RUN_ID` | Run the complete reconciliation procedure before continuing |
| `harness pause RUN_ID` | Request a safe persisted pause; do not imply immediate termination before acknowledgement |
| `harness cancel RUN_ID` | Persist cancellation intent, interrupt safely, reconcile state, and finish `CANCELLED` |
| `harness evaluate RUN_ID` | Run missing deterministic checks, then only necessary read-only evaluation |
| `harness cleanup RUN_ID` | Verify terminal state, exact workspace ownership and containment; never remove unrelated worktrees |

## Normal runbook

1. Run `doctor`; stop on an unusable required dependency or policy failure.
2. Record repository remote/ref/HEAD, worktree list, dirty state, Codex executable identity/version, generated schema identity, validators, and budgets.
3. Validate the accepted goal and handoff schemas.
4. Acquire a task-specific worktree and persist its canonical identity.
5. Run the fast baseline and store the result.
6. Select one unblocked task and persist selection.
7. Execute one coherent change through the fake adapter until its lifecycle is proven; introduce the real adapter only after its prerequisites pass.
8. Inspect the diff, run task-specific deterministic validation, then broader regression checks when warranted.
9. Use the read-only verifier only for remaining subjective criteria.
10. Checkpoint and choose continue, complete, block, approval, budget, failure, or cancellation explicitly.

## Concurrency and ownership

- One exclusive run lock protects canonical state and recovery.
- One task owns one worktree; one coordinator owns each shared artifact or side effect.
- Read-only evidence collection may run concurrently only when inputs and outputs are disjoint.
- A stale base hash, lock loss, repository divergence, or overlapping write scope stops for reconciliation.
- SQLite transactions and outbox sequence, not chat timing, order state.

## Observability and evidence retention

Record normalized lifecycle, validation, approval, action, retry, checkpoint, recovery, policy, and terminal events. Include correlation IDs and evidence paths, not large raw output or secrets. Retention and deletion policy must be configured before real credentials or personal data are used. A final report distinguishes `planned`, `implemented`, `tested locally`, `blocked`, and `unverified`.

## Required test evidence

Implementation cannot claim acceptance until it supplies:

- transition and invalid-transition tests;
- outbox crash injection before/after SQLite commit and JSONL delivery;
- process/App Server/worktree/Git/validation reconciliation tests;
- checkpoint interruption and rollback tests;
- finite retry/backoff, budget, and no-progress tests;
- lost-response duplicate-action tests;
- deterministic-failure precedence and read-only-verifier tests;
- all canonical unit, integration, and six representative evaluation fixtures from the build brief;
- the controlled live App Server initialize/thread/turn/tool/approval/interrupt/reconnect smoke test;
- the full quality and security reports required by `C-605` and `C-606`.

`evals/work_loop_acceptance_cases.yaml` defines the Work-facing cases; execution results belong in separate result artifacts and must not rewrite the expected cases.

## Known limitations and escalation

- Codex App Server behavior is unverified beyond help/generated schemas for observed CLI `0.144.3`; the real adapter remains untested until the controlled smoke run.
- Python dependency compatibility is UNKNOWN until a manifest resolves and tests on the Windows target pass.
- CI is absent and required before release readiness, not before specification/scaffold work.
- Container isolation, multi-agent runtime, cloud scheduling, UI, autonomous PR/release, deployment, dynamic routing, and semantic memory are deferred.
- Escalate narrowly to Sol Max or the highest exposed effort for recovery, idempotency, event ordering, permissions/path security, persistent High failures, or final multi-component integration. Use Pro only for the canonical fresh read-only judgment gates.
