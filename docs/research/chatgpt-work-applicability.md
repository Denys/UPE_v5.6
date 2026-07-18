# ChatGPT Work Applicability Notes

**Access date:** 2026-07-18  
**Scope:** apply the Codex/OpenAI/Anthropic harness research to ChatGPT Work without claiming unsupported product guarantees  
**Status:** research recommendation, no external action or implementation

## Executive conclusion

ChatGPT Work should **not** be reduced to a passive steering screen. Current official documentation describes Work as a surface for substantial multi-step research, analysis, workflows, recurring updates, files, and finished deliverables. It can use files, plugins, approved tools, and, on desktop, local files/apps/browser access. Goal mode, Projects, skills/plugins, scheduled tasks, and permission modes provide useful native harness pieces.

However, Work is **not the v0 software-harness control plane**. The project requires strict process reconciliation, worktree/Git inspection, typed lifecycle state, SQLite/JSONL durability, exact retry/idempotency, budget accounting, deterministic validators, App Server compatibility checks, and restart recovery. Those remain the responsibility of the trusted WSL2 host plus Codex App Server.

The practical boundary is therefore:

- **Work:** research, source-grounded synthesis, project knowledge, long-running deliverables, recurring reports, fresh-context review, steering, and approvals.
- **Codex/host harness:** repository mutation, commands/tests, isolated worktrees, process state, durable run state, retries, recovery, security enforcement, and proof of completion.
- **Shared system of record:** versioned files with stable source IDs and explicit evidence, not conversation memory alone.

Humans have spent decades rediscovering that a UI is not a database. Agent products have graciously offered a fresh opportunity to learn it again.

---

## 1. Current native Work capabilities relevant to harness design

| Capability | Documented Work behavior | Harness use | Boundary |
|---|---|---|---|
| Work mode | Delegates substantial tasks and produces reviewable briefs, decks, analyses, recurring updates, workflows, or files; can use files, plugins, and approved tools. | Run source research, synthesize findings, create reports and artifacts. | Product-managed execution is not the canonical v0 run-state database. |
| Desktop local access | Work can use local files, apps, and browser when available and approved. | Inspect non-code local project material and create/update artifacts. | Use least privilege; repository coding/testing stays in Codex unless the task is genuinely everyday-work rather than software engineering. |
| `/goal` | Desktop Goal mode supports pause, resume, edit, clear; goal text includes outcome, constraints, and verification. Web Work supports hosted long-running work from the prompt. | Bounded research, artifact production, and review loops. | Native completion checking is not assumed equivalent to independently persisted acceptance evidence. |
| Projects and chats | Projects keep related chats, files, instructions, and connected sources together; distinct outcomes should use separate chats. | Store UPE kernel, source set, research chats, review chats, and deliverables. | A ChatGPT Project has no direct local-folder access; upload/connect required sources. |
| Skills | Reusable instructions/resources for focused workflows; ChatGPT can select them or the user can invoke with `@`. | Package source-matrix extraction, evidence labeling, and independent review after manual validation. | Skill is procedure, not mutable state, secret storage, or authorization. |
| Plugins/connectors | Installable bundles can provide skills and MCP-backed connected services. | Narrow authoritative/private source access. | Select least privilege; connector content is evidence, not behavioral authority. |
| Scheduled tasks | Background recurring work; desktop can run in local project/worktree with machine/app on; web can use uploaded context/tools but has no persistent local folder/worktree. | Periodic research updates, monitoring, status reports, and stable skill-driven workflows. | Test manually first. Web runs must receive durable instructions and accessible sources on each run. |
| Permissions | `Ask for approval` corresponds to workspace write plus on-request approval; sandbox and reviewer are separate controls; full access is high risk. | Default local Work posture and human gate for consequential actions. | Full access and unattended network/file mutation are excluded by default. |
| Workspace Agents trigger API | External systems can trigger a published agent, continue by `conversation_key`, and safely retry with `Idempotency-Key`. | Future event-triggered workflows. | Current response is only `202`; no public run ID or response retrieval, so it cannot satisfy strict v0 reconciliation. |

