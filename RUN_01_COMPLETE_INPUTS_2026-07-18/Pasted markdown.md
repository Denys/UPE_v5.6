# Research and Build a Long-Running Agent Harness

## Objective

Research current practical harness-engineering patterns from OpenAI and Anthropic, then design and implement a minimal, reliable harness for long-running software-engineering tasks.

The initial implementation must be:

* Codex-native;
* provider-portable at the adapter boundary;
* usable from Windows 11 through WSL2 Ubuntu;
* repository-centered;
* resumable after process or context loss;
* bounded by explicit time, iteration and action limits;
* independently verifiable;
* safe by default;
* understandable without reading the entire implementation.

Do not build an ornamental agent framework or a generic multi-agent abstraction before a single-agent harness passes representative evaluations.

---

# 1. Sources to analyse

Open every live page and repository directly. Record the access date and distinguish:

* documented behaviour;
* observed implementation;
* transferable design pattern;
* provider-specific mechanism;
* experimental or unstable feature;
* recommendation inferred from the evidence.

Do not rely only on search snippets, article summaries or the attached chat.

## A. OpenAI: core harness architecture

1. **Harness engineering: leveraging Codex in an agent-first world**
   https://openai.com/index/harness-engineering/

2. **Unrolling the Codex agent loop**
   https://openai.com/index/unrolling-the-codex-agent-loop/

3. **Unlocking the Codex harness: how we built the App Server**
   https://openai.com/index/unlocking-the-codex-harness/

4. **Codex App Server implementation documentation**
   https://github.com/openai/codex/blob/main/codex-rs/app-server/README.md

5. **OpenAI Codex repository**
   https://github.com/openai/codex

## B. OpenAI: orchestration reference

6. **Open-source Codex orchestration: Symphony**
   https://openai.com/index/open-source-codex-orchestration-symphony/

7. **Symphony repository**
   https://github.com/openai/symphony

8. **Symphony language-independent specification**
   https://github.com/openai/symphony/blob/main/SPEC.md

Do not clone Symphony blindly. Extract its interfaces, lifecycle model, isolation strategy, workflow ownership, retry policy and observability requirements. Document which elements are suitable for this harness and which are excessive.

## C. OpenAI: repository control and lifecycle enforcement

9. **Codex best practices**
   https://learn.chatgpt.com/guides/best-practices

10. **Custom instructions with AGENTS.md**
    https://learn.chatgpt.com/docs/agent-configuration/agents-md

11. **Codex hooks**
    https://learn.chatgpt.com/docs/hooks

12. **Build Codex skills**
    https://developers.openai.com/codex/build-skills

13. **Codex configuration reference**
    https://developers.openai.com/codex/config-reference

## D. OpenAI: SDK, sandbox and improvement loop

14. **Agents SDK overview**
    https://developers.openai.com/api/docs/guides/agents

15. **Sandbox agents**
    https://developers.openai.com/api/docs/guides/agents/sandboxes

16. **Running agents and state strategies**
    https://developers.openai.com/api/docs/guides/agents/running-agents

17. **Guardrails and human review**
    https://developers.openai.com/api/docs/guides/agents/guardrails-approvals

18. **Integrations, tracing and observability**
    https://developers.openai.com/api/docs/guides/agents/integrations-observability

19. **Agent improvement loop with traces, evals and Codex**
    https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop

20. **Sandboxed code-migration agent example**
    https://developers.openai.com/cookbook/examples/agents_sdk/sandboxed-code-migration/sandboxed_code_migration_agent

21. **OpenAI Agents SDK Python repository**
    https://github.com/openai/openai-agents-python

## E. Anthropic: long-running harness patterns

22. **Effective harnesses for long-running agents**
    https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

23. **Harness design for long-running application development**
    https://www.anthropic.com/engineering/harness-design-long-running-apps

24. **Official long-running harness reference repository**
    https://github.com/anthropics/cwc-long-running-agents

