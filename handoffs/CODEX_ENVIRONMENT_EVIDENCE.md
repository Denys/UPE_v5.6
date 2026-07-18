# Codex Environment Evidence — C-101 through C-105

**Captured:** 2026-07-18T22:43:25.4294702+02:00
**Overall:** TESTED LOCALLY; SAFETY DELIVERY FAIL

## Repository and runtime identity

- Intended repository root: `C:\Users\denko\CodexWork\UPE_5.6`.
- Validation worktree: `C:\Users\denko\CodexWork\UPE_5.6_pr1_fix`.
- Baseline: `refs/heads/main` at `f4ff123e0723b5047bb17eaa23f419534bf5abb4`.
- Delivery branch: `refs/heads/agent/windows-materialization-handoff-refresh`.
- Materialization commit: `ecd9415e6caa60e4e8746fdf79e9a8b3fb3af262`, whose parent is the baseline.
- Target PR: `Denys/UPE_v5.6#1`, open, draft, mergeable, and unmerged when inspected.
- Target repository: `https://github.com/Denys/UPE_v5.6`, default branch `main`, intentional temporary `PUBLIC` visibility, viewer permission `ADMIN`.
- Legacy upstream: `https://github.com/denkovtll/UPE_v5.6.git`; upstream PR #1 was independently observed merged as `bcbd6b385946420351f01a7474c285951dcfed19`.
- Active runtime: Windows-native Codex on Windows 11 Home `10.0.22621`, 64-bit.
- Python: `3.14.3`; `uv`: `0.11.25`; Git: `2.53.0.windows.1` with worktree support.
- Codex: CLI `0.144.3`; desktop package `26.715.3651.0`.
- App Server: help and TypeScript/JSON schema generators available; generated surfaces are experimental tooling.
- WSL2: `NOT APPLICABLE` for the active target. Docker: not inspected because it is neither configured evidence nor materially required before ADR-001.

## PASS / FAIL / UNKNOWN findings

| Item | Result | Direct finding |
|---|---|---|
| C-101 | PASS | Baseline, delivery branch, materialization commit, target PR, remotes, and unrelated main-worktree changes are explicit. |
| C-102 | PASS | Windows-native inventory is the active evidence; WSL2 is not a dependency. Python compatibility remains unknown until a manifest exists. |
| C-103 | PASS | Codex CLI `0.144.3` App Server help and generated TypeScript/JSON surfaces were captured and version-pinned. |
| C-104 | PASS | The build brief and four accepted research files are present at canonical paths and Git-blob-identical to verified bundle sources. |
| C-105 | PASS | The YAML and Markdown packet record template fields, commands, results, approvals, verification, conflicts, and the next action. |
| Handoff contract | PASS | All supplied top-level and nested handoff-template fields are present; `tested_locally` is an allowed status. |
| Evidence integrity | PASS | Bundle, manifest, canonical-blob, YAML, JSON, path-scope, and mutable-file whitespace checks pass. |
| Safety delivery | FAIL | A separate legacy-upstream PR was merged. Its actor and authorization chain were not established. The target `Denys/UPE_v5.6#1` PR remains draft and unmerged. |
| ADR gate | BLOCKED | `docs/architecture/ADR-001-harness-boundary.md` and `gate-records/ADR-001-PASS.yaml` do not exist. |
| External research correctness | UNKNOWN | W-101 must reconcile current official web evidence with local observations. |
| Python implementation compatibility | UNKNOWN | No accepted implementation manifest exists in this pre-ADR pass. |

## Files created or changed in the delivery diff

- `AGENTS.md`
- `Pasted markdown.md`
- `docs/research/chatgpt-work-applicability.md`
- `docs/research/codex-runtime-observations.md`
- `docs/research/local-target-context.md`
- `docs/research/pattern-comparison.md`
- `docs/research/research-state.yaml`
- `docs/research/source-matrix.md`
- `handoffs/CODEX_ENVIRONMENT_EVIDENCE.md`
- `handoffs/CODEX_ENVIRONMENT_HANDOFF.yaml`

The five accepted canonical files are Git-blob-identical to the verified nested bundle:

- `Pasted markdown.md`
- `docs/research/source-matrix.md`
- `docs/research/pattern-comparison.md`
- `docs/research/chatgpt-work-applicability.md`
- `docs/research/research-state.yaml`

The historical nested bundle remains as provenance. It was not rewritten.

## Commands actually run