Official current product sources:

- https://help.openai.com/en/articles/20001275
- https://learn.chatgpt.com/docs/get-started-with-work
- https://learn.chatgpt.com/docs/long-running-work
- https://learn.chatgpt.com/docs/projects
- https://learn.chatgpt.com/docs/skills-and-plugins
- https://learn.chatgpt.com/docs/automations
- https://learn.chatgpt.com/docs/permission-modes
- https://learn.chatgpt.com/workspace-agents/trigger-runs
- https://learn.chatgpt.com/docs/feature-maturity

---

## 2. Harness-layer applicability map

| Harness layer | Work-native use | Additional artifact discipline | Codex/host requirement |
|---|---|---|---|
| Goal and scope | Work prompt or `/goal`; Project Instructions provide active UPE invariants. | `goal.yaml`/research brief with objective, scope, non-goals, criteria, sources, and stop conditions. | Host parses and enforces coding-run contract. |
| Planning | `/plan` or a bounded Work planning chat when outcome is unclear. | Save accepted plan/decision, not the entire deliberation transcript. | Orchestrator selects one unblocked task; planner agent remains deferred. |
| Source research | Web/file/plugin tools with citations; separate chats for independent source groups. | Stable source IDs, access date, evidence label, URL/commit, limitation, decision impact. | Codex inspects repository source at exact commits and local environment. |
| Mutable progress | Work progress row/status messages help the operator. | `research-state.yaml`, `PROGRESS.md`, decisions/blockers, evidence paths. | SQLite run/task state and JSONL event log are canonical for coding runs. |
| Workspace isolation | Separate chats; desktop scheduled tasks may use worktrees. | No two Work chats write the same connected source/artifact concurrently. | Worktree manager verifies path containment, Git state, and cleanup ownership. |
| Tool use | Direct narrow tools/plugins for source-linked retrieval and artifacts. | Record inputs, outputs, errors, and redaction status when material. | Host policy gates commands/network/secrets; MCP tools enforce their own authorization. |
| Validation | Work can inspect artifacts, sources, and outputs; code/data tools can perform deterministic checks. | Default-FAIL checklist and criterion-level evidence. | Tests/build/lint/types/schemas/diff/security checks decide completion. |
| Model evaluation | Fresh Work reviewer chat can assess subjective research, clarity, or completeness. | Read-only review brief: goal, criteria, actual artifact, concise evidence, `PASS|FAIL|INSUFFICIENT_EVIDENCE`. | Optional evaluator is invoked only after deterministic checks cannot decide. |
| Approval | Work asks the user and supports permission modes. | Record approved action, scope, and expiry in state. | Host centralizes external/destructive/financial/production actions and idempotency. |
| Recovery | Same chat may resume; Project preserves shared context. | Explicit checkpoint/handoff file allows fresh-chat continuation. | Reconcile persisted state, process, worktree, Git, last event, and last validation. |
| Observability | Progress, Scheduled inbox, reviewable deliverables. | Compact status report plus links/paths to large evidence. | Structured events, normalized provider errors, metrics, and audit log. |
| Scheduling | Work scheduled tasks after manual testing. | Durable prompt/skill and accessible sources per run; explicit stop/report rules. | Cloud scheduler remains deferred for coding v0; local host controls strict runs. |

---

## 3. Recommended Work Project layout

```text
ChatGPT Project: UPE / Long-Running Harness Research
├── Project Instructions
│   └── active UPE stable-core kernel only
├── Sources
│   ├── 01_UPE_v5.6.0_FULL_REFERENCE.md
│   ├── 04_GPT_5.6_RUNTIME_PROFILE.md
│   ├── 05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md
│   ├── 06_SOURCE_MAP.md
│   ├── capability-registry.yaml
│   ├── harness-build-brief.md
│   └── relevant local/source documents
├── Chats
│   ├── OpenAI core/App Server research
│   ├── OpenAI SDK/security/evals research
│   ├── Anthropic long-running/evals research
│   ├── ChatGPT Work applicability
│   └── coordinator merge/review
└── Durable outputs
    ├── source-matrix.md
    ├── pattern-comparison.md
    ├── chatgpt-work-applicability.md
    └── research-state.yaml
```

