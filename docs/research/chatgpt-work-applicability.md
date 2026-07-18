# ChatGPT Work Applicability Notes

**Access date:** 2026-07-18  
**Scope:** apply the Codex/OpenAI/Anthropic harness research to ChatGPT Work without claiming unsupported product guarantees  
**Status:** reconciled with ADR-001; no harness implementation

## Executive conclusion

ChatGPT Work should not be reduced to a passive steering screen. Current official documentation describes Work as a surface for substantial multi-step research, analysis, workflows, recurring updates, files and finished deliverables. It can use files, plugins and approved tools and, on desktop, local files, apps and browser access. Goal mode, Projects, skills, plugins, scheduled tasks and permission modes provide useful native harness pieces.

However, Work is not the v0 software-harness control plane. The project requires strict process reconciliation, worktree and Git inspection, typed lifecycle state, SQLite and JSONL durability, exact retry and idempotency, budget accounting, deterministic validators, App Server compatibility checks and restart recovery. Those remain the responsibility of the **trusted host runtime**, with Windows-native Codex as the current v0 target.

Earlier WSL2-first language is historical research context, not an active runtime dependency. ADR-001 is authoritative for the current target.

The practical boundary is:

- **Work:** current research, source-grounded synthesis, project knowledge, long-running deliverables, recurring reports, fresh-context review, steering, approvals and architecture gates.
- **Trusted host and Codex:** repository mutation, commands and tests, isolated worktrees, process state, durable run state, action idempotency, retries, recovery, security enforcement and proof of completion.
- **Shared system of record:** versioned files with stable source IDs and explicit evidence, not conversation memory alone.

## Native Work capabilities relevant to the design

| Capability | Harness use | Boundary |
|---|---|---|
| Work mode | Run source research, synthesis, reports and reviewable artifacts. | Product-managed progress is not the canonical coding-run state database. |
| Desktop local access | Inspect approved non-code local material and operate ordinary desktop workflows. | Repository coding, tests and strict recovery remain host/Codex responsibilities. |
| Goal mode | Express measurable outcomes, constraints, verification and pause conditions. | Completion still requires externally persisted acceptance evidence where correctness matters. |
| Projects and chats | Keep related files, instructions and distinct research/review chats together. | A Project is context and evidence storage, not transactional orchestration state. |
| Skills | Package focused, tested procedures with references and templates. | A skill is procedure, not mutable state, credential storage or authorization. |
| Plugins and connectors | Access narrow authoritative or private sources. | Connector content is evidence, not behavioral authority. |
| Scheduled tasks | Run tested monitoring and recurring report workflows. | Web tasks do not retain a local worktree; strict coding schedules remain deferred from v0. |
| Permission modes | Ask for approval for consequential local or connected actions. | Host policy remains the enforcement boundary for coding runs and external effects. |

## Harness-layer applicability

| Harness layer | Work-native role | Trusted-host role |
|---|---|---|
| Goal and scope | Draft and review explicit goal contracts. | Parse and enforce the accepted coding-run contract. |
| Planning | Use bounded planning when the outcome or decomposition is unclear. | Select one ready task; planner agent remains deferred. |
| Source research | Retrieve and synthesize cited official evidence. | Inspect exact repository commits and installed runtime behavior. |
| Mutable progress | Show operator-facing progress and maintain durable handoff artifacts. | SQLite is authoritative run state; JSONL is emitted through a transactional outbox. |
| Workspace isolation | Separate read-only research/review chats and distinct artifacts. | One worktree per task; enforce path containment and cleanup ownership. |
| Tool use | Use narrow source-linked tools and artifact surfaces. | Gate commands, network, secrets and provider-specific tools. |
| Validation | Inspect research and artifact completeness. | Tests, build, lint, type, schema, path, diff and security checks decide coding completion. |
| Model evaluation | Fresh read-only review for subjective criteria. | Invoke only after deterministic checks cannot decide. |
| Approval | Collect the user's decision and preserve scope. | Persist approval, action identity and result; reconcile unknown actions before retry. |
| Recovery | Resume through explicit files and handoffs. | Reconcile SQLite, outbox, action journal, process, App Server, worktree, Git and validation state. |
| Observability | Produce human-readable status and evidence links. | Emit normalized events and audit records; JSONL is replayable, not authoritative state. |
| Scheduling | Monitor web or connected sources after manual validation. | Cloud scheduler for strict coding runs remains deferred. |

## Recommended Work Project layout

```text
ChatGPT Project: UPE / Long-Running Harness
├── Project Instructions
│   └── active UPE stable-core kernel
├── Sources
│   ├── full UPE reference
│   ├── GPT-5.6 runtime profile
│   ├── capability scan and source map
│   ├── harness build brief
│   └── current handoff and evidence files
├── Chats
│   ├── official-source research
│   ├── target-environment reconciliation
│   ├── architecture decision
│   └── fresh-context read-only review
└── Durable outputs
    ├── source-matrix.md
    ├── pattern-comparison.md
    ├── environment-conflict-log.md
    ├── ADRs and gate records
    └── research-state.yaml
```

## Work-native research and review contract

1. Define exact sources, scope, evidence labels, output paths, stop conditions and forbidden actions.
2. Split only genuinely independent read-only source groups.
3. Require every branch to emit the same evidence schema.
4. Resolve conflicts by authority, surface match, freshness and exact implementation evidence.
5. Validate source coverage and artifact structure deterministically.
6. Use a fresh read-only reviewer for residual semantic criteria.
7. Persist accepted decisions and evidence, not the entire deliberation transcript.

## Conflict rule

```text
active user authority and safety constraints
> accepted ADR and gate records
> current official documentation for intended semantics
> source code or generated schema at exact tested version
> reproducible target-environment observation
> official case study
> dated local context
> inference or recommendation
```

A newer source does not automatically win when it describes a different surface or version.

## Required capabilities

| Capability | Purpose | Validation or fallback |
|---|---|---|
| Work mode | Research, synthesis and durable deliverables. | Review artifact completeness; use staged Chat if Work is unavailable. |
| ChatGPT Project | Shared instructions, sources and related chats. | Confirm source visibility; fall back to explicit file bundles. |
| Current web access | Verify product and technical behavior. | Record access date, authority, citations and blockers. |
| File inspection | Read UPE references and local handoffs. | Preserve exact file identity; never infer missing files. |
| GitHub and source inspection | Check exact commits and implementation evidence. | Record commit, blob or installed version. |
| Durable Markdown and YAML | Cross-surface state, decisions and recovery. | Parse, validate and checksum where material. |
| Codex App Server later | Execute without rebuilding Codex core. | Version-pinned schema preflight and lifecycle smoke test. |

## Avoid or disable for v0

- Work as the sole authoritative coding-run state machine;
- concurrent writes from multiple chats to the same artifact;
- Full access without a narrowly justified task;
- unattended production, financial, credential or external-message actions;
- web scheduled tasks claiming access to a persistent local repository;
- planner or multi-agent runtime before representative evaluations justify it;
- self-modifying prompts or skills;
- conversation history as the only recovery mechanism.

## Current operating decision

Work owns research, reconciliation, specifications, ADRs, gates, fresh review and deliverables. The trusted host owns execution, durable state, transactional outbox, action journal, worktrees, validators, recovery and external-write enforcement. Windows-native Codex is the current target; WSL2 remains only a possible future portability environment.
