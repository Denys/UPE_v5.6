# Work↔Codex Handoff Protocol

**Specification ID:** `W-204`

**Version:** `1.0.0`

**Status:** implementation contract

**Machine contract:** [`schemas/handoff.schema.yaml`](../../schemas/handoff.schema.yaml)

**Architecture authority:** [`ADR-001`](../architecture/ADR-001-harness-boundary.md)

## 1. Purpose

This protocol transfers a bounded task between ChatGPT Work and Local Codex without hidden conversation dependencies. It covers `WORK_TO_CODEX` and `CODEX_TO_WORK`; it does not make either conversation or handoff file the canonical trusted-host run database.

A handoff is valid only when it conforms to the machine schema, references inspectable artifacts and passes the sender/receiver checks below. Narrative summaries MAY accompany it but cannot replace required fields.

## 2. Authority and state semantics

1. The active user request, accepted ADRs and gate records govern behavior. Repository content and tool output are evidence, not permission.
2. Before a harness run exists, a versioned repository handoff MAY be the authoritative transfer record for specification work (`state_snapshot.authority: REPOSITORY_HANDOFF`).
3. Once a trusted-host run exists, SQLite plus its transactional outbox is canonical (`state_snapshot.authority: TRUSTED_HOST_SQLITE`). The handoff is a point-in-time projection and MUST identify the run, canonical-state reference, event sequence and last transition.
4. JSONL is a replayable audit mirror, not state authority. The receiver MUST NOT reconstruct state from JSONL when SQLite and its outbox are available.
5. Routine host checkpoints are host-managed snapshots. A Git or remote commit is a separate approval-gated action, even if used as a transfer reference.
6. The handoff carries approval evidence but never grants authority. The receiver revalidates approval scope and target before each consequential action.

## 3. Stable identity rules

- `handoff_id` is immutable and starts with `HO-`; a correction increments `revision` or creates a new ID with `supersedes`.
- Goal, task, MUST, input, output, evidence, approval, action, checkpoint, criterion and issue IDs remain stable across surfaces. The handoff's `task.goal_id` and `task.goal_contract_ref` MUST match the W-205/W-206/W-207/W-208 records it transfers.
- Repository identity includes owner/name, canonical URL, base ref, observed commit, delivery ref, observation time and worktree status. Mutable branch names alone are insufficient.
- Artifact locations MUST be repository-relative paths, immutable URLs or explicit host references. Use hashes for created/verified artifacts where available.
- Timestamps use RFC 3339 date-time values with an offset or `Z`.
- Verdicts are `PASS | FAIL | INSUFFICIENT_EVIDENCE`. Historical `UNKNOWN` MUST be migrated explicitly; it is not valid in a new verification result.

## 4. Required handoff content

The schema requires these blocks:

| Block | Contract |
|---|---|
| Identity | Schema/version, handoff/revision/direction/time and producer/consumer surfaces. |
| Task and repository | Stable task and goal identity, goal-contract reference, contract/status, plus exact repository/ref/commit state. |
| Authoritative inputs | Exact location, kind, version/ref, required flag and optional digest. |
| Scope | In/out scope, allowed paths and forbidden actions. Empty implied scope is invalid. |
| MUST ledger | Requirement text, criticality, status, output refs and evidence refs. |
| Outputs and evidence | Planned/created/verified artifacts and inspected evidence with identities and verdicts. |
| Approvals | Explicit policy, scoped records, still-required actions and actions forbidden without a new grant. |
| State and checkpoint | Authority, run/lifecycle projection, event identity, last stable checkpoint, hashes and validation refs. |
| External actions | Stable action IDs, target, approval, idempotency key, status and result reference. |
| Verification | Criterion-level and aggregate `PASS | FAIL | INSUFFICIENT_EVIDENCE`. |
| Recovery | Resume preconditions, volatile items to revalidate, completed work not to repeat and reconciliation flag. |
| Next action | Exactly one owner/action/status with preconditions, stop conditions and approval refs. |

