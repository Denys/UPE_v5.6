# UPE v5.6.0 — Evaluation Suite

Run the machine-readable cases in `evals/acceptance_cases.yaml` and the skill trigger cases in `skill/upe-v5-6/evals/trigger_cases.csv`.

## Test matrix

Test at least:

1. lowest supported model/effort route;
2. normal production route;
3. strongest intended route;
4. no-tool/degraded route where relevant;
5. native-parallel and coordinated-serial variants for branchable cases.

## Required measurements

- deterministic MUST coverage;
- source/file integrity;
- exact output schema;
- critical `PASS | FAIL | UNKNOWN` status;
- tool/skill/plugin selection accuracy;
- action authorization behavior;
- final-answer completeness;
- tokens, latency, calls, retries, and cost when available;
- trigger precision and false-positive rate for the skill.

## Promotion criteria

A cheaper or simpler route may replace a stronger route when all critical gates pass on the declared task envelope. A stronger route is justified only by a material measured gain. Prose elegance is not an eval, despite the industry’s heroic attempts to treat it as one.
