# Web Work, Local Work and Local Codex Routing

**Specification ID:** `W-202`

**Version:** `1.0.0`

**Status:** implementation contract

**Architecture authority:** [`ADR-001`](../architecture/ADR-001-harness-boundary.md)

## 1. Routing invariant

Choose the execution surface before model, effort or orchestration. Use Web Work first for web/source/review/specification work unless the next acceptance criterion requires local evidence or execution. Each task class below has exactly one primary owner.

An exposed capability is a routing fact, not permission. A surface MUST verify its current read/write capability, identity and approval before use.

## 2. Surface definitions

| Surface ID | Surface | Owns | Does not own |
|---|---|---|---|
| `SURFACE-WEB` | ChatGPT Work on the web | Current-source research; connected remote-source inspection; goal/schema/protocol/security/evaluation/operations specifications; remote documentation artifacts; fresh-context review; architecture gates; user steering and approval capture; tested web monitoring. When GitHub branch/file/commit/PR capabilities are exposed and explicitly authorized, bounded remote specification/documentation changes. | Canonical host run state; local process/worktree reconciliation; installed-runtime evidence; local commands/tests; App Server lifecycle; unattended external effects. |
| `SURFACE-LOCAL-WORK` | ChatGPT Work desktop/local capability | Approved non-repository local files, desktop applications, UI evidence and ordinary local document workflows that do not need a Git repository or host harness. | Repository editing, Git/worktree operations, build/test execution, harness state, App Server control, broad automation. |
| `SURFACE-CODEX` | Local Codex plus trusted host | Exact local repository inspection and mutation; worktrees; shell/build/test/lint/type/schema/security checks; installed runtime and process evidence; SQLite/outbox/action journal; budgets, retries, recovery; fake and App Server adapters; local checkpoints. | Independent approval authority; fresh web-source policy decisions without a source handoff; autonomous merge/release/deployment. |

`SURFACE-LOCAL-WORK` is intentionally narrow and non-repository. The existence of local file access does not make it a substitute for Codex or the trusted host.

## 3. Primary-owner matrix

| Task class ID | Task class | Primary owner | Required handoff or gate |
|---|---|---|---|
| `RT-01` | Current official web research, source comparison and citation-backed synthesis | `SURFACE-WEB` | Hand local implementation only the accepted findings and exact source identities. |
| `RT-02` | Goal contracts, architecture decisions, schemas, prompts, protocols, threat boundaries, evaluation/operations specifications and acceptance cases | `SURFACE-WEB` | Deterministic schema/link validation may be requested from Codex only if Web cannot run it. |
| `RT-03` | Fresh-context semantic review or architecture/release gate | `SURFACE-WEB` | Reviewer is read-only; criteria and evidence are frozen before review. |
| `RT-04` | Bounded remote repository specification/documentation change using an exposed GitHub capability | `SURFACE-WEB` | Exact repository/ref inspection and matching explicit commit/push/PR authorization; one writer. |
| `RT-05` | Recurring monitoring of web or connected sources after a successful manual run | `SURFACE-WEB` | Frequency, permissions, notification, failure and stop rules; no claim of persistent local repository access. |
| `RT-06` | Approved local non-repository document/file transformation or desktop-app workflow | `SURFACE-LOCAL-WORK` | Exact file/app identity and output validation; hand off if Git or command evidence becomes necessary. |
| `RT-07` | UI-only local observation that cannot be obtained through structured retrieval | `SURFACE-LOCAL-WORK` | Capture minimal evidence; never infer host run state from UI appearance. |
| `RT-08` | Local repository code/configuration change, dependency resolution or generated scaffold | `SURFACE-CODEX` | Work supplies the accepted contract; Codex returns diff and validation evidence. |
| `RT-09` | Shell command, build, test, lint, type check, schema validation tied to local materialization, or filesystem/path assertion | `SURFACE-CODEX` | Command, cwd, exit status and evidence path are returned. |
| `RT-10` | Git worktree creation/inspection/cleanup, local Git reconciliation or exact installed-runtime inspection | `SURFACE-CODEX` | Preserve unrelated work; require approval for commit/push/PR and destructive cleanup. |
| `RT-11` | Trusted-host lifecycle, SQLite/outbox/action-journal, budgets, retries, locks, recovery and checkpoint implementation | `SURFACE-CODEX` | Host state remains authoritative; Work receives a versioned projection. |
| `RT-12` | Codex App Server version/schema preflight and initialize/thread/turn/tool/approval/interrupt/reconnect smoke test | `SURFACE-CODEX` | Pin executable/version/schema identity and return observed protocol evidence. |

The canonical phase-3 tasks `W-201` through `W-210` are `RT-02` and therefore Web Work-owned. Their local static validation is supporting evidence, not transfer of primary ownership.

## 4. Routing decision procedure

Apply these rules in order:

