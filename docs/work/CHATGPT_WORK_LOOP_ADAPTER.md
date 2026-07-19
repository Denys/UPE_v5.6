# ChatGPT Work Loop Adapter

**Specification ID:** `W-201`

**Version:** `1.0.0`

**Status:** implementation contract

**Architecture authority:** [`ADR-001`](../architecture/ADR-001-harness-boundary.md)

## 1. Purpose and boundary

This document defines the Work-facing loop for research, reconciliation, specification, review, steering, approvals and durable deliverables. It is an operator adapter around the accepted goal and evidence contracts; it is **not** the trusted-host run loop.

Normative terms `MUST`, `MUST NOT`, `SHOULD` and `MAY` are used as requirements.

Work MAY use exposed web, file, connector, GitHub or artifact capabilities. Capability exposure is not authorization. Work MUST NOT claim persistent local-process control, worktree isolation, deterministic command execution or restart-safe host state unless those facts arrive as inspected evidence from the trusted host.

When a harness run exists, its SQLite state and transactional outbox remain authoritative. Work conversation, project context, remote thread state and this adapter's checkpoints are views or transfer artifacts; they MUST NOT invent or advance host lifecycle state.

## 2. Required inputs and outputs

Before execution, the adapter MUST resolve these inputs:

| ID | Input | Requirement |
|---|---|---|
| `WL-I01` | Task identity | Stable task or bundle ID, objective and requested output paths. |
| `WL-I02` | Authoritative inputs | Exact repository paths, source URLs, file identities, accepted ADRs and gate records. |
| `WL-I03` | Contract | MUST IDs, scope, non-goals, evidence requirements, done conditions and budgets. |
| `WL-I04` | Capability plan | Actual surface, required/optional/disabled capabilities, permissions, validation and fallback. |
| `WL-I05` | Repository identity | Required for repository work: owner/name, canonical URL, base ref, observed commit and intended delivery ref. |
| `WL-I06` | Approval snapshot | Explicit action, target, scope, grant source and expiry or revocation condition. Empty is valid only when no consequential write is planned. |
| `WL-I07` | Latest state | Latest valid handoff/checkpoint and, for a host run, the canonical-state reference and event sequence. |

If a required input is absent, Work MUST obtain it through a read-only inspection or return `INSUFFICIENT_EVIDENCE`, `APPROVAL_REQUIRED` or `BLOCKED`; it MUST NOT reconstruct it from hidden conversation memory.

Every completed Work stage MUST produce or update:

- a MUST-to-output coverage ledger;
- evidence references with exact source, path, ref or object identity;
- criterion-level verification results using `PASS | FAIL | INSUFFICIENT_EVIDENCE`;
- an explicit list of created/modified outputs and unmodified exclusions;
- approval use and external state-change records;
- a checkpoint or versioned handoff sufficient for fresh-context resume;
- one next action, or an explicit terminal/paused outcome.

## 3. Work loop

The steps below are ordered. A step MAY be skipped only when its precondition is demonstrably not applicable and that decision is recorded.

| Step | Contract |
|---|---|
| `WL-01 RESOLVE` | Identify surface, task, exact repository/source/file identities, active authority, current ref/state, risk, freshness and requested deliverables. Read before claiming. |
| `WL-02 FREEZE` | Record all MUST IDs, evidence requirements, assumptions, action boundaries and done conditions. Later evidence cannot silently rewrite them. |
| `WL-03 DISCOVER` | Select the narrowest exposed capabilities. Record prerequisites, read/write scope, approval, validation and a safe fallback. |
| `WL-04 ROUTE` | Choose the primary surface using [`WEB_VS_LOCAL_ROUTING.md`](WEB_VS_LOCAL_ROUTING.md) before choosing model/effort. Transfer out-of-surface work with a W-204 handoff. |
| `WL-05 SELECT` | Select one ready, bounded Work task or coherent specification bundle. Record dependencies and the acceptance checks before mutation. |
| `WL-06 EXECUTE` | Perform one coherent unit. Read-only branches MAY run independently; all shared or external writes MUST be serialized by one coordinator. |
| `WL-07 VERIFY` | Run available deterministic checks first. Invoke a read-only independent model verifier only under [`GENERATOR_VERIFIER_PROTOCOL.md`](GENERATOR_VERIFIER_PROTOCOL.md). |
| `WL-08 REPAIR` | Apply the smallest change that addresses failed criteria, preserving passing work and evidence. Never repeat an unchanged failed attempt. |
| `WL-09 CHECKPOINT` | Persist the contract delta, artifacts, evidence, verdicts, approval state, unresolved items, recovery instructions and next action. |
| `WL-10 DECIDE` | Continue, complete, hand off, request approval or stop under the outcome rules below. |

## 4. Verification and completion

### 4.1 Verdicts

- `PASS`: sufficient inspected evidence establishes the criterion.
- `FAIL`: evidence establishes that the criterion is violated.
- `INSUFFICIENT_EVIDENCE`: the available evidence cannot establish either pass or fail.

Missing evidence is never `PASS`. `INSUFFICIENT_EVIDENCE` is not interchangeable with `FAIL` and MUST identify the missing evidence and smallest acquisition step.

### 4.2 Gate order

Work MUST evaluate these gates in order:

1. **Contract and coverage:** every MUST maps to an output; scope, exclusions and required format are satisfied.
2. **Evidence and integrity:** sources and files were inspected; claims, links, calculations, schemas and artifacts are validated proportionally.
3. **Feasibility, safety and delivery:** capabilities and permissions are real; writes are authorized and serialized; the output is usable.

