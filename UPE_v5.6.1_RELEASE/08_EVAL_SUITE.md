# UPE v5.6.1 — Evaluation Suite

Run:

- `evals/acceptance_cases.yaml` for general UPE behavior;
- `evals/terminal_audit_cases.yaml` for independence, scoring, delta, versioning, and integration;
- `skill/upe-v5-6/evals/trigger_cases.csv` for UPE skill invocation;
- `skill/upe-v5-6/evals/terminal_audit_trigger_cases.csv` for the terminal-gate materiality decision.

## Test matrix

Test at least:

1. lowest supported model/effort route;
2. normal production route;
3. strongest intended route;
4. no-tool/degraded route where relevant;
5. fresh delegated worker and separate-chat/process fallback;
6. same-context negative control;
7. native-parallel and coordinated-serial variants where relevant.

## General measurements

- deterministic MUST coverage;
- source/file integrity;
- exact output schema;
- critical `PASS | FAIL | UNKNOWN` status;
- tool/skill/plugin selection accuracy;
- action authorization behavior;
- final-answer completeness;
- tokens, latency, calls, retries, and cost when available;
- skill-trigger precision and false-positive rate.

## Terminal-gate measurements

- correct material/non-material/pending trigger classification;
- qualifying independence with zero false `PASS` on shared/unknown/write-capable routes;
- blocker detection despite a high aggregate score;
- anchored dimension scores with evidence notes;
- arithmetic consistency for baseline, headroom, absolute/relative delta, and headroom capture;
- projected versus empirical separation;
- complete revision and change map;
- correct compatible, breaking, and `NO_RELEASE` version decision;
- exactly one coordinator disposition and affected re-test result per proposed change.

## Promotion criteria

A release passes only when:

- deterministic structural checks pass;
- all critical contract/evidence/safety gates pass;
- the independent route qualifies or the release is explicitly partial with an `UNKNOWN` gate and a complete handoff;
- no critical blocker is overridden by a numeric score;
- empirical claims are backed by representative executed evals.

A cheaper or simpler route may replace a stronger route only when all critical gates pass on the declared envelope. Prose quality alone is not an eval.
