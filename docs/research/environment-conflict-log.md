# Environment Conflict Log

**Date:** 2026-07-18  
**Stage:** W-101 evidence reconciliation  
**Decision owner:** ChatGPT Work / ADR-001

| ID | Conflict | Evidence | Resolution | Blocking? |
|---|---|---|---|---|
| EC-01 | Build brief and early research say WSL2-first; active operator/runtime evidence says Windows-native only | `Pasted markdown.md`; `codex-runtime-observations.md`; `local-target-context.md` | Active user/runtime evidence governs the target. Windows-native is v0 primary. WSL2 language remains historical and is not silently deleted. | No |
| EC-02 | OpenAI describes App Server as a client-facing standard while installed CLI labels the surface experimental | Official App Server article/README; local CLI `0.144.3` help and generated schemas | Adopt behind a strict adapter. Pin binary/version and generated schemas; run compatibility preflight and live smoke test; do not expose raw protocol in core modules. | No, conditional |
| EC-03 | C-103 schema inspection passed, but no live initialize/thread/turn handshake ran | `app-server-protocol-observations.md` | Architecture may freeze; real-adapter completion remains blocked until a controlled smoke test passes. | No for ADR; yes for adapter completion |
| EC-04 | Local handoff reports safety delivery FAIL because a legacy-upstream PR was merged | `CODEX_ENVIRONMENT_EVIDENCE.md`; `local-target-context.md` | Record as an external safety incident. Do not infer authorization. Target PR remains draft/unmerged. Future merge/release requires explicit approval. | No for ADR |
| EC-05 | Repository is intentionally public while older requirements expected private | Active operator note and GitHub observation | Public visibility is accepted temporarily. Any visibility change/private recreation is a separate post-gate action. | No |
| EC-06 | Python 3.14.3 is installed; build brief says Python 3.12+ but no manifest exists | Runtime observation; build brief | Keep architecture language at Python 3.12+. Establish an actual supported range through dependency resolution and tests during scaffold implementation. | No |
| EC-07 | No CI checks protect the PR | GitHub/local evidence | Require deterministic local validation now and CI before release readiness. CI absence does not block architecture or specification work. | No |
| EC-08 | Work/App Server threads preserve context, but the harness needs crash-safe canonical state | Official docs and research comparison | SQLite + JSONL + repository artifacts are canonical. Thread/conversation state is execution context only. | No |

## Resolution rule

Conflicts are resolved by instruction authority and discriminating evidence:

1. active user/runtime scope;
2. current official documentation for intended semantics;
3. installed-version observations for compatibility;
4. inference;
5. recommendation.

Unknowns remain explicit and are attached to the narrow phase they block.
