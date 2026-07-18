

user:

Analyze chat contents and list of important links on loops implementation with codex and relevant for their understanding/application Anthropic papers @Cerca 

---

# Analysis of the loops chat

The uploaded chat has the **right conceptual backbone**: it distinguishes turn, goal, time, proactive, repair, and eval loops, then reduces the Codex implementation to `AGENTS.md + skill + /goal + verifier + hook + automation + worktree + durable state`. That is the useful part([OpenAI][1]) into a 36-link comparative library mixing product commands, API mechanics, Anthropic research, Codex implementation, and Hermes experiments. Humans do enjoy turning reading lists into small archaeological sites. tive verdict

The key conclusion should be retained:

```text
A loop is not “keep the model thinking.”

A reliable loop is:
objective
+ bounded scope
+ observable state
+ executable verification
+ structured feedback
+ iteration/cost limit
+ checkpoint and rollback
+ human gate for consequential actions
```

Three corrections materially improve the original chat:

1. **OpenAI now has direct Codex harness literature.** The Codex side no longer needs to be inferred mainly from `/goal`, Cookbook pages, and Agents SDK documentation. `Unrolling the Codex agent loop`, `Harness engineering`, and `Unlocking the Codex harness` now form a coherent implementation sequence. ([OpenAI][1])hropic’s most transferable material is its harness engineering, not Claude-specific slash commands.** `/goal`, `/loop`, routines, and Claude workflows are useful product comparisons, but the enduring lessons are external state, verifier design, context-efficient logs, generator/evaluator separation, and carefully bounded parallelism.

2. **Codex scheduled tasks need a more precise caveat.** Local-project tasks require the machine powered on, the desktop app running, and the project present on disk. Web scheduled tasks can use uploads, connected tools, skills, and plugins, but do not retain a local project directory or worktree between runs. ([OpenAI Developers][2]). Essential Codex implementation links

These are the sources I would give Codex first.

| Priority | Official source                                                                                                                                                                                                                                             | What it contributes |
| -------: | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
|        1 | **Unrolling the Codex agent loop** ([OpenAI][3])ual mechanics: a turn can contain many model/tool iterations; tools modify the environment; context grows; compaction, permissions, sandboxing, and termination are harness concerns.                       |                     |
|        2 | **Follow a goal** ([OpenAI Developers][4])icial long-running `/goal` pattern: objective, verifiable end state, bounded progress, and validation loop.                                                                                                       |                     |
|        3 | **Iterate on difficult problems** ([OpenAI Developers][5])d improvement loop: baseline, one focused change, rerun eval, inspect artifacts, record score delta, repeat.                                                                                      |                     |
|        4 | **Harness engineering: leveraging Codex in an agent-first world** ([OpenAI][1])ory-level design: agent legibility, structured documentation as source of truth, architecture enforcement, increasing autonomy, and continuous cleanup of accumulated drift. |                     |
|        5 | **Build iterative repair loops with Codex** ([OpenAI Developers][6])e repair architecture: review → repair → execute/validate → structured remaining delta → next pass, with iteration limits and audit artifacts.                                          |                     |
|        6 | **Codex best practices** ([OpenAI Developers][7])nstructions belong: `AGENTS.md`, skills, coherent chats, and bounded subagents rather than one swollen prompt attempting governance, memory, tooling, and theology simultaneously.                         |                     |

## Especially important insight from OpenAI’s harness article

OpenAI explicitly reports that the “one enormous `AGENTS.md`” approach failed. Their working structure is a **short `AGENTS.md` used as a map**, pointing to a structured `docs/` knowledge base that serves as the repository’s system of record. ([OpenAI][1])s directly to your UPE architecture:

```text
AGENTS.md / Project kernel  = active map and invariants
docs/ / project files       = detailed source of truth
skill                       = repeatable operating procedure
state file                  = current loop progress
scripts/tests/evals         = deterministic verification
```

---

# 2. Supporting Codex primitives

Once the six core sources are understood, these define the practical machinery.

| Primitive                      | Important source                                                                                                                                                   | Use in a loop |
| ------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------- |
| **`AGENTS.md`**                | Custom instructions with `AGENTS.md` ([OpenAI Developers][8])ory map, setup commands, invariants, forbidden changes, and definition of done.                       |               |
| **Skills**                     | Build skills ([OpenAI Developers][9]) the reusable loop method, references, scripts, output schema, and verification procedure.                                    |               |
| **Hooks**                      | Codex hooks ([OpenAI Developers][10])nistic lifecycle enforcement: validation, blocking dangerous actions, logging, formatting, or injecting context.              |               |
| **Subagents**                  | Codex subagents ([OpenAI Developers][11])dent exploration, implementation, testing, or adversarial verification. Not useful for one serial bottleneck.             |               |
| **Worktrees**                  | Codex worktrees ([OpenAI Developers][12]) parallel agents and scheduled changes from unfinished work in the main checkout.                                         |               |
| **Scheduled tasks**            | Codex scheduled tasks ([OpenAI Developers][2])ng maintenance, monitoring, reports, or repo operations.                                                             |               |
| **Agents SDK state**           | Running agents ([OpenAI Developers][13])ustom application loops with sessions, conversation IDs, or lightweight response-to-response continuation.                 |               |
| **Codex App Server**           | Unlocking the Codex harness ([OpenAI][14])he complete Codex loop with persistent threads, streaming events, approvals, diffs, reconnection, and rich client state. |               |
| **Codex as MCP server**        | Use Codex with Agents SDK ([OpenAI Developers][15])persistent Codex sessions as tools inside a larger orchestrated agent system.                                   |               |
| **Agent improvement flywheel** | Traces, evals, and Codex ([OpenAI Developers][16]) traces and human/model feedback into durable evals and evidence-backed harness changes.                         |               |

## App Server versus MCP versus `codex exec`

The current OpenAI guidance implies three distinct integration levels:

* **`codex exec`** for one-off or CI-style runs with structured output and a clear process exit.
* **Codex MCP server** when another agent framework should call Codex as a tool.
* **Codex App Server** when you need the complete harness: persistent threads, rich event streams, approvals, diffs, configuration, and reconnectable clients. ([OpenAI][14])tinction was missing from the original chat and is important for actual implementation.

---

# 3. Anthropic papers most useful for Codex

These are not merely “Claude papers.” They contain harness patterns directly applicable to Codex.

## Tier A: essential

### 1. Effective harnesses for long-running agents

This is the strongest practical companion to Codex `/goal`. Anthropic separates the first session into an **initializer agent** and later sessions into incremental coding agents. The initializer creates a reproducible start script, progress log, feature inventory, and initial git state; subsequent agents read that state, test the inherited environment, implement one bounded item, commit, and update progress. ([Anthropic][17]) Codex application:**

```text
bootstrap phase
→ machine-readable feature/backlog file
→ progress/handoff file
→ reproducible start and test scripts
→ one item per iteration
→ verified status update
→ reversible commit/checkpoint
```

### 2. Building Effective AI Agents

This is the architecture-selection paper. It distinguishes prompt chaining, routing, parallelization, orchestrator-workers, evaluator-optimizer, and open-ended agents, while recommending the simplest architecture that satisfies the task. ([Anthropic][18]) Codex application:**

```text
simple task                  → normal turn
fixed multistage task        → serial skill/workflow
hard task with score         → eval loop
independent workstreams      → subagents/worktrees
dynamic decomposition        → orchestrator-workers
long-running autonomous task → goal + harness + state + gates
```

