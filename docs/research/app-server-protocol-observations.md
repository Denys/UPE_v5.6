# C-103 App Server Protocol Observations

**Captured:** 2026-07-18T18:58:11.3504065+02:00
**Status:** PASS for installed-version schema capture; runtime handshake not attempted

## Generator identity

- Codex CLI: `codex-cli 0.144.3`
- Executable: `C:\Users\denko\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`
- Executable SHA-256: `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`
- `codex app-server --help`, `generate-ts --help`, and `generate-json-schema --help` exited `0`.
- The installed CLI explicitly labels App Server and both generators `[experimental]`.

## Fresh capture and tracked-artifact comparison

A fresh four-bundle capture was generated outside the worktree at `C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806` to avoid overwriting tracked evidence while unrelated worktree changes were present.

```powershell
codex app-server generate-ts --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\typescript'
codex app-server generate-json-schema --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\json-schema'
codex app-server generate-ts --experimental --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\typescript'
codex app-server generate-json-schema --experimental --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\json-schema'
```

All four commands exited `0`.

| Bundle | Tracked files | Fresh files | Raw manifest differences | Semantic result |
|---|---:|---:|---:|---|
| Default TypeScript | 598 | 598 | 0 | Identical |
| Default JSON Schema | 267 | 267 | 2 manifest lines | Semantically identical |
| Experimental TypeScript | 671 | 671 | 0 | Identical |
| Experimental JSON Schema | 337 | 337 | 2 manifest lines | Semantically identical |

The only raw differences were key ordering in `codex_app_server_protocol.v2.schemas.json` in each JSON bundle. Parsed JSON objects were equal and byte sizes matched. Canonical JSON bundle SHA-256 values matched fresh versus tracked:

- default: `354c12557637eb8f10834dce9a03e6e2aeedffda5e26daa7192c9b83ed99c430`
- experimental: `e55f70390a03e454a8d77ae15e3cff5bc8f469f3371b96045b7430abdd4aa085`

All 604 fresh JSON files parsed successfully. No tracked schema file was rewritten.

## Experimental and unsupported-for-v0 labeling

The repository's `stable\` directory means only “generated without `--experimental`”; it is not a stability guarantee because the whole App Server surface is labeled experimental by CLI `0.144.3`.

Everything under `experimental\` was emitted only with `--experimental` and is unsupported for v0 architecture commitments unless later official/runtime evidence explicitly promotes it. Experimental-only surfaces include fuzzy-file-search sessions and v2 collaboration-mode, current-time, environment, memory-reset, process, remote-control, background-terminal, elicitation, thread-items, thread-memory-mode, realtime, thread-search, thread-settings, and thread-turn-list types. Names alone do not establish behavior or event ordering.

## Boundary and cleanup status

No App Server daemon, initialize handshake, thread, turn, approval, or event-order smoke test was run. No adapter was built. The capture proves only the schema surface emitted by installed CLI `0.144.3`.

Cleanup of the temporary verification directory was attempted only after its resolved path was verified inside `C:\Users\denko\AppData\Local\Temp\`; recursive removal was rejected by the execution policy. The temporary directory therefore remains and is not part of the repository or handoff upload.
