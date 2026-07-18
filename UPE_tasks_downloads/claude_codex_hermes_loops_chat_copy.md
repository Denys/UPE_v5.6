# Chat Conversation Copy — Claude Loops, OpenAI/Codex Loops, Hermes Loops

**Created:** 2026-07-09  
**Topic:** Mapping Claude “loops” concepts to OpenAI Codex, Agents SDK, Automations, and Hermes-agent loops.  
**Purpose:** Agent-readable Markdown copy for later use in Codex / Hermes / coworking workflows.

---

## 1. User

> @OpenAI Platform  
> Does OpenAI has an article on similar theme?
>
> https://claude.com/blog/getting-started-with-loops
>
> Any Hermes loops?

---

## 2. Assistant

### Reality check

Yes. OpenAI does not seem to have one single “Getting started with loops” article with the same Claude taxonomy, but the same concept is covered across **Codex**, **Agents SDK**, and **Cookbook** docs.

The Claude article defines loops as agents repeating work cycles until a stop condition is met, grouped into **turn-based**, **goal-based**, **time-based**, and **proactive** loops.

Source:
- https://claude.com/blog/getting-started-with-loops

### Closest OpenAI equivalents

| Claude loop type | OpenAI equivalent | Best source |
|---|---|---|
| **Turn-based loop** | Normal Codex / Agents SDK agent loop: model call → tool call → observe → continue → final answer | OpenAI Agents SDK “Running agents” |
| **Goal-based loop** | **Codex `/goal` / Goal mode** | Closest direct equivalent |
| **Time-based loop** | **Codex Automations** | Codex scheduled/background tasks |
| **Proactive loop** | Automations + skills + worktrees + possibly hooks/subagents | Codex best practices |
| **Repair/eval loop** | Codex iterative repair loop / Agents eval flywheel | OpenAI Cookbook |

### Best OpenAI articles/docs to read

1. **Follow a goal — Codex use case**  
   This is the most Claude-`/goal`-like article. It explains `/goal <objective>`, validation conditions, progress checkpoints, and when to pause/resume/clear.  
   Source: https://developers.openai.com/codex/use-cases/follow-goals

2. **Build iterative repair loops with Codex**  
   Best for practical engineering style: review → repair → validate → feed remaining delta into the next pass. It also stresses audit trails and max-iteration stop criteria.  
   Source: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex

3. **Build an Agent Improvement Loop with Traces, Evals, and Codex**  
   More meta: traces + human/model feedback → evals → Codex proposes harness changes. Good analogue to self-improvement, but grounded in evals rather than vague “agent learns itself.”  
   Source: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop

4. **Running agents — OpenAI Agents SDK**  
   Best API-level explanation of the internal agent loop and state continuation strategies. It separates `history`, `session`, `conversationId`, and `previousResponseId`.  
   Source: https://developers.openai.com/api/docs/guides/agents/running-agents

5. **Codex Automations**  
   Best time-based/proactive analogue. Important caveat: project-scoped automations need the local Codex app machine powered on, Codex running, and the project available on disk.  
   Source: https://developers.openai.com/codex/app/automations

### Codex status

OpenAI’s Codex changelog says **Goal mode is no longer experimental** and is available in the **Codex app, IDE extension, and CLI**; it can drive toward an objective for “hours or even days.”

Source:
- https://developers.openai.com/codex/changelog

So the practical OpenAI/Codex translation of the Claude article is:

```text
/goal Complete [objective] without stopping until [verifiable end state].
```

with explicit:

```text
- files/docs to read first
- allowed scope
- validation commands
- checkpoint report format
- stop condition
- pause condition
- max attempts / max time / human-review gate
```

This matches the project’s surface separation: Codex skills/hooks/plugins/automations are Codex concepts, not Custom GPT or ChatGPT Project concepts.

### Hermes loops

Yes, Hermes has loop concepts, but they are **third-party Nous Research/Hermes concepts**, not OpenAI features.

Hermes docs describe several loop layers:

