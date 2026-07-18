# Codex Environment Evidence — C-101 through C-105

**Captured:** 2026-07-18T19:42:13.2622869+02:00
**Overall status:** BLOCKED

## Repository and runtime identity

- Repository root: `C:\Users\denko\CodexWork\UPE_5.6`
- Git: `refs/heads/main` at `eed3b046c5910dfc51c28b2cd7a368d609370c44`
- `origin`: `https://github.com/Denys/UPE_v5.6.git`
- `upstream`: `https://github.com/denkovtll/UPE_v5.6.git`
- Remote `main` matches local HEAD.
- GitHub: `Denys/UPE_v5.6`, default `main`, viewer permission `ADMIN`, live visibility `PUBLIC`.
- The public visibility conflicts with the original private-repository requirement.
- Windows: Windows 11 Home `10.0.22621`, 64-bit.
- WSL: `2.7.10.0`; Ubuntu `24.04.3 LTS` on WSL2.
- Windows tools: Python `3.14.3`; uv `0.11.25`; Git `2.53.0.windows.1`; Codex CLI `0.144.3`.
- WSL tools: Python `3.12.3`; uv `0.9.25`; Git `2.43.0`; native Codex unavailable.
- Codex desktop package: `26.715.3651.0`; ChatGPT desktop classic: `1.2026.190.0`.
- App Server generator identity: Codex CLI `0.144.3`, executable SHA-256 `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`.

## PASS / FAIL / UNKNOWN

| Item | Result | Direct finding |
|---|---|---|
| C-101 | PASS | Corrected repository/ref/origin are unambiguous; visibility, legacy upstream, configuration, and pre-existing changes are recorded. |
| C-102 | PASS | Runtime inventory is complete and supplied Codex minimums pass. WSL-native Codex separately FAILS with exit 126. |
| C-103 | PASS | Installed `0.144.3` App Server generators are available; tracked default/experimental schemas validate and match the retained direct capture semantically. |
| C-104 | FAIL / BLOCKED | Accepted research ZIP and four required accepted files are absent; nothing was copied or reconstructed. |
| C-105 | PASS | Corrected blocked-state handoff packet is present. |
| Contract | FAIL | C-104 cannot complete, and making the repository private requires a forbidden external mutation. |
| Evidence integrity | UNKNOWN | Generated schemas validate, but accepted-research checksums cannot be checked and checked-out text does not byte-match package manifests after CRLF conversion. |
| Safety delivery | PASS | No user change was staged/reverted; no remote setting, commit, push, PR, deployment, or external write occurred. |

## Pre-existing worktree state preserved

Before evidence edits:

```text
## main...origin/main
?? CHAT_COPY_Pro_Loop_Engineering_research.md
?? codex_loops_harness_anthropic_reading_map_2026-07-18.md
?? prompt_harness.txt
```

These three user-owned files remain untracked and unchanged. `prompt_harness.txt` is a short intake note. The two Markdown files are raw research/background inputs, not the accepted C-104 package.

## Files created, changed, or copied

Changed only:

- `docs\research\local-target-context.md`
- `docs\research\codex-runtime-observations.md`
- `docs\research\app-server-protocol-observations.md`
- `handoffs\CODEX_ENVIRONMENT_HANDOFF.yaml`
- `handoffs\CODEX_ENVIRONMENT_EVIDENCE.md`

Copied: none.

Existing generated evidence inspected without rewrite:

- `docs\research\generated-app-server-schema\codex-cli-0.144.3\`

Retained direct capture outside the repository:

- `C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\`

## Commands actually run

```powershell
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git symbolic-ref --quiet HEAD
git status --short --branch
git remote -v
git worktree list --porcelain
git ls-remote --heads origin refs/heads/main
gh repo view Denys/UPE_v5.6 --json nameWithOwner,url,visibility,isPrivate,defaultBranchRef,viewerPermission

Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
wsl.exe --version
wsl.exe --status
wsl.exe --list --verbose
wsl.exe -d Ubuntu --exec sh -lc 'printf "os="; . /etc/os-release; printf "%s\n" "$PRETTY_NAME"; uname -srmo; python3 --version; uv --version 2>&1 || true; git --version; printf "codex_path="; command -v codex || echo MISSING; if command -v codex >/dev/null 2>&1; then timeout 5s codex --version; printf "codex_exit=%s\n" "$?"; fi'

py -3 --version
uv --version
git --version
git worktree -h
codex --version
Get-FileHash -Algorithm SHA256 C:\Users\denko\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe
Get-AppxPackage | Where-Object { $_.Name -match 'ChatGPT|OpenAI|Codex' -or $_.PackageFullName -match 'ChatGPT|OpenAI|Codex' } | Select-Object Name,Version

codex app-server --help
codex app-server generate-ts --help
codex app-server generate-json-schema --help