### 3. Demystifying evals for AI agents

This supplies the missing epistemology of loops: the final answer, transcript, and actual environmental outcome are not the same thing. The outcome is what exists in the environment after the run, while an eval harness runs trials, records trajectories, grades results, and aggregates evidence. ([Anthropic][19]) Codex application:** completion must be based on the repository, tests, database, deployed application, generated document, or other observable artifact. The sentence “all tests pass” is not itself a test result. Charming attempt, though.

### 4. Effective context engineering for AI agents

This explains why loops decay even when the model is capable: context is finite, and dumping every log, tool definition, failed branch, and historical thought into it reduces the probability of the next correct action. ([Anthropic][20]) Codex application:**

* Canonical state belongs in files.
* Logs should be compact and searchable.
* Tool output should be reduced before entering model context.
* Only relevant docs and tools should be exposed.
* Long chats need deliberate compaction and handoff state.

### 5. Harness design for long-running application development

This advances the simple loop into a **generator/evaluator system**. Anthropic found that a separately calibrated evaluator can be more reliably critical than asking the generator to critique itself. The system used browser interaction, explicit grading criteria, sprint contracts, hard thresholds, and feedback passed into subsequent iterations. ([Anthropic][21])r also provides an important restraint: evaluator overhead becomes unnecessary for work comfortably within the generator’s reliable capability and remains valuable near the capability boundary. ([Anthropic][21]) Codex application:** use a verifier subagent or separate review pass for frontier, subjective, safety-sensitive, or difficult-to-detect work. Do not add a judicial branch to rename a variable.

### 6. Building a C compiler with a team of parallel Claudes

This is unusually practical. The core lessons are:

* The verifier must be extremely strong, or agents optimize the wrong target.
* Test output must be concise and machine-searchable.
* Fast deterministic subsets prevent the agent from spending the geological age running every test.
* Parallelism works when failures or modules are independent.
* Parallelism fails when every agent encounters the same serial bottleneck and overwrites the same work. ([Anthropic][22]) Codex application:** improve the harness and verifier before escalating agent count.

---

## Tier B: highly relevant extensions

| Anthropic source                                                                                                                                                                                       | Codex lesson |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------ |
| **How we built our multi-agent research system** ([Anthropic][23])orker needs a distinct objective, expected output, tools/sources, and scope boundary. Otherwise agents duplicate work or leave gaps. |              |
| **Dynamic workflows** ([Claude][24])gh-scale orchestration into code. The script owns loops, branching, and intermediate variables rather than filling the model’s context with every worker result.   |              |
| **Scaling Managed Agents** ([Anthropic][25])e model intelligence from the environment and harness. Model-specific compensations can become stale as models improve.                                    |              |
| **Code execution with MCP** ([Anthropic][26])ols on demand and process intermediate data in code rather than sending every tool schema and raw result through model context.                           |              |
| **How we built Claude Code auto mode** ([Anthropic][27])permissions by risk and environment boundary, avoiding both unrestricted autonomy and approval fatigue.                                        |              |
| **Building agents with the Claude Agent SDK** ([Anthropic][28])implementation cycle: gather context → act → verify → repeat.                                                                           |              |

---

# 4. Most important cross-platform insight

Anthropic’s dynamic-workflow documentation draws a useful distinction:

| Mechanism        | Who owns the plan?                | Where intermediate state lives? |
| ---------------- | --------------------------------- | ------------------------------- |
| Subagents        | Main model, turn by turn          | Model context                   |
| Skills           | Main model following instructions | Model context                   |
| Agent teams      | Lead agent                        | Shared task structure           |
| Dynamic workflow | Executable script                 | Script variables                |

A scripted workflow can coordinate dozens or hundreds of bounded workers without routing every intermediate result through the main context. ([Claude][24])x equivalents are:

```text
small delegation        → Codex subagents
isolated implementation → subagents + worktrees
repeatable method       → Agent Skill
custom orchestration    → Agents SDK
embedded Codex runtime  → App Server
Codex as specialist     → Codex MCP server
issue-driven system     → Symphony-style orchestration
```

OpenAI’s Symphony is particularly relevant for always-on, issue-tracker-driven Codex systems rather than one manually supervised loop. ([OpenAI][29]). Recommended Codex repository harness

```text
repository/
├── AGENTS.md
│   # Short map, invariants, commands, scope, definition of done
│
├── docs/
│   ├── architecture.md
│   ├── product-spec.md
│   ├── testing.md
│   └── decisions/
│
├── agent/
│   ├── state.json
│   ├── progress.md
│   ├── backlog.json
│   └── best-result.json
│
├── scripts/
│   ├── bootstrap.sh
│   ├── verify-fast.sh
│   ├── verify-full.sh
│   └── summarize-failure.py
│
├── evals/
│   ├── cases/
│   ├── graders/
│   └── results/
│
├── .agents/skills/
│   └── project-loop/
│       └── SKILL.md
│
└── hooks / CI
    # Deterministic validation and policy enforcement
```

## Loop contract

```text
START
1. Read AGENTS.md, state, progress, backlog, and recent git history.
2. Verify the environment and reproduce the current baseline.
3. Select one bounded item or independent workstream.
4. State its exact acceptance condition.

ITERATE
5. Make one coherent change.
6. Run fast or targeted verification.
7. Convert failure into structured next-pass feedback.
8. Run regression checks after a local pass.
9. Record score, evidence, changed files, and remaining delta.
10. Preserve the best result and create a reversible checkpoint.

STOP
11. Stop on verified success.
12. Pause on repeated no-progress, exhausted budget, missing evidence,
    unsafe action, or a required human decision.
13. Judge the actual environment, not the final narrative.
```

---

# 6. Recommended reading order

For someone implementing the system rather than merely admiring agent diagrams:

1. **Unrolling the Codex agent loop**
2. **Effective harnesses for long-running agents**
3. **Harness engineering**
4. **Follow a goal**
5. **Iterate on difficult problems**
6. **Demystifying evals for AI agents**
7. **Build iterative repair loops with Codex**
8. **Effective context engineering**
9. **Harness design for long-running application development**
10. **Building a C compiler with parallel Claudes**
11. **Codex skills, hooks, subagents, and worktrees**
12. **App Server or Agents SDK**, only when building a custom orchestrator

This sequence moves from loop mechanics to repository environment, then verification, context management, parallelism, and finally custom orchestration. A merciful improvement over opening all 36 tabs and learning mainly that browsers have finite width.

# Downloadable research map

The full Markdown version contains raw official URLs, the complete source matrix, a Codex `/goal` template, repository layout, session contracts, and a decision table:

[Download the Codex Loops and Anthropic Harness Reading Map](sandbox:/mnt/data/codex_loops_harness_anthropic_reading_map_2026-07-18.md)

[1]: https://openai.com/index/harness-engineering/ "Harness engineering: leveraging Codex in an agent-first world | OpenAI"
[2]: https://developers.openai.com/codex/app/automations "
  Scheduled tasks | ChatGPT Learn
"
[3]: https://openai.com/index/unrolling-the-codex-agent-loop/ "Unrolling the Codex agent loop | OpenAI"
[4]: https://developers.openai.com/codex/use-cases/follow-goals/?export=pdf "
  Follow a goal | ChatGPT use cases
"
[5]: https://developers.openai.com/codex/use-cases/iterate-on-difficult-problems "
  Iterate on difficult problems | ChatGPT use cases
