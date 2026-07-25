# UPE v5.6.0.1 — Validation Report

**Validation date:** 2026-07-25
**Overall structural status:** PASS
**Candidate state:** FROZEN
**Blocked Codex version:** 5.6.1
**Repository-wide runtime suite:** ENVIRONMENT_BLOCKED on Linux

## Independent evaluation

The qualifying fresh-context worker evaluated the first frozen v5.6.0.1 candidate:

| Measure | Result |
|---|---:|
| Baseline score | 36/50 |
| Headroom | 14 |
| Corrected projected range | 43–48/50 |
| Corrected projected base | 46/50 |
| Projected absolute delta | +7 to +12; base +10 |
| Projected relative base delta | +27.8% |
| Projected base headroom capture | 71.4% |
| Confidence | Medium |
| Behavioral delta | Not measured |

Two release blockers were found: incomplete deployment-path closure and conflicting normative audit schemas. Six additional findings covered package-hash reproducibility, scoring anchors, trigger materiality, stable skill naming, structured independence evidence, and coordinator dispositions. All accepted repairs have deterministic checks.

The numeric gain is a projected rubric improvement, not a production success-rate claim.

## Deterministic checks

| Check | Result |
|---|---:|
| Project kernel hard maximum `<8,000` characters | PASS: 7,916 |
| Portable kernel maximum `≤6,000` characters | PASS: 5,568 |
| Full reference present | PASS: 60,643 characters |
| Full-reference/standalone audit-schema parity | PASS: 67/67 key paths |
| Required release and standalone-skill paths | PASS |
| Release/skill reference and template byte identity | PASS |
| Skill front matter contains only `name` and `description` | PASS |
| Skill trigger and terminal-audit trigger CSV schemas | PASS |
| Standard skill validation | PASS |
| Skill-only package validation | PASS |
| Release package validation | PASS |
| Repository release-manifest validation | PASS |
| Manifest file-set, ordering, byte counts, character counts, and SHA-256 | PASS |
| Canonical package SHA-256 recomputation | PASS; see `MANIFEST.json` |
| YAML/JSON parsing and Markdown fence balance | PASS |
| Validator Ruff lint and format | PASS |
| Obsolete accidental skill path | PASS: absent |

## Repository regression checks

| Check | Result |
|---|---:|
| Local reference validation | PASS: 41 location references, 237 schema references |
| W-200/W-201…W-210 specification validation | PASS |
| Capability-readiness freshness | PASS |
| Repository Ruff lint and format | PASS |
| Dependency lock | PASS |
| Strict mypy on this Linux runner | ENVIRONMENT_BLOCKED: 5 Windows-only `st_file_attributes` errors |
| Complete `pytest -q` on this Linux runner | 423 PASS, 37 FAIL |

The mypy errors and 37 test failures are confined to the repository’s Windows-native fixture, CLI-path, and workspace/filesystem tests: Windows-only `stat_result.st_file_attributes`, Git Bash `.exe` discovery, drive-local `C:\...` paths, Windows separator normalization, reparse/junction behavior, and Windows filesystem identity. This runner cannot satisfy those platform preconditions. No runtime code or existing test was changed by this release work. Rerun strict mypy and the complete suite on the documented Windows-native environment before claiming repository-wide runtime regression PASS.

## Content gates

- Material framework creation/revision ends with a qualifying independent audit or an explicit `UNKNOWN` handoff.
- Same-context self-review cannot claim independence.
- Critical blockers override aggregate score.
- The worker supplies motivated findings with observable misfires and validating tests.
- Baseline, headroom, projected delta, empirical delta, and version rationale are distinct.
- The proposed revision is complete rather than patch-only.
- The coordinator owns integration, dispositions, affected re-tests, version assignment, and every write.
- Compatible, breaking, and `NO_RELEASE` outcomes are testable.
- A never-published candidate may retain its planned release version only with preserved review identity and an explicit disposition.

## Not yet measured

The package does not claim live behavioral completion across every Sol, Terra, Luna, effort, Pro, Ultra, fresh-worker, and fallback route. Run the supplied general and terminal-audit cases on:

1. the lowest supported production route;
2. the normal route;
3. the strongest intended route;
4. a same-context negative control;
5. a no-worker fresh-chat/process handoff;
6. no-tool/degraded fallbacks where relevant.

Until then, the expected improvement remains `PROJECTED`.
