# C-102 Codex Runtime Observations

**Captured:** 2026-07-18, corrected for the active target  
**Status:** PASS

## Active target environment

| Surface | Finding |
|---|---|
| Windows host | Active and supported execution environment |
| Windows-native Codex CLI/App Server | PASS from prior direct inspection |
| WSL2 | `NOT APPLICABLE` to the current target runtime |
| Docker | `NOT APPLICABLE` unless ADR-001 later establishes a material isolation need |

## Observed Windows toolchain

- Windows 11 Home `10.0.22621`, 64-bit.
- Python `3.14.3` observed; compatibility with the proposed Python 3.12+ implementation remains to be established after `pyproject.toml` exists.
- `uv 0.11.25`.
- Git `2.53.0.windows.1`, with worktree support.
- Codex CLI `0.144.3`.
- Codex desktop package `26.715.3651.0`.
- App Server help and TypeScript/JSON schema generators are available on Windows and labeled experimental.

## WSL2 reconciliation

Earlier files describe a WSL2-first architecture. That is a documented research/build-brief assumption, not the active runtime decision. It must remain visible for ADR-001 comparison, but it does not represent a failed dependency for this repository.

Do not report the inherited Windows npm shim or missing WSL-native Codex installation as a blocker. For the present target, WSL execution was outside scope.

## Finding

`C-102` is `PASS` for the active Windows-native environment. App Server compatibility evidence is version-pinned to Codex CLI `0.144.3`. The future implementation runtime and dependency set remain `UNKNOWN` until the ADR and project manifest are accepted.