"
[6]: https://developers.openai.com/cookbook/examples/codex/build_iterative_repair_loops_with_codex "
  Build iterative repair loops with Codex
"
[7]: https://developers.openai.com/codex/learn/best-practices "
  Best practices | ChatGPT Learn
"
[8]: https://developers.openai.com/codex/agent-configuration/agents-md?utm_source=chatgpt.com "Custom instructions with AGENTS.md | ChatGPT Learn"
[9]: https://developers.openai.com/codex/build-skills "
  Build skills | ChatGPT Learn
"
[10]: https://developers.openai.com/codex/hooks "
  Hooks | ChatGPT Learn
"
[11]: https://developers.openai.com/codex/subagents "
  Subagents | ChatGPT Learn
"
[12]: https://developers.openai.com/codex/environments/git-worktrees "
  Worktrees | ChatGPT Learn
"
[13]: https://developers.openai.com/api/docs/guides/agents/running-agents "
  Running agents | OpenAI API
"
[14]: https://openai.com/index/unlocking-the-codex-harness/ "Unlocking the Codex harness: how we built the App Server | OpenAI"
[15]: https://developers.openai.com/codex/mcp-server?utm_source=chatgpt.com "Use Codex with the Agents SDK | ChatGPT Learn"
[16]: https://developers.openai.com/cookbook/examples/agents_sdk/agent_improvement_loop "
  Build an Agent Improvement Loop with Traces, Evals, and Codex
"
[17]: https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents "Effective harnesses for long-running agents \ Anthropic"
[18]: https://www.anthropic.com/engineering/building-effective-agents "Building Effective AI Agents \ Anthropic"
[19]: https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents "Demystifying evals for AI agents \ Anthropic"
[20]: https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents "Effective context engineering for AI agents \ Anthropic"
[21]: https://www.anthropic.com/engineering/harness-design-long-running-apps "Harness design for long-running application development \ Anthropic"
[22]: https://www.anthropic.com/engineering/building-c-compiler "Building a C compiler with a team of parallel Claudes \ Anthropic"
[23]: https://www.anthropic.com/engineering/multi-agent-research-system "How we built our multi-agent research system \ Anthropic"
[24]: https://code.claude.com/docs/en/workflows "Orchestrate subagents at scale with dynamic workflows - Claude Code Docs"
[25]: https://www.anthropic.com/engineering/managed-agents "Scaling Managed Agents: Decoupling the brain from the hands \ Anthropic"
[26]: https://www.anthropic.com/engineering/code-execution-with-mcp?utm_source=chatgpt.com "Code execution with MCP: building more efficient AI agents"
[27]: https://www.anthropic.com/engineering/claude-code-auto-mode?utm_source=chatgpt.com "How we built Claude Code auto mode: a safer way to skip ..."
[28]: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk?utm_source=chatgpt.com "Building agents with the Claude Agent SDK"
[29]: https://openai.com/index/open-source-codex-orchestration-symphony/?utm_source=chatgpt.com "An open-source spec for Codex orchestration: Symphony."


---

user:
Evaluate what can be implemented here in ChatGPT/Work

---

answ:
# Evaluation: what can be implemented in ChatGPT / Work

## Verdict

**Most of the loop and harness architecture can now be implemented directly in ChatGPT Work.** The original chat’s conclusion that skills, plugins, automations, and goal-style execution were mainly Codex concepts is now partly obsolete. ChatGPT Work has since gained long-running tasks, desktop `/goal`, scheduled tasks, plugins, skills, connected tools, editable artifacts, and GPT-5.6 Ultra orchestration. 

The remaining gap is **deterministic enforcement**. Work can follow a repair or evaluation loop, but plain instructions do not create a guaranteed external state machine, transactional checkpoint system, CI runner, or independent evaluator. For those, Codex, workspace agents, MCP, or the Agents SDK remain stronger.

My practical classification:

| Level                           | Meaning                                                       |
| ------------------------------- | ------------------------------------------------------------- |
| **Native**                      | Directly supported by Work                                    |
| **Prompt/skill implementation** | Usable, but depends on model compliance and observable checks |
| **Surface-dependent**           | Requires desktop, web, plugin, or an organization workspace   |
| **External runtime required**   | Needs Codex, API, CI, or a custom agent harness               |

---

# 1. Loop-by-loop feasibility

| Loop pattern                  | ChatGPT Work status                              | Practical implementation                                                                                                      |
| ----------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| Turn/tool loop                | **Native**                                       | Work gathers context, plans steps, uses tools, observes results, and continues until it produces the deliverable.             |
| Goal loop                     | **Native**                                       | Desktop supports `/goal`; Work on the web uses an explicit outcome, constraints, and review criteria in the initial prompt.   |
| Repair loop                   | **Prompt/skill implementation**                  | Attempt → run check → interpret failure → repair → repeat, with a maximum-attempt and no-progress stop rule.                  |
| Eval loop                     | **Prompt/skill implementation**                  | Baseline → candidate → rubric/test → compare → accept/reject. Stronger with a separate verifier chat or deterministic script. |
| Time loop                     | **Native**                                       | Scheduled Tasks can run once, recur, trigger on an event, or monitor for meaningful changes.                                  |
| Proactive loop                | **Native with tools**                            | Scheduled Task + skill/plugin + connected app + notification/action rule.                                                     |
| Multi-agent loop              | **Native but partly opaque**                     | GPT-5.6 Ultra coordinates four agents by default; separate Work chats can also handle independent branches.                   |
| Durable workflow              | **Native in Projects, limited as state storage** | Keep files, instructions, chats, saved responses, and connected sources together in a Project.                                |
| Shared reusable agent         | **Organization plans**                           | Workspace agents provide reusable workflows, tools, memory, schedules, Slack/API triggers, approvals, and analytics.          |
| Arbitrary coded workflow      | **External runtime required**                    | Use Codex, a plugin/MCP app, workspace-agent API triggers, or the Agents SDK.                                                 |
| Genuine self-improvement loop | **External eval system required**                | Work may revise instructions, but promotion should require stored evals, versioned changes, and rollback.                     |

Work is explicitly designed to stay with complex projects for hours, break them into steps, work across applications and files, and let the user monitor, redirect, or approve important actions. ([OpenAI][1])

---

# 2. Goal loops are now directly implementable

The strongest correction to the old analysis concerns `/goal`.

In the **ChatGPT desktop app**, `/goal` starts Goal mode. The goal text serves as both the first prompt and the completion criteria, and the progress controls support pause, resume, edit, and clear. In **Work on the web**, the equivalent is to put the outcome, constraints, and review criteria directly into the prompt. ([OpenAI Developers][2])

Therefore, this Anthropic-style contract is now usable almost verbatim:

```yaml
goal:
  outcome:
  done_when:
  authoritative_inputs:
  constraints:
  excluded_scope:
  allowed_tools:
  approval_required_for:
  verification:
  max_attempts:
  no_progress_stop:
  checkpoint_format:
  final_outputs:
```

### Recommended Work prompt

