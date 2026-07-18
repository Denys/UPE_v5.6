# C-101 Local Target Context

**Captured:** 2026-07-18T19:42:13.2622869+02:00
**Status:** PASS; corrected target is unambiguous and unrelated local state is preserved

## Repository identity

- Repository root: `C:\Users\denko\CodexWork\UPE_5.6`
- Branch: `main`
- Git ref: `refs/heads/main`
- Commit: `eed3b046c5910dfc51c28b2cd7a368d609370c44`
- Worktree: `C:/Users/denko/CodexWork/UPE_5.6`
- `origin`: `https://github.com/Denys/UPE_v5.6.git`
- `upstream`: `https://github.com/denkovtll/UPE_v5.6.git`
- `origin/refs/heads/main`: `eed3b046c5910dfc51c28b2cd7a368d609370c44`, matching local HEAD.
- GitHub identity: `Denys/UPE_v5.6`, default branch `main`, viewer permission `ADMIN`.
- Live visibility: `PUBLIC`, confirmed independently by the read-only GitHub connector and `gh repo view`.
- Target identity: unambiguous because the user explicitly supplied this local path and GitHub repository, and `origin` matches it.

The original requirement said the repository should be private. The live repository is public. Changing visibility would be an external account mutation and is forbidden in this pass, so the mismatch is recorded as an unresolved blocker. The legacy `upstream` remote is preserved and was not changed.

## Worktree state to preserve

Before this corrected evidence refresh:

```text
## main...origin/main
?? CHAT_COPY_Pro_Loop_Engineering_research.md
?? codex_loops_harness_anthropic_reading_map_2026-07-18.md
?? prompt_harness.txt
```

All three files are user-owned raw inputs. They were read for classification but were not moved, copied, rewritten, staged, or treated as the accepted C-104 package.

## Instructions, README, manifests, and configuration

- Root `AGENTS.md` and `chatgpt_work_harness_implementation_routing_2026-07-18\NEXT_LOCAL_CODEX_PROMPT.md` were read and applied.
- No root `README.md` exists. The routing-package `README.md` and `UPE_v5.6.0_RELEASE\README.md` were read.
- `harness_implementation_backlog.yaml` records C-101 through C-105 as the bounded pre-ADR evidence slice.
- `CURRENT_PRODUCT_DELTA_2026-07-18.md` and `WORK_CODEX_HANDOFF_TEMPLATE.yaml` were read.
- `.gitattributes` contains `* text=auto`; system Git configuration sets `core.autocrlf=true`.
- No `pyproject.toml`, `uv.lock`, `requirements*.txt`, `package.json`, lockfile, `Cargo.toml`, `go.mod`, Dockerfile, or Compose file was found.
- `Pasted markdown.md` was not found under `C:\Users\denko\CodexWork`.
- Root `prompt_harness.txt` is a 13-line intake note referencing the two raw research attachments; it is not a detailed build brief.
- The two raw research Markdown files provide source/background material but do not carry the accepted-package labels, four required C-104 filenames, or checksum contract.

## Manifest observations

The checkout does not byte-match the supplied manifests because Git converted text to CRLF:

| Manifest | Raw SHA-256 matches | LF-normalized matches | Finding |
|---|---:|---:|---|
| Root `MANIFEST.sha256` | 0/3 | 3/3 | Content matches after line-ending normalization |
| Routing `MANIFEST.sha256` | 0/8 | 8/8 | Content matches after line-ending normalization |
| Release `MANIFEST.json` | 1/26 | 25/26 | The CSV matches raw; the other 25 match after LF normalization |

For the release manifest, each of the 26 entries matches either its raw bytes or its LF-normalized bytes. This supports content preservation, but the checked-out byte-level manifest contract is not a clean PASS and was not repaired in this evidence-only pass.

## Commands

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
git config --show-origin --get core.autocrlf
git check-attr text eol -- AGENTS.md chatgpt_work_harness_implementation_routing_2026-07-18/NEXT_LOCAL_CODEX_PROMPT.md UPE_v5.6.0_RELEASE/01_UPE_v5.6.0_FULL_REFERENCE.md UPE_v5.6.0_RELEASE/skill/upe-v5-6/evals/trigger_cases.csv
rg --files C:\Users\denko\CodexWork
```

## Finding

`C-101` is `PASS`: the corrected repository, ref, remotes, GitHub identity, configuration, and pre-existing worktree state are recorded. The public/private mismatch, legacy `upstream`, missing named build brief, and checkout line-ending checksum behavior remain explicit.
