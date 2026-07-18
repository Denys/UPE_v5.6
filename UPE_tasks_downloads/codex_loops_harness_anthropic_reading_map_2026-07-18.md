# Codex Loops and Harness Engineering
## Curated implementation links and Anthropic cross-application map

**Reviewed:** 18 July 2026  
**Input analysed:** `claude_codex_hermes_loops_chat_copy.md`  
**Purpose:** Give Codex a compact, authoritative reading set for implementing reliable long-running, repair, eval, scheduled, and multi-agent loops.

---

## 1. Executive assessment of the original chat

The chat reached the right core conclusion:

```text
A useful loop is not “the agent keeps thinking.”
A useful loop is:
objective + bounded scope + executable verification + persistent state
+ iteration/cost cap + audit trail + rollback + human gate for risky actions.
```

Its strongest Codex formulation is also worth retaining:

```text
AGENTS.md       = durable repository policy and map
skill           = reusable workflow method
/goal           = bounded long-running objective
verifier/evals  = objective feedback and stopping condition
hook            = deterministic lifecycle gate
automation      = recurring trigger
worktree        = isolation for parallel/background work
progress log    = durable handoff state
```

### What needed updating

1. **OpenAI now has direct harness literature.** The original chat said OpenAI lacked one central article comparable to Anthropic’s loop material. That was true enough earlier, but the 2026 OpenAI set now includes `Unrolling the Codex agent loop`, `Harness engineering`, and `Unlocking the Codex harness`.
2. **The list was too broad for implementation.** It contained 36 unique URLs and mixed product tutorials, API loop mechanics, recurring-task features, research architecture, and Hermes material. Useful as a library, less useful as a build order.
3. **Scheduled-task caveat needs refinement.** Codex tasks that require local project files need the machine on and the desktop app running. Web scheduled tasks can use uploaded files, connected tools, skills, and plugins, but do not preserve a local folder or worktree between runs.
4. **Anthropic’s most useful contribution is harness design, not Claude command syntax.** `/goal`, `/loop`, routines, and Claude-specific product controls are useful comparisons, but the durable lessons for Codex are externalized state, strong verifiers, context-efficient logs, generator/evaluator separation, and parallelism only over independent work.
5. **Newer Anthropic sources deserve promotion.** `Effective context engineering`, `Building a C compiler with a team of parallel Claudes`, and `Scaling Managed Agents` sharpen several lessons only implicit in the original chat.

---

# 2. Minimum reading set

Read these first. Everything else is optional elaboration.

## OpenAI / Codex: six essential sources

### 1. Unrolling the Codex agent loop
https://openai.com/index/unrolling-the-codex-agent-loop/

**Why it matters:** The clearest low-level account of a Codex turn: prompt assembly, model inference, tool calls, observations, final assistant message, context growth, permissions, and compaction. Read this before inventing a wrapper around behaviour Codex already provides.

**Implementation takeaway:** Distinguish a *turn* from the many model/tool iterations inside it. The primary output can be changed files and observed state, not merely the final message.

### 2. Follow a goal
https://developers.openai.com/codex/use-cases/follow-goals

**Why it matters:** Official long-running goal-loop pattern for migrations, refactors, retry loops, experiments, and other tasks with a verifiable finish.

**Implementation takeaway:** `/goal` needs an objective, end condition, allowed scope, validation commands, checkpoint format, pause conditions, and failure budget.

### 3. Iterate on difficult problems
https://developers.openai.com/codex/use-cases/iterate-on-difficult-problems

**Why it matters:** The cleanest practical Codex eval loop: baseline, one focused change, rerun eval, inspect artifacts, record score delta, repeat until threshold or budget.

**Implementation takeaway:** Keep a checked-in loop log with current best score, last change, regression/improvement, and next experiment.

### 4. Harness engineering: leveraging Codex in an agent-first world
https://openai.com/index/harness-engineering/

**Why it matters:** The repo-level operating system around Codex. It covers agent legibility, repository knowledge as the system of record, architecture enforcement, increasing autonomy, and continuous entropy cleanup.

**Implementation takeaway:** Keep `AGENTS.md` short and use it as a map into structured `docs/`, scripts, tests, schemas, and enforcement. Do not make it a 1,000-page sacred scroll.