| Hermes loop | Meaning |
|---|---|
| **Agent loop internals** | Hermes assembles prompts/tools, calls providers, executes tools sequentially or concurrently, manages conversation history, compression, retries, fallback models, and iteration budgets. |
| **`/goal` persistent goals** | Hermes’ user-facing goal loop. A judge model checks after each turn whether the goal is satisfied; if not, Hermes feeds a continuation prompt back into the session until done, paused/cleared, or budget-limited. |
| **Learning loop** | Hermes claims a “built-in learning loop”: memory nudges, autonomous skill creation, skill self-improvement, cross-session recall, and user modeling. |
| **Scheduled automations** | Hermes README mentions natural-language cron-style automations for unattended daily/weekly tasks. |
| **Self-evolution loop** | Separate Hermes self-evolution repo uses DSPy + GEPA to optimize skills/prompts/tool descriptions/code; current repo says Phase 1 skill evolution is implemented, while continuous improvement loop is planned. |

Sources:
- https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop
- https://github.com/nousresearch/hermes-agent/blob/main/website/docs/user-guide/features/goals.md
- https://hermes-agent.nousresearch.com/docs/
- https://github.com/nousresearch/hermes-agent
- https://github.com/NousResearch/hermes-agent-self-evolution

Interesting detail: Hermes’ own `/goal` docs explicitly say their implementation was inspired by **Codex CLI `/goal`** by Eric Traut/OpenAI, while implemented independently for Hermes.

### Recommendation

For these use cases, separate them like this:

- **Codex `/goal`**: best for bounded engineering work with tests, repo edits, migrations, eval improvement, reports.
- **Codex Automations + Skills**: best for recurring job-search scans, repo audits, report generation, inbox/GitHub monitoring.
- **Agents SDK loops**: best when building your own product/workflow outside ChatGPT/Codex and need explicit state, tools, evals, and observability.
- **Hermes loops**: promising for persistent personal-agent workflows, but treat the “self-improving” claims skeptically until logs, skill diffs, eval criteria, and rollback behavior are verified.

---

## 3. User

> Claude selected articles on loops and loop implementation? @Cerca

---

## 4. Assistant

## Selected Claude/Anthropic sources on loops

### Best starting point

| Priority | Source | Why read it |
|---:|---|---|
| 1 | **Getting started with loops** | Main Claude article. Defines loops as repeated work cycles until a stop condition, then separates **turn-based**, **goal-based**, **time-based**, and **proactive** loops. It also maps them to `/goal`, `/loop`, `/schedule`, skills, workflows, and routines. |
| 2 | **Keep Claude working toward a goal** | Direct implementation doc for `/goal`: Claude keeps working across turns until a condition is met; a small evaluator model checks the condition after each turn. Best for “don’t stop until tests pass / issue queue empty / acceptance criteria met.” |
| 3 | **Run prompts on a schedule** | Direct implementation doc for `/loop` and session-scoped cron-style prompts. Important caveat: `/loop` is session-scoped and expires/depends on running Claude Code; durable unattended work should use routines, desktop scheduled tasks, or GitHub Actions. |
| 4 | **Automate work with routines** | Cloud-side proactive loops: saved prompt + repos + connectors + schedule/API/GitHub triggers, running on Anthropic-managed infrastructure. Still marked research preview, so treat behavior and limits as moving target. |

Sources:
- https://claude.com/blog/getting-started-with-loops
- https://code.claude.com/docs/en/goal
- https://code.claude.com/docs/en/scheduled-tasks
- https://code.claude.com/docs/en/routines

### Implementation-level docs

| Source | Use it for |
|---|---|
| **How tool use works** | The core API loop: Claude emits `tool_use`, your code executes tools, returns `tool_result`, and repeats while `stop_reason == "tool_use"`. Also explains server-side loops and `pause_turn`. |
| **Tutorial: Build a tool-using agent** | Concrete code-level tutorial. It explicitly introduces the `while response.stop_reason == "tool_use"` loop and shows tool execution + result feedback. |
| **Tool Runner SDK** | Higher-level implementation. The SDK runner handles the agentic loop, tool execution, state, error wrapping, and type validation; manual loop is still recommended for custom logging, approval, or conditional execution. |
| **Building agents with the Claude Agent SDK** | Conceptual SDK article. The useful mental model is: **gather context → take action → verify work → repeat**. |
| **Build an orchestration mode** | Advanced implementation: session-level orchestration, parallel subagents, explicit caps, journal file, and standing consent for workflow fan-out. Useful if you want “heavy agent mode” rather than simple tool loops. |