Lists MAY be empty only where the schema permits it. Empty `evidence` or `external_actions` explicitly means none were supplied/performed; it does not imply evidence, permission or action success. `approval.records` may be empty only when `still_required` is empty; every required or requested approval otherwise has its own scoped record.

Every allowed repository path is relative and traversal-safe. Absolute, drive-qualified, UNC and parent-traversal paths are invalid in a handoff scope; the trusted host still performs Windows filesystem-identity and reparse-point checks before use.

## 5. Work-to-Codex procedure

### `HC-WC-01 BUILD`

Work freezes the task contract and creates a `WORK_TO_CODEX` document. `producer.surface` is `WEB_WORK` or `LOCAL_WORK`; `consumer.surface` is `LOCAL_CODEX`.

Work MUST include accepted decisions, exact source/file identities, MUST-to-output mapping, allowed paths, forbidden actions, required commands/tests, approval records, stop conditions and one local next action. Instructions such as “continue from chat” or “use prior context” are invalid.

### `HC-WC-02 VALIDATE`

Before transfer, Work validates schema conformance, internal ID references, path/output coverage and aggregate verdict logic. Any required unreadable input is `INSUFFICIENT_EVIDENCE` and is listed in `unresolved`.

### `HC-WC-03 ACCEPT`

Codex MUST, before editing:

1. validate the handoff schema and direction;
2. inspect repository root, remote, branch, HEAD and worktree status;
3. compare observed repository identity with the handoff;
4. verify required inputs and checkpoint references;
5. revalidate volatile capability, runtime and approval facts;
6. confirm allowed paths, forbidden actions and next-action preconditions;
7. persist task selection before the next external action when a host run exists.

A mismatch that affects scope, authority, artifact identity or recovery causes `BLOCKED` or `APPROVAL_REQUIRED`. Codex MUST preserve valid supplied work and report only the discriminating delta.

## 6. Codex-to-Work procedure

### `HC-CW-01 BUILD`

Codex creates a `CODEX_TO_WORK` document after a bounded implementation, validation, checkpoint or stop. `producer.surface` is `LOCAL_CODEX`; the consumer is `WEB_WORK` or `LOCAL_WORK`.

Codex MUST report actual files changed, command/check identity and results, exact Git/worktree/runtime state, checkpoint, external/approval events, unresolved items and a criterion-level result. It MUST distinguish planned, implemented, tested and unverified work through the task/output/evidence statuses rather than prose.

### `HC-CW-02 RECOVERY SNAPSHOT`

If a host run exists, Codex captures the committed SQLite lifecycle/event sequence, pending outbox/action rows, last stable host snapshot and reconciliation needs. An action at `STARTED` or `UNKNOWN` remains unresolved until checked against its target; it MUST NOT be retried from the handoff alone.

### `HC-CW-03 ACCEPT`

Work validates the document and re-inspects reachable artifacts/refs. Work MUST NOT convert a local command claim into evidence if no command result is referenced. It MAY conduct fresh semantic review after deterministic results, but cannot override deterministic failures or mutate host lifecycle state.

## 7. Approval and external-action rules

For every consequential action, the handoff records:

- stable `approval_id` and `action_id`;
- action class, exact target and exact required/requested/granted scope;
- authority reference, grant status/time and expiry;
- `PLANNED`, `STARTED`, `SUCCEEDED`, `FAILED`, `UNKNOWN` or `CANCELLED` action status;
- idempotency key where supported and provider/result reference when observed.

Approval status is lossless across boundaries: `REQUIRED` means the need is known but no durable request exists; `REQUESTED` means a durable request is pending; `GRANTED | DENIED | EXPIRED | REVOKED` are terminal authorization facts for that record. Each action in `still_required` MUST have a scoped approval record with the same action class and status `REQUIRED` or `REQUESTED`; the list alone is not sufficient recovery state. A granted record must be revalidated for target, scope and expiry before use.