### 5. Build iterative repair loops with Codex
https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex

**Why it matters:** Runnable implementation rather than philosophy. It demonstrates review → repair → execute/validate → structured remaining delta → next iteration, with iteration caps and per-pass audit artifacts.

**Implementation takeaway:** Every pass should preserve review findings, changed artifact, validation result, judgment, and remaining delta.

### 6. Codex best practices
https://developers.openai.com/codex/learn/best-practices

**Why it matters:** Practical placement rules: durable repo guidance in `AGENTS.md`, repeated procedures in skills, bounded delegation to subagents, and one coherent chat per coherent problem.

**Implementation takeaway:** Fork only when work genuinely branches. Parallelism is a topology decision, not a personality trait.

---

## Anthropic: six essential papers for Codex users

### 1. Effective harnesses for long-running agents
https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents

**Why it matters:** The most immediately transferable paper. It uses an initializer/coding-agent split, feature list, progress file, `init.sh`, git commits, startup checks, and one-feature-at-a-time progress across context windows.

**Translate to Codex:** Create a bootstrap phase, `progress.md` or `state.json`, machine-readable backlog, reliable restart/test command, and explicit session-close protocol.

### 2. Building Effective AI Agents
https://www.anthropic.com/engineering/building-effective-agents

**Why it matters:** Foundational architecture taxonomy: prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer, and autonomous agents. It also argues for the simplest architecture that works.

**Translate to Codex:** Select direct execution, serial stages, subagents, or an eval loop by task shape. Do not deploy sixteen agents where `pytest` and one competent loop would suffice.

### 3. Demystifying evals for AI agents
https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents

**Why it matters:** Separates transcript, final answer, and actual environmental outcome. Defines the evaluation harness as the system that runs tasks, records trajectories, grades results, and aggregates evidence.

**Translate to Codex:** Grade the repo, database, application, test results, or produced artifact. Never accept “tests pass” because an agent typed those syllables.

### 4. Effective context engineering for AI agents
https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents

**Why it matters:** Explains why long loops fail when context becomes an indiscriminate landfill. Context is finite and should contain the information most likely to drive the next correct action.

**Translate to Codex:** Keep canonical state in files, summarize large tool output, expose only relevant tools/docs, and make logs grep-friendly and task-oriented.

### 5. Harness design for long-running application development
https://www.anthropic.com/engineering/harness-design-long-running-apps

**Why it matters:** Generator/evaluator architecture, calibrated grading criteria, browser-based QA, sprint contracts, hard thresholds, feedback loops, plateau behaviour, and the warning that evaluator overhead is justified only near the generator’s capability boundary.

**Translate to Codex:** Use a separate verifier/subagent for difficult or subjective work; agree on a testable sprint contract before implementation; retain the best artifact, not blindly the last iteration.

### 6. Building a C compiler with a team of parallel Claudes
https://www.anthropic.com/engineering/building-c-compiler

**Why it matters:** A candid, highly practical account of sustained autonomous coding. The main lessons are verifier quality, compact error output, fast deterministic test subsets, fresh-container orientation, progress files, and when parallel agents stop helping.

**Translate to Codex:** Parallelize independent failing tests or modules. Do not parallelize a single serial bottleneck where every agent discovers the same next bug and tramples the same files.

---

# 3. Full Codex implementation stack

## Core loop and persistence

| Source | Use |
|---|---|
| Unrolling the Codex agent loop | Understand turn/tool mechanics, context growth, compaction, permissions |
| Running agents, Agents SDK | Build application-level turns and choose session, conversation ID, or previous-response continuation |
| Unlocking the Codex harness: App Server | Embed the complete Codex harness with thread lifecycle, persistence, streamed events, approvals, diffs, and reconnectable clients |
| Codex as MCP server | Invoke persistent Codex conversations from an Agents SDK or other MCP orchestrator |

Links:

- https://openai.com/index/unrolling-the-codex-agent-loop/
- https://developers.openai.com/api/docs/guides/agents/running-agents
- https://openai.com/index/unlocking-the-codex-harness/
- https://developers.openai.com/codex/mcp-server

## Goal, repair, and eval loops

