# UPE v5.6.0.1 — GPT-5.6 Runtime Profile

**Availability profile date:** 2026-07-18
**Framework revision date:** 2026-07-25
**Volatility:** high. Verify official product/model documentation before relying on availability, plan access, limits, pricing, or UI labels.

This file adapts the stable UPE core to the GPT-5.6 family. It is not the core itself. Replace or patch this profile when product behavior changes; do not casually rewrite authority, evidence, safety, state, or acceptance rules.

## 1. Version semantics

`UPE v5.6.0.1` means:

- `5.6`: target GPT generation/family used for the runtime adapter;
- `.0`: stable UPE line for that family;
- final `.1`: first compatible patch on that line;
- stable core lineage: inherited from UPE v4.1 and the v4.3 adaptive-branching branch;
- current framework revision: v5.6.0.1;
- future compatible patches on this line: v5.6.0.2, v5.6.0.3, and so on;
- reserved line: v5.6.1 is frozen and blocked from Codex use unless the user explicitly authorizes it;
- a core change must be explicitly labeled `CORE_CHANGE`; a normal model migration changes this profile, adapters, skill, and evals first.

v5.6.0.1 adds the terminal-audit core invariant CC-5.6.0.1-01 and includes its pre-publication packaging and calibration repairs. The version does not claim that every core rule was replaced.

## 2. Keep six axes separate

Do not collapse these into a single ladder:

1. **Surface:** standard ChatGPT, Work, Codex, API, Custom GPT, agent runtime, or unknown.
2. **Model tier:** Sol, Terra, Luna, or another exposed model.
3. **Reasoning effort:** product/API-specific effort control.
4. **Execution mode:** standard or pro where supported.
5. **Orchestration:** single agent, staged serial, native multi-agent, Ultra-style coordination, or programmatic tool stage.
6. **Review independence:** same-context self-review, fresh serial context, delegated independent worker, or external/manual reviewer.

A subscription is not proof of exposure. “Sol Pro,” API pro mode, `max` effort, and Ultra are not interchangeable labels. A stronger model or a separate branch is not automatically an independent reviewer; independence also requires no candidate authorship, a frozen evidence bundle, and read-only scope.

## 3. Current official GPT-5.6 profile

As of the profile date:

- **Sol** is the flagship tier for complex professional work.
- **Terra** is the balanced capability/cost tier.
- **Luna** is the fastest and lowest-cost tier for efficient or high-volume work.
- In standard ChatGPT, Medium/High/Extra High use Sol and the Pro choice uses Sol Pro where available. Terra and Luna are not selectable in ordinary ChatGPT conversations.
- Work, Codex, and the API expose different combinations. Verify the current product page before encoding availability.
- In the API, `gpt-5.6` aliases Sol. Reasoning effort and pro mode are independent controls. Ultra is an orchestration feature on supported products, not another effort value.

See `06_SOURCE_MAP.md` for official evidence.

## 4. Model selection by workload, not prestige

| Route | Prefer when | Avoid as default when |
|---|---|---|
| Luna | High-volume extraction, classification, formatting, normalization, constrained transformation, deterministic checks, repetitive tool work with exact schemas | Requirements are ambiguous, evidence conflicts, judgment is failure-expensive, or final synthesis spans domains |
| Terra | Well-scoped professional analysis, routine research with sources, bounded multi-step coding/data/file work, structured drafting, serial workflow execution | The task needs frontier judgment, deep conflict resolution, difficult architecture, or high-value final review |
| Sol | Ambiguous goals, cross-domain synthesis, serious prompt/agent architecture, hard debugging, failure-expensive review, deep research, complex artifacts, final integration | Mechanical high-volume work where Terra/Luna pass the same evals |
| Pro/max | An indivisible hard task where extra model work produces a measured reliability gain | Routine work, latency-sensitive work, or tasks whose evals show no material gain |
| Ultra/native multi-agent | Cleanly separable workstreams where concurrent evidence, implementation, or verification reduces time or error | Atomic work, tightly dependent steps, side-effecting actions, or work without a merge/verification budget |
| Independent framework auditor | Fresh-context review of a frozen reusable-framework candidate; use Sol for ambiguous/architectural/high-cost review and Terra for bounded rubric-based review when representative evals show it is sufficient | Same-context role play, shared mutable drafting, or any route allowed to publish/overwrite the candidate |

## 5. GPT-5.6 prompting adaptations

Carry these traits into active instructions:

