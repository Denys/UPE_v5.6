# Codex Environment Evidence — C-101 through C-105

**Captured:** 2026-07-18T18:34:41.6551604+02:00  
**Overall status:** BLOCKED

## Repository and runtime identity

- Source directory: `C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE`
- Intended private GitHub repository: `Denys/UPE_v5.6`
- Git repository root/ref/status/worktree: `UNKNOWN`; the source directory is not a Git repository.
- GitHub: connected account `Denys`; installed-repository search for `UPE_v5.6` returned 0 matches.
- Windows: Windows 11 Home `10.0.22621`, 64-bit.
- WSL: 2.7.10.0; Ubuntu 24.04.3 LTS on WSL2.
- Windows tools: Python 3.14.3; uv 0.11.25; Git 2.53.0.windows.1; Codex CLI 0.144.3.
- WSL tools: Python 3.12.3; uv 0.9.25; Git 2.43.0; native Codex unavailable.
- Codex desktop package: 26.715.3651.0; ChatGPT desktop classic: 1.2026.190.0.
- App Server schema generator: Codex CLI 0.144.3, SHA-256 `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`.

## PASS / FAIL / UNKNOWN

| Item | Result | Finding |
|---|---|---|
| C-101 | FAIL / BLOCKED | No Git repository/ref/status/remote/worktree exists. |
| C-102 | PASS | Runtime inventory complete; supplied desktop and CLI minimums pass. WSL Codex separately FAILS. |
| C-103 | PASS | Default and experimental TypeScript/JSON Schema bundles generated and validated. |
| C-104 | FAIL / BLOCKED | Accepted research ZIP and four accepted research files are absent; nothing was copied or rewritten. |
| C-105 | PASS | Blocked-state handoff packet created. |
| Contract | FAIL | C-101 and C-104 acceptance conditions are unmet. |
| Evidence integrity | UNKNOWN | Local manifests and schemas validate; accepted research checksums are unavailable. |
| Safety delivery | PASS | No pre-existing file, Git state, remote, credential, or external system was mutated. |

## Files created/copied

Created:

- `docs\research\local-target-context.md`
- `docs\research\codex-runtime-observations.md`
- `docs\research\app-server-protocol-observations.md`
- `docs\research\generated-app-server-schema\codex-cli-0.144.3\stable\typescript\` — 598 files
- `docs\research\generated-app-server-schema\codex-cli-0.144.3\stable\json-schema\` — 267 files
- `docs\research\generated-app-server-schema\codex-cli-0.144.3\experimental\typescript\` — 671 files
- `docs\research\generated-app-server-schema\codex-cli-0.144.3\experimental\json-schema\` — 337 files
- `handoffs\CODEX_ENVIRONMENT_HANDOFF.yaml`
- `handoffs\CODEX_ENVIRONMENT_EVIDENCE.md`

Copied: none. No placeholder or reconstructed research file was created.

## Commands actually run

```powershell
git -C 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE' rev-parse --show-toplevel
git -C 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE' status --short
git -C 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE' status --short --branch
git -C 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE' rev-parse --verify HEAD
git -C 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE' symbolic-ref --quiet --short HEAD
git -C 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE' remote -v
git -C 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE' worktree list --porcelain
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture | Format-List
wsl.exe --version
wsl.exe --status
wsl.exe --list --verbose
py -0p
py -3 --version
uv --version
git --version
git worktree -h
codex --version
codex app-server --help
codex app-server generate-ts --help
codex app-server generate-json-schema --help
codex app-server generate-ts --out 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\stable\typescript'
codex app-server generate-json-schema --out 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\stable\json-schema'
codex app-server generate-ts --experimental --out 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\experimental\typescript'
codex app-server generate-json-schema --experimental --out 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\experimental\json-schema'
rg --files 'C:\Users\denko\CodexWork' | rg -i '(chatgpt_work_harness_research_2026-07-18\.zip$|docs[\\/]research[\\/](source-matrix\.md|pattern-comparison\.md|chatgpt-work-applicability\.md|research-state\.ya?ml)$|Pasted markdown\.md$)'
```

Additional exact WSL probes, file reads, checksum commands, generated-file validation, and their observed results are recorded in the three `docs\research\*-observations.md` evidence files and the YAML command ledger. GitHub connector operations were read-only: resolve login, list installed accounts, and search installed repositories.

## Unresolved conflicts

1. The opening request asks to create `UPE_v5.6`, while the same pass forbids external mutation and says to stop when one is required. No repository was created.
2. The explicit source directory is not a Git repository; Git identity evidence cannot exist without initialization.
3. `chatgpt_work_harness_research_2026-07-18.zip` and the four accepted C-104 files are absent across `C:\Users\denko\CodexWork`. The available routing ZIP is a different package.
4. `Pasted markdown.md` is absent; `UPE_tasks_downloads\prompt_harness.txt` is the only located build-request equivalent.
5. WSL has no native Node/Codex installation. Its inherited Windows npm Codex shim fails with exit 126 (`exec: node: Permission denied`).
6. Docker is UNKNOWN by instruction because no Docker configuration or material requirement was found.

## Exact evidence paths

- `C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\local-target-context.md`
- `C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\codex-runtime-observations.md`
- `C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\app-server-protocol-observations.md`
- `C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\`
- `C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\handoffs\CODEX_ENVIRONMENT_HANDOFF.yaml`
- `C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\handoffs\CODEX_ENVIRONMENT_EVIDENCE.md`

## Next action

Upload the handoff packet to ChatGPT Work for `W-101`. Reconcile the absent accepted research package and contradictory repository-creation authorization before any Git initialization or GitHub mutation.
