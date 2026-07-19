# Workflow: <stable goal ID>

> Template projection only. Once a host run exists, SQLite plus its transactional outbox is
> canonical. This file cannot advance lifecycle state, grant approval, or prove completion.

## Identity and authority

- Goal contract: `<repository-relative path or immutable reference>`
- Task/backlog IDs: `<IDs>`
- Contract version: `<version>`
- Repository/base/head/worktree: `<exact identities>`
- Active authority reference: `<user grant or none>`
- Latest stable checkpoint: `<path/ref/hash>`

## Objective and done condition

`<One bounded objective and observable environmental end state>`

## Scope

- Allowed paths: `<exact paths>`
- Locked paths: `<exact paths>`
- Non-goals: `<explicit exclusions>`
- Consequential actions: `<forbidden or exact granted classes/targets>`

## Frozen verification contract

| Criterion ID | Requirement | Method | Evidence required | Pass condition | Blocking |
|---|---|---|---|---|---|
| `<ID>` | `<requirement>` | `DETERMINISTIC | MODEL | HYBRID` | `<evidence>` | `<condition>` | `true` |

## Iteration

1. Revalidate repository, worktree, runtime, contract, approval, and budget identity.
2. Load canonical state/checkpoint and run the fast baseline.
3. Select and persist one ready task or one failed criterion.
4. Make one coherent allowed change.
5. Run deterministic validation, inspect the diff, and store evidence by reference.
6. Use the read-only evaluator only for assigned criteria that deterministic checks cannot settle.
7. Checkpoint, update projections, and choose continue, complete, block, approval, budget, failure,
   cancellation, or handoff explicitly.

## Limits and stops

- Iterations/time/tokens/cost/retries: `<limits>`
- No-progress threshold and signature: `<rule>`
- Stop on divergence, unsafe path, missing dependency/evidence, approval need, ambiguous external
  result, exhausted budget, or cancellation.

## Recovery

- Stable state authority/reference: `<SQLite path and sequence, or pre-run repository handoff>`
- Pending outbox/action records: `<refs or none>`
- Worktree/process/App Server reconciliation: `<required checks>`
- Items not to repeat: `<verified artifact/evidence IDs>`
- One next action: `<owner, action, preconditions, stop conditions>`
