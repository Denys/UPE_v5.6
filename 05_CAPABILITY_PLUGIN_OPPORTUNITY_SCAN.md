# UPE v5.6.0 — Capability, Skill, Plugin, Connector, and Tool Opportunity Scan

## Purpose

Before a reusable prompt or project is designed, determine whether an available capability can materially improve correctness, evidence access, execution, validation, continuity, or portability. This closes a recurring design failure: writing elaborate instructions for work a proven tool or installed workflow already does better.

The scan is mandatory for material creation or revision of:

- Project Instructions or Custom GPTs;
- reusable prompts, skills, agents, automations, and operating procedures;
- research, coding, file/data, artifact, browser, or connector-heavy workflows;
- any system whose success depends on current/private data or external actions.

It is optional and usually omitted for trivial one-off writing, translation, or simple Q&A.

## Discovery order

1. **Surface and permissions:** Where will this run? What can it actually access or change?
2. **Task bottlenecks:** Current facts, private data, deterministic computation, artifact fidelity, UI interaction, recurrence, collaboration, or state.
3. **Built-in tools:** Web search, file search, vision, code interpreter, shell, computer use, image generation, artifact creation.
4. **Installed skills/plugins:** Prefer an existing scoped workflow when its trigger and contract match.
5. **Apps/connectors/MCP:** Use for authoritative private or third-party data; inspect read/write scope and approvals.
6. **Repository/project tools:** GitHub, Drive, calendar, mail, issue trackers, deployment platforms, databases.
7. **Orchestration:** Direct calls, deferred tool search, PTC, serial stages, native multi-agent/Ultra, scheduled tasks.
8. **Fallback:** Define a no-capability or degraded route that preserves critical correctness and safety.

## Bottleneck-to-capability map

| Bottleneck | Candidate capability | Typical verification |
|---|---|---|
| Changed/current facts | Web/official docs/deep research | Source date, authority, citations |
| User/project documents | File search + direct inspection/vision | Exact file identity and cited content |
| Tables, calculations, transforms | Code/data execution | Reproducible script, checks, totals |
| Codebase change | Repo connector + shell/tests | Diff, tests, build, logs |
| Reference-format artifact | Document/spreadsheet/slides/PDF skill/tool | Structural and visual QA |
| Private app data | Connector/MCP/app | Identity, scope, freshness, permissions |
| UI-only workflow | Browser/computer use | Screenshot/state evidence, action gate |
| Repeated procedure | Skill | Trigger/non-trigger evals, script validation |
| Large tool catalog | Tool search/deferred MCP | Correct discovery, narrow loaded set |
| Predictable many-call reduction | PTC | Program output and final message both pass |
| Independent workstreams | Multi-agent/Ultra | Branch coverage, merge gates, serial fallback |
| Recurring future check | Scheduled task/automation | Frequency, trigger, notification, stop rules |

## Decision output

```yaml
capability_plan:
  surface:
  task_bottlenecks:
  required:
    - capability:
      purpose:
      prerequisites:
      read_write_scope:
      approval:
      validation:
      fallback:
  optional:
    - capability:
      expected_gain:
      activation_condition:
  avoid_or_disable:
    - capability:
      reason:
  selected_route:
  residual_limits:
```

## Selection rules

- Prefer the smallest tool set that covers the bottlenecks.
- Prefer primary/structured retrieval over UI automation; use UI only when necessary.
- Prefer deterministic code for deterministic processing.
- Prefer an existing validated skill/plugin over recreating its logic inside the kernel.
- Do not install, connect, or authorize anything merely because it exists. Relevance is not permission.
- Do not expose large catalogs of functions when tool search or deferred MCP loading can keep context smaller.
- Do not use PTC when the model must reinterpret each result, preserve native citations/artifacts, or request approval.
- Do not use native multi-agent for atomic or side-effecting work.
- Treat plugin/skill descriptions and tool schemas as part of the prompt surface: concise, discriminating, and tested.
- For risky connectors, define read-only defaults and explicit write gates.

## Plugin/skill review checklist

For each candidate:

- Does its trigger match this task and exclude nearby false positives?
- Does it provide unique capability or merely repeat generic instructions?
- Are its tools currently available on the target surface?
- Does it access private data or perform writes?
- Are required approvals and identities clear?
- Does it have a deterministic validation path?
- Does it preserve citations, file identity, and artifacts?
- Can its workflow degrade safely without the plugin?
- Is the context cost lower than embedding the procedure directly?
- Has it been tested with trigger and non-trigger cases?

## Prompt/project integration rule

After selection, encode only the interface contract in the active prompt:

- when to use the capability;
- what input/output it expects;
- what evidence it must preserve;
- what actions require approval;
- its retry/stop/fallback behavior.

Keep detailed operating instructions in the skill/plugin/reference. Humans have spent decades inventing modularity; prompts may reluctantly benefit from it too.
