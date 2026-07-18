---
name: upe-v5-6
description: Evaluate, rewrite, compress, expand, migrate, package, or test reusable prompts, Project Instructions, Custom GPTs, Agent Skills, agents, tool/plugin procedures, research/coding/file workflows, and automations. Use when the user asks for prompt-system design, capability discovery, deployability review, model/runtime adaptation, or regression evals. Do not trigger for ordinary one-off writing, simple factual Q&A, direct translation, or summarization unless the user asks to turn it into a reusable prompt or workflow.
---

# UPE v5.6.0 Skill

## Goal

Turn a reusable prompt or workflow into a capability-aware, source-grounded, action-safe, testable, and portable operating system while keeping simple work simple.

## Load policy

1. Read the active user request and applicable project instructions first.
2. Read `references/UPE_v5.6.0_FULL_REFERENCE.md` only for serious evaluation, migration, architecture, agent/tool/file/automation design, or conflict resolution.
3. Read `references/GPT_5.6_RUNTIME_PROFILE.md` only when model, effort, pro mode, Ultra/multi-agent, PTC, or product surface matters.
4. Read `references/CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md` for reusable or capability-dependent systems.
5. Use scripts only for deterministic validation or packaging.

## Workflow

### 1. Freeze the contract

Capture every explicit MUST constraint, required evidence, assumptions, action boundaries, done criteria, and output location. Do not silently simplify the task.

### 2. Resolve the runtime

Separate target surface, model tier, reasoning effort, standard/pro mode, orchestration, tools, permissions, freshness, risk, state, and artifact target. Actual exposure overrides presets.

### 3. Run capability discovery when triggered

Inspect relevant built-in tools, installed skills/plugins, apps/connectors/MCP, files, code/data, artifact capabilities, browser/computer use, agents, tool search, PTC, and schedules.

Produce `Required`, `Optional`, and `Avoid/Disable`, with prerequisites, read/write scope, approval, validation, fallback, and measurable gain. Prefer a suitable existing skill/plugin over recreating it.

Skip this step for trivial one-off work with no material capability gain.

### 4. Compile instruction layers

Place content in the cheapest durable layer:

- kernel for always-on invariants;
- reference for detail and dated guidance;
- skill for a repeatable triggered process;
- project files for facts, sources, templates, and user data;
- tool descriptions for schemas and side effects;
- state for progress;
- evals for observable behavior.

### 5. Choose execution adapters

Use `atomic_direct`, `coordinated_serial`, or `native_parallel`. Branch only cleanly separable read-only work. Keep a serial fallback and centralize every external action.

Use direct tools by default. Use tool search for large deferred catalogs; PTC only for a bounded predictable reduction stage; browser/computer use only for UI-only work or evidence.

### 6. Evaluate or build

For evaluation, score the ten UPE dimensions and list critical blockers. For creation/rewrite, preserve intent and produce deployable artifacts, not merely advice.

### 7. Verify

Evaluate:

1. Contract coverage.
2. Evidence/file/code/artifact integrity.
3. Feasibility, action safety, and delivery.

Mark `PASS | FAIL | UNKNOWN`. Repair critical failures. A critical unknown requires verification or an explicit partial label.

### 8. Package

When requested or useful, provide:

- full reference;
- project kernel within the hard character cap;
- portable kernel;
- runtime/model profile;
- capability plan;
- skill bundle;
- source map;
- changelog;
- state schema;
- eval suite and validation report.

## Output rules

- Lead with the verdict or deliverable.
- Keep copy-ready instructions free of meta-commentary.
- Distinguish measured from projected improvements.
- Report only capabilities, branches, tools, tests, and actions actually used.
- Do not expose hidden reasoning; provide concise rationale, evidence, decisions, and validation.

## Validation

Run:

```bash
python scripts/validate_package.py <release-root>
```

For skill-only validation, pass the skill directory. Review `evals/trigger_cases.csv` and `evals/acceptance_cases.yaml` on the lowest supported model route and the strongest intended route.
