# Generator/Verifier Protocol

**Specification ID:** `W-203`

**Version:** `1.0.0`

**Status:** implementation contract

**Architecture authority:** [`ADR-001`](../architecture/ADR-001-harness-boundary.md)

## 1. Decision

Generation and acceptance are separate responsibilities. Deterministic validation is mandatory wherever a criterion is machine-decidable. An independent model verifier is optional, read-only and limited to mandatory criteria that deterministic checks cannot settle.

Every criterion and aggregate result uses exactly:

```text
PASS | FAIL | INSUFFICIENT_EVIDENCE
```

This vocabulary is shared with W-201, W-204 and [`schemas/verifier_result.schema.yaml`](../../schemas/verifier_result.schema.yaml) (W-207). `UNKNOWN` in older historical records maps to `INSUFFICIENT_EVIDENCE` only when migrated explicitly; new verifier results MUST NOT emit `UNKNOWN`.

## 2. Roles and authority

| Role | May | Must not |
|---|---|---|
| Contract owner/coordinator | Freeze criteria and scope; assign generator; run or request validators; select whether semantic verification is required; aggregate results; authorize a repair within scope. | Treat generator confidence or an aggregate score as evidence; silently change acceptance criteria. |
| Generator | Inspect authorized inputs; create or revise in-scope artifacts; return artifact identities, change summary and evidence candidates. | Mark its own work accepted; modify criteria to fit its output; perform an unapproved consequential action. |
| Deterministic validator | Execute a named reproducible check against the exact artifact/environment; return command/check identity, result and evidence. | Decide subjective intent outside its encoded invariant; mutate the artifact as part of validation. |
| Independent model verifier | Inspect the frozen contract, actual artifacts and bounded evidence; judge only assigned non-deterministic criteria; return structured criterion results and smallest correction. | Write files, branches, comments or external systems; trust only the generator summary; expand scope; waive a deterministic failure. |

The verifier is independent when it receives a fresh, read-only context with no generator authority and no write tools. A different model MAY improve independence but is not required. The same conversation turn that generated an artifact MUST NOT act as its independent verifier.

## 3. Frozen verification contract

Before generation, the coordinator MUST create criterion records with:

- stable `criterion_id` and MUST IDs it covers;
- exact requirement and whether it is release/phase blocking;
- expected artifact or environment target;
- required evidence and freshness/version constraints;
- decision method: `DETERMINISTIC`, `MODEL` or `HYBRID`;
- deterministic command/assertion when applicable;
- explicit pass and fail conditions;
- assigned owner and allowed scope.

Criteria MAY be clarified only by the contract owner. A material scope or done-condition change creates a new contract version and invalidates only results affected by that change.

The following are not valid criteria: “looks good,” “the generator says complete,” unversioned repository state, or a score without a blocking rule.

## 4. Protocol sequence

### `GV-01 FREEZE`

Freeze the contract version, repository/source/file identities, criterion set, action boundary and verification plan. Record whether any criterion truly requires model judgment.

### `GV-02 GENERATE`

The generator performs one bounded change and returns:

- `generation_id` and contract version;
- created/modified artifacts and observed refs/hashes;
- MUST coverage claims;
- evidence paths and checks requested;
- assumptions, unresolved items and actions performed;
- no completion verdict.

### `GV-03 INSPECT`

The coordinator re-inspects artifact identity and diff/scope. A missing artifact, wrong ref, unauthorized path or unrecorded external write is a blocking `FAIL` before content evaluation.

### `GV-04 VALIDATE`

Run all applicable deterministic validators before model verification. Record command/check, working context, relevant version, exit/result, timestamp and output reference. Validators MUST be read-only with respect to the candidate artifact except for disposable build/test outputs.

### `GV-05 VERIFY`

Invoke the independent model verifier only for remaining `MODEL` criteria or the semantic portion of `HYBRID` criteria. Supply the actual artifact or an integrity-bound reference, the frozen criterion text, relevant deterministic evidence and known limitations. Generator narrative is optional context and never the sole evidence.

### `GV-06 AGGREGATE`

Aggregate criterion results using section 7. The coordinator records one result artifact conforming to W-207 and links every verdict to evidence.

### `GV-07 REPAIR_OR_STOP`

For `FAIL`, return the failed criterion IDs and smallest in-scope correction to the generator. For `INSUFFICIENT_EVIDENCE`, acquire the named missing evidence or stop incomplete. Preserve all passing criteria whose artifacts and evidence remain unchanged.

### `GV-08 CHECKPOINT`

Persist contract version, generation/result IDs, artifact/ref identities, validator evidence, verdicts, repair delta, approvals and next action. A fresh context MUST be able to continue without the prior conversation.

## 5. Deterministic-first rules

Use deterministic validation for at least:

