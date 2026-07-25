# UPE v5.6.1 Release Pack

UPE v5.6.1 adds a terminal independent framework-audit and improvement gate while preserving the GPT-5.6 runtime target:

```text
v5.6.1 = GPT-5.6 runtime adapter + UPE revision 1
```

`CORE_CHANGE CC-5.6.1-01` requires a materially created or revised reusable framework to be frozen and reviewed by a qualifying independent, read-only worker before release. The worker must produce motivated findings, an evidence-anchored 0–50 baseline, improvement headroom, a calibrated projected delta, any empirical delta separately, a complete proposed revision, and a reasoned version decision.

## Start here

1. Paste `02_UPE_v5.6.1_PROJECT_INSTRUCTIONS_KERNEL.md` into Project Instructions.
2. Upload the full reference, runtime profile, capability scan, source map, and independent-worker contract as project files.
3. Use the portable kernel in smaller projects or constrained model routes.
4. Use `skill/upe-v5-6/` on Agent Skills-compatible surfaces.
5. Run deterministic validation and the representative behavioral evals.

## Independence rule

A reviewer is independent only when it did not author the candidate, receives a frozen evidence bundle rather than hidden author reasoning, has read-only candidate scope, and has no external side-effect authority. A same-context role switch is self-review and leaves the independent gate `UNKNOWN`.

The coordinator retains final authority: it accepts, modifies, or rejects each proposed change, reruns affected checks, assigns the release version, and preserves projected versus empirical claims.

## Contents

| File | Purpose |
|---|---|
| `01_UPE_v5.6.1_FULL_REFERENCE.md` | Durable manual, exact audit schema, scoring, delta, version, and integration contracts |
| `02_UPE_v5.6.1_PROJECT_INSTRUCTIONS_KERNEL.md` | Always-on kernel, hard-capped below 8,000 characters |
| `03_UPE_v5.6.1_PORTABLE_KERNEL.md` | Reduced cross-project/lower-tier kernel |
| `04_GPT_5.6_RUNTIME_PROFILE.md` | Dated model, effort, orchestration, and reviewer-route guidance |
| `05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md` | Capability discovery and selection procedure |
| `06_SOURCE_MAP.md` | Official source map and limits for volatile capability claims |
| `07_CHANGELOG_AND_MIGRATION.md` | v5.6.0 → v5.6.1 change and migration record |
| `08_EVAL_SUITE.md` | Human-readable regression and terminal-gate suite |
| `09_CAPABILITY_REGISTRY_TEMPLATE.yaml` | Persistent capability and independence-evidence template |
| `10_UPE_STATE_TEMPLATE.yaml` | Resume/checkpoint state template |
| `11_VALIDATION_REPORT.md` | Deterministic results and remaining behavioral evidence |
| `12_INDEPENDENT_FRAMEWORK_AUDITOR_IMPROVER.md` | Standalone worker invocation and exact output contract |
| `evals/acceptance_cases.yaml` | General machine-readable UPE acceptance cases |
| `evals/terminal_audit_cases.yaml` | Independent-gate and versioning cases |
| `skill/upe-v5-6/` | Self-contained skill with references, assets, evals, metadata, and validator |

## Validation

From the repository root:

```powershell
uv run python UPE_v5.6.1_RELEASE/skill/upe-v5-6/scripts/validate_package.py UPE_v5.6.1_RELEASE
uv run python scripts/validate_release.py UPE_v5.6.1_RELEASE --manifest UPE_v5.6.1_RELEASE/MANIFEST.json --normalize-text-eol
```

For the extracted skill alone:

```powershell
python scripts/validate_package.py .
```

Deterministic structural validation does not make the projected behavioral improvement empirical. Run the supplied cases on the lowest supported and strongest intended model routes before making that claim.