- **Leaner prompts:** state each instruction once; keep only examples and style rules that encode a requirement or repair a measured gap.
- **Outcome focus:** give goal, context, hard constraints, evidence, approval boundaries, success criteria, and output. Do not prescribe every thought or microstep unless the route is constrained.
- **Proactive local execution:** allow safe in-scope inspection, local edits, and non-destructive validation; gate external, destructive, costly, public, or scope-expanding actions once in a clear policy.
- **No blanket brevity:** GPT-5.6 is concise by default. Specify what must survive compression instead of chanting “be concise” until the useful content evaporates.
- **Reference fidelity:** for documents, spreadsheets, slides, UI, and templates, inspect the reference system, extract layout/content invariants, then validate the output against them.
- **Intent understanding with boundaries:** let the model infer ordinary implementation detail, but explicitly define important ambiguities that require a question.

## 6. Lower-effort and lower-tier adaptation

Sol at lower effort, Terra, and Luna can preserve more of the result envelope when the workflow is made operationally explicit:

1. Freeze the complete MUST ledger before execution.
2. Split work into short bounded stages with one output schema each.
3. Supply only the relevant inputs for the current stage.
4. Prefer deterministic tools for parsing, calculation, transformation, and validation.
5. Checkpoint findings and restore the coordinator role between stages.
6. Use a separate verifier for material conflict, high risk, or expensive failure. For the terminal reusable-framework gate, it must satisfy the independence contract; a role switch in the authoring context does not.
7. Spend remaining budget on merge and acceptance, not decorative exploration.

This preserves control structure, not equivalent latent compute. Expected variables across tiers are breadth, speed, concurrency, nuance, polish, and recovery depth. Required invariants are authority, MUST coverage, source/file integrity, action safety, critical factual conclusions, and exact output schema within the declared task envelope.

## 7. Cognitive adapters

### `atomic_direct`
Use for simple, deterministic, or indivisible work. One pass, then a proportionate check.

### `coordinated_serial`
Use for constrained models, dependent stages, or absent native agents. Each stage has objective, inputs, MUST IDs, schema, stop condition, and checkpoint.

### `native_parallel`
Use for independent read-only workstreams. The coordinator owns the contract, merge, conflict resolution, final verification, and every side effect.

Default branch depth is one. Add depth only when a branch exposes a new material uncertainty. Reserve capacity for the merge.

## 8. Tool adapters

### Direct tool calls
Default for one/few calls, small results, semantic judgment between calls, native citations/artifacts, or approvals.

### Tool search
Use when many functions or MCP tools exist and deferred discovery is supported. Keep namespace/server descriptions discriminating and the loaded set narrow.

### Programmatic Tool Calling
Use for one bounded predictable reduction stage: filtering, joining, ranking, deduplication, aggregation, validation, or compression of large intermediate outputs. Specify eligible tools, schemas, concurrency/retry/stop limits, and a handoff back to direct model judgment. Multiple calls alone do not justify it.

### Native multi-agent / Ultra
Use when work divides cleanly into independent streams. Keep identical branch briefs and a serial fallback. Never let branches send, publish, purchase, delete, schedule, or mutate shared external state.

### Independent framework audit
After a reusable framework candidate is frozen, prefer a fresh delegated worker with no candidate authorship and read-only access. Pass the frozen request/contract, original and candidate artifacts, declared evidence, eval results, limits, version scheme, and output schema. Do not pass hidden author reasoning. If no fresh worker exists, export the bundle to a separate chat/process; a same-context critique is advisory and leaves the independent gate `UNKNOWN`.

Use one normal audit cycle. Add a second only when the first exposes a critical or architectural repair. The coordinator, not the reviewer, owns integration, affected re-tests, version assignment, and release.

## 9. Recommended UPE routing shorthand

A practical cost-first boundary, subject to evals:

- **Luna:** `clear + repeatable + schema-bound + cheaply verifiable`.
- **Terra:** `well-scoped + multi-step + professional + moderate judgment`.
- **Sol:** `ambiguous or cross-domain + failure-expensive + difficult synthesis/review`.
- **Sol Pro/max:** `hard and largely indivisible`.
- **Sol + Ultra/native multi-agent:** `hard and cleanly branchable`.
- **Independent auditor:** `frozen reusable-framework candidate + fresh context + read-only + quantified critique/revision`.

Do not send `2+2` to an orchestration cathedral merely because the cathedral is available.

## 10. Migration test

When moving an existing workflow to GPT-5.6:

1. preserve the current model/effort prompt as baseline;
2. remove duplicated instructions and irrelevant tools one group at a time;
3. test the same effort and one level lower where applicable;
4. compare Sol/Terra/Luna only on representative tasks inside the declared envelope;
5. measure task success, MUST coverage, evidence, final-answer completeness, tokens, latency, calls, retries, and cost;
6. keep a cheaper/lighter route only when critical gates still pass;
7. use Pro/max/Ultra/PTC only where measured gain justifies the extra work;
8. for reusable framework migrations, compare the independent baseline score with projected revision range, then rerun representative evals before calling the gain empirical.