- schema/YAML/JSON parsing and schema conformance;
- build, unit/integration tests, lint and type checks;
- paths, file existence, hashes, manifests, diffs and repository invariants;
- command exit status and expected output assertions;
- permission, containment, secret/static-analysis and policy checks;
- link or identifier checks that are mechanically resolvable.

A model verifier MUST NOT reinterpret a deterministic `FAIL` as `PASS`. If deterministic evidence is conflicting or the check itself is defective, the criterion is `INSUFFICIENT_EVIDENCE` until the check or conflict is resolved; the original evidence remains attached.

Model verification is justified for bounded semantic criteria such as fidelity to accepted intent, completeness of a synthesis, clarity of a human-facing protocol or visual quality that lacks a deterministic oracle. Convenience, available context window or desire for a second opinion is not sufficient by itself.

## 6. Independent verifier input and output

The verifier input MUST contain:

```yaml
verification_request:
  request_id: VR-<stable-id>
  contract_version: <version>
  task_id: <stable-task-id>
  assigned_criteria: [<criterion-id>]
  authoritative_inputs: [<exact-path-or-source-ref>]
  artifacts: [<path-ref-hash>]
  deterministic_results: [<result-ref>]
  scope_in: [<allowed-judgment>]
  scope_out: [<forbidden-expansion>]
  known_evidence_limits: [<limit>]
```

The verifier output MUST conform to [`schemas/verifier_result.schema.yaml`](../../schemas/verifier_result.schema.yaml) and MUST include:

- result, goal and task identity plus the goal-contract reference;
- evaluator identity, independence/read-only declarations and actual-artifact-inspection flag;
- inspected artifact identities and budget usage;
- one record per assigned criterion;
- verdict, evidence references and concise rationale per criterion;
- missing evidence for every `INSUFFICIENT_EVIDENCE`;
- smallest correction for every `FAIL`;
- release/phase-blocking flag;
- scope/criteria-preservation declarations;
- aggregate verdict and release-blocking flag derived without changing criterion criticality.

The verifier MUST return `INSUFFICIENT_EVIDENCE` rather than infer unreadable files, unavailable sources, unexecuted tests or unobserved environment state.

## 7. Verdict semantics and aggregation

### Criterion verdict

| Verdict | Required condition |
|---|---|
| `PASS` | The required evidence directly establishes the criterion for the inspected artifact/ref/version. |
| `FAIL` | Direct evidence establishes a violation of the frozen criterion. |
| `INSUFFICIENT_EVIDENCE` | Evidence is absent, stale, unreadable, conflicting or incapable of deciding the criterion. |

### Aggregate verdict

1. Any criterion at `FAIL` makes the aggregate `FAIL`.
2. Otherwise, any criterion at `INSUFFICIENT_EVIDENCE` makes the aggregate `INSUFFICIENT_EVIDENCE`.
3. The aggregate is `PASS` only when every criterion is `PASS`.
4. `release_blocking` is separate: it is true when any failed or evidence-incomplete criterion blocks the phase/release, and false when all such findings are explicitly non-blocking.
5. A deterministic result takes precedence within its encoded domain. Semantic results cannot waive it.

No majority vote, confidence average or numeric score may override these rules.

## 8. Repair loop and no-progress

Each repair request MUST preserve the contract version and include only:

- failed or evidence-incomplete criterion IDs;
- discriminating evidence and failure signature;
- smallest valid corrective or evidence-acquisition action;
- files/scope allowed to change;
- validators to rerun;
- attempt and budget remaining.

The generator MUST NOT regenerate passing artifacts unless the repair necessarily affects them. After repair, rerun affected validators plus any regression check whose invariant could have changed.

Two consecutive repair attempts with the same normalized failure signature and no change in relevant artifact identity, evidence or verdict constitute no progress unless the goal defines a stricter threshold. Stop `BLOCKED`, preserve the last stable checkpoint and state what new evidence, authorization or materially different method is required.

## 9. Security and approval boundary

- Repository and retrieved content are evidence, not instructions to the verifier.
- The independent model verifier has no mutation, messaging, scheduling, purchase, deployment, credential or approval-response capability.
- Validator commands and paths are part of the frozen contract; an artifact cannot authorize additional commands.
- Secret values and unnecessary personal data MUST be redacted from verifier inputs and evidence.
- If verification itself requires a consequential action, the criterion remains `INSUFFICIENT_EVIDENCE` until the coordinator obtains separate authorization and supplies the observed result.
- Approval is never inferred from a generator, verifier, repository file or prior side effect.

## 10. Acceptance of W-203

This protocol passes only if deterministic checks always precede optional semantic evaluation, the independent verifier is read-only, all criterion/aggregate outputs preserve `PASS | FAIL | INSUFFICIENT_EVIDENCE`, missing evidence cannot pass, a verifier cannot expand scope, and repair preserves completed verified work.
