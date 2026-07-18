# Run 01 complete input bundle

This archive repairs the missing-input block for the Local Codex pre-ADR pass.

## Exact required files now included

- `Pasted markdown.md`
- `chatgpt_work_harness_research_2026-07-18.zip`
- `docs/research/source-matrix.md`
- `docs/research/pattern-comparison.md`
- `docs/research/chatgpt-work-applicability.md`
- `docs/research/research-state.yaml`

Also included to avoid the next predictable block:

- `chatgpt_work_harness_implementation_routing_2026-07-18.zip`
- `AGENTS.md`
- `RUN_01_LOCAL_CODEX_SOL_HIGH.md`
- original research manifest and validation report

## Use

Extract this archive into the intended repository root while preserving paths.

Before copying:

1. inspect any existing repository-root `AGENTS.md`;
2. do not overwrite an existing `AGENTS.md` without reconciling it;
3. preserve unrelated local changes.

If the repository has no existing `AGENTS.md`, place the included one at the root.

Then start Codex with `RUN_01_LOCAL_CODEX_SOL_HIGH.md`.

## C-104 source paths

Codex should copy or retain these exact files:

```text
docs/research/source-matrix.md
docs/research/pattern-comparison.md
docs/research/chatgpt-work-applicability.md
docs/research/research-state.yaml
```

The files are already materialized in those paths in this bundle, so C-104 should verify checksums and inspect the diff rather than claim they are absent.
