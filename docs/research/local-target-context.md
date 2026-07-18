# C-101 Local Target Context

**Captured:** 2026-07-18T18:58:11.3504065+02:00
**Status:** PASS; unrelated concurrent worktree changes preserved

## Repository identity

- Repository root: `C:\Users\denko\CodexWork\UPE_v5.6`
- Branch: `main`
- Git ref: `refs/heads/main`
- Commit: `ce15f58028d2ca8c0a56820601747b2f872c4903`
- Worktree: `C:/Users/denko/CodexWork/UPE_v5.6`
- Remote: `origin` → `https://github.com/denkovtll/UPE_v5.6.git`
- Remote `refs/heads/main`: `ce15f58028d2ca8c0a56820601747b2f872c4903`, matching local HEAD at inspection.
- GitHub identity: `denkovtll/UPE_v5.6`, private, default branch `main`, viewer permission `ADMIN`, verified with read-only `gh repo view`.
- Target identity: unambiguous.

The connected GitHub app returned 404 for this private repository, so connector visibility is unavailable. Local Git and authenticated read-only `gh` checks establish the repository identity; no connector or GitHub write was performed.

## Current worktree state to preserve

The first snapshot was clean (`## main...origin/main`). During inspection, unrelated user-owned changes appeared. Before any Codex edit, `git status --short` showed:

- 27 tracked release-pack paths deleted from the repository root, including root `README.md`, `MANIFEST.json`, `evals/`, and `skill/` content;
- untracked `AGENTS.md`, `MANIFEST.sha256`, `RUN_01_LOCAL_CODEX_SOL_HIGH.md`, `RUN_02_WEB_SOL_PRO.md`, `RUN_SUMMARY.json`, and `UPE_v5.6.0_RELEASE/`;
- the release pack reappearing under untracked `UPE_v5.6.0_RELEASE/`.

These changes were not made, staged, reverted, or normalized by this pass. The nested release manifest contains 26 entries with 0 checksum mismatches, consistent with an intact relocation, but Git rename classification was not assumed or staged.

During final verification, untracked `harness-for-every-task\harness-for-every-task-anthropic.pdf` also appeared. It is preserved as additional user-owned state and is not the named accepted research archive or any of the four C-104 artifacts.

## Instruction, README, manifest, and configuration inspection

- Applicable root `AGENTS.md` was read after it appeared. No nested `AGENTS.md` applies to `docs/research/` or `handoffs/`.
- The current root `README.md` is deleted in the worktree; `UPE_v5.6.0_RELEASE\README.md` and the routing-package `README.md` were read.
- `.gitattributes` contains `* text=auto` after a comment describing LF normalization.
- `UPE_v5.6.0_RELEASE\MANIFEST.json`: 26 entries, 0 missing or mismatched.
- Root `MANIFEST.sha256`: 3 entries, 0 missing or mismatched.
- Routing `MANIFEST.sha256`: 8 entries, 0 missing or mismatched.
- `harness_implementation_backlog.yaml`, `CURRENT_PRODUCT_DELTA_2026-07-18.md`, `WORK_CODEX_HANDOFF_TEMPLATE.yaml`, `NEXT_LOCAL_CODEX_PROMPT.md`, and `RUN_01_LOCAL_CODEX_SOL_HIGH.md` were read.
- No `pyproject.toml`, `uv.lock`, `requirements*.txt`, `package.json`, `Cargo.toml`, `go.mod`, Dockerfile, or Compose file was found.
- `Pasted markdown.md` was not found under `C:\Users\denko\CodexWork`; the available `UPE_tasks_downloads\prompt_harness.txt` is only a short routing request, not the named authoritative build brief.

## Commands

```powershell
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' rev-parse --show-toplevel
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' branch --show-current
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' rev-parse HEAD
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' status --short --branch
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' worktree list --porcelain
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' remote -v
git -C 'C:\Users\denko\CodexWork\UPE_v5.6' ls-remote --heads origin refs/heads/main
gh repo view denkovtll/UPE_v5.6 --json nameWithOwner,url,visibility,isPrivate,defaultBranchRef,viewerPermission
```

## Finding

`C-101` is `PASS`: repository identity, ref, remote, worktree state, instructions, manifests, and unrelated local changes are recorded. The concurrent reorganization remains fully preserved and uncommitted.