```powershell
git rev-parse --show-toplevel
git branch --show-current
git rev-parse HEAD
git symbolic-ref --quiet HEAD
git status --short --branch
git remote -v
git worktree list --porcelain
git log -4 --date=iso-strict
git rev-parse refs/remotes/origin/agent/windows-materialization-handoff-refresh
git rev-parse origin/agent/windows-materialization-handoff-refresh^
gh repo view Denys/UPE_v5.6 --json nameWithOwner,url,visibility,isPrivate,defaultBranchRef,viewerPermission
gh pr view 1 --repo Denys/UPE_v5.6 --json number,state,isDraft,mergeable,baseRefName,baseRefOid,headRefName,headRefOid,commits,changedFiles,additions,deletions,url
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture
py -3 --version
uv --version
git --version
git worktree -h
codex --version
Get-FileHash -Algorithm SHA256 C:\Users\denko\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe
codex app-server --help
codex app-server generate-ts --help
codex app-server generate-json-schema --help
codex app-server generate-ts --out C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\typescript
codex app-server generate-json-schema --out C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\json-schema
codex app-server generate-ts --experimental --out C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\typescript
codex app-server generate-json-schema --experimental --out C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\json-schema
py -3 -c "import hashlib,zipfile,pathlib; r=pathlib.Path('RUN_01_COMPLETE_INPUTS_2026-07-18'); z=zipfile.ZipFile('RUN_01_COMPLETE_INPUTS_2026-07-18.zip'); names=[n for n in z.namelist() if not n.endswith('/')]; c=[x.split('  ',1) for x in z.read('CHECKSUMS.sha256').decode().splitlines() if x]; assert len(names)==14 and all(hashlib.sha256(z.read(p)).hexdigest()==h for h,p in c); rz=zipfile.ZipFile(r/'chatgpt_work_harness_research_2026-07-18.zip'); m=[x.split('  ',1) for x in (r/'RESEARCH_ORIGINAL_MANIFEST.sha256').read_text().splitlines() if x]; assert all(hashlib.sha256(rz.read('chatgpt_work_harness_research/'+p)).hexdigest()==h for h,p in m); print(f'PACKAGE_HASHES PASS outer={len(names)}/14 checksums={len(c)}/12 inner={len(m)}/6')"
py -3 -c "import json,pathlib,yaml; r=pathlib.Path('.'); t=yaml.safe_load((r/'chatgpt_work_harness_implementation_routing_2026-07-18/WORK_CODEX_HANDOFF_TEMPLATE.yaml').read_text(encoding='utf-8')); h=yaml.safe_load((r/'handoffs/CODEX_ENVIRONMENT_HANDOFF.yaml').read_text(encoding='utf-8')); s=yaml.safe_load((r/'docs/research/research-state.yaml').read_text(encoding='utf-8')); missing=[f'{section}.{key}' for section in ('work_to_codex','codex_to_work') for key in t[section] if key not in h.get(section,{})]; assert not missing and h['codex_to_work']['status'] in {'planned','implemented','tested_locally','blocked','unverified'} and h['codex_to_work']['verification']=={'contract':'PASS','evidence_integrity':'PASS','safety_delivery':'FAIL'} and s is not None; files=list((r/'docs/research/generated-app-server-schema/codex-cli-0.144.3').rglob('*.json')); [json.loads(p.read_text(encoding='utf-8')) for p in files]; print('STRUCTURE PASS template_fields=%d json=%d' % (sum(len(t[x]) for x in ('work_to_codex','codex_to_work')),len(files)))"
git diff --check f4ff123e0723b5047bb17eaa23f419534bf5abb4..HEAD -- AGENTS.md docs/research/codex-runtime-observations.md docs/research/local-target-context.md handoffs/CODEX_ENVIRONMENT_EVIDENCE.md handoffs/CODEX_ENVIRONMENT_HANDOFF.yaml
```

An exact PowerShell `git rev-parse` loop compared each canonical path at `HEAD` with its corresponding nested-source path at baseline `f4ff123e...`. Additional read-only PowerShell probes inspected changed paths, ADR/gate absence, PR state, and commit status.

## Observed results

- Outer bundle: `14/14` entries matched; `CHECKSUMS.sha256`: `12/12` raw matches; inner research manifest: `6/6` matches.
- Generated schema inventory: 598 non-experimental TypeScript, 267 non-experimental JSON, 671 experimental TypeScript, and 337 experimental JSON files; all 604 JSON files parsed.
- Codex executable SHA-256: `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`.
- Codex desktop mode and CLI exceed the supplied minimum versions `26.707.30751` and `0.144.0`.
- No ADR, gate pass, harness module, adapter, release, deployment, or target-PR merge is present.
- No CI or commit-status checks are configured for the target PR head.
- The main worktree's unrelated modified/untracked files were preserved and excluded by using the linked validation worktree.
- Full-diff whitespace checking reports existing trailing spaces in accepted research Markdown. Those bytes are intentionally preserved because canonical Git blob identity is the stronger C-104 acceptance condition. The mutable evidence-file subset passes `git diff --check`.

## Evidence paths

- `Pasted markdown.md`
- `docs/research/local-target-context.md`
- `docs/research/codex-runtime-observations.md`
- `docs/research/app-server-protocol-observations.md`
- `docs/research/generated-app-server-schema/codex-cli-0.144.3/`
- `docs/research/source-matrix.md`
- `docs/research/pattern-comparison.md`
- `docs/research/chatgpt-work-applicability.md`
- `docs/research/research-state.yaml`
- `handoffs/CODEX_ENVIRONMENT_HANDOFF.yaml`
- `handoffs/CODEX_ENVIRONMENT_EVIDENCE.md`
- `RUN_01_COMPLETE_INPUTS_2026-07-18/CHECKSUMS.sha256`
- `RUN_01_COMPLETE_INPUTS_2026-07-18/RESEARCH_ORIGINAL_MANIFEST.sha256`

## Unresolved conflicts

- The intended Windows-native target conflicts with earlier WSL2-first research assumptions; ADR-001 must decide the boundary without rewriting the research.
- The legacy-upstream merge exists, but its actor and authorization history are unknown.
- The target repository is intentionally public; private recreation or visibility change remains a separately authorized post-gate action.
- There are no CI checks.

## Next action

Upload this handoff packet to ChatGPT Work for `W-101`. Preserve the legacy-upstream merge as a safety finding, then run `W-102`, `P-101`, and `G-ADR`. Do not merge the target draft PR or begin harness implementation before review and the ADR gate passes.