```text
Complete the following goal as a long-running Work task.

OUTCOME
[Exact result to produce]

DONE WHEN
- [Observable condition 1]
- [Observable condition 2]
- [Required artifact exists and has been inspected]
- [All critical checks pass]

READ FIRST
- [Project source or file]
- [Template]
- [Authoritative source]

CONSTRAINTS
- Preserve [...]
- Do not change [...]
- Use only [...]
- Ask for approval before [...]

EXECUTION
1. Inspect the inputs.
2. Establish the baseline.
3. Work in bounded iterations.
4. After every material change, run the relevant verification.
5. Feed failures into the next iteration.
6. Preserve completed work and do not retry an unchanged failing action.
7. Stop after [N] failed attempts or when progress has stalled.

CHECKPOINT
Report:
- completed;
- evidence;
- failed checks;
- remaining work;
- next action;
- approval needed.

FINAL DELIVERY
Provide [...]
Do not declare completion unless the DONE WHEN conditions are evidenced.
```

That is a genuine goal loop. It is not an incantation for “think very hard until destiny intervenes.”

---

# 3. Repair loops can be implemented well

A repair loop is a particularly good fit for Work:

```text
inspect
→ establish baseline
→ make one coherent change
→ validate
→ convert failure into structured feedback
→ repair
→ run regression checks
→ deliver or stop
```

ChatGPT Work can research, analyze, operate across files and connected applications, and create editable documents, spreadsheets, presentations, reports, and Sites. It can also follow existing templates and reference files. ([OpenAI][1])

The loop becomes reliable when verification is **observable**:

| Work type                  | Suitable verifier                                                          |
| -------------------------- | -------------------------------------------------------------------------- |
| Research report            | Source coverage, citation audit, claim/evidence matrix                     |
| Document                   | Required-section checklist, pagination, links, rendered inspection         |
| Spreadsheet                | Recalculation, totals, formulas, reconciliation checks                     |
| Presentation               | Slide count, required content, master/template fidelity, visual inspection |
| Email workflow             | Recipient, subject, attachments, draft-versus-send gate                    |
| Calendar workflow          | Date, timezone, duration, attendees, conflict check                        |
| Data analysis              | Reproducible calculation, schema check, totals, missingness                |
| Website                    | Browser rendering, interaction checks, console errors                      |
| Prompt/system instructions | Acceptance cases, MUST coverage, negative tests                            |

The UPE rule already captures the right behaviour: preserve successful work, inspect the error, change a material variable, and never repeat an unchanged failure. The framework also explicitly routes serious work through discover → execute → merge/verify → deliver/persist. 

---

# 4. Eval loops are feasible, but not automatically rigorous

A Work task can run this process:

```text
baseline
→ candidate change
→ evaluator rubric
→ score and evidence
→ accept/reject
→ next candidate
```

However, there are three levels of evaluator independence.

## Level 1: same-chat evaluator

The generator creates an output and then evaluates it in a later stage.

**Useful for:** formatting, coverage, basic consistency, obvious failures.

**Weakness:** the model already knows and is psychologically attached, in the machine sense, to its own answer. Self-review often becomes a small ceremony in which the accused also chairs the tribunal.

## Level 2: separate verifier chat

Use another Work chat in the same Project:

* Generator chat has write access.
* Verifier chat is read-only.
* Both use the same project files and acceptance criteria.
* The verifier returns only defects, evidence, severity, and pass/fail status.
* The generator repairs from that report.

OpenAI recommends keeping related Work chats and sources together in a Project, while using separate chats for independent tasks and avoiding concurrent writes to the same connected source. ([OpenAI Developers][2])

This is the best no-code implementation of Anthropic’s generator/evaluator separation.

## Level 3: deterministic or external evaluator

Use:

* a script;
* spreadsheet formulas;
* test runner;
* repository CI;
* plugin/MCP tool;
* Codex;
* Agents SDK evals;
* workspace-agent test cases.

This is required when acceptance must be reproducible rather than merely persuasive.

---

# 5. Scheduled and proactive loops are native

Scheduled Tasks can:

* run once in the future;
* recur on a schedule;
* monitor for changes;
* run in an existing chat or as a standalone task;
* use uploaded context and connected tools;
* invoke skills for more complex procedures. ([OpenAI Help Center][3])

That makes the following Anthropic-style loops directly possible:

```text
daily mailbox triage
weekly UPE source refresh
monthly capability-registry review
monitor a webpage or connected source for changes
periodic project status synthesis
recurring job-search report
weekly repository or document audit
scheduled KPI/report generation
```

### Web versus desktop tasks

| Surface                  | Scheduled-task behaviour                                                                           |
| ------------------------ | -------------------------------------------------------------------------------------------------- |
| Web Work                 | Uses uploaded/project context and connected tools; cannot directly access a folder on the computer |
| Desktop Work             | Can work with local projects and optionally an isolated worktree                                   |
| Desktop with local files | Computer must remain on and the ChatGPT app must remain running                                    |
| Cloud-connected sources  | Can run without direct local-folder access                                                         |

These limitations are important. A web task cannot inspect `C:\Users\denko\Hermes\Affitto` merely because the prompt mentions it with conviction. ([OpenAI Developers][4])

---

# 6. Skills and plugins are now relevant to Work

This is the other major correction to the original chat.

A **skill** packages instructions, resources, examples, templates, schemas, and optional scripts for a repeatable workflow. A **plugin** distributes one or more skills and may also add connectors or MCP-backed tools. ([OpenAI Developers][5])

Plugins are now supported in:

* Work mode on ChatGPT web;
* Work mode in the ChatGPT desktop app;
* Codex in the desktop app;
* Codex CLI.

They are **not available in Chat mode, the IDE extension, or mobile**. ([OpenAI Developers][6])

## Consequence for UPE

The existing `upe-v5-6` skill can be used as follows:

| Surface                | Best deployment                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------- |
| ChatGPT desktop Work   | Install the UPE skill directly or package it as a plugin                              |
| ChatGPT web Work       | Package UPE as a plugin                                                               |
| iOS Work               | Use Project Instructions + uploaded UPE references; plugins are currently unavailable |
| Codex                  | Install the skill or plugin in the repository/user environment                        |
| Shared team deployment | Publish a plugin or build a workspace agent                                           |

The current UPE skill should therefore be retained, but **a Work-compatible plugin wrapper is now justified**. OpenAI recommends starting with a local skill while iterating and creating a plugin when the workflow is stable, shared, or needs connectors, MCP configuration, lifecycle hooks, or broader distribution. ([OpenAI Developers][7])

---

# 7. What can be implemented in this exact UPE Project

## Implement now

### A. Project-level harness

Keep:

```text
Project Instructions
└── UPE always-on kernel

Project Sources
├── full UPE reference
├── GPT-5.6 runtime profile
├── capability scan
├── official source map
├── loop/harness adapter
├── capability registry
└── current UPE state
```

A ChatGPT Project preserves shared instructions, uploaded files, connected sources, and related Chat and Work chats. The Project is the **context and evidence layer**, not by itself an autonomous loop engine. ([OpenAI Developers][8])

### B. Work goal adapter

Add a reference file such as:

```text
07_CHATGPT_WORK_LOOP_ADAPTER.md
```

It should define:

* goal contracts;
* repair-loop contracts;
* evaluator separation;
* checkpoint schema;
* no-progress and iteration limits;
* scheduled-task conversion;
* mobile/web/desktop differences;
* Codex/API escalation boundary.

### C. Work-loop state

Use a compact project artifact:

```yaml
work_loop_state:
  goal:
  done_when:
  status: running | blocked | review | complete
  iteration:
  completed:
  evidence:
  failed_checks:
  remaining:
  approvals_needed:
  next_action:
  stop_reason:
```

