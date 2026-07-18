# UPE v5.6.0 — Release Notes, Migration, and Change Control

## Executive decision

UPE v5.6.0 is not a fashionable rewrite of the core. It is a controlled migration of the UPE lineage to GPT-5.6:

- v4.1 supplied the hybrid kernel/reference/state architecture;
- v4.3 supplied the complete MUST ledger, adaptive branch/merge contract, serial Ultra emulation, merge gates, and cross-tier acceptance suite;
- v5.6.0 freezes those durable invariants and adds a GPT-5.6 runtime adapter, capability/plugin discovery, skill packaging, and stronger placement/eval rules.

## Versioning rule

```text
UPE v<target GPT major>.<target GPT minor>.<UPE patch>
```

Examples:

- `v5.6.0`: first UPE release adapted to GPT-5.6;
- `v5.6.1`: UPE correction or improvement while targeting GPT-5.6;
- `v5.7.0`: first runtime adaptation to GPT-5.7;
- `CORE_CHANGE`: explicit label required when a durable behavioral invariant changes.

Published release files are immutable: any redistributed content change increments the UPE patch. A private verification note may update a last-checked date without a release, but its change type remains `RUNTIME_PROFILE`, not `CORE_CHANGE`.

## Preserved core

- minimal scaffold first;
- hybrid kernel + full reference + state;
- authority/evidence separation and prompt-injection resistance;
- current-source and file-integrity rules;
- action governance and least privilege;
- complete MUST ledger;
- direct/native-parallel/coordinated-serial adapters;
- evidence-based merge, no majority vote;
- `PASS | FAIL | UNKNOWN` gates;
- sequential recovery without restarting successful work;
- eval-driven change control.

## Added in v5.6.0

1. **Model-aligned versioning** with a separate UPE patch number.
2. **Stable-core charter** and explicit `CORE_CHANGE` governance.
3. **Prompt Stack Compiler:** rules are placed in kernel, reference, skill, project data, tool schema, state, or eval rather than piled together.
4. **Capability Opportunity Scan:** every reusable prompt/project is checked for useful tools, installed skills/plugins, connectors, MCP, artifacts, code/data, browser, agents, and schedules.
5. **Two-layer routing:** cognitive adapter and tool adapter are selected independently.
6. **GPT-5.6 profile:** Sol/Terra/Luna, effort, pro mode, Ultra/multi-agent, PTC, tool search, lean prompting, and artifact fidelity are separated and dated.
7. **Cross-tier operationalization:** lower-effort Sol, Terra, and Luna use bounded stages, narrow inputs, exact schemas, deterministic tools, checkpoints, and verifier gates.
8. **Skill package:** progressive-disclosure `SKILL.md`, references, validation script, trigger evals, and acceptance suite.
9. **Artifact/reference fidelity contract** for documents, spreadsheets, slides, PDFs, UI, and templates.
10. **Plugin/tool false-positive controls:** relevant capability is selected, irrelevant capability is explicitly avoided.

## Corrected from v4.3

- Removed “Pro defaults to Sol + Ultra” from permanent doctrine. Ultra is selected only for cleanly branchable work and only when exposed.
- Removed plan labels as a proxy for capability. Surface and actual exposure govern.
- Replaced fixed branch counts in the kernel with task-shape and budget rules. Dated profiles may recommend ranges.
- Distinguished standard ChatGPT Sol Pro, API pro mode, reasoning effort, `max`, and Ultra orchestration.
- Added direct/tool-search/PTC/UI tool routing so “use more tools” no longer masquerades as strategy.
- Added negative selection: capabilities may be `Avoid/Disable`, not merely enabled because the settings page contains a checkbox.

## Migration from v4.1/v4.3

1. Paste `02_UPE_v5.6.0_PROJECT_INSTRUCTIONS_KERNEL.md` into Project Instructions.
2. Upload `01_UPE_v5.6.0_FULL_REFERENCE.md`, `04_GPT_5.6_RUNTIME_PROFILE.md`, `05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md`, and `06_SOURCE_MAP.md` as project files.
3. Use `03_UPE_v5.6.0_PORTABLE_KERNEL.md` in projects with tighter instruction budgets or lower-tier models.
4. Install the `upe-v5-6` skill where the Agent Skills format is supported.
5. Run the eval suite on the lowest supported route and the strongest intended route.
6. Preserve project-specific domain instructions and sources outside UPE; UPE is the control system, not the domain encyclopedia.

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

## Promotion rule

A change may enter the kernel only when it is:

- broadly applicable across UPE tasks;
- stable across product surfaces or expressed capability-conditionally;
- short enough to justify permanent context cost;
- linked to a real failure mode;
- not better placed in a skill, reference, tool description, state file, or eval;
- validated on representative positive and negative cases.