### Placement rules

1. **Project Instructions:** stable UPE invariants, authority, capability realism, approval boundaries, acceptance behavior.
2. **Project sources:** full reference, volatile runtime facts, source map, task brief, templates, domain corpus.
3. **Skill:** a focused, tested research/evaluation procedure with schemas and examples.
4. **Plugin/connector:** only when it grants necessary authoritative/private data or a reusable tool; use the narrowest scope.
5. **State file:** current objective, completed source IDs, unresolved gaps, evidence, and next action.
6. **Chat:** one distinct outcome or independent branch, not permanent canonical memory.

---

## 4. Work-native research workflow

### Stage 1 — Contract

Create a goal with:

- exact source IDs and URLs;
- required fields for every source;
- access date;
- evidence labels;
- output paths;
- no-implementation boundary;
- completion rule and blockers.

### Stage 2 — Independent read-only source groups

Use separate chats only for separable evidence groups, for example:

- OpenAI Codex core/App Server;
- OpenAI orchestration/repository controls;
- OpenAI Agents SDK/security/evals;
- Anthropic long-running/evals/scaling;
- ChatGPT Work product applicability.

Each chat emits the same schema:

```yaml
source_id:
source_title:
url:
published_or_updated:
accessed: 2026-07-18
scope:
harness_layers: []
concrete_mechanism:
evidence_type: documentation | source_code | experiment | opinion
transferability: generic | openai_specific | anthropic_specific
limitations:
decision_impact: adopt | adapt | reject | defer
work_applicability:
exact_commit_or_version:
```

### Stage 3 — Coordinator merge

The coordinator:

1. verifies all 30 IDs exist exactly once;
2. resolves conflicts by source authority, freshness, and exact implementation evidence;
3. separates documented fact from inference/recommendation;
4. records gaps as `UNKNOWN`;
5. deduplicates repeated patterns;
6. writes the matrix and comparison;
7. updates `research-state.yaml`.

Branches do not vote. Three confident summaries cannot out-authorize one current protocol document, despite the democratic appeal.

### Stage 4 — Deterministic validation

Check:

- 30 primary source rows;
- required columns present;
- URLs and exact repo commits recorded;
- all 10 comparisons covered;
- Work applicability contains native/adapted/Codex-only decisions;
- missing local files listed explicitly;
- no implementation or external mutation performed;
- package manifest/checksums generated.

### Stage 5 — Fresh-context review

A separate Work reviewer receives only:

- active brief;
- completed artifacts;
- concise evidence index;
- validation results.

It returns criterion-level `PASS`, `FAIL`, or `INSUFFICIENT_EVIDENCE` and the smallest corrective action. It has no write assignment to the source artifacts.

---

## 5. Merge protocol with Codex research

The ChatGPT/Work and Codex research streams should merge through stable records, not transcript paste.

### Stable IDs

- `OAI-01` through `OAI-21`
- `ANT-22` through `ANT-30`
- supplemental local sources use `LOCAL-*`
- Work product sources use `WORK-*`

### Required Codex-side additions

For each source or implementation claim, Codex should record:

- source ID;
- exact repository/ref/commit inspected;
- file and relevant line/range;
- observed command or test, if any;
- documented vs observed vs inferred;
- conflict with current Work findings, if any;
- architecture impact.

### Conflict rule

```text
active authority and safety constraints
> current official documentation
> source code at exact tested commit
> reproducible local observation
> official case study
> local dated reference/context
> inference or recommendation
```

A newer source does not automatically win when it describes a different version or surface. Surface and version must match.

### Merge acceptance

