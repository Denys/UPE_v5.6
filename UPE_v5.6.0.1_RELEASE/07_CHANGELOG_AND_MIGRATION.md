# UPE v5.6.0.1 — Release Notes, Migration, and Change Control

## Release decision

`5.6.0 → 5.6.0.1` — compatible UPE patch with one explicit durable core change.

`CORE_CHANGE CC-5.6.0.1-01` adds a terminal independent framework auditor/improver. The GPT target remains 5.6; authority hierarchy, supported framework classes, and action boundaries remain compatible.

The v5.6.0.1 candidate was frozen and independently reviewed. The worker found two release blockers and six lower-severity defects, and the coordinator integrated the validated repairs before the final freeze. The `5.6.1` identifier is reserved and blocked from Codex use unless the user explicitly authorizes it.

## Added in v5.6.0.1

- A terminal audit trigger for material reusable-framework creation or revision.
- A concrete materiality rule covering behavior, authority, required I/O, capability routing, action boundaries, state/recovery, deployment, and acceptance.
- A qualifying-independence test: no candidate authorship, fresh context/process, frozen evidence only, read-only candidate scope, and no external side-effect authority.
- A frozen review bundle with sorted per-file SHA-256 records and a reproducible package hash.
- Blocker-first critique with an evidence-anchored ten-dimension 0–50 baseline.
- Quantified headroom, low/base/high projected improvement, relative delta, headroom capture, confidence, and assumptions.
- Strict separation between projected gain and empirical metrics.
- A complete proposed revision, change map, and coordinator disposition per proposed change.
- Compatible, breaking, and `NO_RELEASE` version decisions with explicit alternatives.
- Trigger, independence, blocker, scoring, schema, version, and no-gain evals.

## Independent audit result

The fresh-context worker scored the initial frozen candidate `36/50`, found two release blockers, and projected the corrected package at `43–48/50` with base `46` (`+10`). Those score gains are projected, not measured behavioral performance.

Deterministically verified repairs included:

- complete release-path closure;
- exact full-reference/standalone audit-schema parity;
- reproducible per-file and package hashing;
- common 0–5 scoring anchors and a no-behavioral-eval ceiling;
- observable trigger materiality;
- stable `skill/upe-v5-6/` discovery;
- structured independence evidence;
- one coordinator disposition per proposed change.

## Why this is not a breaking release

The change adds a pre-release acceptance gate without removing or incompatibly redefining UPE’s purpose, authority hierarchy, supported inputs/outputs, or action boundary. For UPE’s family-bound `5.6.r.p` scheme, that is a patch increment from `5.6.0` to `5.6.0.1`; the future `5.6.1` UPE line remains unconsumed.

For a generic two-part framework version `x.y`:

- compatible material improvement: `x.(y+1)`;
- breaking public-contract change: `(x+1).0` by default;
- no defensible safe material gain: keep `x.y` and return `NO_RELEASE`.

If a framework explicitly defines `(x+1).y`, follow and record that convention rather than silently mixing schemes.

## Migration from v5.6.0

1. Replace the Project Instructions kernel with `02_UPE_v5.6.0.1_PROJECT_INSTRUCTIONS_KERNEL.md`.
2. Replace the full reference and portable kernel with the v5.6.0.1 files.
3. Add `12_INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md` to project sources.
4. Replace the capability registry template so independence evidence can be recorded structurally.
5. Replace the `upe-v5-6` skill as a unit; keep its stable discovery name.
6. Run deterministic package validation.
7. Run general and terminal-audit behavioral cases on the lowest supported and strongest intended routes.

## Versioning rule

```text
UPE v<target GPT major>.<target GPT minor>.<UPE line>.<UPE patch>
```

Published release files are immutable. Any redistributed compatible change increments the final patch component. Promoting the UPE line increments the third component and resets the patch. A durable behavioral invariant additionally requires a `CORE_CHANGE` record. The reserved `5.6.1` line cannot be selected automatically by Codex.

## Change record template

```yaml
upe_change:
  version:
  date:
  change_type: CORE_CHANGE | RUNTIME_PROFILE | KERNEL | SKILL | TOOL_ROUTING | EVAL | DOC
  change:
  failure_mode_fixed:
  evidence_or_trigger:
  expected_improvement:
  regression_risk:
  affected_surfaces:
  test_cases:
  acceptance_criteria:
  measured_result:
  keep_modify_or_remove:
```
