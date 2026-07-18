# Codex Environment Evidence — C-101 through C-105

**Captured:** 2026-07-18T18:58:11.3504065+02:00
**Overall status:** BLOCKED

## Repository and runtime identity

- Repository: `C:\Users\denko\CodexWork\UPE_v5.6`
- Git: `refs/heads/main` at `ce15f58028d2ca8c0a56820601747b2f872c4903`
- Remote: private `https://github.com/denkovtll/UPE_v5.6`, default branch `main`, viewer permission `ADMIN`.
- Remote `main` matches local HEAD. The GitHub app connector returned 404; authenticated local `gh` supplied the private-repository evidence.
- Windows: Windows 11 Home `10.0.22621`, 64-bit.
- WSL: 2.7.10.0; Ubuntu 24.04.3 LTS on WSL2.
- Windows tools: Python 3.14.3; uv 0.11.25; Git 2.53.0.windows.1; Codex CLI 0.144.3.
- WSL tools: Python 3.12.3; uv 0.9.25; Git 2.43.0; native Codex unavailable.
- Codex desktop package: 26.715.3651.0; ChatGPT desktop classic: 1.2026.190.0.
- App Server generator: Codex CLI 0.144.3, executable SHA-256 `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`.

## PASS / FAIL / UNKNOWN

| Item | Result | Direct finding |
|---|---|---|
| C-101 | PASS | Repository/ref/remote/worktree are unambiguous; concurrent unrelated changes are recorded and preserved. |
| C-102 | PASS | Runtime inventory complete; supplied Codex minimums pass. WSL-native Codex separately FAILS with exit 126. |
| C-103 | PASS | Fresh default and experimental schema captures semantically match tracked CLI 0.144.3 evidence. |
| C-104 | FAIL / BLOCKED | Accepted research ZIP and four accepted files are absent; nothing was copied or reconstructed. |
| C-105 | PASS | Blocked-state handoff packet refreshed. |
| Contract | FAIL | C-104 and the named authoritative build brief remain unavailable. |
| Evidence integrity | UNKNOWN | Local manifests/runtime/schema evidence validate, but accepted research checksums cannot be checked. |
| Safety delivery | PASS | No user change was staged/reverted; no commit, push, PR, deployment, or external write occurred. |

## Pre-existing worktree changes preserved

The repository was initially clean. During inspection, the following user-owned changes appeared before Codex edited any evidence file:

```text
 D 01_UPE_v5.6.0_FULL_REFERENCE.md
 D 02_UPE_v5.6.0_PROJECT_INSTRUCTIONS_KERNEL.md
 D 03_UPE_v5.6.0_PORTABLE_KERNEL.md
 D 04_GPT_5.6_RUNTIME_PROFILE.md
 D 05_CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md
 D 06_SOURCE_MAP.md
 D 07_CHANGELOG_AND_MIGRATION.md
 D 08_EVAL_SUITE.md
 D 09_CAPABILITY_REGISTRY_TEMPLATE.yaml
 D 10_UPE_STATE_TEMPLATE.yaml
 D 11_VALIDATION_REPORT.md
 D MANIFEST.json
 D README.md
 D evals/acceptance_cases.yaml
 D skill/upe-v5-6/SKILL.md
 D skill/upe-v5-6/assets/capability_registry_template.yaml
 D skill/upe-v5-6/assets/evaluation_report_template.md
 D skill/upe-v5-6/assets/upe_state_template.yaml
 D skill/upe-v5-6/evals/acceptance_cases.yaml
 D skill/upe-v5-6/evals/trigger_cases.csv
 D skill/upe-v5-6/references/CAPABILITY_PLUGIN_OPPORTUNITY_SCAN.md
 D skill/upe-v5-6/references/GPT_5.6_RUNTIME_PROFILE.md
 D skill/upe-v5-6/references/SOURCE_MAP.md
 D skill/upe-v5-6/references/UPE_v5.6.0_FULL_REFERENCE.md
 D skill/upe-v5-6/references/UPE_v5.6.0_PORTABLE_KERNEL.md
 D skill/upe-v5-6/references/UPE_v5.6.0_PROJECT_INSTRUCTIONS_KERNEL.md
 D skill/upe-v5-6/scripts/validate_package.py
?? AGENTS.md
?? MANIFEST.sha256
?? RUN_01_LOCAL_CODEX_SOL_HIGH.md
?? RUN_02_WEB_SOL_PRO.md
?? RUN_SUMMARY.json
?? UPE_v5.6.0_RELEASE/
```

