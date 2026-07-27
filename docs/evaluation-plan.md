# Harness evaluation plan

## Objective

The harness decides completion from evidence, not from a generator's final
message. This plan describes the implemented validation/evaluation path at
`origin/main` `c8370a53b2d1b5cdf4c5f448ad7aae9c34a412dd`, observed on
2026-07-27.

The evaluation order is fixed:

```text
frozen criteria and commands
  -> deterministic validation
  -> optional read-only model evaluation for unresolved semantic criteria
  -> checkpoint
  -> explicit completion evidence
```

## Verdicts and precedence

New criterion and evaluator results use:

- `PASS`: the criterion is supported by inspected evidence;
- `FAIL`: a concrete requirement failed; and
- `INSUFFICIENT_EVIDENCE`: the required observation is missing, unreadable,
  stale, malformed, timed out, or otherwise inconclusive.

Aggregate deterministic precedence is `FAIL`, then
`INSUFFICIENT_EVIDENCE`, then all-`PASS`. A phase gate may still use
`UNKNOWN`, but model and validator results do not.

Deterministic `FAIL` cannot be downgraded by a model. Deterministic
`INSUFFICIENT_EVIDENCE` cannot be waived by a model. A model evaluator is
invoked only when deterministic validation is `PASS` and the frozen request
contains mandatory semantic criteria that deterministic checks cannot settle.

## Deterministic validation

[`validation.py`](../src/harness/validation.py) requires a frozen structured
validator command and checks, before process execution:

- exact Run/Task identity and `VALIDATING` state;
- exact selected workspace;
- criterion IDs limited to the task;
- exact command identity and order from `Task.validation_commands`; and
- bounded timeout and output policy.

The process runner uses an explicit argument vector, exact cwd, explicit
environment, and `shell=False`. Standard output and error are stored as bounded
binary artifacts. Structured evidence contains metadata and relative
`LocationReference` records, not captured output.

Normalization is:

| Observation | Verdict |
|---|---|
| Exit code 0 within bounds | `PASS` |
| Nonzero exit | `FAIL` / `NONZERO_EXIT` |
| Timeout with any partial output retained by reference | `INSUFFICIENT_EVIDENCE` |
| Process start/I/O error | `INSUFFICIENT_EVIDENCE` |
| Malformed process result | `INSUFFICIENT_EVIDENCE` |
| Output exceeds configured limit | `INSUFFICIENT_EVIDENCE` |
| Evidence artifact cannot be written | no passing evidence is produced |

Only an all-`PASS` batch can create the finalization evidence consumed by the
orchestrator.

## Optional model evaluator

[`evaluation.py`](../src/harness/evaluation.py) exposes one read-only evaluator
port. The request and result are frozen value records containing criteria and
location references; no filesystem, subprocess, network, persistence, approval,
or write handle is supplied.

The evaluator must:

- declare itself independent from the generator and `READ_ONLY`;
- preserve criterion IDs, order, statements, and mandatory flags exactly;
- evaluate only mandatory unresolved semantic criteria;
- use only supplied evidence references;
- limit correction targets to candidate artifacts;
- report actual-artifact inspection for any `PASS` or `FAIL`; and
- preserve `PASS`, `FAIL`, and `INSUFFICIENT_EVIDENCE`.

Rewritten, removed, added, or reordered criteria are protocol errors.
Evidence/correction scope expansion is rejected. An all-insufficient result may
truthfully state that no artifact could be inspected.

There is no real model evaluator implementation in v0. A future implementation
must add a host-enforced read-only execution boundary; the interface alone is
not a security sandbox.

## Acceptance matrix

| Case | Expected result | Primary tests |
|---|---|---|
| Passing exact validator command | Bounded referenced output and `PASS` | [`test_validation.py`](../tests/unit/test_validation.py) |
| Scope, workspace, task, or command mismatch | Reject before process execution | [`test_validation.py`](../tests/unit/test_validation.py) |
| Nonzero validator | `FAIL`; no model override | [`test_validation.py`](../tests/unit/test_validation.py), [`test_evaluation.py`](../tests/unit/test_evaluation.py) |
| Timeout, execution error, malformed result, or overflow | `INSUFFICIENT_EVIDENCE` with normalized kind | [`test_validation.py`](../tests/unit/test_validation.py) |
| Deterministic pass and no semantic criterion | Evaluator call count remains zero | [`test_evaluation.py`](../tests/unit/test_evaluation.py) |
| Deterministic pass with frozen semantic criterion | Preserve evaluator verdict and criteria | [`test_evaluation.py`](../tests/unit/test_evaluation.py) |
| Rewritten criteria or expanded evidence/correction refs | Protocol rejection | [`test_evaluation.py`](../tests/unit/test_evaluation.py) |
| Provider says “done” without evidence | Run stops at `VALIDATING` | [`test_lifecycle.py`](../tests/unit/test_lifecycle.py) |
| Passing validation without checkpoint/evidence | Completion rejected | [`test_lifecycle.py`](../tests/unit/test_lifecycle.py) |
| SQLite/JSONL interruption or conflicting replay | Deduplicate exact replay or fail closed | [`test_state_store.py`](../tests/unit/test_state_store.py), [`test_events.py`](../tests/unit/test_events.py) |
| Budget/retry/no-progress boundaries | Exact stop/retry decision without I/O | [`test_budgets.py`](../tests/unit/test_budgets.py), [`test_retry_policy.py`](../tests/unit/test_retry_policy.py) |
| Approval, command, path, network, and redaction negatives | Deny or redact without effect | [`test_approvals.py`](../tests/unit/test_approvals.py), [`test_permissions.py`](../tests/unit/test_permissions.py) |
| App Server terminal notification shapes | Schema-defined correlation, one terminal, fail closed on conflict | [`test_codex_adapter.py`](../tests/unit/test_codex_adapter.py) |

The broader acceptance-case catalogue is
[`work_loop_acceptance_cases.yaml`](../evals/work_loop_acceptance_cases.yaml).
Its `execution_status` fields are not evidence that a case has run; only current
test output is.

## C-410 documentation gate

C-410 is accepted only when all four declared outputs exist and:

1. internal Markdown links resolve;
2. setup, operation, recovery, approvals, and limitations match source;
3. documentation/reference validators pass;
4. the focused C-401–C-409/C-505 unit suites pass;
5. the complete repository suite and static gates pass; and
6. the current diff is limited to the four C-410 documents.

The exact local commands are listed in
[`operations.md`](operations.md#documentation-and-development-validation).

## Exclusions and open evidence

- No live model, real external action, cleanup effect, or network request is
  part of C-410 validation.
- The corrected C-501 adapter is covered by deterministic unit tests, but the
  real App Server smoke remains C-502.
- PR #22 merged the C-501 terminal-notification correction, and C-410
  revalidated the current base with the complete repository suite. The
  canonical frontier therefore marks C-502 ready; executing its controlled
  live smoke still requires separate authorization and is not part of C-410.
- Restart/reconciliation is C-503 and integrated security is C-506.
- Python 3.12 and 3.13 remain unverified by the historical package gates; the
  current C-410 handoff must report the Python version actually used.

Historical package evidence is available in
[`C-404-GATE.yaml`](../validation/C-404-GATE.yaml) and
[`C-408-GATE.yaml`](../validation/C-408-GATE.yaml), but fresh command output is
required for this work package.