Sources:
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/build-a-tool-using-agent
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner
- https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk
- https://platform.claude.com/docs/en/build-with-claude/mid-conversation-effort-example

### Claude Code loop-control primitives

| Source | What it adds |
|---|---|
| **Best practices for Claude Code** | The key practical rule: give Claude a pass/fail check so “the loop closes on its own.” It explicitly recommends tests, build exits, screenshots, `/goal`, Stop hooks, verification subagents, and workflows. |
| **Steering Claude Code: CLAUDE.md, skills, hooks, subagents** | Decision framework for where to put loop instructions: persistent repo memory, reusable skills, deterministic hooks, isolated subagents, etc. |
| **Extend Claude with skills** | Skills can encode repeatable verification logic; the skill-creator plugin can run comparison/eval loops and A/B skill versions. |
| **Automate actions with hooks** | Hooks are deterministic lifecycle gates: run formatters, block edits, validate commands, inject context, or use prompt/agent-based hooks when judgment is needed. |
| **Dynamic workflows docs** | Scripted multi-agent orchestration for audits, migrations, cross-checked research, and “keep fixing until a check passes” patterns. |
| **A harness for every task** | Blog version of dynamic workflows. Useful for mental models and example prompts: competing theories, workflow-based self-review, root-cause mining, claim verification, etc. |

Sources:
- https://www.anthropic.com/engineering/claude-code-best-practices
- https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more
- https://docs.anthropic.com/en/docs/claude-code/skills
- https://code.claude.com/docs/en/hooks-guide
- https://code.claude.com/docs/en/workflows
- https://claude.com/blog/a-harness-for-every-task-dynamic-workflows-in-claude-code

### Agent architecture / reliability articles

| Source | Why it matters |
|---|---|
| **Building Effective AI Agents** | Anthropic’s general agent architecture piece. It defines agents as LLMs using tools based on environmental feedback in a loop, and highlights evaluator-optimizer loops, stopping conditions, sandboxing, testing, and guardrails. |
| **How we built our multi-agent research system** | Good for multi-agent loop architecture: planner agent + parallel search agents + coordination/evaluation challenges. |
| **Demystifying evals for AI agents** | Useful when you want loops that improve reliably rather than just run longer. Covers grader types, transcript metrics, tool-call counts, token metrics, and research-agent eval difficulties. |
| **Introducing advanced tool use** | Important when loops should be explicit code rather than hidden model reasoning: programmatic tool calling moves loops, conditionals, transformations, and error handling into Python-like orchestration. |
| **Effective harnesses for long-running agents** | Good for long-running work where context windows roll over and you need a harness/environment strategy rather than one endless chat. |
| **Harness design for long-running application development** | More experimental but relevant for autonomous software-building loops and frontend/application harness design. |

Sources:
- https://www.anthropic.com/engineering/building-effective-agents
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
- https://www.anthropic.com/engineering/advanced-tool-use
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- https://www.anthropic.com/engineering/harness-design-long-running-apps

### Reading order

1. **Getting started with loops**  
2. **Best practices for Claude Code**  
3. **Keep Claude working toward a goal**  
4. **Run prompts on a schedule**  
5. **How tool use works**  
6. **Tutorial: Build a tool-using agent**  
7. **Tool Runner SDK**  
8. **Steering Claude Code**  
9. **Dynamic workflows docs / A harness for every task**  
10. **Building Effective AI Agents**

### Practical takeaway

Claude’s loop stack is roughly:

```text
Manual turn loop
→ /goal for verifiable stop condition
→ /loop for session polling
→ /schedule / routines for durable recurring work
→ skills/hooks for verification and policy gates
→ dynamic workflows/subagents for parallel or adversarial loops
→ API tool-use loop / Tool Runner for custom products
```

For engineering/Codex/Hermes-style use, the strongest pattern is still boring: **define a measurable stop condition, give the agent tools to verify it, cap iterations/cost, and log enough evidence that a second pass can audit the result.**

---

## 5. User

> Compare codex with Claude loops

---

## 6. Assistant

## Executive summary