| Source | Use |
|---|---|
| Follow a goal | Long bounded tasks with a verifiable stopping condition |
| Iterate on difficult problems | Scored optimization with running log and artifact inspection |
| Iterative repair loops cookbook | Code-level review/repair/validate implementation and audit trail |
| Agent improvement loop | Convert traces and human/model feedback into durable evals and proposed harness changes |

Links:

- https://developers.openai.com/codex/use-cases/follow-goals
- https://developers.openai.com/codex/use-cases/iterate-on-difficult-problems
- https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex
- https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop

## Repository harness and deterministic controls

| Source | Use |
|---|---|
| Harness engineering | Repo legibility, docs as system of record, architecture enforcement, cleanup loops |
| AGENTS.md | Durable repo map, commands, conventions, constraints, done definition |
| Skills | Reusable loop methods with references/scripts |
| Hooks | Deterministic lifecycle enforcement and validation |
| Worktrees | Isolate parallel/background changes |

Links:

- https://openai.com/index/harness-engineering/
- https://developers.openai.com/codex/agent-configuration/agents-md
- https://developers.openai.com/codex/build-skills
- https://developers.openai.com/codex/hooks
- https://developers.openai.com/codex/environments/git-worktrees

## Scheduling and parallelism

| Source | Use |
|---|---|
| Scheduled tasks | Recurring or monitored work; local-project and web behaviour differ |
| Subagents | Bounded independent exploration, implementation, tests, or verification |
| Symphony | Issue-tracker-driven always-on Codex orchestration at organizational scale |

Links:

- https://learn.chatgpt.com/docs/automations
- https://developers.openai.com/codex/subagents
- https://openai.com/index/open-source-codex-orchestration-symphony/

---

# 4. Additional Anthropic papers and docs worth retaining

## Multi-agent delegation

### How we built our multi-agent research system
https://www.anthropic.com/engineering/multi-agent-research-system

Use it to design branch briefs. Each worker needs a distinct objective, output format, tools/sources, and task boundary. Otherwise agents duplicate work and leave gaps.

### A harness for every task / Dynamic workflows
https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code
https://code.claude.com/docs/en/workflows

Use these to understand **script-owned orchestration**. The workflow code owns the loop, branching, and intermediate variables; model context receives only distilled outputs. For Codex, the analogue is a Python/TypeScript orchestrator, App Server client, Agents SDK workflow, CI job, or issue-driven system such as Symphony.

## Tool and context efficiency

### Code execution with MCP
https://www.anthropic.com/engineering/code-execution-with-mcp

Use it when a loop has many tools or large intermediate results. Load tools on demand, filter/aggregate in code, and return only what the model needs.

### Writing effective tools for agents
https://www.anthropic.com/engineering/writing-tools-for-agents

Use it to improve tool descriptions, errors, outputs, and affordances. A loop cannot repair what its tools report ambiguously.

## Harness evolution and safety

### Scaling Managed Agents: Decoupling the brain from the hands
https://www.anthropic.com/engineering/managed-agents

Use it as a warning against freezing model-specific limitations into the permanent harness. Keep model intelligence, environment execution, policy, and task-specific harness layers separable.

### How we built Claude Code auto mode
https://www.anthropic.com/engineering/claude-code-auto-mode

Use it for permission design. Autonomy should be granted by action class and environment boundary, not by tiring the human into approving everything.

### Building agents with the Claude Agent SDK
https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk

Useful implementation mental model: gather context → act → verify → repeat. Secondary to the six essential papers, but practical when translating Claude SDK examples to Agents SDK or a Codex App Server client.

---

# 5. Direct translation of Anthropic lessons into a Codex repository

```text
repo/
├── AGENTS.md                  # Short map, invariants, commands, done criteria
├── docs/
│   ├── architecture.md        # Source of truth
│   ├── product-spec.md
│   └── decisions/             # ADRs / durable decisions
├── agent/
│   ├── state.json             # Current objective, completed/pending, blockers
│   ├── progress.md            # Human-readable handoff and iteration log
│   ├── backlog.json           # Machine-readable tasks/features + status
│   └── best-result.json       # Best score/artifact, not merely latest
├── scripts/
│   ├── bootstrap.sh           # Reproducible setup/startup
│   ├── verify-fast.sh         # Cheap deterministic checks every iteration
│   ├── verify-full.sh         # Full acceptance/regression gate
│   └── summarize-failure.py   # Compact, structured feedback
├── evals/
│   ├── cases/
│   ├── graders/
│   └── results/
├── .agents/skills/
│   └── project-loop/SKILL.md  # Repeatable loop method
└── hooks / CI                 # Deterministic enforcement
```