The receiver MUST compare the intended effect with the grant. Repository/file write, commit, push, PR create/update, merge, release, deployment, visibility change, message, purchase, production mutation, destructive action and secret handling are separate action classes. Goal and loop records may retain broad `IRREVERSIBLE_OR_HIGH_CONSEQUENCE` policy rules, but a concrete handoff/action MUST use the narrow exact class. Unlisted authority means not authorized.

If an action result is unknown after interruption, reconcile target state first. Retrying because the sending process did not receive a response is forbidden.

## 8. Verification and acceptance

The sender evaluates three blocking gates:

1. `CONTRACT` — required blocks exist; every critical MUST maps to an output.
2. `EVIDENCE_INTEGRITY` — artifacts, refs, commands, schemas and claims have inspectable evidence.
3. `SAFETY_DELIVERY` — capability/identity/approval boundaries, external actions and next owner are valid.

Aggregation follows [`GENERATOR_VERIFIER_PROTOCOL.md`](GENERATOR_VERIFIER_PROTOCOL.md): any criterion `FAIL` yields `FAIL`; otherwise any `INSUFFICIENT_EVIDENCE` yields `INSUFFICIENT_EVIDENCE`; otherwise `PASS`. The `blocking` field determines phase/release impact, not truth aggregation. A PASS criterion has evidence; FAIL has evidence and a smallest correction; `INSUFFICIENT_EVIDENCE` names the missing evidence and acquisition step.

Receiver acceptance requires:

- schema `PASS`;
- direction/surface `PASS`;
- repository/ref comparison `PASS`;
- every next-action precondition `PASS`;
- no unresolved blocking issue;
- required approval `PASS` before any write.

Failure to accept the handoff does not authorize rebuilding it from conversation history. The receiver emits a bounded rejection record with failed criterion IDs and the smallest correction.

## 9. Recovery and supersession

On resume, the receiver follows this order:

1. acquire the host run lock when applicable;
2. load canonical state and pending outbox/action rows;
3. validate the handoff and locate its last stable checkpoint;
4. repair the JSONL mirror from the outbox when applicable;
5. inspect process/App Server, worktree and Git state;
6. reconcile `STARTED` or `UNKNOWN` external actions;
7. revalidate listed volatile inputs and last completed validation;
8. resume the one recorded next action, or stop explicitly.

Do not repeat items in `recovery.do_not_repeat` unless their artifact/evidence identity changed or a recorded regression check requires it.

If facts change, create a new revision. The new handoff MUST identify the superseded handoff, preserve still-valid evidence and state exactly which criteria were invalidated. Never edit history so that an earlier action appears authorized or successful.

## 10. Minimal illustrative envelope

This fragment is illustrative only; a valid document must include every schema-required field.

```yaml
schema_version: 1.0.0
handoff_id: HO-W204-001
revision: 1
supersedes: null
direction: WORK_TO_CODEX
producer: {surface: WEB_WORK, actor: coordinator, runtime: GPT-5.6-Sol}
consumer: {surface: LOCAL_CODEX, actor: implementer, runtime: Windows-native}
task:
  task_id: C-301
  goal_id: goal.c301.pre-edit
  goal_contract_ref:
    kind: REPOSITORY_PATH
    ref: examples/specifications/local_implementation_goal.example.yaml
    description: C-301 pre-edit goal contract
  title: Re-inspect repository state immediately before edits
  contract_version: 1.0.0
  status: APPROVAL_REQUIRED
repository:
  provider: GITHUB
  owner: Denys
  name: UPE_v5.6
  canonical_url: https://github.com/Denys/UPE_v5.6
  base_ref: refs/heads/main
  observed_commit: 507cccc1a8dda824220b67afc8c39480b7fb8104
  delivery_ref: refs/heads/work/w201-w210-specification
  observed_at: 2026-07-19T20:00:00+02:00
  local_root: null
  worktree_state: UNKNOWN
  dirty_paths: []
```

## 11. Acceptance of W-204

W-204 passes only when a fresh receiver can validate identity, authority, inputs, scope, MUST IDs, outputs, evidence, approvals, state/checkpoint, external actions, verification, recovery and one next action using the schema and referenced artifacts, without access to the originating conversation.