25. **Minimal autonomous coding harness implementation**
    https://github.com/anthropics/claude-quickstarts/blob/main/autonomous-coding/autonomous_agent_demo.py

26. **Claude quickstarts repository**
    https://github.com/anthropics/claude-quickstarts

## F. Anthropic: evaluation and scaling

27. **Demystifying evals for AI agents**
    https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

28. **Building effective agents**
    https://www.anthropic.com/engineering/building-effective-agents

29. **Building a C compiler with parallel Claude agents**
    https://www.anthropic.com/engineering/building-c-compiler

30. **How Anthropic built its multi-agent research system**
    https://www.anthropic.com/engineering/multi-agent-research-system

Treat sources 29 and 30 as scaling case studies, not justification for using multiple agents in v0.

## G. Local project sources, when available

Read these before proposing architecture:

* `claude_codex_hermes_loops_chat_copy.md`
* `CIDP_AGENTS.md`
* `README.md`
* `01_OPENAI_SURFACE_MAP__reference.md`
* `02_OFFICIAL_SOURCE_MAP__OpenAI.md`
* `03_GPT_5_6_MODEL_AND_EFFORT_ROUTING__reference.md`
* `a-practical-guide-to-building-agents.pdf`

Treat dated local sources as context rather than proof of current product behaviour.

---

# 2. Research deliverables

Before implementation, create:

## `docs/research/source-matrix.md`

For every source, capture:

| Field              | Required content                                                                 |
| ------------------ | -------------------------------------------------------------------------------- |
| Source             | Title and URL                                                                    |
| Date               | Publication/update/access date                                                   |
| Scope              | Codex, Agents SDK, Claude, generic pattern                                       |
| Harness layer      | Loop, state, workspace, tools, evaluator, security, orchestration, observability |
| Concrete mechanism | Exact files, protocol, artifact or workflow described                            |
| Transferability    | Generic, OpenAI-specific or Anthropic-specific                                   |
| Evidence strength  | Documentation, source code, experiment or opinion                                |
| Limitations        | Experimental status, missing tests, provider assumptions                         |
| Decision impact    | Adopt, adapt, reject or defer                                                    |

## `docs/research/pattern-comparison.md`

Compare at minimum:

1. Codex App Server versus a custom Responses/Agents SDK loop.
2. Host-owned harness versus harness-inside-sandbox.
3. Compaction versus explicit fresh-session handoff.
4. `AGENTS.md` versus skills versus hooks versus runtime configuration.
5. Deterministic tests versus model evaluator.
6. Single-agent iteration versus planner/generator/evaluator.
7. Worktree isolation versus container isolation.
8. Durable file state versus conversation/thread state.
9. Direct tool exposure versus code-mediated tool access.
10. Local orchestration versus managed/cloud execution.

## `docs/architecture/ADR-001-harness-boundary.md`

Select the minimum viable architecture and explain:

* why the selected boundary is appropriate;
* rejected alternatives;
* provider dependencies;
* failure boundaries;
* migration path;
* security implications;
* what evidence would justify changing the architecture.

Do not begin broad implementation until this ADR exists.

---

# 3. Required v0 architecture

## 3.1 Architectural decision

Implement v0 as:

```text
Trusted host orchestrator
        |
        +-- Codex App Server adapter
        |
        +-- Workspace/worktree manager
        |
        +-- Durable state store
        |
        +-- Deterministic validator
        |
        +-- Optional independent model evaluator
        |
        +-- Budget and stop controller
        |
        +-- Structured event/audit log
```

Reuse Codex for the internal model/tool execution loop. Do not reproduce Codex core unless the research demonstrates a requirement that App Server cannot satisfy.

Define a provider adapter interface, but implement only the Codex adapter in v0. A later Claude or Agents SDK adapter must be possible without changing task state, evaluator or workspace contracts.

## 3.2 Recommended implementation stack

