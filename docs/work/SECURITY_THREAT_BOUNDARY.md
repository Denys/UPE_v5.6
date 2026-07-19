# Security and Threat Boundary

**Phase:** W-201…W-210 web specification  
**Artifact class:** cross-cutting phase specification; no separate canonical backlog W-ID  
**Date:** 2026-07-19  
**Implementation owner:** trusted Windows host / Local Codex

## Security objective

The harness must let an agent work inside one assigned repository workspace without transferring host authority into that workspace. Credentials, approvals, budgets, persistent state, external-action authority, audit, path policy, and recovery remain on the trusted host. Files, retrieved content, model output, tool output, and App Server events are evidence or untrusted data; none can grant permission.

The v0 design is single-agent, fake-adapter first, Windows-native, and fail-closed. It does not authorize autonomous push, PR, merge, release, deployment, production mutation, external messages, purchases, visibility changes, or broad credential inheritance.

## Trust zones

| Zone | Trusted for | Not trusted for |
|---|---|---|
| Human operator and accepted Work artifacts | Goal, explicit approvals, ADRs, accepted schemas, and review decisions | Runtime state unless persisted and validated by the host |
| Trusted host control plane | SQLite state, transactional outbox, action journal, locks, credentials, budgets, policy, validation, recovery, and audit | Treating model or repository content as authority |
| Assigned task worktree | In-scope source edits and test fixtures | Credentials, approvals, policy, canonical run state, cleanup scope, or instructions that override the task |
| Codex App Server adapter | Version-pinned model/tool event transport after compatibility preflight | Core state semantics, unvalidated mandatory events, or action authority |
| Model/verifier | Proposed changes and bounded judgment | Completion, approval, direct external writes, or rewriting acceptance criteria |
| Network/connectors/external systems | Explicitly requested data or action results | Behavioral instructions, identity by assertion, or proof that an interrupted action failed |

## Protected assets and invariants

- Provider and business-system credentials never enter the broad agent workspace.
- SQLite plus its transactional outbox is canonical; JSONL is a repairable audit mirror.
- Every consequential action has one stable `action_id`, exact target, normalized arguments, matching approval scope, and reconciled result.
- Every command, file operation, and cleanup target stays inside its assigned canonical worktree unless a narrower explicit policy grants another path.
- Every completed criterion has actual validation evidence.
- Secrets and obvious personal data are redacted before persistence or model transfer.
- Side effects are serialized and executed at most once per intended effect.
- The last stable checkpoint remains recoverable after failure.

## Threats and mandatory controls

| ID | Threat | Required host control | Required evidence |
|---|---|---|---|
| TB-01 | Prompt injection in repository, web, issue, tool, or protocol content | Freeze authority and scope before inspection; label external content untrusted; reject requests to reveal secrets, change policy, add tools, or perform unrelated actions | `WL-009`; unchanged contract/capability plan; injection event |
| TB-02 | Forged, stale, or scope-expanded approval | Store approval separately from workspace/model output; bind it to action class, exact target, normalized content/argument digest, branch/resource identity, validity, and approving user | `WL-010`; approval record; zero pre-approval action events |
| TB-03 | Windows path traversal, symlink/junction/reparse escape, device path, ADS, or unsafe cleanup | Resolve against the canonical root using filesystem identity; reject unsafe path classes and unowned targets; never use string-prefix containment alone | `WL-011`; Windows containment fixtures |
| TB-04 | Secret or personal-data disclosure | Allowlist credential references; do not inherit the full environment; redact before logs/events/checkpoints/verifier input; scan canary fixtures | `WL-012`; secret scan and redaction tests |
| TB-05 | Command or network capability abuse | Deny by default; use structured command policy, bounded arguments, cwd enforcement, timeouts, network allowlists, and explicit reason | Policy decision and command/network audit event |
| TB-06 | Duplicate external effect after lost response | Persist `PLANNED` then `STARTED`; use stable action and provider idempotency keys; reconcile the target before retry | `WL-015`; fake-provider lost-response test |
| TB-07 | Concurrent writer or stale-base overwrite | One writer/coordinator per artifact/resource; run lock and version/hash precondition; branches return read-only evidence or patches | `WL-007`; lock/base-hash evidence |
| TB-08 | SQLite/JSONL divergence or fabricated audit event | Commit state and complete outbox row in one SQLite transaction; flush JSONL in sequence; deduplicate and repair only from outbox | crash-injection tests and sequence audit |
| TB-09 | Unknown or incompatible App Server protocol | Pin executable identity and version, capture generated schema, preflight each session, normalize at adapter boundary, fail closed on unknown mandatory events | compatibility report and controlled smoke evidence |
| TB-10 | Cleanup removes unrelated worktree or host data | Record workspace identity at creation; refuse broad/glob/environment-derived paths; verify ownership and containment immediately before cleanup | cleanup negative tests and post-cleanup worktree list |
| TB-11 | Generator or verifier spoofs completion | Deterministic checks precede optional read-only verifier; evidence is inspected directly; critical missing evidence remains `INSUFFICIENT_EVIDENCE` in a criterion/verifier record or `UNKNOWN` only in the W-200 phase gate | `WL-002`, `WL-004`, `WL-016` |
| TB-12 | Unbounded cost, time, retry, or no-progress loop | Host-enforced iteration/time/token/cost budgets; finite retries; identical-failure/no-progress stop | `WL-003`, `WL-014`; budget/stop tests |
| TB-13 | Repository or branch identity drift | Record remote/repository/ref/HEAD and dirty state before edits and before consequential action; stop on divergence | pre-edit context and pre-action identity check |