**Codex and Claude now have very similar loop concepts, but Claude names the taxonomy more explicitly.** Claude talks directly about **turn-based, goal-based, time-based, and proactive loops**; Codex exposes roughly the same stack as **normal agent turns, `/goal`, automations, skills/hooks, eval-driven loops, and Agents SDK orchestration**.

Practical read:

- **Codex is stronger for repo-centered engineering loops**: tests, diffs, worktrees, eval logs, migrations, prompt/eval optimization.
- **Claude Code is more explicit and polished in loop vocabulary**: `/goal`, `/loop`, `/schedule`, routines, dynamic workflows, subagents.
- **Claude has a more formal “loop ladder” article.**
- **Codex has better OpenAI-native integration with evals, Responses API, Agents SDK, and Codex-specific repo workflows.**
- For engineering use: **Codex is the better default for controlled engineering loops; Claude’s loop docs are very useful as design language.**

## 1. Concept mapping

| Loop pattern | Claude naming | Codex/OpenAI equivalent | Practical difference |
|---|---|---|---|
| Single interactive loop | **Turn-based loop** | Normal Codex turn / Agents SDK run | Same basic loop: model → tools → result → continue. |
| “Keep working until done” | Claude Code `/goal` | Codex `/goal` / Goal Mode | Very similar. Claude documents the evaluator mechanism more explicitly; Codex frames it as long-running work toward a verifiable stop condition. |
| Polling / recurring session loop | Claude `/loop` | Codex **thread automations** | Claude has explicit `/loop`; Codex has heartbeat-style thread automations. |
| Durable scheduled/background work | Claude **routines** / `/schedule` | Codex **standalone/project automations** | Claude routines run on Anthropic-managed cloud infra; Codex automations run in local project or worktree with Codex app/sandbox model. |
| Reusable loop procedure | Claude skills | Codex skills | Very similar: reusable instructions/resources/scripts loaded when relevant. |
| Deterministic lifecycle gates | Claude hooks | Codex hooks | Very similar conceptually: shell/script hooks at agent lifecycle points. |
| Parallel/multi-agent orchestration | Claude dynamic workflows / subagents / agent teams | Codex subagents / worktrees / SDK orchestration | Claude’s dynamic workflow docs are more explicit about script-held orchestration. Codex has strong repo/worktree/eval bias. |
| API-level tool loop | Claude Messages API / Tool Runner | OpenAI Agents SDK / Responses API loop | Same core architecture: model asks for tools, app executes, model continues. |

Claude’s own article defines the ladder as **turn-based → goal-based → time-based → proactive loops** and maps them to `/goal`, `/loop`, `/schedule`, and dynamic workflows.

Source:
- https://claude.com/blog/getting-started-with-loops

## 2. Goal loop: Codex `/goal` vs Claude `/goal`

### Codex `/goal`

Codex `/goal` is intended for long-running work with a **verifiable stopping condition**. OpenAI’s docs position it for migrations, large refactors, deployment retry loops, experiments, prototypes, and prompt/eval optimization. The recommended setup is explicit: objective, stop condition, files/docs to read first, validation commands/artifacts, checkpoints, and pause/resume/clear controls.

OpenAI also says Goal Mode is no longer experimental and is available in the **Codex app, IDE extension, and CLI**, and can drive toward an objective for “hours or even days.”

Sources:
- https://developers.openai.com/codex/use-cases/follow-goals
- https://developers.openai.com/codex/changelog

### Claude `/goal`

Claude `/goal` is session-scoped: one active goal per session. It uses a separate evaluator after every turn, with a yes/no decision and reason; a “no” feeds guidance back into the next turn. Important caveat: the evaluator does **not** run commands or read files independently, so the condition must be demonstrated in the conversation transcript, for example by Claude running tests and surfacing results.

Source:
- https://code.claude.com/docs/en/goal

### Judgment

**Codex `/goal` feels more engineering-workflow-native.** It pushes toward repo checks, artifacts, progress logs, and evals.

**Claude `/goal` is more transparent about the meta-evaluator.** That is useful because the user knows exactly what can and cannot be judged.

For hard engineering work, write the goal in Codex style:

```text
/goal Complete [objective] until [test/eval/build condition passes].
Read [files/docs] first.
Do not change [excluded scope].
After each checkpoint run [commands].
Keep a log of changes, test results, and remaining blockers.
Stop if [condition] or if [safety/blocker condition].
```

