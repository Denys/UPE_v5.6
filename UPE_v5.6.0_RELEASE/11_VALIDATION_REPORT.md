# UPE v5.6.0 — Validation Report

**Validation date:** 2026-07-18  
**Overall structural status:** PASS

## Deterministic checks

| Check | Result |
|---|---:|
| Project kernel hard maximum 8,000 characters | PASS: 7,749 characters |
| Preferred kernel window 7,200–7,800 | PASS |
| Portable kernel maximum 6,000 characters | PASS: 4,662 characters |
| Full reference present | PASS: 40,050 characters |
| Skill `SKILL.md` front matter | PASS |
| Skill includes clear trigger and non-trigger boundary | PASS |
| Skill ZIP contains one top-level folder | PASS |
| Release ZIP extracts cleanly | PASS |
| Release validator runs from extracted archive | PASS |
| Skill validator runs from extracted skill ZIP | PASS |
| YAML acceptance, capability-registry, and state files parse | PASS |
| Manifest includes SHA-256 hashes and file sizes | PASS |
| Unfinished placeholder markers | PASS: none found |

## Content gates reviewed

- Stable core is separated from dated GPT-5.6 product/model guidance.
- Surface, model tier, reasoning effort, pro mode, and orchestration are distinct.
- Sol Pro, API pro mode, `max`, and Ultra are not treated as one ladder.
- Capability discovery includes built-in tools, installed skills/plugins, apps/connectors/MCP, repositories, artifacts, browser/computer use, agents, PTC, and schedules.
- Capability selection requires `Required`, `Optional`, and `Avoid/Disable` rather than blindly enabling every shiny checkbox.
- Lower-tier adaptation preserves the MUST ledger, source/file integrity, action gates, exact schema, checkpoints, and critical acceptance.
- Native parallel work has a coordinated-serial fallback.
- External side effects remain centralized.
- PTC and multi-agent use are selected by task shape, not by availability alone.
- Reference-based artifacts require source-system inspection and structural/visual validation.

## Not yet measured

The package defines but does not claim completion of live behavioral evals across every Sol, Terra, Luna, effort, Pro, and Ultra configuration. Those require execution on the target surfaces with representative project tasks and cost/latency telemetry.

Do not promote a projected model-routing advantage to a measured claim until the same acceptance cases have been run on:

1. the lowest supported production route;
2. the normal route;
3. the strongest intended route;
4. no-tool/degraded fallbacks;
5. native-parallel and coordinated-serial variants where relevant.

## Recommended first v5.6.1 evidence

After 20–40 real UPE tasks, record:

- missed or silently weakened MUST constraints;
- false-positive and false-negative skill triggers;
- capability scan choices that changed the result;
- tools/plugins enabled but unused;
- cases where Terra or Luna passed the Sol acceptance envelope;
- cases where Pro/max/Ultra produced a material gain;
- repeated clarification, retry, or checkpoint failures;
- kernel rules that consumed context without fixing a measured failure.

Patch the runtime profile, skill, or evals first. Change the stable core only when the evidence survives the temptation to redesign everything after one memorable failure.