For a long task, update it at meaningful checkpoints. Save the response or state artifact into the Project sources so that a new chat can resume from explicit state rather than reconstructing history through interpretive archaeology. ChatGPT Projects support saving useful responses as project sources. ([OpenAI Help Center][9])

### D. Generator and verifier chats

Within the same Project:

```text
Chat 1: Generator / operator
Chat 2: Read-only verifier
Chat 3: Research or evidence branch, when independent
```

Only one chat receives write permission for a particular connected file or application.

### E. Scheduled maintenance

Once the workflow works reliably in an ordinary Work run:

```text
test manually
→ save as skill/template
→ schedule
→ review initial runs
→ expand permissions only after evidence
```

OpenAI’s own prompting guidance recommends refining recurring work in a normal chat before scheduling it. ([OpenAI Developers][10])

---

# 8. What should not enter the stable UPE core

The loop research does **not** justify rewriting the core. The core already contains the durable parts:

* bounded execution;
* explicit done criteria;
* tool and capability discovery;
* state and recovery;
* serial versus parallel routing;
* centralized side effects;
* `PASS | FAIL | UNKNOWN`;
* verification before delivery.

The following belong in a **dated Work runtime adapter or skill**, not in the permanent kernel:

* `/goal` availability;
* Work-versus-Chat behaviour;
* plugin surface availability;
* scheduled-task mechanics;
* Ultra’s default agent count;
* current plan eligibility;
* workspace-agent availability;
* mobile versus web versus desktop limitations.

That is precisely the kind of volatile product guidance the UPE architecture already says to separate from stable behavioural invariants. The existing documentation places model availability and prompting traits in a runtime profile, repeatable procedures in skills, current progress in state, and expected behaviour in evals. 

---

# 9. What still requires Codex or the API

These cannot be fully reproduced by Project Instructions alone:

| Requirement                                     | Better surface                                      |
| ----------------------------------------------- | --------------------------------------------------- |
| Direct local repository access and Git history  | Codex desktop, CLI, IDE, or cloud                   |
| Deterministic commands after every edit         | Codex hooks, scripts, or CI                         |
| Git checkpoints and rollback                    | Codex/repository workflow                           |
| Explicit coded branching and loops              | Agents SDK or custom workflow                       |
| Complete traces and tool-call evaluation        | Agents SDK/evals infrastructure                     |
| Programmatic tool calling                       | Responses API                                       |
| Arbitrary large-scale multi-agent orchestration | Responses API multi-agent or coded workflow         |
| Transactional state and idempotency             | External database/workflow engine                   |
| Exact retry/backoff policies                    | Application code                                    |
| Genuine automated prompt promotion              | Eval service + version control                      |
| Unattended local work while the machine is off  | Cloud Codex, workspace agent, or hosted application |

GPT-5.6 Ultra can coordinate four agents in parallel by default, but that is model orchestration, not a replacement for explicit state, branch ownership, deterministic merge rules, or a workflow engine. ([OpenAI][11])

---

# 10. Workspace agents are the closest Anthropic-routine equivalent

For Business and Enterprise workspaces, workspace agents are the strongest direct analogue to Anthropic routines:

* reusable agent configuration;
* model and effort selection;
* connected apps, MCPs, skills, files, and tools;
* schedules;
* Slack channel deployment;
* API triggers;
* shared use;
* approval policies;
* usage analytics. ([OpenAI Help Center][12])

On a personal Pro Lite account, this particular builder is not currently the primary route. The practical personal equivalent is:

```text
ChatGPT Project
+ Work mode
+ explicit goal contract
+ project sources
+ connected apps
+ skill/plugin where the surface supports it
+ Scheduled Task
+ separate verifier chat
```

That delivers most of the operational value without pretending a Project is secretly a cloud workflow server wearing a conversation interface.

# Final recommendation

## Implement in UPE v5.6.1

1. Add `CHATGPT_WORK_LOOP_ADAPTER.md`.
2. Add the `goal_contract` and `work_loop_state` schemas.
3. Add generator/verifier separation rules.
4. Add Work Scheduled Task conversion guidance.
5. Add mobile/web/desktop capability distinctions.
6. Wrap the existing UPE skill as a Work plugin.
7. Add acceptance cases for:

   * goal completion with evidence;
   * repair after failed verification;
   * no-progress stop;
   * separate read-only verifier;
   * scheduled monitoring;
   * mobile plugin fallback;
   * concurrent-write prevention;
   * local-folder access incorrectly assumed on web;
   * Ultra used only for independent branches.
8. Leave the stable core unchanged.

**Bottom line:** ChatGPT Work can now host the practical loop system itself. Codex remains preferable when the verifier is code, the state is a repository, rollback matters, or the workflow needs deterministic machinery rather than a very competent model being repeatedly asked to behave itself.

[1]: https://openai.com/index/chatgpt-for-your-most-ambitious-work/ "ChatGPT is now a partner for your most ambitious work | OpenAI"
[2]: https://learn.chatgpt.com/docs/long-running-work "
  Long-running work | ChatGPT Learn
"
[3]: https://help.openai.com/en/articles/10291617-tasks-in-chatgpt?utm_source=chatgpt.com "Scheduled Tasks in ChatGPT"
[4]: https://learn.chatgpt.com/docs/automations "
  Scheduled tasks | ChatGPT Learn
"
[5]: https://developers.openai.com/codex/build-skills "
  Build skills | ChatGPT Learn
"
[6]: https://developers.openai.com/codex/plugins "
  Plugins | ChatGPT Learn
"
[7]: https://developers.openai.com/codex/build-plugins "
  Build plugins | ChatGPT Learn
"
[8]: https://learn.chatgpt.com/docs/projects?utm_source=chatgpt.com "Projects and chats | ChatGPT Learn"
[9]: https://help.openai.com/en/articles/10169521-projects-in-chatgpt "Projects in ChatGPT | OpenAI Help Center"
[10]: https://learn.chatgpt.com/docs/prompting?utm_source=chatgpt.com "Prompting | ChatGPT Learn - OpenAI Developers"
[11]: https://openai.com/index/gpt-5-6/ "GPT-5.6: Frontier intelligence that scales with your ambition | OpenAI"
[12]: https://help.openai.com/en/articles/20001143-chatgpt-workspace-agents-for-enterprise-and-business "ChatGPT Workspace Agents for Enterprise and Business | OpenAI Help Center"


---

user:
Split implementations tasks between ChatGPT / work web and local Work / Codex What can be done in web, leave doing to web, otherwise do in local. What is better doing with Pro What could be done with Sol , effort: max vs high

---

answ:

# Recommended split: Web first, local only when the environment requires it

The governing rule should be:

```text
Can the task be completed from uploaded files, connected sources,
plugins, web research, and reviewable artifacts?

YES → ChatGPT Work on the web.

NO, because it needs local files/apps/browser but not repository tooling
→ Local Work.

NO, because it needs Git, shell commands, tests, worktrees, hooks,
durable machine state, or executable validation
→ Local Codex.
```

**Choose the surface before choosing the model.** A more intelligent model does not acquire a filesystem, Git history, or a test runner by telepathy. The original loops analysis already identified the right components: goal, verification, bounded iterations, audit state, rollback, and human gates. 

Current OpenAI documentation supports the same boundary: Work web handles files, plugins, approved tools, deliverables, recurring work, and multi-step workflows; desktop Work additionally gains local files, applications, and browser access. Codex adds repository execution, local development tools, Git environments, and worktrees. ([OpenAI Developers][1])

