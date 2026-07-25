---
name: upe-v5-6
description: Evaluate, rewrite, package, or test reusable prompts, Project/Custom GPT instructions, skills, agents, tool workflows, automations, and UPE frameworks. Use for prompt-system design, capability/deployability review, GPT-5.6 runtime migration, regression evals, or terminal independent framework audit. Do not trigger for ordinary one-off writing, simple factual Q&A, direct translation, or summarization unless a reusable system is requested.
---

# UPE v5.6.0.1

Turn a reusable prompt or workflow into a capability-aware, source-grounded, action-safe, testable, and portable operating system.

## Load policy

1. Read the active request and applicable instructions first.
2. Read `references/UPE_v5.6.0.1_FULL_REFERENCE.md` for serious evaluation, architecture, migration, framework creation/revision, or conflict resolution.
3. Read `references/GPT_5.6_RUNTIME_PROFILE.md` when surface, model, effort, mode, orchestration, or reviewer-route independence matters.
4. Read `references/CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md` for reusable or capability-dependent systems.
5. Read `references/INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md` when the terminal gate triggers.
6. Use `scripts/validate_package.py` for deterministic release or skill validation and inspect `evals/` for behavioral cases.

## Workflow

1. Freeze every explicit MUST, required evidence, assumption, action boundary, done criterion, and output location.
2. Resolve surface, model/runtime axes, capabilities, permissions, freshness, risk, actions, state, and artifact target.
3. Run the capability scan for material reusable or capability-dependent work.
4. Put invariants in the kernel, details in references, repeated procedures here, facts in project files, mutable progress in state, and expected behavior in evals.
5. Choose the shortest reliable cognitive and tool adapters; centralize every side effect.
6. Build or evaluate the deployable artifact.
7. Pass contract, evidence/integrity, and feasibility/safety/delivery gates.
8. If a reusable framework was materially created or revised, freeze it and invoke a qualifying independent worker. Semantic-preserving mechanical edits do not trigger.
9. Integrate only evidence-backed changes, record one disposition per proposed change, and rerun affected checks.
10. Deliver verified scope or an exact partial result.

## Terminal independent gate

A qualifying worker:

- did not author the candidate;
- runs in a fresh context or process;
- receives a complete frozen evidence bundle rather than hidden author reasoning;
- has read-only candidate scope;
- has no external side-effect authority.

Unknown or contradictory critical evidence prevents `PASS`. A same-context role change is self-review and leaves the independent gate `UNKNOWN`.

Require blocker-first motivated findings, an anchored 0–50 baseline, headroom, low/base/high projected improvement, empirical results separately, a complete proposed artifact, a change map, and a reasoned version decision. The coordinator owns integration, re-tests, release numbering, and all writes.

For two-part `x.y`, use `x.(y+1)` for compatible improvement, `(x+1).0` by default for a breaking public-contract change, and unchanged `x.y` with `NO_RELEASE` when no safe material gain is defensible. Follow another explicit project convention only when recorded.

## Validation

For the extracted skill:

```bash
python scripts/validate_package.py .
```

For the complete release:

```bash
python skill/upe-v5-6/scripts/validate_package.py <release-root>
```

Behavioral gains remain projected until the supplied cases run on the lowest supported and strongest intended routes.