## 3. Time-based loops: Claude `/loop` / routines vs Codex automations

### Claude

Claude separates short-lived `/loop` from more durable **routines**. `/loop` is session-oriented and can be stopped with `Esc`; fixed-interval loops run until stopped or until seven days elapse.

Claude **routines** are more durable: saved Claude Code configurations with prompt, repositories, connectors, and triggers. They can run on a schedule, API call, or GitHub event, and they run on Anthropic-managed cloud infrastructure, so they can continue when the laptop is closed. They are marked **research preview**, and behavior/limits/API may change.

Sources:
- https://code.claude.com/docs/en/scheduled-tasks
- https://code.claude.com/docs/en/routines

### Codex

Codex automations can run as thread automations, standalone automations, or project/worktree-style background runs. Thread automations are recurring wake-ups attached to the same thread; standalone automations start fresh scheduled runs and report findings in Triage. Codex automations can use plugins and skills, and Git repos can run in the local project or a dedicated worktree.

Important security caveat: Codex automations run unattended using the default sandbox settings; full access mode is elevated risk because background runs may modify files, run commands, and access network without asking.

Source:
- https://developers.openai.com/codex/app/automations

### Judgment

**Claude routines look stronger for cloud-style unattended recurring loops.**  
**Codex automations look stronger when the recurring loop is tied to a real repo/worktree and reviewable diffs.**

For job-search/email/GitHub/report workflows, Codex automations are attractive if the output should become files/reports in a project. Claude routines are attractive if the workflow should run remotely from connectors without relying on local machine state.

## 4. Eval/improvement loops

This is where **Codex is especially strong**.

OpenAI has a dedicated Codex use case for “scored improvement loops”: define an eval system, run one focused improvement at a time, rerun evals, log scores, inspect artifacts, and continue until explicit thresholds are reached. It explicitly recommends combining deterministic checks with LLM-as-judge checks and keeping machine-readable eval outputs.

Source:
- https://developers.openai.com/codex/use-cases/iterate-on-difficult-problems

Claude has the same general philosophy: give Claude tests, builds, screenshots, or another pass/fail check, otherwise the user becomes the verification loop. Anthropic states the loop closes on its own only when Claude has a check it can run and iterate against.

Source:
- https://www.anthropic.com/engineering/claude-code-best-practices

### Judgment

For **self-improvement / GEPA-like / prompt optimization / code repair**, Codex has the cleaner practical pattern:

```text
baseline → eval → focused change → eval → log delta → repeat → stop threshold
```

Claude can do it, but Codex’s docs are more directly aligned with eval-driven engineering workflows.

## 5. Reusable loop machinery: skills + hooks

### Skills

Codex skills package task-specific instructions, resources, and optional scripts; Codex initially sees skill name/description/path, then loads full `SKILL.md` only when it chooses to use the skill. They are available in Codex CLI, IDE extension, and app.

Source:
- https://developers.openai.com/codex/skills

Claude skills are very similar: a `SKILL.md` file gives Claude reusable instructions; skills load only when used, and can be invoked directly or automatically. Claude also notes that custom commands have been merged into skills, and bundled skills include `/debug`, `/code-review`, `/loop`, etc.

Source:
- https://docs.anthropic.com/en/docs/claude-code/skills

### Hooks

Codex hooks run deterministic scripts during the Codex lifecycle and can log conversations, block secrets, run validation at turn stop, or customize prompting by directory. Hook trust is explicit: non-managed command hooks must be reviewed and trusted before they run.

Source:
- https://developers.openai.com/codex/hooks

Claude hooks are also lifecycle commands: they run when Claude edits files, finishes tasks, needs input, etc. Anthropic frames them as deterministic control so actions always happen rather than depending on the LLM. Claude also supports prompt-based or agent-based hooks for judgment cases.

Source:
- https://docs.anthropic.com/en/docs/claude-code/hooks-guide

### Judgment

Rough parity.

Suggested use:

- **Codex skills/hooks**: encode engineering protocol, repo validation, report generation, anti-anchoring checks, artifact templates.
- **Claude skills/hooks**: encode Claude Code session behavior, app verification, `/loop` recipes, fast review/check procedures.