codex app-server generate-ts --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\typescript'
codex app-server generate-json-schema --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\json-schema'
codex app-server generate-ts --experimental --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\typescript'
codex app-server generate-json-schema --experimental --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\json-schema'

rg --files C:\Users\denko\CodexWork | rg -i '(Pasted markdown\.md$|chatgpt_work_harness_research_2026-07-18.*\.zip$|source-matrix\.md$|pattern-comparison\.md$|chatgpt-work-applicability\.md$|research-state\.ya?ml$)'
git config --show-origin --get core.autocrlf
git check-attr text eol -- AGENTS.md chatgpt_work_harness_implementation_routing_2026-07-18/NEXT_LOCAL_CODEX_PROMPT.md UPE_v5.6.0_RELEASE/01_UPE_v5.6.0_FULL_REFERENCE.md UPE_v5.6.0_RELEASE/skill/upe-v5-6/evals/trigger_cases.csv
py -3 -c "import yaml,pathlib; d=yaml.safe_load(pathlib.Path(r'C:\Users\denko\CodexWork\UPE_5.6\handoffs\CODEX_ENVIRONMENT_HANDOFF.yaml').read_text(encoding='utf-8')); assert d['codex_to_work']['status']=='blocked'; assert d['codex_to_work']['repository_root']==r'C:\Users\denko\CodexWork\UPE_5.6'; print('yaml_validation=PASS')"
git diff --check
git diff --name-only
git status --short --branch
```

PowerShell in-memory validators also ran over all three package manifests and all generated JSON files. A read-only Python comparison checked relative file sets, LF-normalized TypeScript content, and parsed JSON equality between the corrected checkout and the retained direct capture.

## Observed results

- Local HEAD and `origin/main` match at `eed3b046c5910dfc51c28b2cd7a368d609370c44`.
- Both read-only GitHub probes report `Denys/UPE_v5.6` as `PUBLIC`.
- Codex desktop `26.715.3651.0` exceeds supplied minimum `26.707.30751`.
- Codex CLI `0.144.3` exceeds supplied minimum `0.144.0`.
- WSL-native Codex fails with `exec: node: Permission denied`, exit `126`.
- App Server and both generators are available on Windows and explicitly labeled experimental.
- Schema counts: 598 non-`--experimental` TypeScript, 267 non-`--experimental` JSON, 671 experimental TypeScript, and 337 experimental JSON.
- All 604 tracked JSON schema files parse; no TypeScript file is empty.
- The tracked and direct-capture file sets match. TypeScript matches after LF normalization; parsed JSON objects match. The only normalized JSON text difference is object-key ordering in one aggregate v2 schema file per bundle.
- No `Pasted markdown.md`, accepted research ZIP, `source-matrix.md`, `pattern-comparison.md`, `chatgpt-work-applicability.md`, or `research-state.yaml` exists under `C:\Users\denko\CodexWork`.
- Checkout-byte manifest results are root 0/3, routing 0/8, release 1/26. Root/routing content fully matches after LF normalization; release entries match per-file using raw bytes for the CSV and LF-normalized bytes for the other 25.
- The cause is directly observable: `.gitattributes` uses `* text=auto` and system Git sets `core.autocrlf=true`.
- Handoff YAML parses and corrected repository/status assertions pass.
- `git diff --check` exits `0`; the only tracked modifications are the three research observations and two handoff files listed above.

## Unresolved conflicts and unknowns

1. GitHub repository visibility is public, but the original requirement says private. Resolving it requires an external GitHub settings mutation.
2. The legacy `upstream` remote still points to `denkovtll/UPE_v5.6`.
3. `Pasted markdown.md` is absent; `prompt_harness.txt` is only an intake note.
4. The accepted research archive and all four C-104 output files are absent.
5. Checked-out text bytes do not satisfy the supplied manifest hashes after CRLF conversion; no line-ending policy repair was authorized.
6. WSL lacks native Node/Codex and cannot invoke the inherited Windows npm shim.
7. Docker was not probed because no Docker configuration or material requirement exists.

## Exact evidence paths

- `C:\Users\denko\CodexWork\UPE_5.6\docs\research\local-target-context.md`
- `C:\Users\denko\CodexWork\UPE_5.6\docs\research\codex-runtime-observations.md`
- `C:\Users\denko\CodexWork\UPE_5.6\docs\research\app-server-protocol-observations.md`
- `C:\Users\denko\CodexWork\UPE_5.6\docs\research\generated-app-server-schema\codex-cli-0.144.3\`
- `C:\Users\denko\CodexWork\UPE_5.6\handoffs\CODEX_ENVIRONMENT_HANDOFF.yaml`
- `C:\Users\denko\CodexWork\UPE_5.6\handoffs\CODEX_ENVIRONMENT_EVIDENCE.md`

## Next action

Upload the two handoff files to ChatGPT Work for `W-101`. Provide the accepted research package before ADR reconciliation.
