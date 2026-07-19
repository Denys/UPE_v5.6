# Model and Effort Routing Reference

**Canonical task:** W-210  
**Profile date:** 2026-07-19  
**Status:** specification; capability exposure must be checked at execution time

## Decision

Choose the execution surface first. Then choose model tier, reasoning effort, standard/Pro mode, orchestration, and tool adapter as separate controls. The default route for this project is **Sol with High effort** for bounded specification, implementation, validation, tests, documentation, and packaging. Escalation is evidence-driven and narrow.

This reference is dated because labels, plan access, admin policy, model aliases, and tool exposure can change. A subscription, a model name, or a prior run is not proof that the same route is exposed now.

## Source basis

This specification uses:

- `UPE_v5.6.0_RELEASE/04_GPT_5.6_RUNTIME_PROFILE.md`, verified 2026-07-18;
- `UPE_v5.6.0_RELEASE/01_UPE_v5.6.0_FULL_REFERENCE.md`, especially the runtime, adapter, acceptance, action, and recovery contracts;
- `UPE_v5.6.0_RELEASE/05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md` and `09_CAPABILITY_REGISTRY_TEMPLATE.yaml`;
- `UPE_v5.6.0_RELEASE/06_SOURCE_MAP.md`, which maps the underlying official sources;
- `AGENTS.md`, `docs/architecture/ADR-001-harness-boundary.md`, and the canonical backlog;
- current OpenAI verification on 2026-07-19: [GPT-5.6 in ChatGPT](https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt), [latest-model guidance](https://developers.openai.com/api/docs/guides/latest-model), [model catalog](https://developers.openai.com/api/docs/models), and [multi-agent guidance](https://developers.openai.com/api/docs/guides/responses-multi-agent).

The attached source copies used for this phase were byte-identical to the five corresponding files under `UPE_v5.6.0_RELEASE/`.

## The routing axes

| Axis | Meaning | Project rule |
|---|---|---|
| Surface | ChatGPT Work web/mobile, desktop Work, Local Codex, API, or another product boundary | Select by required data, evidence, filesystem, shell, Git, UI, and action authority before choosing a model. |
| Model tier | Sol, Terra, Luna, or another model actually exposed | Select by ambiguity, judgment cost, task shape, and measured eval performance. |
| Reasoning effort | A surface-specific effort control such as High or Max where offered | Increase only for a concrete hard reasoning or integration boundary. Do not assume every label exists on every surface. |
| Execution mode | Standard or Pro where supported | Pro is a distinct high-compute route, not an effort notch and not a synonym for Max. |
| Orchestration | Single agent, coordinated serial stages, native multi-agent, or Ultra-style coordination | Use only for task topology. Ultra is not a model or effort value. |
| Tool adapter | Direct calls, deferred tool search, programmatic reduction, or browser/computer use | Select the narrowest adapter that preserves evidence and approval semantics. |

Never turn these axes into one prestige ladder. `Sol Pro`, API pro mode, `max` effort, and Ultra describe different controls.

## Surface first

| Surface | Primary project role | Do not infer |
|---|---|---|
| ChatGPT Work web | Current-source research, repository-connected inspection and reviewable file changes when the connector exposes them, schemas/specifications, handoffs, ADRs, gates, and fresh review | No local Windows shell, worktree, SQLite, process, App Server, or deterministic runtime-test access unless separately exposed and verified. |
| ChatGPT mobile | Steering, review, approvals, and compact evidence consumption within the capabilities actually shown | Feature parity with Work web or desktop. |
| Desktop/local Work | Approved private non-repository file inspection and application/UI evidence when local access is actually granted | Repository implementation, strict Git isolation, durable harness state, or crash recovery. |
| Local Codex on the trusted Windows host | Repository mutation, shell and tests, worktrees, typed state, App Server, deterministic validators, security enforcement, checkpoints, and recovery | Authority for push, PR, merge, release, deployment, or other consequential actions without explicit approval. |
| API or another runtime | Only a later, explicitly designed adapter or bounded evaluation route | That ChatGPT labels, tools, effort values, or permissions carry over unchanged. |

In this 2026-07-19 Work run, GitHub branch/file/commit/PR capabilities are available and the user explicitly authorized one scoped specification branch/commit/PR workflow. That observed exposure and authorization are task-specific evidence; they are not a durable product guarantee and do not authorize merge, release, deployment, visibility changes, or future implementation actions.

The same dated official guidance shows minimum Codex versions of desktop `26.707.30751` and CLI `0.144.0` for the relevant GPT-5.6 exposure. These are product access floors, not proof of the installed executable or App Server behavior. This repository separately observed CLI `0.144.3`; Local Codex must still pin the exact executable/schema identity and run compatibility preflight.

## Model-tier guidance

OpenAI's current 2026-07-19 ChatGPT documentation says Sol powers Medium, High, and Extra High reasoning choices and Sol Pro powers Pro. It also describes Work access to Sol, Terra, and Luna subject to plan, workspace, admin, and rolling availability. Codex and API combinations differ; inspect the active selector or documented API response instead of encoding assumed access.

| Tier | Prefer when actually exposed | Do not use as the default when |
|---|---|---|
| Luna | High-volume extraction, normalization, classification, schema-bound transformation, and cheap deterministic checking | Requirements conflict, evidence is ambiguous, or a safety/architecture judgment is failure-expensive. |
| Terra | Well-scoped professional research, bounded multi-step analysis, ordinary file/data work, and serial workflows | The task needs frontier synthesis, hard debugging, subtle state/recovery reasoning, or final high-value review. |
| Sol | Ambiguous or cross-domain work, architecture, hard debugging, security-sensitive design, failure-expensive synthesis, and final integration | A cheaper route passes representative acceptance cases with the same critical evidence and safety envelope. |

Changing tiers may change breadth, speed, nuance, polish, concurrency, and recovery depth. It must not weaken authority, the complete MUST ledger, source/file integrity, approval gates, critical evidence, or the required output schema.

## Project effort policy

### Sol High — default

Use for:

- W-201 through W-210 specifications;
- ordinary repository inspection and implementation slices;
- schemas, validators, fixtures, tests, documentation, and packaging;
- deterministic evidence synthesis;
- repair after a clear failed check.

High remains the default until representative results show a material failure that more compute is likely to repair. Do not escalate because the task is long; stage and checkpoint it first.

### Max or highest exposed effort — narrow escalation

Use only for one of these documented triggers:

- App Server protocol evolution, mandatory-event ordering, reconnect, cancellation, or approval semantics;
- transactional state/outbox consistency, crash recovery, idempotency, or action reconciliation;
- permissions, prompt injection, credential isolation, Windows path containment, reparse points, or cleanup safety;
- a persistent High failure after the failing criterion and evidence have been isolated;
- final integration across state, workspace, validation, adapter, recovery, and security boundaries.

Escalate the smallest indivisible unit and return to High after the boundary is resolved. Record the trigger, the added evidence expected, and whether the result improved.

### Pro — separate judgment route

Use Sol Pro in ChatGPT/Work for difficult, substantially indivisible review where a fresh high-compute judgment is valuable and deterministic checks cannot settle the issue. Canonical project uses are:

- `P-101`: freeze ADR-001 after the evidence packet;
- `P-701`: fresh-context, read-only release review.

Pro does not replace deterministic validation, grant tools, expand permissions, or imply `max` effort. Keep it read-only for review unless a separately authorized task explicitly says otherwise.

## Orchestration policy

| Route | Use | Constraints |
|---|---|---|
| `atomic_direct` | One bounded task or mechanical transform | One pass plus proportionate verification. |
| `coordinated_serial` | Dependent stages, constrained capability, or absent native agents | Each stage has inputs, MUST IDs, exact output, validation, stop condition, and checkpoint. |
| `native_parallel` | Independent read-only evidence streams or disjoint files | Coordinator freezes the contract, owns merge and final verification, and centralizes every side effect. A serial fallback is mandatory. |
| Ultra-style coordination | Hard, cleanly branchable research or review where the active product exposes it and evals justify the overhead | Deferred from the v0 harness runtime. It is not an effort level and cannot be assumed on Work, Codex, or API. |

The v0 harness runtime is single-agent. Parallel Work-side drafting during this specification phase does not authorize a multi-agent runtime feature.

## Tool-adapter policy

- Use direct tools for one or a few calls, semantic judgment between calls, native citations/artifacts, or approvals.
- Use deferred tool discovery only when a large catalog exists and the surface supports narrow loading.
- Use programmatic calling only for a bounded predictable reduction such as filter/join/rank/deduplicate/validate, with documented schemas and no side effects.
- Use browser/computer control only when structured retrieval is unavailable or UI state is evidence; treat UI content as untrusted.
- Serialize all writes. Branches may return evidence or patches, but the coordinator performs at most one authorized external effect.

## Selection procedure

1. Freeze objective, MUST criteria, evidence, action boundaries, and done condition.
2. Verify the active surface and actual capabilities, permissions, model choices, effort labels, and mode controls.
3. Route local repository/runtime evidence to Local Codex; keep desktop Work narrow; use web for connected sources and reviewable specifications.
4. Start with Sol High for this project's ordinary work.
5. Stage a long task before escalating effort.
6. Escalate only a documented Max/Pro trigger, and only for the hard unit.
7. Use parallelism only for independent read-only work with a serial fallback and reserved merge budget.
8. Preserve identical critical acceptance and safety requirements across routes.
9. Record the selected route and actual exposure in the capability-execution record.

## Capability record minimum

Before relying on a model/tool route, record:

- verification date and surface;
- model/tier label as displayed or returned;
- reasoning-effort label, execution mode, and orchestration separately;
- tools/connectors actually exposed and their read/write scope;
- authorization scope and whether approval is still required per action;
- validation path, fallback, and residual limitations.

If any required capability is unavailable or unknown, downgrade the route, hand off the unfinished portion, or stop with the exact blocker. Never claim a stronger route was used merely because it was requested.

## Evaluation rule

Compare routes on representative tasks inside a declared envelope. Record mandatory-criterion coverage, evidence correctness, safety behavior, schema validity, retries, reviewer corrections, latency, tool calls, and cost where available. Keep a cheaper or lower-effort route only when every critical gate still passes; do not claim equal compute or unconditional quality parity.