- every material architecture claim maps to at least one source ID;
- App Server claims map to the exact Codex commit/version used;
- product behavior claims are freshly verified;
- contradictions are resolved or preserved as explicit `UNKNOWN`;
- no Codex implementation starts before `ADR-001-harness-boundary.md` is accepted.

---

## 6. Capability opportunity scan for this project

### Required

| Capability | Purpose | Validation/fallback |
|---|---|---|
| Work mode | Long research, synthesis, and durable deliverables. | Review artifact completeness; fall back to staged Chat if unavailable. |
| ChatGPT Project | Shared instructions, source files, and related chats. | Confirm source visibility; fall back to explicit file bundle. |
| Web/official-source access | Current product and technical behavior. | Access dates, authority, citations; mark blocked pages. |
| File inspection | UPE references and local research context. | Exact file identity/content; do not infer missing files. |
| GitHub/source inspection | Exact commits and implementation evidence. | Record SHA/blob and lines; fall back to downloaded release/source. |
| Durable Markdown/YAML artifacts | Cross-surface handoff and recovery. | Schema/checklist plus checksums. |
| Codex App Server later | Repository execution without rebuilding Codex core. | Version-pinned smoke test and generated schema compatibility. |

### Optional

| Capability | Use only when | Guardrail |
|---|---|---|
| `/goal` | Research/deliverable has a measurable finish and may take many steps. | Explicit constraints, verification, pause conditions, and budget. |
| Separate Work chats | Source groups are genuinely independent/read-only. | No shared writes; coordinator owns merge. |
| Independent model reviewer | Subjective or semantic criteria remain after deterministic checks. | Read-only, fresh context, criterion-level structured verdict. |
| Scheduled tasks | Prompt/skill has passed manual runs and input sources remain available. | Narrow access, first-run review, stop/report rule, no Full access. |
| Workspace Agents trigger API | Fire-and-forget events are useful despite absent response retrieval. | Idempotency key; do not claim run reconciliation. |
| Docker | Dependencies or commands require material isolation. | Narrow mounts/network, disposable environment, host-owned state. |

### Avoid or disable in v0

- multi-agent coding execution;
- shared write access from parallel chats or agents;
- conversation/thread as the only state;
- unlimited iterations or silent retries;
- Full access or broad inherited credentials;
- autonomous push, merge, PR, release, deployment, purchase, or external message;
- self-modifying prompts/skills;
- blind Symphony or quickstart cloning;
- Workspace Agents API as a strict execution backend before run/result retrieval exists;
- speculative abstractions whose only test is that the class name sounds expandable.

---

## 7. Known limitations and `UNKNOWN`s

1. **Work rollout and surface availability are volatile.** Official help currently describes gradual rollout and differences among web/mobile/desktop. Verify at use time.
2. **Cloud and desktop Work histories are not currently one universal state surface.** Cloud Work conversations and desktop-local Work threads/files have documented separation at launch.
3. **Native Goal/Scheduled internals are product-managed.** They are useful, but this research does not claim inspectable typed lifecycle/state equivalent to the proposed host harness.
4. **Workspace Agents result retrieval is unavailable through the current trigger API.** This blocks strict external reconciliation.
5. **Feature maturity:** the documentation defines Experimental/Beta/Stable labels, but this research did not find a maturity label attached to every individual Work capability. Treat unspecified maturity as `UNKNOWN`, not “stable because the button looks polished.”
6. **No direct Codex smoke run was performed in this ChatGPT research surface.** Repository commits and docs were inspected; environment behavior must be verified by Codex in the target WSL2 repository.
7. **Several named local files were not located.** They remain explicit input gaps in `source-matrix.md` and `research-state.yaml`.

---

## 8. Recommendation for the next increment

1. Put this package into the harness repository under `docs/research/`.
2. Let Codex add direct environment/repository observations without rewriting these evidence labels.
3. Resolve any source/version conflicts.
4. Write `docs/architecture/ADR-001-harness-boundary.md`.
5. Validate the ADR against the active brief and threat boundary.
6. Only then implement the state model and fake adapter.