---

# 1. Tasks to leave in ChatGPT Work on the web

These should **not** be repeated locally unless web execution exposes a concrete limitation.

## A. Research and source management

| Implementation task                                                | Web owner          | Recommended route                                                      |
| ------------------------------------------------------------------ | ------------------ | ---------------------------------------------------------------------- |
| Refresh current OpenAI Work/Codex/model documentation              | Work web           | **Sol High**                                                           |
| Analyze Anthropic harness papers and extract transferable patterns | Work web           | **Sol High**                                                           |
| Maintain the OpenAI/Anthropic source matrix                        | Work web           | **Sol High**                                                           |
| Compare documented claims and identify contradictions              | Work web           | **Sol High**, escalate final conflicts to **Pro**                      |
| Produce dated source-map updates                                   | Work web           | **Sol High**                                                           |
| Monitor official documentation for changes                         | Web Scheduled Task | **Terra or Sol High**                                                  |
| Generate weekly research-change reports                            | Web Scheduled Task | **Terra** for routine runs, **Sol High** when synthesis is substantial |

Work web is the correct owner because it can use uploaded files, connected sources, plugins, and approved tools, and can produce reusable reports, spreadsheets, presentations, and recurring updates. Scheduled tasks can also use plugins and skills. ([OpenAI Developers][1])

### Use Ultra only when the source groups are genuinely separable

For example:

```text
Branch 1: OpenAI Work documentation
Branch 2: Codex harness and App Server
Branch 3: OpenAI model and effort controls
Branch 4: Anthropic long-running harness papers
Coordinator: reconcile and write one source matrix
```

Do not use Ultra merely because the reading list is long. Ultra is a subagent orchestration mode, not a ceremonial upgrade to the word “research.” ([OpenAI Developers][2])

---

## B. Work-loop specification

Create these artifacts in Work web:

```text
docs/work/
├── CHATGPT_WORK_LOOP_ADAPTER.md
├── WEB_VS_LOCAL_ROUTING.md
├── GENERATOR_VERIFIER_PROTOCOL.md
├── SCHEDULED_TASK_PATTERNS.md
├── MODEL_EFFORT_ROUTING.md
└── WORK_CODEX_HANDOFF_PROTOCOL.md

schemas/
├── goal_contract.schema.yaml
├── work_loop_state.schema.yaml
├── verifier_result.schema.yaml
└── capability_execution_record.schema.yaml

evals/
└── work_loop_acceptance_cases.yaml
```

### Model assignment

| Artifact                    | Initial creation | Final review   |
| --------------------------- | ---------------- | -------------- |
| Work loop adapter           | Sol High         | Pro            |
| Web/local routing matrix    | Sol High         | Sol Max or Pro |
| Goal contract schema        | Sol High         | Sol Max        |
| Loop-state schema           | Sol High         | Sol Max        |
| Generator/verifier protocol | Sol High         | Pro            |
| Scheduled-task patterns     | Sol High         | Sol High       |
| Acceptance cases            | Sol High         | Sol Max        |
| Capability execution record | Sol High         | Sol Max        |
| UPE migration notes         | Sol High         | Pro            |

These are specification and knowledge-work tasks. They depend primarily on source synthesis, requirement preservation, and reviewable text artifacts, so local execution adds no value yet. Projects can share uploaded files, project instructions, and connected sources across separate Work chats, while each distinct outcome remains isolated. ([OpenAI Developers][3])

---

## C. UPE documentation updates

Leave the following in Work web:

1. Draft the proposed **UPE v5.6.1 runtime additions**.
2. Update the Work applicability section.
3. Add goal, repair, eval, time, and proactive-loop patterns.
4. Add web/local/Codex routing guidance.
5. Update the capability scan.
6. Add scheduled-task guidance.
7. Draft release notes and migration instructions.
8. Produce the human-readable acceptance suite.
9. Create the final report, PDF, slides, or comparison spreadsheet.
10. Run a fresh-context review in a separate Work chat.

This follows the existing UPE design: stable invariants stay in the core, while product-specific Work, model, plugin, and scheduling behaviour belongs in dated references and skills. 

### Do not change the stable kernel yet

The loop work does not reveal a missing core invariant. UPE already has:

* bounded execution;
* capability discovery;
* explicit state;
* verification;
* direct/serial/parallel routing;
* centralized external actions;
* recovery;
* `PASS | FAIL | UNKNOWN`.

The new material belongs in a **Work runtime adapter, schemas, skill, and eval suite**, not another round of constitutional amendments because a product menu acquired new buttons.

---

## D. Plugin and skill design

Work web should handle:

* defining the skill’s trigger boundary;
* writing `SKILL.md`;
* drafting references and examples;
* designing positive and negative trigger cases;
* defining required plugins/connectors;
* deciding what capabilities should be avoided;
* creating the plugin specification;
* reviewing privacy and permission requirements.

However, **final skill/plugin packaging and validation should move to local Codex**.

Skills are the authoring format, while plugins distribute skills and connectors to Work web. Standalone skills are available directly in desktop/Codex surfaces; Work web consumes them through plugins. ([OpenAI Developers][4])

---

## E. Web scheduled tasks

Keep a scheduled task in web when it operates entirely on:

* public web sources;
* uploaded Project files;
* Google Drive or other connected sources;
* email/calendar/GitHub plugins;
* cloud-accessible documents;
* monitoring and reporting;
* generating a result in ChatGPT, a connected app, or a project source.

Examples:

```text
Weekly: check official OpenAI model and Work documentation for changes.
Monthly: audit whether the UPE runtime profile remains current.
Daily: collect important harness-related updates and return a source-backed digest.
Weekly: compare current project files against the capability registry.
```

Web scheduled tasks should **not** claim to update a local Git repository or inspect a local folder. Local project and worktree execution belongs to desktop Codex. ([OpenAI Developers][5])

---

# 2. Use local Work only for local, non-repository context

Local Work should be a narrow middle layer.

## Appropriate local Work tasks

| Task                                                                   | Why local Work                                   |
| ---------------------------------------------------------------------- | ------------------------------------------------ |
| Inspect private local documents that should not be uploaded            | Requires desktop filesystem access               |
| Work with Word, Excel, PowerPoint, browser, or another desktop app     | Requires application access                      |
| Compare a generated artifact against a local visual/template reference | Requires local source and visual inspection      |
| Operate a local browser-based admin interface                          | UI state is part of the evidence                 |
| Review a local PDF/document package before release                     | Local rendering or application behaviour matters |
| Demonstrate an application workflow for later skill creation           | Requires local computer-use access               |

Work desktop can use local files, applications, and browser tools when available and approved. ([OpenAI Developers][1])

## Do not use local Work for

* Git branching;
* worktrees;
* package validation scripts;
* schema testing;
* repository-wide refactoring;
* hooks;
* CI;
* test runners;
* application compilation;
* local state-machine implementation;
* App Server integration.

Those tasks belong to Codex.

---

# 3. Tasks for local Codex

Local Codex owns anything where the result must be **executed, tested, versioned, or proven on the machine**.

## A. Repository and package implementation

| Implementation task                            | Recommended model |
| ---------------------------------------------- | ----------------- |
| Create repository structure                    | Sol High          |
| Create branch or worktree                      | Sol High          |
| Materialize accepted Work artifacts into files | Sol High          |
| Implement the UPE skill package                | Sol High          |
| Build the Work plugin wrapper                  | Sol High          |
| Add plugin manifest and connector mappings     | Sol High          |
| Add scripts, assets, and reference copies      | Sol High          |
| Validate skill front matter and trigger cases  | Sol High          |
| Generate archives, manifests, and hashes       | Sol High          |
| Review Git diff and create commit              | Sol High          |