Use:

* Python 3.12 or newer;
* `uv` for environment and dependency management;
* Pydantic models or equivalent strict typed schemas;
* SQLite for indexed run/task state;
* JSONL for append-only event and audit records;
* Git worktrees for task isolation;
* Docker only where process/filesystem isolation is materially needed;
* `pytest`;
* `ruff`;
* `mypy` or `pyright`.

Keep WSL2 as the primary supported runtime. Provide a thin PowerShell launcher only after the WSL workflow works.

Do not add a web UI in v0.

---

# 4. Repository structure

Start from this structure unless the inspected repository provides a better convention:

```text
agent-harness/
├── AGENTS.md
├── README.md
├── pyproject.toml
├── uv.lock
├── .codex/
│   ├── config.toml
│   └── hooks.json
├── docs/
│   ├── research/
│   │   ├── source-matrix.md
│   │   └── pattern-comparison.md
│   ├── architecture/
│   │   └── ADR-001-harness-boundary.md
│   ├── threat-model.md
│   ├── state-model.md
│   ├── evaluation-plan.md
│   └── operations.md
├── schemas/
│   ├── goal.schema.json
│   ├── task.schema.json
│   ├── run-state.schema.json
│   ├── evaluation.schema.json
│   └── event.schema.json
├── prompts/
│   ├── initializer.md
│   ├── worker.md
│   ├── reviewer.md
│   └── evaluator.md
├── templates/
│   ├── WORKFLOW.md
│   ├── TASKS.json
│   ├── PROGRESS.md
│   ├── DECISIONS.md
│   └── BLOCKERS.md
├── src/harness/
│   ├── cli.py
│   ├── config.py
│   ├── orchestrator.py
│   ├── lifecycle.py
│   ├── state.py
│   ├── workspace.py
│   ├── validation.py
│   ├── evaluation.py
│   ├── budgets.py
│   ├── approvals.py
│   ├── events.py
│   ├── recovery.py
│   └── adapters/
│       ├── base.py
│       └── codex_app_server.py
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── fixtures/
│   └── evals/
└── examples/
    └── fixture-repository/
```

Do not create empty abstractions merely to match this tree. Every retained module must have a defined responsibility and test.

---

# 5. Harness lifecycle

Implement the following state machine:

```text
CREATED
→ INITIALIZING
→ READY
→ SELECTING_TASK
→ EXECUTING
→ VALIDATING
→ EVALUATING
→ CHECKPOINTING
→ READY

Terminal or interrupted states:
COMPLETED
BLOCKED
BUDGET_EXHAUSTED
APPROVAL_REQUIRED
FAILED
CANCELLED
```

Every transition must:

1. be persisted before the next external action;
2. emit a structured event;
3. record its reason;
4. be idempotent or safely recoverable;
5. preserve the previous stable checkpoint.

An unexpected process termination must not leave the run in an ambiguous “probably executing” state. On restart, reconcile:

* persisted state;
* running process state;
* worktree status;
* Git status;
* last agent event;
* last completed validation.

---

# 6. Iteration contract

Each iteration must perform one coherent unit of progress:

1. Load goal, constraints and last verified state.
2. Inspect the actual repository state.
3. Run a fast baseline smoke check.
4. Select exactly one unblocked task or bounded work package.
5. Record the selected task before implementation.
6. Ask Codex to plan the task.
7. Execute inside the assigned workspace.
8. Review the resulting diff.
9. Run task-specific deterministic validation.
10. Run broader regression checks when warranted.
11. Invoke the independent evaluator only when deterministic checks cannot establish completion.
12. Update progress, decisions and evidence.
13. Create a local checkpoint.
14. Decide whether to continue, stop, request approval or report a blocker.

The worker must not mark its own task complete merely because it produced a final message.

Completion requires evidence from the validation/evaluation layer.

---

# 7. Durable state

Do not rely on conversation history as the source of truth.