## Session-start contract

1. Read `AGENTS.md`, `agent/state.json`, `agent/progress.md`, and recent git history.
2. Run `scripts/bootstrap.sh` or check environment health.
3. Run the fast verifier to detect inherited breakage.
4. Select one bounded backlog item or one independent workstream.
5. State the exact acceptance condition before editing.

## Iteration contract

1. Make one coherent change.
2. Run targeted/fast verification.
3. If it fails, convert the result into structured next-pass feedback.
4. If it passes, run relevant regression checks.
5. Update state, score, artifact path, and remaining delta.
6. Commit or create a reversible checkpoint.
7. Stop on success, repeated no-progress, budget exhaustion, unsafe action, or missing human decision.

## Session-close contract

1. Leave the repo runnable or revert to the last working checkpoint.
2. Record exact commands and observed results.
3. Update backlog status only after verification.
4. Write the next recommended action and unresolved blocker.
5. Preserve the best known artifact/score separately from the latest attempt.

---

# 6. Recommended `/goal` template for Codex

```text
/goal Complete [objective] until [verifiable environmental end state].

Read first:
- AGENTS.md
- [specification / architecture sources]
- agent/state.json
- agent/progress.md
- recent git history

Scope:
- May change: [paths/components]
- Must not change: [excluded paths/interfaces/data]
- External actions: [none / exact approved scope]

Loop:
1. Reproduce or baseline the current state.
2. Choose one bounded improvement or failing criterion.
3. Make one coherent change.
4. Run [fast verifier].
5. Run [targeted/full verifier] when appropriate.
6. Record score, changed files, observed result, remaining delta, and next step.
7. Preserve the best passing artifact and a reversible checkpoint.

Stop successfully when:
- [all required checks pass]
- [artifact/environment condition is observed]

Pause and report when:
- the same failure persists for [N] materially different attempts;
- progress does not improve for [N] iterations;
- the time/token/cost budget is reached;
- a destructive, production, financial, credential, or external-write decision is required;
- required evidence or access is unavailable.

Do not claim completion from the final message alone. Verify the repository, tests,
application, database, or produced artifact and report the observed evidence.
```

---

# 7. Decision table: which loop to use

| Task shape | Codex mechanism | Harness pattern |
|---|---|---|
| One coherent change, easy verification | Normal Codex turn | Direct edit → test → report |
| Long serial migration/refactor | `/goal` | Backlog + progress log + checkpoints + full gate |
| Repeated repair of many artifacts | `codex exec` / script / cookbook pattern | Review → repair → validate → structured delta |
| Subjective or frontier output | Eval-driven loop | Generator + calibrated evaluator + best-artifact retention |
| Many independent files/issues | Subagents + worktrees | One bounded worker per item + coordinator/verifier |
| One serial bottleneck | Single strong agent | Do not parallelize; improve verifier/context instead |
| Recurring local repo maintenance | Scheduled task + worktree + skill | Isolated run + audit report/PR |
| Recurring cloud/data workflow | Web scheduled task / workspace agent | Connected tools + explicit persistent sources |
| Embedded Codex product | App Server | Persistent threads, events, approvals, diffs, reconnect |
| Custom multi-agent application | Agents SDK + Codex MCP/App Server | Code-owned state, branching, gates, observability |

---

# 8. Links from the original chat that can be deprioritized

These are not wrong; they are simply lower priority for implementing Codex loops:

- Claude `/goal`, `/loop`, scheduled-task, and routines docs: useful for product comparison, but not the durable Codex architecture.
- Low-level Claude tool-runner tutorials: useful when implementing directly on the Claude API, less relevant once Codex/App Server or OpenAI Agents SDK owns the loop.
- Hermes self-evolution links: useful as a third-party experiment, but should remain separate from the OpenAI/Anthropic implementation authority set.
- General marketing or taxonomy articles after the core harness papers have been read: they add vocabulary more than enforcement.

Keep the original chat as a broad comparative library; use this document as the implementation reading order.
