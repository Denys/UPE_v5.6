# UPE v5.6.0.2 — Draft Notes, Migration, and Change Control

## Release decision

`5.6.0.1 → 5.6.0.2` — compatible runtime/workflow patch. Candidate state: `DRAFT`; no GitHub merge, tag, release, or deployment is implied.

`RUNTIME_ADAPTER RA-5.6.0.2-01` maps the existing terminal auditor/improver to native Web Work subagent operations. The GPT target, authority hierarchy, supported framework classes, action boundaries, and terminal worker’s proposal-only authority remain compatible.

Frozen v5.6.0.1 remains immutable. The `5.6.1` identifier remains reserved and blocked from Codex use unless the user explicitly authorizes it.

## Added in v5.6.0.2

- `web_work_native_subagent` activation gate based on current-run spawn/result/fresh-context operations.
- Standard workflow: hidden frozen v1 → visible validated Reviewer 1 payload → UPE dispositions/rework → published v2 → fresh Reviewer 2.
- One review payload is both shown in the main chat and passed unchanged to UPE.
- Separate cognitive-independence, candidate-integrity, action-authority, and technical-isolation records.
- Inline frozen copy / immutable reference as qualifying candidate transport; shared writable path downgraded to advisory unless enforced.
- Hash-bound parent/child envelopes and candidate hash recheck after review.
- Quantified negligible-gain exit plus bounded blocker repair and total-review limits.
- Explicit fast mode that publishes `DRAFT_UNAUDITED` v1 but cannot bypass formal release review.
- User-steering invalidation and stale-review recovery.
- Hooks/heartbeats restricted to lifecycle/liveness, never review-content concatenation.
- Seventeen machine-readable Web Work adapter cases and deterministic package checks for their structure.

## Inherited from v5.6.0.1

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

## Inherited v5.6.0.1 independent audit result

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

## Why v5.6.0.2 is not breaking

The change adds a surface adapter and operational detail without removing or incompatibly redefining UPE’s purpose, authority hierarchy, inputs/outputs, action boundary, or terminal audit schema. For UPE’s family-bound `5.6.r.p` scheme, that is a patch increment from `5.6.0.1` to draft `5.6.0.2`; the `5.6.1` line remains unconsumed.

For a generic two-part framework version `x.y`:

- compatible material improvement: `x.(y+1)`;
- breaking public-contract change: `(x+1).0` by default;
- no defensible safe material gain: keep `x.y` and return `NO_RELEASE`.

If a framework explicitly defines `(x+1).y`, follow and record that convention rather than silently mixing schemes.

## Migration from v5.6.0.1

1. Replace the Project Instructions kernel with `02_UPE_v5.6.0.2_PROJECT_INSTRUCTIONS_KERNEL.md`.
2. Replace the full reference, portable kernel, runtime profile, capability scan, registry, state, and eval files.
3. Add `13_WEB_WORK_NATIVE_SUBAGENT_ADAPTER.md` to project sources.
4. Replace the `upe-v5-6` skill as a unit; keep its stable discovery name.
5. Run deterministic package validation.
6. Run general, terminal-audit, and Web Work adapter behavioral cases on normal/strongest/fallback routes.
7. Keep v5.6.0.2 labeled draft until its own independent/coordinator gates pass.

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
