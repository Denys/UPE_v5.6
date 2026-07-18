# Codex Environment Evidence — C-101 through C-105

**Captured:** 2026-07-18, refreshed after canonical materialization  
**Overall status:** COMPLETE FOR WEB MERGE

## Repository and runtime identity

- Repository root: `C:\Users\denko\CodexWork\UPE_5.6`
- Git: `refs/heads/main` at `f4ff123e0723b5047bb17eaa23f419534bf5abb4`
- `origin`: `https://github.com/Denys/UPE_v5.6.git`
- GitHub: `Denys/UPE_v5.6`, default `main`, viewer permission `ADMIN`.
- Visibility: `PUBLIC`, intentionally and temporarily; private recreation is deferred until after the architecture gate.
- Active execution environment: Windows-native Codex.
- WSL2: `NOT APPLICABLE` for the current target runtime.
- Earlier WSL2-first statements remain research assumptions to reconcile in ADR-001.

## PASS / FAIL / UNKNOWN

| Item | Result | Direct finding |
|---|---|---|
| C-101 | PASS | Repository/ref/runtime and intentional public visibility are current and explicit. |
| C-102 | PASS | Windows-native runtime inventory is the active evidence; WSL2 is not a dependency. |
| C-103 | PASS | Codex CLI `0.144.3` App Server help and generated schema surface were inspected and version-pinned. |
| C-104 | PASS | The build brief and four accepted research files are now present at canonical repository paths. |
| C-105 | PASS | The handoff packet is refreshed; stale commit, missing-file, WSL-blocker, and visibility-surprise claims are removed. |
| ADR gate | BLOCKED | `docs/architecture/ADR-001-harness-boundary.md` and `gate-records/ADR-001-PASS.yaml` do not yet exist. |
| External research correctness | UNKNOWN | Structural package validation passed; W-101 must reconcile current official web evidence with local observations. |
| Safety delivery | PASS | No merge, release, deployment, visibility mutation, or private-repository recreation was performed. |

## Canonical materialization

The following files are present at repository-root-relative paths:

- `Pasted markdown.md`
- `docs/research/source-matrix.md`
- `docs/research/pattern-comparison.md`
- `docs/research/chatgpt-work-applicability.md`
- `docs/research/research-state.yaml`

The historical nested bundle remains available as provenance and was not rewritten.

## Corrected runtime interpretation

Windows-native Codex is the supported execution environment. WSL2 is not a failed dependency and should not block the evidence merge or ADR. Prior WSL2-first statements must remain visible in the evidence packet as an alternative assumption whose costs and portability implications are decided by ADR-001.

## Corrected visibility interpretation

Public GitHub visibility is intentional and temporary. It does not block W-101 or ADR-001. Any later private recreation or visibility change is a separate external action requiring explicit authorization.

## Evidence paths

- `docs/research/local-target-context.md`
- `docs/research/codex-runtime-observations.md`
- `docs/research/app-server-protocol-observations.md`
- `docs/research/generated-app-server-schema/codex-cli-0.144.3/`
- `handoffs/CODEX_ENVIRONMENT_HANDOFF.yaml`
- `handoffs/CODEX_ENVIRONMENT_EVIDENCE.md`

## Next action

Run the Web Work architecture-freeze pass:

1. `W-101` — merge local and current official evidence;
2. `W-102` — create the ADR evidence packet;
3. `P-101` — write ADR-001;
4. `G-ADR` — create `ADR-001-PASS.yaml` or a precise blocked record.

Do not begin harness implementation before the ADR gate passes.
