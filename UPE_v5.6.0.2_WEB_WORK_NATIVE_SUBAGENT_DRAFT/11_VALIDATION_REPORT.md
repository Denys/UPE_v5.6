# UPE v5.6.0.2 — Draft Validation Report

**Validation date:** 2026-07-26  
**Candidate state:** DRAFT  
**Frozen published baseline:** v5.6.0.1  
**Blocked Codex version:** v5.6.1  
**Scope:** `web_work_native_subagent` integration  
**Overall structural status:** PASS for the frozen candidate  
**Behavioral status:** NOT RUN

## Integration result

The draft adds one compatible surface adapter without modifying the frozen v5.6.0.1 package:

- standard mode: hidden frozen v1 → Reviewer 1 → visible validated review payload → UPE dispositions/rework → published v2 → fresh Reviewer 2;
- fast mode: immediate `DRAFT_UNAUDITED` v1 with no formal-release bypass;
- one hash-bound review payload is both shown and passed unchanged to UPE;
- Reviewer 1 and Reviewer 2 remain proposal-only; UPE/coordinator owns every disposition, write, version, and final publication;
- negligible-gain, material-gain, blocker-repair, and round-limit exits are quantified;
- user steering invalidates stale reviewed hashes;
- hooks/heartbeats are limited to lifecycle/liveness and are not content transport;
- cognitive independence, candidate integrity, action authority, and technical isolation are recorded separately.

## Grounding

Official documentation verified on 2026-07-26 describes subagent delegation on supported Work/Codex routes and Ultra’s use of subagents. The adapter does not infer actual current-run operations, context controls, a per-child sandbox, or a reviewer tool allowlist from product documentation alone. Runtime activation requires exposed fresh-child spawn and result-return operations.

## Deterministic checks

| Check | Result |
|---|---:|
| Active kernel maximum `<8,000` characters | PASS: 7,997 |
| Portable kernel maximum `≤6,000` characters | PASS: 5,996 |
| Full-reference/standalone audit-schema parity | PASS: 67/67 key paths |
| Web Work adapter eval case shape and IDs | PASS: W01–W17 |
| Standard/fast markers and convergence thresholds | PASS |
| YAML parsing and Markdown fence balance | PASS |
| Skill front matter and trigger CSV schema | PASS |
| Release/skill canonical-copy identity | PASS |
| Required release/skill paths | PASS |
| Manifest file set/hash/package hash | PASS: canonical payload count and hash recorded in `MANIFEST.json` |

## Behavioral evidence

`evals/web_work_native_subagent_cases.yaml` is deliberately labeled `NOT_RUN`. It specifies activation, publication behavior, candidate/payload integrity, independence downgrade, rework ownership, fresh post-review, convergence, fast mode, steering, and heartbeat negative cases.

Deterministic validation does not establish:

- that every eligible Work account exposes the same native operations;
- that the complete hidden-v1 → review → v2 → post-review loop passes on each intended model/effort route;
- that a native child has a separate security sandbox or tool allowlist;
- empirical task-quality, latency, token, or cost improvement.

## Independent audit

Reviewer 1 ran in a fresh child context against the frozen candidate. The review was cognitively independent but advisory: the child shared a host path that was technically writable, so strict `audit_status` remained `UNKNOWN`. It scored the candidate **41/50** and projected a repaired range of **44–48/50**, with a base estimate of **46/50** and medium confidence. Behavioral gains remain `PROJECTED`.

The coordinator accepted all four findings:

| ID | Disposition | Integrated repair | Affected checks |
|---|---|---|---|
| F01 | ACCEPT | Bind the complete stored, surfaced, and UPE-rework review payload to identical SHA-256 values. | W04; adapter markers; registry/state schema |
| F02 | ACCEPT | Make spawn, result return, fresh context, and immutable/inline candidate transport mandatory; classify lifecycle controls as preferred with bounded fallback. | W01; activation contract |
| F03 | ACCEPT | Replace stale manifest-pending wording with regenerated-candidate status. | Release validator; manifest verification |
| F04 | ACCEPT | Clarify fast-mode formal-release continuation, automatic-round accounting, exact v2 binding, and review history. | W09, W12, W15; state schema |

Because a Work child may share host filesystem permissions, every audit must report cognitive independence and technical isolation separately and must not overclaim security-grade isolation. A shared-writable-path review remains advisory and leaves the terminal gate `UNKNOWN`.

## Release boundary

This package is a reviewable draft, not a merged/tagged/released/deployed UPE version. Formal release requires:

1. manifest regeneration and deterministic PASS after any accepted review change;
2. terminal reviewer findings and UPE coordinator dispositions;
3. affected re-tests;
4. representative behavioral execution or an explicit `PROJECTED/NOT_RUN` limitation;
5. explicit user authorization for any GitHub write, merge, tag, release, or deployment.
