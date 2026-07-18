# C-101 Local Target Context

**Captured:** 2026-07-18, refreshed from current operator and GitHub evidence  
**Status:** PASS

## Repository identity

- Repository root: `C:\Users\denko\CodexWork\UPE_5.6`
- Branch: `main`
- Git ref: `refs/heads/main`
- Commit: `f4ff123e0723b5047bb17eaa23f419534bf5abb4`
- `origin`: `https://github.com/Denys/UPE_v5.6.git`
- Remote `main` matches local `main` at the captured commit.
- GitHub repository: `Denys/UPE_v5.6`
- Viewer permission: `ADMIN`
- Visibility: `PUBLIC`, intentionally and temporarily.
- Private recreation is deferred until after the ADR gate and is not a blocker for evidence merge or architecture work.

## Runtime scope

- Active execution environment: Windows-native Codex.
- WSL2: `NOT APPLICABLE` for the current target environment.
- Earlier WSL2-first requirements remain visible as research assumptions to be reconciled in ADR-001 rather than silently rewritten.

## Repository state

The operator reported a clean `main` at `f4ff123e0723b5047bb17eaa23f419534bf5abb4`, matching `origin/main`. The outer bundle and nested research packages were structurally and cryptographically validated before materialization.

## Canonical materialization

The following inputs are required at repository-root-relative paths:

- `Pasted markdown.md`
- `docs/research/source-matrix.md`
- `docs/research/pattern-comparison.md`
- `docs/research/chatgpt-work-applicability.md`
- `docs/research/research-state.yaml`

This update materializes those paths without changing the historical nested bundle.

## Finding

`C-101` is `PASS`: repository/ref identity, current runtime scope, intentional public visibility, and the canonical-input requirement are explicit. ADR-001 remains blocked until the architecture decision and gate record exist.
