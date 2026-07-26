# UPE v5.6.0.2 Web Work Native-Subagent Draft

UPE v5.6.0.2 integrates the existing terminal framework auditor with native Web Work subagent operations:

```text
v5.6.0.2 = GPT-5.6 runtime adapter + UPE line 0 + compatible patch 2
```

`RUNTIME_ADAPTER RA-5.6.0.2-01` adds a standard hidden-v1 → visible review → UPE-v2 → fresh post-review loop, explicit fast mode, hash-bound handoffs, bounded convergence, and honest degraded routes. Frozen v5.6.0.1 remains unchanged.

## Start here

1. Paste `02_UPE_v5.6.0.2_PROJECT_INSTRUCTIONS_KERNEL.md` into Project Instructions.
2. Upload the full reference, runtime profile, capability scan, source map, independent-worker contract, and Web Work adapter as project files.
3. Use the portable kernel in smaller projects or constrained model routes.
4. Use `skill/upe-v5-6/` on Agent Skills-compatible surfaces.
5. Run deterministic validation and the representative behavioral evals.

## Independence rule

A reviewer is independent only when it did not author the candidate, receives a frozen evidence bundle rather than hidden author reasoning, has read-only candidate scope, and has no external side-effect authority. The Web Work adapter separately records cognitive independence and technical isolation; the word “subagent” does not prove a sandbox.

The coordinator retains final authority: it accepts, modifies, or rejects each proposed change, reruns affected checks, assigns the release version, and preserves projected versus empirical claims.

## Version state

Published `5.6.0.1` remains frozen. This `5.6.0.2` package is an unpublished draft candidate. The `5.6.1` identifier remains reserved and blocked from Codex use without explicit user authorization.

## Contents

| File | Purpose |
|---|---|
| `01_UPE_v5.6.0.2_FULL_REFERENCE.md` | Durable manual, audit schema, Web Work route, scoring, delta, version, and integration contracts |
| `02_UPE_v5.6.0.2_PROJECT_INSTRUCTIONS_KERNEL.md` | Always-on kernel, hard-capped below 8,000 characters |
| `03_UPE_v5.6.0.2_PORTABLE_KERNEL.md` | Reduced cross-project/lower-tier kernel |
| `04_GPT_5.6_RUNTIME_PROFILE.md` | Dated model, effort, orchestration, and reviewer-route guidance |
| `05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md` | Capability discovery and selection procedure |
| `06_SOURCE_MAP.md` | Official source map and limits for volatile capability claims |
| `07_CHANGELOG_AND_MIGRATION.md` | v5.6.0.1 → v5.6.0.2 change and migration record |
| `08_EVAL_SUITE.md` | Human-readable regression and terminal-gate suite |
| `09_CAPABILITY_REGISTRY_TEMPLATE.yaml` | Persistent capability and independence-evidence template |
| `10_UPE_STATE_TEMPLATE.yaml` | Resume/checkpoint state template |
| `11_VALIDATION_REPORT.md` | Deterministic results and remaining behavioral evidence |
| `12_INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md` | Standalone worker invocation and exact output contract |
| `13_WEB_WORK_NATIVE_SUBAGENT_ADAPTER.md` | Native Work state machine, modes, envelopes, exits, and fallbacks |
| `evals/acceptance_cases.yaml` | General machine-readable UPE acceptance cases |
| `evals/terminal_audit_cases.yaml` | Independent-gate and versioning cases |
| `evals/web_work_native_subagent_cases.yaml` | Native Work activation, workflow, convergence, and negative cases |
| `skill/upe-v5-6/` | Self-contained skill with references, assets, evals, metadata, and validator |

## Validation

From the repository root:

```powershell
python UPE_v5.6.0.2_WEB_WORK_NATIVE_SUBAGENT_DRAFT/skill/upe-v5-6/scripts/validate_package.py UPE_v5.6.0.2_WEB_WORK_NATIVE_SUBAGENT_DRAFT
```

For the extracted skill alone:

```powershell
python scripts/validate_package.py .
```

Deterministic structural validation does not make the projected behavioral improvement empirical. Run the supplied cases on the lowest supported and strongest intended model routes before making that claim.