A critical `FAIL` requires repair or a failed/blocked outcome. A critical `INSUFFICIENT_EVIDENCE` requires evidence acquisition or an explicitly incomplete outcome. Aggregate scores and fluent prose cannot override either condition.

The generator's completion statement is never completion evidence. Repository-affecting work is complete only when the intended ref and artifacts are re-inspected and required deterministic checks pass.

## 5. Repair and no-progress control

For each repair attempt, Work MUST record:

- `attempt_id`, affected MUST/criterion IDs and prior verdict;
- the failure or evidence-gap signature;
- the bounded change proposed;
- new evidence and changed artifact identities;
- the resulting verdict.

An attempt is measurable progress only if it changes at least one of: a failed criterion, relevant evidence, a material artifact hash/ref, a blocking dependency or an approved action state.

Work MUST stop retrying when any configured iteration/time/cost limit is reached, or when the configured no-progress threshold is reached. If the goal does not configure a threshold, two consecutive attempts with the same normalized failure signature and no measurable progress trigger `BLOCKED`. The checkpoint MUST preserve successful work and state the discriminating change needed for another attempt.

Transient capability errors MAY be retried only with bounded backoff or a materially different fallback. A potentially non-idempotent action with an unknown result MUST be reconciled against the target system before any retry.

## 6. Approval and side-effect contract

Work MAY proceed with relevant reads, analysis, drafts and in-scope reversible artifact preparation. Before a commit, push, PR create/update, merge, release, deployment, repository visibility change, external message, purchase, production mutation, destructive action or non-routine secret handling, it MUST have an explicit grant matching:

- action class and intended effect;
- exact repository/system and destination;
- branch/ref or resource identity;
- content/path scope;
- allowed sequence or count;
- validity window or revocation condition.

The coordinator MUST perform at most one authorized action for one intended effect and record the observed result. A grant for branch/commit/PR work does not authorize merge, release, deployment, visibility change or unrelated mutation. A handoff transports approval evidence but cannot grant new authority.

If a consequential action is required but no matching grant exists, the next outcome is `APPROVAL_REQUIRED`; Work MUST NOT weaken the action, target or scope description to fit an older approval.

## 7. Checkpoints, handoffs and recovery

A Work checkpoint MUST contain, directly or by immutable reference:

- task and checkpoint IDs plus creation time;
- repository/source identities and observed refs;
- completed and pending MUST IDs;
- artifact paths, versions and hashes where available;
- deterministic and model-verifier results;
- assumptions, decisions, unresolved items and blockers;
- approvals used, denied, expired or still required;
- external writes and their returned identities;
- exact recovery preconditions, items not to repeat and one next action.

For specification-only work before a host run exists, a versioned repository artifact MAY be the transfer checkpoint. For an active host run, the checkpoint MUST reference the trusted-host canonical state and last stable host snapshot; it MUST NOT replace SQLite, the outbox or the action journal.

Routine host checkpoints are patch/diff snapshots with hashes, validation evidence and recovery metadata. Work MUST NOT request or imply a Git commit merely to create a checkpoint. Commit remains a separately approved action.

Cross-surface transfer MUST use [`WORK_CODEX_HANDOFF_PROTOCOL.md`](WORK_CODEX_HANDOFF_PROTOCOL.md) and [`schemas/handoff.schema.yaml`](../../schemas/handoff.schema.yaml). A fresh receiver MUST be able to resume using the handoff and referenced artifacts without the originating conversation.

## 8. Outcomes and escalation

`WL-10` records exactly one outcome:

| Outcome | Condition |
|---|---|
| `COMPLETE` | Every critical criterion is `PASS`; required deliverables and post-write identity checks exist. |
| `CONTINUE` | The next bounded Work step is ready, authorized and within budget. |
| `HANDOFF_REQUIRED` | The next step belongs to another surface or requires trusted-host evidence/execution. |
| `APPROVAL_REQUIRED` | A necessary consequential action lacks a matching current grant. |
| `BLOCKED` | A dependency, capability, identity conflict, safety condition or no-progress stop prevents a valid next step. |
| `CANCELLED` | The user cancelled the task. |

Escalation MUST be tied to a discriminating need, not prestige. Work escalates to a stronger/fresh reviewer only when material ambiguity, evidence conflict, security/approval interpretation or subjective acceptance remains after deterministic checks. It routes to Local Codex when exact local repository, process, worktree, App Server or validator evidence is required. It MUST preserve completed artifacts and request only the missing work.

## 9. Concurrency and ownership

- Read-only research MAY be parallelized when workstreams are independent and share a common result contract.
- Concurrent writers MUST NOT target the same artifact, branch, PR field or external effect.
- One coordinator owns contract freeze, conflict resolution, all consequential writes, merge of branch results and final acceptance.
- Conflicts are resolved by authority, exact surface/version match, freshness and discriminating evidence; never by vote or prose concatenation.
- If parallel execution is unavailable, incomplete workstreams run serially from the same briefs. Completed work is not regenerated.

## 10. Acceptance tests for this specification

`W-201` passes only if a reviewer can trace goal freeze, repair, deterministic-first evaluation, checkpoint, recovery, no-progress, approval and escalation behavior to stable sections above, and no section assigns trusted-host canonical state or process control to Work.