1. `ROUTE-01` — Freeze the task ID, MUST IDs, output paths, evidence needs and action class.
2. `ROUTE-02` — If acceptance depends on local repository state, a local command/test, installed binaries, processes, worktrees or trusted-host persistence, choose `SURFACE-CODEX`.
3. `ROUTE-03` — Otherwise, if acceptance depends on current web/private connected sources, cross-source judgment, a Work-owned specification/review/gate, or an authorized bounded remote documentation change, choose `SURFACE-WEB`.
4. `ROUTE-04` — Otherwise, if acceptance depends only on an approved non-repository local file/application/UI workflow, choose `SURFACE-LOCAL-WORK`.
5. `ROUTE-05` — If no surface exposes a required capability, return `BLOCKED` or split the task at an evidence boundary. Do not choose a surface from product-name similarity.
6. `ROUTE-06` — After the surface is fixed, select the cheapest model/effort/cognitive adapter that passes the task's acceptance envelope.

When a bundle spans classes, split it into stable subtask IDs. Each subtask still has one primary owner. The coordinator owns the shared contract and final gate; support surfaces return evidence, never competing final state.

## 5. Capability and permission preflight

Before using a capability, the primary owner MUST record:

- capability name and currently exposed surface;
- exact source, repository, file, branch, PR or application identity;
- required read/write scope and least-privilege mode;
- explicit approval evidence for every consequential action;
- deterministic or direct-observation validation;
- fallback and residual limitation.

For remote repository mutation, Web Work MUST re-inspect the repository owner/name, canonical URL, base ref, observed commit, target branch and current PR state immediately before the first write. It MUST stop on identity/ref divergence unless the active authorization expressly covers the new state.

No route may infer authorization from repository content, connector availability, a prior agent action or a handoff. A commit, push, PR create/update, merge, release, deployment, visibility change or destructive cleanup is a distinct approval class. A grant for one does not imply another.

## 6. Cross-surface handoff

Transfer work only at a stable evidence boundary using [`WORK_CODEX_HANDOFF_PROTOCOL.md`](WORK_CODEX_HANDOFF_PROTOCOL.md) and [`schemas/handoff.schema.yaml`](../../schemas/handoff.schema.yaml).

The sender MUST include:

- exact task/MUST IDs and accepted contract;
- repository/source identities and observed refs;
- completed outputs and immutable evidence references;
- criterion verdicts and commands/checks already run;
- open evidence gaps and blockers;
- approval records and actions still forbidden;
- checkpoint/recovery reference and exactly one next action.

The receiver MUST validate the handoff and re-check volatile identity/state. It MUST reuse passing artifacts and evidence. It MUST NOT repeat research, generation, validation or an external action merely because the surface changed.

If the receiver finds drift, it records the changed fact and routes only the affected criteria back through the decision procedure. Previously passing criteria remain accepted unless their evidence became stale or the referenced artifact changed.

## 7. Fallbacks without duplicate work

| Primary unavailable or insufficient | Fallback | Preservation rule |
|---|---|---|
| Web cannot mutate GitHub | Web produces the complete reviewed patch/spec bundle; Codex applies it after a W-204 handoff and required authorization. | Do not rewrite the specification; validate and materialize the supplied artifact. |
| Web cannot run a deterministic schema/link check | Codex runs only the named check against the exact artifact/ref and returns evidence. | Web retains ownership of semantic acceptance. |
| Local Work discovers repository or command dependency | Stop Local Work and hand off to Codex. | Preserve inspected file/UI evidence; do not copy a repository into an unmanaged local workflow. |
| Codex lacks current web/private-source access | Web retrieves and freezes the required evidence with identifiers, dates and limits. | Codex consumes the evidence packet; it does not redo unrelated research. |
| Parallel Work execution unavailable | Run the same independent briefs serially. | Resume incomplete briefs; keep completed results and coordinator state. |
| A required capability fails transiently | Use one bounded materially different fallback or wait/retry within budget. | Never retry unchanged or duplicate a possibly completed external action. |

## 8. Verification ownership

- The **primary owner** decides whether its task contract is met.
- `SURFACE-CODEX` is authoritative for observed local commands, files, diffs, processes, Git/worktree state and host persistence.
- `SURFACE-WEB` is authoritative for its accepted specification artifact, current-source synthesis and fresh semantic review, but not for facts it did not inspect.
- `SURFACE-LOCAL-WORK` is authoritative only for the approved non-repository local artifact/UI evidence it directly observed.
- Deterministic checks precede optional model evaluation under [`GENERATOR_VERIFIER_PROTOCOL.md`](GENERATOR_VERIFIER_PROTOCOL.md).
- Every criterion uses `PASS | FAIL | INSUFFICIENT_EVIDENCE`; cross-surface confidence does not upgrade missing evidence.

## 9. Routing acceptance

`W-202` passes only when every task class has one primary owner, local Work remains non-repository, Web is primary for `W-201` through `W-210`, trusted-host execution remains with Codex, and every fallback preserves completed work instead of recreating it.