Codex can work directly in a repository, edit files, run local tools, inspect commands and diffs, and preserve the development loop in one session. ([OpenAI Developers][6])

---

## B. Deterministic validation

Local Codex should implement and run:

```text
scripts/
├── validate_release.py
├── validate_schema.py
├── validate_skill.py
├── validate_plugin.py
├── validate_character_limits.py
├── run_acceptance_cases.py
├── compare_expected_outputs.py
└── generate_manifest.py
```

It should verify:

* YAML/JSON parsing;
* schema validity;
* character limits;
* required files;
* reference-copy identity;
* trigger-positive and trigger-negative cases;
* package layout;
* duplicate source IDs;
* broken internal references;
* archive extraction;
* checksums;
* clean Git status;
* regression results.

### Model assignment

* **Sol High:** writing ordinary validators, fixing package problems, routine test execution.
* **Sol Max:** designing the validation architecture, handling subtle schema interactions, diagnosing nondeterministic failures, or reconciling several validator layers.
* **Pro:** unnecessary for ordinary validator implementation. The tests, not the model’s aura, decide whether the YAML parses.

---

## C. Durable loop state and harness implementation

Local Codex should implement anything resembling an actual external harness:

```text
runtime/
├── loop_runner.py
├── state_store.py
├── checkpoint.py
├── retry_policy.py
├── budget.py
├── verifier.py
├── event_log.py
├── permissions.py
└── recovery.py
```

This includes:

* typed lifecycle state;
* durable JSON/SQLite/JSONL persistence;
* idempotency;
* exact retry rules;
* no-progress detection;
* budget accounting;
* restart recovery;
* event logging;
* process reconciliation;
* tool-call records;
* approval state;
* verifier execution;
* rollback/checkpoint handling.

### Model assignment

| Component                   | Start with  | Escalate to Max when                                   |
| --------------------------- | ----------- | ------------------------------------------------------ |
| State schema implementation | Sol High    | State transitions become subtle or concurrent          |
| Checkpoint/recovery         | Sol High    | Restart consistency or partial commits are difficult   |
| Retry policy                | Sol High    | Idempotency and side effects interact                  |
| Budget accounting           | Sol High    | Several agents/tools share limits                      |
| Verifier runner             | Sol High    | Multiple grader types or uncertain aggregation         |
| Event log                   | Sol High    | Replay/reconciliation requirements appear              |
| Permission layer            | **Sol Max** | Consequential action boundaries are involved           |
| App Server integration      | **Sol Max** | Versioning, reconnectability, or event ordering matter |
| Multi-agent coordinator     | **Sol Max** | Branch ownership, merge, and recovery are non-trivial  |

This is where Max earns its supper.

---

## D. Worktrees and parallel implementation

Use worktrees only when tasks can change separate files or modules safely:

```text
Worktree A: plugin packaging
Worktree B: schema validators
Worktree C: acceptance runner
Worktree D: documentation build
Coordinator: merge, run complete validation, commit
```

Worktrees are available only in Codex in the desktop app and isolate multiple independent chats in the same Git repository. Scheduled repository tasks can also run in dedicated background worktrees. ([OpenAI Developers][7])

Do not parallelize:

* two agents editing the same manifest;
* migrations whose second stage depends on the first;
* final version-number changes;
* release packaging before validation;
* external publication;
* permission-sensitive actions.

---

## E. Local scheduled tasks

Use local Codex Scheduled Tasks when the task must:

* inspect a local repository;
* run tests or linters;
* update versioned files;
* create a commit or reviewable diff;
* use a worktree;
* execute local scripts;
* inspect a development server;
* read generated logs;
* update a local source registry.

Examples:

```text
Weekly: run UPE acceptance cases and produce a regression report.
Monthly: refresh local source snapshots and open a reviewable diff.
Nightly: validate skill and plugin packages.
On schedule: inspect deprecated links and update only the status registry.
```

Codex scheduled tasks can run in the local project or a dedicated worktree; web scheduled tasks cannot provide persistent access to that local checkout. ([OpenAI Developers][5])

---

# 4. What should be done with Pro

## Pro is best for difficult, substantially indivisible judgment

In standard ChatGPT, Medium, High, and Extra High use GPT-5.6 Sol, while Pro uses the separate GPT-5.6 Sol Pro model. OpenAI describes Sol Pro as the highest-capability GPT-5.6 option for difficult tasks and longer-running workflows. It is not merely another effort notch above Max. ([OpenAI Help Center][8])

## Use Pro for these UPE/harness tasks

### 1. Final architecture decision

Give Pro:

* the accepted research matrix;
* Work applicability analysis;
* Codex implementation findings;
* constraints;
* alternatives;
* unresolved conflicts.

Ask it to produce or review:

```text
ADR-001-WEB-LOCAL-CODEX-BOUNDARY.md
```

This is a good Pro task because it requires one coherent decision across product behaviour, architecture, state, permissions, and maintainability.

### 2. Stable-core versus runtime-layer review

Use Pro to decide:

* whether a finding belongs in the core;
* whether it belongs in the Work adapter;
* whether it belongs in a skill;
* whether it belongs in a tool or plugin;
* whether it belongs only in an eval.

This is difficult because a wrong placement creates persistent context cost or fragile behaviour across projects.

### 3. Final kernel compression

Use Pro when compressing a 9–12k draft below 8k while preserving:

* every MUST;
* authority hierarchy;
* action safety;
* capability discovery;
* evidence rules;
* state;
* acceptance gates.

This is a constraint-preservation problem where one elegant omission can quietly remove a safety invariant.

### 4. Conflict resolution

Use Pro when:

* official sources appear inconsistent;
* web findings and observed local behaviour conflict;
* Anthropic patterns must be adapted rather than copied;
* two architecture routes have difficult trade-offs;
* the choice affects future UPE projects.

### 5. Adversarial release review

Give Pro only:

* the release candidate;
* acceptance criteria;
* source index;
* validation report;
* known limitations.

Ask for:

```yaml
criterion:
status: PASS | FAIL | INSUFFICIENT_EVIDENCE
evidence:
smallest_correction:
release_blocking: true | false
```

### 6. Final synthesis and executive documentation

Pro is useful for turning the full technical implementation into:

* an executive summary;
* a final design rationale;
* a deployment recommendation;
* a coherent migration guide;
* a release-readiness verdict.

## Do not spend Pro on

* gathering 30 independent source summaries;
* copying files;
* generating manifests;
* routine coding;
* running tests;
* formatting YAML;
* fixing lint errors;
* creating ZIP archives;
* checking character counts;
* repeated scheduled monitoring;
* straightforward document conversion.

Pro should make difficult decisions, not carry boxes.

---

# 5. Sol High versus Sol Max

Current Work/Codex model controls distinguish reasoning effort from model tier. OpenAI recommends starting with the default effort and increasing it when deeper planning or analysis is needed; High provides greater reasoning depth, while Max provides maximum reasoning depth for the hardest problems. Ultra is separate because it adds automatic delegation. ([OpenAI Developers][2])

## Sol High: the default implementation setting

Use **Sol High** when:

* the objective is clear;
* the architecture has already been accepted;
* files and expected outputs are specified;
* tests or validation exist;
* the task has one principal line of execution;
* failures are observable;
* changes are reviewable and reversible;
* local tools will supply ground truth.

### Examples

* Drafting the Work loop adapter.
* Writing schemas from an accepted design.
* Implementing a skill.
* Creating a plugin manifest.
* Writing validators.
* Building test fixtures.
* Updating documentation.
* Implementing a known state transition.
* Fixing ordinary test failures.
* Creating a scheduled task.
* Packaging a release.
* Reviewing a normal Git diff.

**Default rule:** begin implementation with Sol High.

---

## Sol Max: use for hard, indivisible reasoning

Use **Sol Max** when one or more of these apply:

1. The architecture is unresolved.
2. Requirements conflict.
3. Several layers interact tightly.
4. A mistake is difficult to detect.
5. The task includes security or permission boundaries.
6. State recovery or idempotency is subtle.
7. There is no cheap deterministic verifier.
8. High has already produced one or two materially different failed attempts.
9. The task spans many files and requires maintaining a complex invariant.
10. The final merge must reconcile several independently developed components.

### Examples

* Designing the loop runner’s state machine.
* Defining crash-safe restart semantics.
* Implementing idempotent external actions.
* Designing App Server event reconciliation.
* Designing branch/merge recovery.
* Diagnosing a failure that survived ordinary tests.
* Reviewing permission boundaries.
* Reconciling Work, Codex, and API state models.
* Final integration of plugin, schemas, runtime, and eval runner.
* Proving that a release process cannot silently declare an incomplete run successful.

## Do not use Max merely because

* the task has many files;
* the report is long;
* a build takes time;
* several commands must run;
* a source list contains many links;
* the task sounds important;
* Max is available and therefore feels lonely.

---

## High versus Max decision table

| Question                                              |             High |                           Max |
| ----------------------------------------------------- | ---------------: | ----------------------------: |
| Is the target already designed?                       |                ✓ |                               |
| Are acceptance tests deterministic?                   |                ✓ |                               |
| Is this ordinary multi-file implementation?           |                ✓ |                               |
| Is the problem mainly execution rather than judgment? |                ✓ |                               |
| Are requirements ambiguous or conflicting?            |                  |                             ✓ |
| Is the state/recovery model subtle?                   |                  |                             ✓ |
| Are permissions or irreversible effects involved?     |                  |                             ✓ |
| Has High failed despite meaningful corrections?       |                  |                             ✓ |
| Is this final architecture integration?               |                  |                             ✓ |
| Is the task hard but cleanly separable?               | Use High workers | Consider Ultra, not Max alone |

---

# 6. Pro versus Sol Max

They are separate controls and should not be treated as interchangeable.

| Route              | Best use                                                                              |
| ------------------ | ------------------------------------------------------------------------------------- |
| **Sol High**       | Default professional research and implementation                                      |
| **Sol Extra High** | Long, agentic, reasoning-heavy execution before committing to Max                     |
| **Sol Max**        | Hardest Sol reasoning on Work/Codex, especially tool-rich local work                  |
| **Sol Pro**        | Highest-capability single-agent judgment, final synthesis, difficult indivisible work |
| **Ultra**          | Independent parallel workstreams with coordinator merge                               |

OpenAI’s Codex guidance recommends Medium or High for more complex changes/debugging and Extra High for long, agentic, reasoning-heavy tasks. Max is listed for the hardest problems, while Ultra adds automatic task delegation. ([OpenAI Developers][2])

## Practical priority

```text
Known implementation with tests
→ Sol High

Long implementation needing more planning
→ Sol Extra High

Hard architecture, state, security, or repeated failure
→ Sol Max

Highest-stakes final judgment or synthesis
→ Pro

Several independent workstreams
→ Ultra, followed by one strong coordinator review
```

---

# 7. Recommended end-to-end execution order

## Phase 1: Web Work, Sol High

Produce:

```text
CHATGPT_WORK_LOOP_ADAPTER.md
WEB_VS_LOCAL_ROUTING.md
goal_contract.schema.yaml
work_loop_state.schema.yaml
GENERATOR_VERIFIER_PROTOCOL.md
SCHEDULED_TASK_PATTERNS.md
work_loop_acceptance_cases.yaml
```

Run the official-source refresh and prepare the candidate UPE v5.6.1 changes.

## Phase 2: Web ChatGPT Pro

Perform one architecture freeze:

```text
ADR-001-WEB-LOCAL-CODEX-BOUNDARY.md
```

Pro must decide:

* web versus local ownership;
* stable core versus runtime adapter;
* skill versus plugin;
* canonical state;
* verification boundary;
* action authority;
* release-blocking unknowns.

## Phase 3: Local Codex, Sol High

Implement the accepted specification:

* repository layout;
* skill;
* plugin;
* schemas;
* validators;
* acceptance runner;
* package scripts;
* documentation build;
* manifests and hashes.

## Phase 4: Local Codex, Sol Max

Use Max only for:

* durable state engine;
* recovery/idempotency;
* permission system;
* App Server or Agents SDK integration;
* hard validation failures;
* final multi-component integration.

## Phase 5: Web ChatGPT Pro, fresh context

Give Pro the release candidate, validation report, source index, and acceptance criteria. It performs a **read-only release review**.

## Phase 6: Local Codex, Sol High

Apply only accepted corrections, rerun deterministic validation, package, and commit.

---

# Final routing summary

```text
WEB WORK
Research
Source matrices
Specifications
Schemas as designs
Project/reference documentation
Reports, PDFs, slides, spreadsheets
Scheduled web monitoring
Plugin/skill design
Fresh-context review

LOCAL WORK
Private local documents
Desktop applications
Browser/UI evidence
Local visual/template inspection
Non-repository computer-use workflows

LOCAL CODEX
Repository edits
Git and worktrees
Shell commands
Tests and validators
Skill/plugin packaging
Hooks
Durable state
Retry/recovery/idempotency
App Server or Agents SDK
Local scheduled tasks
Release packaging and commits

SOL HIGH
Default for research and implementation

SOL MAX
Hard architecture, state, recovery, permissions,
subtle debugging, and final integration

PRO
Final architectural judgment, conflict resolution,
kernel preservation, adversarial review, and executive synthesis
```

The clean operating sequence is therefore **Web High → Web Pro decision → Local Codex High → selective Local Max → Web Pro review → Local High release**. This keeps research and document work in the web surface, reserves local execution for things that genuinely require the machine, and prevents expensive reasoning modes from being assigned the sacred task of creating ZIP files.

[1]: https://learn.chatgpt.com/docs/get-started-with-work "
  Get started with Work mode | ChatGPT Learn
"
[2]: https://developers.openai.com/codex/models "
  Models | ChatGPT Learn
"
[3]: https://learn.chatgpt.com/docs/projects "
  Projects and chats | ChatGPT Learn
"
[4]: https://learn.chatgpt.com/docs/build-skills "
  Build skills | ChatGPT Learn
"
[5]: https://learn.chatgpt.com/docs/automations "
  Scheduled tasks | ChatGPT Learn
"
[6]: https://developers.openai.com/codex/cli "
  Codex CLI | ChatGPT Learn
"
[7]: https://developers.openai.com/codex/environments/git-worktrees "
  Worktrees | ChatGPT Learn
"
[8]: https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt "GPT-5.6 in ChatGPT | OpenAI Help Center"