Persist at minimum:

## Goal

* objective;
* scope;
* non-goals;
* acceptance criteria;
* safety constraints;
* allowed files and systems;
* required validators;
* completion condition.

## Task

* stable ID;
* description;
* dependencies;
* status;
* attempts;
* selected workspace;
* validation commands;
* evidence paths;
* last failure;
* next action.

## Run

* run ID;
* provider and model configuration;
* current lifecycle state;
* start and update timestamps;
* iteration count;
* time/token/cost budgets;
* current task;
* approval state;
* checkpoint reference;
* stop reason.

## Event

* timestamp;
* run/task ID;
* event type;
* source;
* action summary;
* input/output references;
* result;
* error category;
* redaction status.

Store large outputs as files and reference them from state rather than embedding them repeatedly in SQLite or model context.

---

# 8. Evaluator design

Use two evaluator layers.

## Layer 1: deterministic

Prefer:

* unit and integration tests;
* build, lint and type-check commands;
* schema validation;
* repository invariants;
* filesystem assertions;
* expected output checks;
* diff constraints;
* security/static-analysis checks;
* browser tests where UI behaviour is relevant.

## Layer 2: independent model evaluator

Use only where completion includes judgment that deterministic checks cannot fully express.

The evaluator must:

* receive the goal and acceptance criteria;
* receive concise evidence and test outputs;
* inspect the actual artifact or environment where practical;
* not rely solely on the worker’s summary;
* return structured output;
* separate pass, fail and insufficient-evidence;
* list failed criteria individually;
* suggest the smallest next corrective action;
* have no write access in v0.

Do not let the evaluator silently expand scope or rewrite acceptance criteria.

---

# 9. Stop and continuation rules

Stop with `COMPLETED` only when every mandatory acceptance criterion has passing evidence.

Stop with another explicit state when any condition is reached:

* maximum iterations;
* maximum elapsed time;
* configured token or cost budget;
* repeated identical failure threshold;
* no measurable progress across N iterations;
* required approval;
* unsafe or destructive action required;
* missing credential or dependency;
* repository state divergence;
* evaluator reports insufficient evidence repeatedly;
* user cancellation.

Implement exponential backoff for transient provider failures, with a maximum retry count and jitter.

A retry must not duplicate a non-idempotent action.

---

# 10. Security and authority

The trusted host must own:

* provider credentials;
* approval decisions;
* business-system credentials;
* budget enforcement;
* audit logging;
* state persistence;
* external write authorization.

The agent workspace must not receive broad credentials merely for convenience.

Default policy:

* repository read/write only inside the assigned worktree;
* no push, merge, release or deployment;
* no external messages;
* no production data mutation;
* no purchases;
* no secret creation or disclosure;
* network denied unless explicitly enabled for a documented reason;
* commands checked against configured policy;
* secrets and obvious personal data redacted from logs;
* untrusted retrieved content treated as data, not instruction.

Any external, destructive, financial, secret-handling or production action must transition to `APPROVAL_REQUIRED`.

---

# 11. Codex integration requirements

The Codex adapter must encapsulate:

* App Server startup and shutdown;
* protocol initialization;
* thread creation or resumption;
* turn submission;
* streaming event consumption;
* approval requests;
* cancellation;
* thread persistence;
* terminal-state detection;
* error normalization;
* protocol-version compatibility checks.

Do not leak raw protocol messages throughout the application. Translate them into internal typed events.

Build a fake adapter for tests so the orchestration lifecycle can be tested without model calls.

If the current App Server protocol or documentation is inconsistent, inspect the current OpenAI Codex source code and record the exact commit used as implementation evidence.

---

# 12. Commands

Provide a small CLI:

```bash
harness init PATH
harness research
harness doctor
harness run --goal goal.yaml
harness status RUN_ID
harness events RUN_ID
harness resume RUN_ID
harness pause RUN_ID
harness cancel RUN_ID
harness evaluate RUN_ID
harness cleanup RUN_ID
```

