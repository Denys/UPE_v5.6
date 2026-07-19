# W-200 Cross-Document Consistency Review

**Review date:** 2026-07-19  
**Repository:** `Denys/UPE_v5.6`  
**Base:** `main@507cccc1a8dda824220b67afc8c39480b7fb8104`  
**Delivery ref:** `work/w201-w210-specification`  
**Scope:** W-201 through W-210 plus the Web-owned supporting package  
**Status:** PASS

## Canonical mapping

The mapping below is copied from `chatgpt_work_harness_implementation_routing_2026-07-18/harness_implementation_backlog.yaml`; the grouped user list was not used to infer task descriptions.

| Task | Canonical title | Canonical output | Dependency |
|---|---|---|---|
| W-201 | Write the ChatGPT Work loop adapter | `docs/work/CHATGPT_WORK_LOOP_ADAPTER.md` | G-ADR |
| W-202 | Finalize the web/local Work/local Codex routing matrix | `docs/work/WEB_VS_LOCAL_ROUTING.md` | G-ADR |
| W-203 | Define the generator/verifier protocol | `docs/work/GENERATOR_VERIFIER_PROTOCOL.md` | G-ADR |
| W-204 | Define the Work-to-Codex and Codex-to-Work handoff protocol | `docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md`; `schemas/handoff.schema.yaml` | G-ADR |
| W-205 | Design the Work goal contract schema | `schemas/goal_contract.schema.yaml` | G-ADR |
| W-206 | Design the Work loop-state schema | `schemas/work_loop_state.schema.yaml` | G-ADR |
| W-207 | Design the verifier-result schema | `schemas/verifier_result.schema.yaml` | W-203 |
| W-208 | Design the capability-execution record | `schemas/capability_execution_record.schema.yaml` | G-ADR |
| W-209 | Create the human-readable Work acceptance cases | `evals/work_loop_acceptance_cases.yaml` | W-201 through W-204 |
| W-210 | Write the dated model/effort routing reference | `docs/work/MODEL_EFFORT_ROUTING.md` | G-ADR |

README, the acceptance record, checkpoint, and implementation brief preserve these exact titles and paths. Supplemental security, recovery/operations, validation, examples, checkpoint, and handoff artifacts are labeled phase support rather than invented W tasks.

## Contract alignment

| Concern | Aligned rule | Evidence |
|---|---|---|
| Goal identity | W-206, W-207, and W-208 records carry the W-205 `goal_id`; W-206 and W-207 also carry its reference. W-204 carries both under `task`. | Schemas plus validated examples |
| C-301 transfer | The local handoff binds C-301 to a distinct `goal.c301.pre-edit` contract, not the completed W-200 goal. | `local_implementation_goal.example.yaml`; `handoff.example.yaml` |
| Verdicts | New criteria/verifier/handoff records use `PASS / FAIL / INSUFFICIENT_EVIDENCE`; only the W-200 phase record retains `UNKNOWN`; lifecycle may use `NOT_EVALUATED`. | W-201, W-203, W-204, W-206, W-207, recovery spec |
| Aggregation | Any criterion FAIL makes the aggregate FAIL; otherwise any insufficient evidence makes it insufficient; PASS requires every criterion PASS. Blocking is separate phase/release impact. | W-203; W-204 and W-207 schema conditionals |
| Approvals | `REQUIRED` means no durable request; `REQUESTED` means pending; `GRANTED / DENIED / EXPIRED / REVOKED` are resolved facts. Concrete actions use exact classes. | W-204 protocol/schema; W-205/W-206 enums; threat specification |
| Capability evidence | Planned requirement, actual exposure, permission, execution, validation, fallback, and residual limits remain distinct. An occurred approval-gated side effect requires actual authorization evidence. | W-208 schema and negative fixture |
| State authority | Work artifacts are transfer/checkpoint views; SQLite plus transactional outbox is canonical after a host run; JSONL is repairable audit output. | ADR-001; W-201; W-204; recovery spec |
| Side effects | One coordinator serializes writes; stable action IDs and target reconciliation precede retry; approval is never transported as authority. | W-201; W-202; W-204; security/recovery specs |
| Paths | Handoff paths are repository-relative and traversal-safe; the host additionally enforces Windows filesystem identity and reparse containment. | W-204 schema/protocol; threat specification |
| Model routing | Surface, tier, effort, Pro, orchestration, and tool adapter are separate axes; exposure is checked at execution time. | W-210 |

## Static and adversarial checks

`scripts/validate_work_specifications.py` performs the durable phase checks:

- required output presence and exact canonical backlog mapping;
- duplicate-key YAML parsing;
- Draft 2020-12 meta-validation for all five schemas;
- six positive instances, including distinct W-200 and C-301 goal contracts;
- required-field, type, enum/const, and additional-property rejection for every schema;
- handoff path, aggregation, and external-action approval rejection;
- verifier aggregation and capability side-effect authorization rejection;
- local JSON Schema reference resolution and unique schema IDs;
- repository/artifact reference existence in the primary examples;
- goal/handoff/loop/verifier/capability identity and reference alignment;
- W-209 unique IDs, oracles, forbidden outcomes, and complete 8+8 coverage;
- local Markdown link resolution.

Execution output is stored in `validation/W-200-STATIC-VALIDATION.json`. Content identity is frozen separately in `validation/W-200-CONTENT-MANIFEST.sha256` to avoid a self-referential commit field inside the checkpoint.

## Repaired integration findings

The integration review found and repaired these issues before acceptance:

- stale current-status text about merged PR #1 and the next executable phase;
- paraphrased README titles that did not exactly match the backlog;
- a four-versus-five schema count;
- incomplete W-200 scope/output fixtures and a completed state listing only W-201;
- a nonexistent W-301 handoff task and a later C-301 goal-identity mismatch;
- missing handoff goal binding;
- lossy approval action/status vocabularies and unscoped pending approvals;
- permissive handoff aggregation, evidence, path, and external-action approval rules;
- a capability side-effect authorization gap;
- phase `UNKNOWN` language leaking into new run/criterion records;
- an invalid conversation-shaped `COMMAND_RESULT` reference;
- the stale root manifest entry for `AGENTS.md`.

## Historical versus current records

Dated Run 01/Run 02 reports, environment handoffs, prompts, and the dated routing package remain historical observations and are not rewritten as if they were current. Current state is carried by README, `AGENTS.md`, `docs/research/research-state.yaml`, the ADR gate follow-up, this review, the W-200 acceptance record, and the W-200 checkpoint. PR #1's later merge is recorded as history and grants no standing authority for another merge or any release/deployment action.

## Remaining later-phase unknowns

The live App Server lifecycle smoke test, dependency compatibility on the Windows target, runtime/state/recovery/security behavior, CI, and release readiness remain explicitly assigned to later C-series tasks. They do not block this specification-only gate and are not claimed as implemented or tested.

## Review conclusion

Coordinator review: **PASS** for internal consistency and specification scope.  
Independent read-only review: **PASS** after the listed repairs; no blocking finding remains.  
The result accepts specifications and handoff readiness only. It does not claim harness implementation, runtime tests, merge, release, or deployment.