The nested release manifest validates 26/26 entries. These changes were left unmodified and un-staged.

During final verification, `?? harness-for-every-task/` also appeared; it contains `harness-for-every-task-anthropic.pdf`. This additional user-owned input was preserved. It is not the named accepted research ZIP or one of the four C-104 files.

## Files created, changed, or copied by this pass

Changed only:

- `docs\research\local-target-context.md`
- `docs\research\codex-runtime-observations.md`
- `docs\research\app-server-protocol-observations.md`
- `handoffs\CODEX_ENVIRONMENT_HANDOFF.yaml`
- `handoffs\CODEX_ENVIRONMENT_EVIDENCE.md`

Copied: none. No accepted research artifact was available.

Temporary verification output was created at `C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806`. It remains outside the repository because recursive cleanup was rejected by execution policy after path validation.

## Commands actually run

```powershell
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' rev-parse --show-toplevel
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' status --short --branch
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' rev-parse --verify HEAD
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' symbolic-ref --quiet --short HEAD
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' remote -v
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' worktree list --porcelain
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' ls-remote --heads origin refs/heads/main
gh repo view denkovtll/UPE_v5.6 --json nameWithOwner,url,visibility,isPrivate,defaultBranchRef,viewerPermission
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
codex app-server generate-ts --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\typescript'
codex app-server generate-json-schema --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\json-schema'
codex app-server generate-ts --experimental --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\typescript'
codex app-server generate-json-schema --experimental --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\json-schema'
rg --files 'C:\Users\denko\CodexWork' | rg -i '(Pasted markdown\.md$|chatgpt_work_harness_research_2026-07-18.*\.zip$|source-matrix\.md$|pattern-comparison\.md$|chatgpt-work-applicability\.md$|research-state\.ya?ml$)'
```

Additional exact checksum, JSON-semantic-comparison, YAML-validation, and diff commands are recorded in the three `docs\research\*-observations.md` files and the YAML handoff.

## Observed verification

- Private remote `main` and local HEAD match.
- Nested release manifest: 26 entries, 0 mismatches.
- Root run manifest: 3 entries, 0 mismatches.
- Routing manifest: 8 entries, 0 mismatches.
- Fresh schema TypeScript bundles: raw-identical to tracked bundles.
- Fresh schema JSON bundles: 604/604 parse; canonical default and experimental bundle hashes match tracked evidence.
- Default canonical JSON SHA-256: `354c12557637eb8f10834dce9a03e6e2aeedffda5e26daa7192c9b83ed99c430`.
- Experimental canonical JSON SHA-256: `e55f70390a03e454a8d77ae15e3cff5bc8f469f3371b96045b7430abdd4aa085`.
- `git diff --check`: PASS.
- Codex-modified tracked paths: exactly the three research observation files and two handoff files listed above.

## Unresolved conflicts and unknowns

1. `Pasted markdown.md` is absent across `C:\Users\denko\CodexWork`.
2. `chatgpt_work_harness_research_2026-07-18.zip` and the four accepted C-104 files are absent.
3. The repository contains a concurrent uncommitted release relocation and new run files. They are preserved, but their intended final Git state is outside this pass.
4. An untracked Anthropic PDF appeared during verification; it was preserved but does not satisfy the accepted research-package contract.
5. WSL lacks native Node/Codex; its inherited Windows npm shim fails with exit 126.
6. The GitHub app connector cannot see the private repository, although local `gh` has ADMIN access.
7. Docker remains UNKNOWN by instruction because no configuration or material requirement exists.
8. Temporary schema verification output remains outside the repository because cleanup was policy-blocked.

## Exact evidence paths

- `C:\Users\denko\CodexWork\UPE_v5.6\docs\research\local-target-context.md`
- `C:\Users\denko\CodexWork\UPE_v5.6\docs\research\codex-runtime-observations.md`
- `C:\Users\denko\CodexWork\UPE_v5.6\docs\research\app-server-protocol-observations.md`
- `C:\Users\denko\CodexWork\UPE_v5.6\docs\research\generated-app-server-schema\codex-cli-0.144.3\`
- `C:\Users\denko\CodexWork\UPE_v5.6\handoffs\CODEX_ENVIRONMENT_HANDOFF.yaml`
- `C:\Users\denko\CodexWork\UPE_v5.6\handoffs\CODEX_ENVIRONMENT_EVIDENCE.md`

## Next action

Upload the two handoff files to ChatGPT Work for `W-101` / Run 02. Supply the missing authoritative build brief and accepted research package before architecture reconciliation.