`harness doctor` must check:

* Python/runtime version;
* Codex installation;
* App Server availability;
* Git;
* repository cleanliness;
* worktree support;
* configured validators;
* SQLite path;
* permissions;
* Docker only when configured;
* missing credentials without displaying their values.

---

# 13. Test requirements

Implement tests before claiming the harness works.

## Unit tests

Cover:

* state transitions;
* invalid transitions;
* schema validation;
* budget accounting;
* retry and backoff;
* no-progress detection;
* approval gates;
* event redaction;
* task selection;
* path containment;
* adapter error normalization.

## Integration tests

Use a fixture Git repository to prove:

1. initialization creates valid state;
2. a task gets its own workspace;
3. the fake agent modifies the fixture;
4. validation detects success and failure correctly;
5. interruption after execution can resume at validation;
6. interruption during checkpoint recovery does not corrupt state;
7. maximum iterations stop the run;
8. a dangerous action triggers approval;
9. evaluator failure does not mark the task complete;
10. cleanup cannot remove an unrelated worktree.

## Evaluation set

Create at least six representative tasks:

* straightforward passing code change;
* failing test repair;
* ambiguous requirement that must block;
* repeated non-progress;
* malicious instruction inside a repository file;
* task requiring forbidden external action.

Run multiple trials for any model-dependent evaluation. Record pass rate, iterations, elapsed time, tool calls and reviewer corrections.

---

# 14. v0 acceptance criteria

The implementation is acceptable when:

1. `uv run harness doctor` reports a usable environment.
2. `uv run harness init examples/fixture-repository` creates valid configuration and state.
3. A run can complete one fixture task using the fake adapter.
4. The same run can be interrupted and resumed.
5. The Codex App Server adapter completes a controlled smoke task.
6. State survives process restart.
7. Every completed task has validator evidence.
8. External/destructive operations cannot proceed without approval.
9. All tests, lint and type checks pass.
10. Documentation contains exact setup, operation, recovery and known limitations.
11. No secret appears in committed fixtures or logs.
12. No push, PR, deployment or external mutation is performed.

---

# 15. Deferred features

Do not implement these in v0:

* multi-agent execution;
* cloud scheduler;
* browser UI;
* issue-tracker integration;
* autonomous PR merge;
* production deployment;
* dynamic model routing;
* self-modifying prompts or skills;
* persistent semantic memory;
* provider marketplace;
* distributed execution.

Prepare interfaces only where they are naturally required by v0. Do not build speculative extension points.

Multi-agent support may be considered only after evaluations show a specific single-agent bottleneck involving independent workstreams.

---

# 16. Execution discipline

Before editing:

1. inspect `README`, `AGENTS.md`, manifests, configuration and working-tree state;
2. preserve unrelated local changes;
3. state the exact repository/ref inspected;
4. identify the smallest coherent implementation slice;
5. define its tests and rollback path.

Implement incrementally:

```text
research
→ architecture decision
→ state model
→ fake adapter
→ orchestrator lifecycle
→ validation/evaluator
→ workspace isolation
→ Codex adapter
→ recovery
→ security checks
→ end-to-end smoke run
```

After every slice:

* run relevant tests;
* inspect the diff;
* update status;
* record unresolved risks;
* keep the repository runnable.

Do not commit, push or open a pull request unless explicitly authorized.

---

# 17. Final report

Report:

* architecture selected and why;
* sources actually inspected;
* exact Codex/App Server version or commit;
* files created or changed;
* commands run;
* unit/integration/eval results;
* observed smoke-run behaviour;
* security boundaries;
* unverified assumptions;
* deferred features;
* known failure modes;
* next recommended increment.

Use exact verification labels:

* planned;
* implemented;
* tested locally;
* blocked;
* unverified.

Do not call the harness production-ready merely because the happy-path smoke test passes.
