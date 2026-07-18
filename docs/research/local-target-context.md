# C-101 Local Target Context

**Captured:** 2026-07-18T22:43:25.4294702+02:00
**Status:** PASS

## Repository identity

- Repository root: `C:\Users\denko\CodexWork\UPE_5.6`
- Baseline branch/ref: `refs/heads/main` at `f4ff123e0723b5047bb17eaa23f419534bf5abb4`
- Delivery branch: `refs/heads/agent/windows-materialization-handoff-refresh`
- Materialization commit: `ecd9415e6caa60e4e8746fdf79e9a8b3fb3af262`
- Target draft PR: `Denys/UPE_v5.6#1`
- `origin`: `https://github.com/Denys/UPE_v5.6.git`
- `upstream`: `https://github.com/denkovtll/UPE_v5.6.git`
- GitHub target visibility: `PUBLIC`, intentionally and temporarily.
- Private recreation is deferred until after the ADR gate and is not a blocker for evidence merge or architecture work.

The baseline and delivery identities are intentionally separate. Commit `f4ff123e...` is the inspected pre-materialization `main` state. The five canonical files first appear in materialization commit `ecd9415e...` on the delivery branch.

## Pull-request and remote state

Read-only GitHub verification established:

- `Denys/UPE_v5.6#1` is open, draft, mergeable, and unmerged.
- It targets `main@f4ff123e...`.
- The materialization commit is one commit ahead of that base.
- No commit-status checks are configured.
- Legacy `denkovtll/UPE_v5.6#1` was merged separately as `bcbd6b385946420351f01a7474c285951dcfed19`, with `ecd9415e...` as a parent.

The legacy-upstream merge contradicts an unqualified “no merge occurred” claim. It is recorded as a safety-delivery finding; no merge was performed against the target `Denys/UPE_v5.6` draft PR.

## Runtime scope

- Active execution environment: Windows-native Codex.
- WSL2: `NOT APPLICABLE` for the current target environment.
- Earlier WSL2-first requirements remain visible as research assumptions to be reconciled in ADR-001 rather than silently rewritten.

## Worktree state preserved

The main worktree remained on `main@f4ff123e...` and contained user-owned changes during PR repair:

```text
 M RUN_01_COMPLETE_INPUTS_2026-07-18/Pasted markdown.md
?? UPE_v5.6.0_Complete_Documentation.pdf
?? UPE_v5.6.0_Recommended_Project_Files.zip
?? harness-for-every-task/extension_prompt.md
```

Those paths were not staged, reverted, copied, or edited by this repair. Work was performed in the isolated linked worktree `C:\Users\denko\CodexWork\UPE_5.6_pr1_fix`.

## Canonical materialization

The following delivery-branch files are blob-identical to their accepted nested-bundle sources at baseline `f4ff123e...`:

- `Pasted markdown.md`
- `docs/research/source-matrix.md`
- `docs/research/pattern-comparison.md`
- `docs/research/chatgpt-work-applicability.md`
- `docs/research/research-state.yaml`

## Finding

`C-101` is `PASS`: baseline, delivery branch, materialization commit, target PR, legacy-upstream merge, Windows runtime scope, and unrelated local changes are distinguished explicitly. ADR-001 remains blocked until the architecture decision and passing gate record exist.
