# Blocker log: <goal/run ID>

> Append-only blocker projection. Missing evidence is not success. Resolved entries remain for
> recovery and no-progress detection.

## Active blockers

### <blocker ID> — <short title>

- Detected at: `<RFC 3339 timestamp>`
- Task/criterion IDs: `<IDs>`
- Category: `DEPENDENCY | IDENTITY | POLICY | APPROVAL | EVIDENCE | NO_PROGRESS | BUDGET | SAFETY`
- State: `ACTIVE`
- Direct evidence/failure signature: `<refs>`
- Attempts and measurable deltas: `<attempt IDs>`
- Last stable checkpoint: `<ref/hash>`
- Required discriminating change: `<evidence, access, authorization, or method>`
- Owner and one next action: `<owner/action>`
- Stop condition: `<condition>`

## Resolved blockers

Move no entry. Append a resolution beneath the original blocker with timestamp, evidence, resulting
criterion verdict, and the task/checkpoint that resumed.
