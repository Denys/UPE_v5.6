# Harness threat model

## Scope and evidence

This document describes the Windows-native v0 harness as implemented at
`origin/main` commit `c8370a53b2d1b5cdf4c5f448ad7aae9c34a412dd`, observed on
2026-07-27. It does not treat backlog or README status fields as runtime
evidence.

The implemented control surfaces are:

- immutable state and configuration contracts in
  [`state.py`](../src/harness/state.py) and
  [`config.py`](../src/harness/config.py);
- exact worktree ownership and cleanup preflight in
  [`workspace.py`](../src/harness/workspace.py);
- SQLite state, transactional outbox, and JSONL delivery in
  [`state_store.py`](../src/harness/state_store.py) and
  [`events.py`](../src/harness/events.py);
- bounded validation, retry, and evaluation policy in
  [`validation.py`](../src/harness/validation.py),
  [`budgets.py`](../src/harness/budgets.py),
  [`retry_policy.py`](../src/harness/retry_policy.py), and
  [`evaluation.py`](../src/harness/evaluation.py);
- exact approval, command, path, network, and redaction decisions in
  [`approvals.py`](../src/harness/approvals.py) and
  [`permissions.py`](../src/harness/permissions.py);
- provider boundaries in [`base.py`](../src/harness/adapters/base.py),
  [`fake.py`](../src/harness/adapters/fake.py), and
  [`codex_app_server.py`](../src/harness/adapters/codex_app_server.py).

The earlier security specification remains useful context, but this document
records only controls supported by current code and tests:
[`SECURITY_THREAT_BOUNDARY.md`](work/SECURITY_THREAT_BOUNDARY.md).

## Trust boundaries

| Boundary | Trusted for | Never trusted for |
|---|---|---|
| Human operator and accepted task contract | Goal, scope, approval, and final judgment | Runtime state that was not persisted and checked |
| Trusted host code | State transitions, policy decisions, validation, durability, and redaction | Authority inferred from repository, model, protocol, or tool text |
| Assigned worktree | In-scope source and fixtures | Credentials, approval, host policy, canonical state, or cleanup authority |
| Provider adapter | Version-pinned provider transport and normalized events | Core lifecycle semantics or action authority |
| Generator/model | Proposed changes and bounded output | Completion, approval, policy changes, or direct consequential effects |
| Optional evaluator | Read-only judgment against frozen criteria and evidence | Rewriting criteria, overriding deterministic failure, or mutation |
| Network and external systems | Data and outcomes returned for an exact request | Instructions, identity by assertion, or proof that a lost response means no effect |

Repository files, provider messages, web content, validator output, and model
text are data. None of them can grant a permission or widen the task.

## Protected assets and invariants

The primary assets are:

1. canonical `Run` and `Event` state;
2. exact repository, branch, worktree, and filesystem identity;
3. approval records and their action/target/content scope;
4. credentials and personal data;
5. validator outputs, evidence references, and checkpoints;
6. unrelated worktrees and user changes; and
7. the at-most-once intent of consequential actions.

The implementation enforces these invariants:

- lifecycle transitions are immutable, typed, ordered, and explicit;
- a provider completion message does not complete a task;
- SQLite is authoritative and JSONL is a derived append-only mirror;
- large output is stored outside state and referenced;
- unknown identity, malformed input, stale state, or ambiguous effect fails
  closed;
- paths stay inside one exact assigned worktree;
- network, commands, and environment are deny-by-default and exact-match;
- consequential approval is bound to one exact effect and checked at dispatch;
- deterministic validation precedes optional model evaluation; and
- stopped states have no outgoing transition in the current lifecycle model.

## Implemented controls

