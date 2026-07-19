# UPE v5.6 Long-Running Harness

UPE is building a minimal, resumable, independently verifiable
software-engineering harness around a portable trusted-host contract and a
Windows-native Codex App Server adapter. The repository currently contains the
accepted specification package and the C-301…C-306 implementation foundation;
it does not yet contain the v0 lifecycle, state engine, provider adapter,
orchestration, recovery, or CLI.

## Current implementation slice

**Status date:** 2026-07-19

| Task | Canonical outcome | Current evidence |
|---|---|---|
| `C-301` | Re-inspect repository state immediately before edits | `PASS`; pre-edit context is recorded. |
| `C-302` | Create the minimal Python/uv repository scaffold | Merged by PR `#4` at `a7e99bd32e71ef047296446c14f9e4376b444fcd`. |
| `C-303` | Materialize accepted research, ADR, schemas, templates, and prompts | Tested locally and published at `049bdec9f826761a9f362385ce0f6d165d99fe3e` in [draft PR #5](https://github.com/Denys/UPE_v5.6/pull/5). |
| `C-304` | Create a short `AGENTS.md` map and repository operating README | `PASS`; concise operating map, commands, invariants, definition of done, and prohibited actions are validated. |
| `C-305` | Create the fixture repository and deterministic baseline commands | `PASS`; reproducible fixture HEAD, positive/known-failure exits, and Windows reparse safety are tested. |
| `C-306` | Create schema and package validators | `PASS`; schema, reference, release, and 14 negative validator cases are tested. |

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
uv sync --all-groups
uv lock --check
uv run python -c "import harness; print(harness.__version__)"
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
```

The current package exposes only the importable `harness` root and version.
Commands such as `uv run harness doctor` and `uv run harness init ...` are v0
acceptance targets, not implemented operating commands.

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

Those runtime rules are accepted contracts, not implemented behavior. Recovery is
currently repository/checkpoint based as recorded in the mutable research state.
Do not call this repository production-ready. C-304…C-306 now have passing
integration evidence, but `C-401` or later runtime work still requires a new
bounded authorization after PR #5 is adopted.