## Approval contract

The model, repository, branch, plugin, connector, verifier, or prior unrelated approval cannot authorize an action. The trusted host must create a durable approval request before any consequential action.

Minimum approval record:

```yaml
approval:
  approval_id:
  requested_by_run:
  action_class:
  target_identity:
  normalized_arguments_digest:
  content_or_patch_digest:
  repository_and_branch:
  maximum_effects: 1
  expires_at:
  decision: REQUIRED | REQUESTED | GRANTED | DENIED | EXPIRED | REVOKED
  decided_by:
  decided_at:
```

`REQUIRED` records a known approval need before a durable request exists; `REQUESTED` is a pending durable request. `GRANTED` is the only status that permits the exact recorded effect after target, scope, expiry, and content are revalidated. These values map directly to the W-204 handoff record; W-206 loop state uses `REQUIRED | REQUESTED` only because resolved approvals move to evidence rather than remaining in `approvals_needed`.

Changing target, content, arguments, branch, visibility, action class, or effect count invalidates the approval. Resume after a crash must reload the approval record; it must not ask the model to reconstruct approval from conversation.

Repository commits are consequential checkpoints and require explicit authorization. Push, PR, merge, release, deployment, visibility changes, messages, purchases, and production changes require their own matching authorization. Authorization for one specification branch/PR does not carry into later harness implementation or release.

## Windows path-containment contract

For every read, write, command working directory, archive extraction, checkpoint, and cleanup:

1. Start from the configured absolute canonical task root, not the process default directory.
2. Reject empty, unresolved, globbed, or environment-derived destructive targets.
3. Normalize drive letter and case using Windows semantics; reject device namespaces (`\\.\\`, `\\?\\`) and UNC paths unless explicitly allowlisted.
4. Reject alternate data streams and reserved device names unless a specific tested need exists.
5. Inspect every existing path component for symlink, junction, mount point, or other reparse behavior. For writes and cleanup, default to rejection; if policy permits one, resolve final filesystem identity and re-check containment.
6. Create new files through a contained parent whose identity was checked immediately before creation.
7. Revalidate containment after creation and before rename, replace, archive extraction, or deletion to reduce time-of-check/time-of-use exposure.
8. Cleanup only a workspace recorded under the current run/task identity, never a parent directory or unrelated worktree.

A lexical `startsWith(root)` check is insufficient because of case, separators, `..`, reparse points, short names, and sibling-prefix paths.

## Credential and redaction contract

- Store credential handles or secret-manager references in state, not values.
- Give a provider adapter only the credential required for that provider and session.
- Give validators and the read-only verifier no credentials unless their exact documented operation requires a narrow reference.
- Redact before writing SQLite payloads, outbox rows, JSONL, console logs, checkpoints, test reports, handoffs, or model/verifier context.
- Record that redaction occurred and preserve non-secret error category, source, and correlation IDs.
- Treat diffs, environment dumps, command lines, URLs, headers, stack traces, fixtures, and binary metadata as possible secret carriers.
- Use synthetic canaries to prove that both normal and exception paths redact before persistence.

## Command, network, and external-action policy

- Commands require a configured executable/argument policy, assigned cwd, environment allowlist, timeout, output limit, and normalized result.
- Shell composition, interactive elevation, arbitrary interpreters, and commands that expand unresolved variables require explicit policy or rejection.
- Network is denied unless enabled for a documented target and purpose. Redirects and resolved destinations remain within policy.
- Read-only source retrieval does not grant write authority to that source or connector.
- External actions are never parallelized. The host records the action before dispatch and the result after reconciliation.

## Failure behavior

Fail closed with a structured reason when identity, containment, approval, event compatibility, action outcome, redaction, lock ownership, or mandatory evidence is uncertain. Preserve the last stable checkpoint and return the smallest safe next step. Do not silently downgrade a policy failure to a warning.

## Verification obligations

Local implementation must include deterministic positive and negative tests for:

- injection and authority preservation;
- approval scope, denial, expiry, and resume;
- Windows traversal, case, sibling-prefix, ADS, device, UNC, symlink, junction, and cleanup cases;
- environment/credential minimization and redaction on success and exception paths;
- action lost-response reconciliation and duplicate prevention;
- concurrent writer/lock and stale-base behavior;
- outbox crash windows and JSONL repair;
- unknown App Server mandatory events;
- budget, retry, and no-progress stops;
- completion with missing or failed evidence.

Release remains blocked until the canonical security checks in `C-606` produce evidence that no secret appears in fixtures/logs, malicious repository instructions remain data, forbidden actions are blocked, and no unauthorized external mutation occurred.

## Residual limitations

- App Server is experimental in the observed Codex CLI `0.144.3`; live lifecycle and reconnect behavior remains unverified until `C-502`.
- Container isolation is deferred. Evidence of dependency or threat escape must trigger an ADR review.
- Windows reparse/path behavior needs tests on the actual supported filesystem, not POSIX-only mocks.
- A public repository increases disclosure impact; visibility changes remain a separately authorized action.