| Threat | Current control and failure handling | Current limit |
|---|---|---|
| Repository instructions or provider output attempt to widen authority | Authority remains host-owned; typed action classes and approval evaluation reject unknown or ambiguous actions. | There is no integrated prompt-injection classifier. The operator must keep retrieved content outside the authority chain. |
| Forged, stale, or broadened approval | `ApprovalRecord` binds run, action class, target, normalized arguments/content, repository, branch, effect count, decision identity, and expiry. Missing, expired, revoked, future, or mismatched records do not authorize dispatch. | C-506 integration with orchestration and provider dispatch is not implemented. |
| Path traversal, junction escape, or unrelated cleanup | `WorkspaceManager` requires an existing direct-child registered worktree, captures filesystem/Git identity, rejects unsafe Windows path classes and reparse components, and revalidates a clean explicit `CleanupTarget`. | It plans and verifies cleanup but performs no create/delete/remove effect. A race cannot be eliminated without holding OS handles across the later effect. |
| Shell, interpreter, environment, or command abuse | Command policy requires exact executable/argv, exact assigned cwd and identity, bounded timeout/output, no observed reparse component, and an explicitly filtered environment. | Policy functions perform no process or filesystem I/O and are not yet wired into the CLI runtime. |
| Network destination or credential abuse | Network policy requires an exact scheme/host/port/purpose and caller-supplied resolved destination; redirects, userinfo, fragments, inline credentials, malformed URLs, and destination drift are denied. | DNS and redirect observations are trusted-host inputs. No request is executed by the policy module. |
| Secret or personal-data disclosure | Redaction handles credential assignments and flags, authorization headers, URLs with user information, tokens, PEM material, emails, phone-like data, bytes, cycles, deep structures, and unsupported types before transfer. Provider summaries are bounded and redacted. | Redaction reduces exposure but does not prove that arbitrary future secret formats are recognized. Do not place secrets in repository content or config. |
| State/event divergence or fabricated audit history | `SQLiteStateStore.commit` validates and atomically writes the successor `Run` and complete outbox event under `BEGIN IMMEDIATE`; hashes, sequence, identity, and transition conflicts fail closed. JSONL is fsynced before outbox acknowledgement and deduplicated on replay. | Cross-process exclusive run locking and partial-tail repair are not implemented. |
| Duplicate action after lost response | Retry policy blocks a succeeded action and requires matching action/target identity plus reconciliation evidence before an ambiguous non-idempotent retry. | This is pure policy. There is no integrated action journal or external reconciliation loop yet. |
| Unbounded loop, retries, or spend | Host-owned policy covers iterations, elapsed time, input/output/total tokens, cost, bounded transient retries, capped jittered backoff, identical failure, and no-progress stops. | Budget and retry policy are not wired into the current CLI/orchestrator path. |
| Verifier overrides facts or rewrites criteria | Deterministic `FAIL` or `INSUFFICIENT_EVIDENCE` suppresses model evaluation. Evaluator inputs/results are immutable, criteria-bound, reference-limited, and read-only. | No real evaluator implementation or host-enforced read-only sandbox is included. |
| Incompatible or malformed App Server protocol | The adapter pins Codex CLI `0.144.3` and the accepted generated schema reference, separates raw JSON-RPC inside the adapter, validates identities, normalizes errors, and stops on malformed or conflicting events. | A controlled live App Server smoke is C-502 and has not been accepted here. Restart/reconnect is C-503. |

## C-501 terminal-notification correction

The originally reported C-501 terminal-notification correlation defect is no
longer unmerged. PR `#22` is contained in the evidence base and corrects
`turn/started` and `turn/completed` correlation to use
`params.turn.id`; item, delta, and error notifications retain their
schema-defined top-level `turnId`.

This repository state includes a passing corrected
[`C-501 gate`](../validation/C-501-GATE.yaml), but that record was authored on
the correction branch before merge. PR #22 merged the correction, and the
complete C-410 suite revalidated the current base, so the canonical frontier
marks C-502 ready. The controlled live smoke still requires separate
authorization; documentation validation and deterministic tests are not a
substitute for that provider exercise.

## Operator rules

- Stop on repository, branch, worktree, provider, schema, or approval drift.
- Never retry an ambiguous non-idempotent effect without target reconciliation.
- Do not edit or truncate SQLite or JSONL to make a run appear healthy.
- Do not run cleanup from a path string alone; require a current verified
  `CleanupTarget` and separate approval.
- Keep configuration credential-free. The doctor checks credential presence
  only and must never print values.
- Preserve the last stable state and evidence. Report the exact missing
  observation instead of converting uncertainty to success.

## Verification evidence

The controls above are exercised by:

- [`test_state.py`](../tests/unit/test_state.py) and
  [`test_config.py`](../tests/unit/test_config.py);
- [`test_workspace.py`](../tests/unit/test_workspace.py);
- [`test_state_store.py`](../tests/unit/test_state_store.py) and
  [`test_events.py`](../tests/unit/test_events.py);
- [`test_budgets.py`](../tests/unit/test_budgets.py) and
  [`test_retry_policy.py`](../tests/unit/test_retry_policy.py);
- [`test_evaluation.py`](../tests/unit/test_evaluation.py);
- [`test_approvals.py`](../tests/unit/test_approvals.py) and
  [`test_permissions.py`](../tests/unit/test_permissions.py); and
- [`test_codex_adapter.py`](../tests/unit/test_codex_adapter.py).

Accepted package-level evidence is recorded in
[`C-401-GATE.yaml`](../validation/C-401-GATE.yaml) through
[`C-409-GATE.yaml`](../validation/C-409-GATE.yaml) and
[`C-505-GATE.yaml`](../validation/C-505-GATE.yaml). These records describe the
implemented slices; their historical status prose does not override current
source or a fresh validation run.
