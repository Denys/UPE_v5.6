# UPE v5.6 Long-Running Harness

UPE is building a minimal, resumable, independently verifiable
software-engineering harness around a portable trusted-host contract and a
Windows-native Codex App Server adapter. The repository currently contains the
accepted specification package, the C-301…C-306 implementation foundation, and
the C-401 typed state/configuration contracts plus the C-402 provider-neutral
interface and deterministic fake adapter. C-403 adds lifecycle sequencing and a
single-task orchestrator against that fake. The repository does not yet contain a
real provider adapter, durable persistence, recovery, executable validators,
evaluator, or CLI.

## Current implementation slice

**Status date:** 2026-07-20

| Task | Canonical outcome | Current evidence |
|---|---|---|
| `C-301` | Re-inspect repository state immediately before edits | `PASS`; pre-edit context is recorded. |
| `C-302` | Create the minimal Python/uv repository scaffold | Merged by PR `#4` at `a7e99bd32e71ef047296446c14f9e4376b444fcd`. |
| `C-303` | Materialize accepted research, ADR, schemas, templates, and prompts | Adopted with C-304…C-306 by merged [PR #5](https://github.com/Denys/UPE_v5.6/pull/5) at `a8c611b09297fb226f046d54fdfa0f64e84d9396`. |
| `C-304` | Create a short `AGENTS.md` map and repository operating README | `PASS`; concise operating map, commands, invariants, definition of done, and prohibited actions are validated. |
| `C-305` | Create the fixture repository and deterministic baseline commands | `PASS`; reproducible fixture HEAD, positive/known-failure exits, and Windows reparse safety are tested. |
| `C-306` | Create schema and package validators | `PASS`; schema, reference, release, and 14 negative validator cases are tested. |
| `C-401` | Implement typed Goal, Task, Run, Event, configuration, and lifecycle models | `PASS` locally; strict immutable models, five JSON schemas, transition legality, and clean-checkout reliability are recorded in [`validation/C-401-GATE.yaml`](validation/C-401-GATE.yaml). |
| `C-402` | Implement the provider adapter interface and fake adapter | `PASS` locally; the synchronous provider protocol and deterministic success/failure/interruption/approval scripts are recorded in [`validation/C-402-GATE.yaml`](validation/C-402-GATE.yaml). |
| `C-403` | Implement lifecycle/orchestration against the fake adapter | `PASS` locally; commit-before-dispatch ordering, canonical provider events, one-task iterations, reasoned stops, and evidence-only completion are recorded in [`validation/C-403-GATE.yaml`](validation/C-403-GATE.yaml). |

The accepted architecture and Work specification baseline is on `main`: ADR-001
and `G-ADR` are `PASS`; canonical `W-201` through `W-210` and the W-200 gate are
`PASS` and were adopted by PR `#3` at
`d0fbfd56c6b533da62db3e4bea147496345b6c90`. Backlog status fields are historical;
use the current state, Git/PR evidence, and task gate together.

## Setup and package checks

Prerequisites are Windows-native Python 3.12+ and
[`uv`](https://docs.astral.sh/uv/). Dependency resolution and tests have been
observed on Python 3.14.3 only; Python 3.12 and 3.13 remain unverified.

```powershell
uv sync --group dev --locked
uv lock --check
uv run python -c "import harness; print(harness.__version__)"
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src tests
```

## UPE framework release packs

- [`UPE_v5.6.0_RELEASE/`](UPE_v5.6.0_RELEASE/) preserves the original GPT-5.6-aligned release.
- [`UPE_v5.6.0.1_RELEASE/`](UPE_v5.6.0.1_RELEASE/) adds `CORE_CHANGE CC-5.6.0.1-01`: a terminal independent, read-only framework auditor/improver with quantified baseline, headroom, projected/empirical delta separation, complete revision, and version decision.
- [`validation/UPE-5.6.0.1-INDEPENDENT-AUDIT.md`](validation/UPE-5.6.0.1-INDEPENDENT-AUDIT.md) and [`validation/UPE-5.6.0.1-COORDINATOR-DISPOSITION.yaml`](validation/UPE-5.6.0.1-COORDINATOR-DISPOSITION.yaml) preserve the first execution of that gate.
- PR #19 is relabeled to v5.6.0.1 and remains frozen. The `5.6.1` identifier is blocked from Codex use unless explicitly authorized by the user.
- [`UPE_v5.6.0.2_WEB_WORK_NATIVE_SUBAGENT_DRAFT/`](UPE_v5.6.0.2_WEB_WORK_NATIVE_SUBAGENT_DRAFT/) is the unpublished, reviewed candidate that adds the `web_work_native_subagent` adapter. Its pre-PR review record is preserved at [`validation/UPE-5.6.0.2-WEB-WORK-NATIVE-SUBAGENT-PRE-PR-REVIEW.md`](validation/UPE-5.6.0.2-WEB-WORK-NATIVE-SUBAGENT-PRE-PR-REVIEW.md). Formal release requires a fresh read-only review of the exact PR head SHA.

Validate v5.6.0.1 with:

```powershell
uv run python UPE_v5.6.0.1_RELEASE/skill/upe-v5-6/scripts/validate_package.py UPE_v5.6.0.1_RELEASE
uv run python scripts/validate_release.py UPE_v5.6.0.1_RELEASE --manifest UPE_v5.6.0.1_RELEASE/MANIFEST.json --normalize-text-eol
```

Validate the v5.6.0.2 candidate with:

```powershell
uv run python UPE_v5.6.0.2_WEB_WORK_NATIVE_SUBAGENT_DRAFT/skill/upe-v5-6/scripts/validate_package.py UPE_v5.6.0.2_WEB_WORK_NATIVE_SUBAGENT_DRAFT
uv run python scripts/validate_release.py UPE_v5.6.0.2_WEB_WORK_NATIVE_SUBAGENT_DRAFT --manifest UPE_v5.6.0.2_WEB_WORK_NATIVE_SUBAGENT_DRAFT/MANIFEST.json --normalize-text-eol
```

The package root still exports only `harness.__version__`. C-401 contracts are
imported explicitly from `harness.state` and `harness.config`; C-402 contracts
and the fake are imported from `harness.adapters`; C-403 sequencing is imported
from `harness.lifecycle` and `harness.orchestrator`. No real provider, durable
persistence, loader, discovery, or CLI behavior is implied. Commands such as
`uv run harness doctor` and `uv run harness init ...` remain unimplemented v0
acceptance targets.

## Specification and slice validation

Validate the accepted W-200/W-201…W-210 package:

```powershell
uv run python scripts/validate_work_specifications.py
```

The C-303 source mappings and hashes are recorded in
[`validation/C-303-MATERIALIZATION.yaml`](validation/C-303-MATERIALIZATION.yaml).

C-305 and C-306 provide these tested entry points. Their combined evidence is in
[`validation/C-304-C-306-GATE.yaml`](validation/C-304-C-306-GATE.yaml):

```powershell
$fixtureBash = 'C:\Program Files\Git\usr\bin\bash.exe'
& $fixtureBash scripts/bootstrap.sh
& $fixtureBash scripts/verify-fast.sh
& $fixtureBash scripts/verify-fast.sh --known-failure
& $fixtureBash scripts/verify-full.sh
& $fixtureBash scripts/verify-full.sh --known-failure
uv run python scripts/validate_schema.py
uv run python scripts/validate_references.py
uv run python scripts/validate_release.py UPE_v5.6.0_RELEASE --manifest UPE_v5.6.0_RELEASE/MANIFEST.json --normalize-text-eol
```

Fixture bootstrap owns only the ignored
`examples/fixture-repository/.fixture-output/` directory and recreates it only
when its owner marker matches. The default fast/full checks must exit `0`; each
`--known-failure` check deliberately exercises the seed's unimplemented behavior
and must exit `1` with a `KNOWN_FAILURE` result.

`validate_schema.py` checks every accepted schema/example mapping;
`validate_references.py` checks local references and cross-record identities.
Both exit `0` only when every check passes and exit `1` with actionable errors
otherwise. The release check above validates the accepted checked-out historical
package; `--normalize-text-eol` accounts for Git checkout conversion of text
files. Raw-byte hash checking remains the default for other package targets; run
`uv run python scripts/validate_release.py --help` before supplying different
package or archive paths.

The combined task result is
[`agent/state/C-304-C-306-result.yaml`](agent/state/C-304-C-306-result.yaml).

## Repository operating map

- Start with [`AGENTS.md`](AGENTS.md) for the concise work rules, commands,
  definition of done, and prohibited actions.
- The authoritative build brief is `Pasted markdown.md`.
- The accepted boundary is
  [`docs/architecture/ADR-001-harness-boundary.md`](docs/architecture/ADR-001-harness-boundary.md),
  with [`gate-records/ADR-001-PASS.yaml`](gate-records/ADR-001-PASS.yaml).
- Mutable status and recovery state live in
  [`docs/research/research-state.yaml`](docs/research/research-state.yaml).
- The canonical task backlog is
  [`harness_implementation_backlog.yaml`](chatgpt_work_harness_implementation_routing_2026-07-18/harness_implementation_backlog.yaml).
- The local implementation sequence and invariants are in
  [`handoffs/W-200-LOCAL-IMPLEMENTATION-BRIEF.md`](handoffs/W-200-LOCAL-IMPLEMENTATION-BRIEF.md).
- Work/local contracts live under [`docs/work/`](docs/work/); schemas and positive
  examples live under [`schemas/`](schemas/) and
  [`examples/specifications/`](examples/specifications/).
- Deterministic commands live under [`scripts/`](scripts/); package, fixture, and
  validator checks live under [`tests/`](tests/).

The dated routing package, Run 01/02 prompts, archives, and C-101…C-105 handoffs
are preserved point-in-time evidence. Their embedded status and next-action
fields do not replace `docs/research/research-state.yaml`.

### Capability-readiness end-of-run hook

The single-file capability report is refreshed from the canonical backlog,
mutable current state, accepted result/gate records, and local Git identity:

```powershell
uv run python scripts/update_capability_readiness_report.py
uv run python scripts/update_capability_readiness_report.py --check
```

The first command updates
`UPE_5.6.0_to_5.6.1_capability_readiness_report_2026-07-19.html`; the second is a
non-mutating freshness gate. Local Codex runs execute the update after task-state
bookkeeping and before final verification. Web-only work is reflected when its
accepted handoff is materialized in the repository.

## W-201…W-210 canonical mapping

| ID | Canonical task | Required output | Dependency |
|---|---|---|---|
| `W-201` | Write the ChatGPT Work loop adapter | `docs/work/CHATGPT_WORK_LOOP_ADAPTER.md` | `G-ADR` |
| `W-202` | Finalize the web/local Work/local Codex routing matrix | `docs/work/WEB_VS_LOCAL_ROUTING.md` | `G-ADR` |
| `W-203` | Define the generator/verifier protocol | `docs/work/GENERATOR_VERIFIER_PROTOCOL.md` | `G-ADR` |
| `W-204` | Define the Work-to-Codex and Codex-to-Work handoff protocol | `docs/work/WORK_CODEX_HANDOFF_PROTOCOL.md`, `schemas/handoff.schema.yaml` | `G-ADR` |
| `W-205` | Design the Work goal contract schema | `schemas/goal_contract.schema.yaml` | `G-ADR` |
| `W-206` | Design the Work loop-state schema | `schemas/work_loop_state.schema.yaml` | `G-ADR` |
| `W-207` | Design the verifier-result schema | `schemas/verifier_result.schema.yaml` | `W-203` |
| `W-208` | Design the capability-execution record | `schemas/capability_execution_record.schema.yaml` | `G-ADR` |
| `W-209` | Create the human-readable Work acceptance cases | `evals/work_loop_acceptance_cases.yaml` | `W-201`…`W-204` |
| `W-210` | Write the dated model/effort routing reference | `docs/work/MODEL_EFFORT_ROUTING.md` | `G-ADR` |

Phase-level Web/Work artifacts also define the security/threat boundary,
recovery/evaluation/operations contract, cross-document/static-validation gate,
and local implementation handoff. They do not create additional W task IDs.

## Runtime invariants and limitations

- Windows-native Codex is the current v0 target; WSL2-first statements are
  historical and superseded by ADR-001 and W-101.
- SQLite will be authoritative lifecycle/action state; JSONL will be a replayable
  audit mirror emitted through a transactional outbox.
- External actions require stable IDs, recorded approval scope, and reconciliation
  before retry. Routine checkpoints are host-managed patch snapshots; Git commits
  are separately authorized milestones.
- Deterministic validation precedes optional read-only model evaluation.
- v0 remains single-agent and fake-adapter-first.

The C-401 lifecycle and configuration layer is a pure model contract; it performs
no persistence, provider call, external action, executable budget enforcement, or
resume/reconciliation behavior. The C-402 fake is in-memory and deterministic; it
does not perform model, filesystem, subprocess, network, persistence, or lifecycle
work. C-403 uses a synchronous commit port to prove that each transition is
acknowledged before provider dispatch; C-406 still owns actual SQLite/outbox
durability. C-403 accepts explicit validation/evaluation/checkpoint references but
does not execute or interpret validators; C-404 owns that layer. Recovery remains
repository/checkpoint based as recorded in the mutable research state. Do not call
this repository production-ready. `C-404` and later behavior require their own
bounded authorization.
