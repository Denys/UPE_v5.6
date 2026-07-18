# UPE v5.6.0 Release Pack

UPE v5.6.0 aligns UPE version numbering with the target GPT model family and adds a separate UPE patch number:

```text
v5.6.0 = GPT-5.6 runtime adapter + UPE revision 0
```

The release keeps the long-lived UPE core stable while updating model-specific execution, tool/plugin discovery, skills, and evals.

## Start here

1. Paste `02_UPE_v5.6.0_PROJECT_INSTRUCTIONS_KERNEL.md` into Project Instructions.
2. Upload the full reference, runtime profile, capability scan, and source map as project files.
3. Use the portable kernel in smaller projects or constrained model routes.
4. Install `skill/upe-v5-6/` on Agent Skills-compatible surfaces.
5. Run the validation script and representative evals.

## Contents

| File | Purpose |
|---|---|
| `01_UPE_v5.6.0_FULL_REFERENCE.md` | Durable manual, contracts, routing, templates, acceptance suite |
| `02_UPE_v5.6.0_PROJECT_INSTRUCTIONS_KERNEL.md` | Always-on kernel, hard-capped below 8k characters |
| `03_UPE_v5.6.0_PORTABLE_KERNEL.md` | Reduced cross-project/lower-tier kernel |
| `04_GPT_5.6_RUNTIME_PROFILE.md` | Dated Sol/Terra/Luna, effort/mode/orchestration guidance |
| `05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md` | Tool, skill, plugin, connector, MCP selection procedure |
| `06_SOURCE_MAP.md` | Official OpenAI source map for volatile claims |
| `07_CHANGELOG_AND_MIGRATION.md` | Changes from v4.1/v4.3 and version governance |
| `08_EVAL_SUITE.md` | Human-readable regression suite |
| `09_CAPABILITY_REGISTRY_TEMPLATE.yaml` | Persistent inventory of actual tools, skills, plugins, connectors, permissions, and fallbacks |
| `10_UPE_STATE_TEMPLATE.yaml` | Resume/checkpoint state template |
| `11_VALIDATION_REPORT.md` | Deterministic validation results and remaining live-eval work |
| `evals/acceptance_cases.yaml` | Machine-readable acceptance cases |
| `skill/upe-v5-6/` | Portable Agent Skill with scripts, references, assets, and evals |

## Design verdict

The key shift is not “use the strongest model.” It is:

> Preserve one stable contract and choose model, effort, mode, orchestration, tools, skills, plugins, and fallbacks independently according to task shape and actual exposure.

That lets lower-effort Sol, Terra, and Luna execute a clean serial control structure without pretending they have Sol Pro/Ultra compute, while stronger configurations spend their advantage on ambiguity, branching, synthesis, and verification rather than on restating the prompt in baroque prose.