## 6. API-level agent loops

OpenAI Agents SDK says one SDK run is one application-level turn; the runner loops through model calls, tool calls, handoffs, and final answer. It also explicitly separates state strategies: local `history`, SDK `session`, OpenAI `conversationId`, or `previousResponseId`.

Source:
- https://developers.openai.com/api/docs/guides/agents/running-agents

Claude’s API tool loop is the same basic structure: while `stop_reason == "tool_use"`, execute tools, return `tool_result`, and continue until the model exits with another stop reason. Claude’s Tool Runner SDK can handle that loop, state, error wrapping, and type validation automatically, with manual loop recommended for human approval, custom logging, or conditional execution.

Sources:
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works
- https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-runner

### Judgment

At API level, neither has magic. Both reduce to:

```text
while model wants tools:
    execute tool
    return result
return final answer
```

Difference is ecosystem:

- **OpenAI**: stronger connection to Responses API, Agents SDK, evals, traces, and Codex.
- **Anthropic**: clear low-level tool-loop docs and a useful Tool Runner abstraction.

## 7. Claude’s unique-ish advantage: dynamic workflows

Claude’s dynamic workflows are worth noting. They are JavaScript scripts that orchestrate many subagents, with the loop/branching/intermediate state held in code rather than Claude’s context window. Anthropic positions them for codebase audits, large migrations, and cross-checked research; the docs explicitly compare subagents, skills, agent teams, and workflows by who holds the plan and where intermediate results live.

Source:
- https://code.claude.com/docs/en/workflows

Codex can do multi-agent/repo/worktree orchestration, but Claude’s dynamic workflow documentation is currently more explicit about **moving orchestration into readable/rerunnable code**.

## Recommendation

| Task type | Better default |
|---|---|
| Repo repair, refactor, migration, firmware/DSP tooling, tests | **Codex `/goal`** |
| Prompt/eval optimization, self-improvement harnesses | **Codex eval-driven loop** |
| Recurring project report written into files | **Codex automation + skill + worktree** |
| Cloud-side recurring connector work | **Claude routines**, if available and acceptable |
| Fast polling in one coding session | **Claude `/loop`** or Codex thread automation |
| Multi-agent cross-check research | **Claude dynamic workflows** or OpenAI Agents SDK, depending on whether local Claude Code workflow or custom API implementation is wanted |
| Productized custom agent | **OpenAI Agents SDK** or Claude SDK; choose by model/tool ecosystem, not loop concept |

## Bottom line

**Claude currently explains loops better; Codex currently operationalizes engineering loops better.**

For “Hermes/Codex self-improvement” direction, borrow Claude’s taxonomy but implement the serious workflow in Codex like this:

```text
Codex skill = method
AGENTS.md = repo policy and verification contract
/goal = bounded long-running objective
eval script = objective score
hook = deterministic guardrail
automation = recurring trigger
worktree = isolation
status log = durable memory
```

That gives the useful part of “loops” without relying on vague autonomous-agent mythology.

---

## 7. Compressed technical conclusions

### Core taxonomy

```text
Turn loop      = interactive model/tool/reply cycle
Goal loop      = keep working until verifiable end state
Time loop      = recurring scheduled polling/execution
Proactive loop = recurring/triggered work with skills, state, tools, and review surface
Repair loop    = attempt → validate → feed errors back → retry
Eval loop      = baseline → modify → score → compare → accept/reject
```

### Strongest Codex pattern

```text
Codex skill = reusable workflow method
AGENTS.md = repo-specific policy/context
/goal = long-running bounded objective
eval/test script = objective pass/fail or score
hook = deterministic guardrail
automation = schedule/trigger
worktree = isolation
status log = durable memory
```

### Strongest Claude pattern

```text
CLAUDE.md = repo/session memory
skill = reusable workflow
/goal = session goal with evaluator
/loop = repeated session prompt
routine = cloud scheduled/triggered work
hook = deterministic lifecycle gate
workflow = script-owned orchestration/subagents
```

### Practical design principle

A useful loop is not “agent keeps thinking.” A useful loop is:

```text
clear objective
+ bounded scope
+ executable verification
+ iteration cap
+ audit log
+ rollback path
+ human-review gate for risky side effects
```

