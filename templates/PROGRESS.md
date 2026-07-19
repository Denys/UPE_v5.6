# Progress projection: <goal/run ID>

> Append-only human-readable projection. It does not replace SQLite/outbox state, validator output,
> or artifact identity. Never rewrite history to make an action appear authorized or successful.

## Current snapshot

- Canonical state reference/event sequence: `<ref or PRE_RUN>`
- Repository/ref/worktree: `<exact identities>`
- Active task/lifecycle state: `<IDs/state>`
- Last stable checkpoint: `<ref/hash>`
- Budgets used/remaining: `<values>`
- Pending approvals/actions: `<stable IDs or none>`
- Next action: `<one owner/action/preconditions>`

## Append-only iteration entries

### <RFC 3339 timestamp> — <iteration/attempt ID>

- Task and criterion IDs: `<IDs>`
- Baseline or prior failure signature: `<evidence>`
- Coherent change: `<summary and artifact refs>`
- Commands/checks and observed results: `<refs>`
- Verdict delta: `<PASS | FAIL | INSUFFICIENT_EVIDENCE by criterion>`
- External actions/approvals: `<stable IDs and observed results, or none>`
- Checkpoint: `<ref/hash>`
- Remaining delta and next action: `<one bounded step>`
