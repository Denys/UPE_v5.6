# C-103 App Server Protocol Observations

**Captured:** 2026-07-18T18:34:41.6551604+02:00  
**Status:** PASS for schema capture; runtime handshake not attempted

## Generator identity

- Codex CLI: `codex-cli 0.144.3`
- Executable: `C:\Users\denko\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`
- Executable SHA-256: `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`
- `codex app-server --help`, `generate-ts --help`, and `generate-json-schema --help` all exited `0`.
- App Server and both schema generators are explicitly labeled `[experimental]` by the installed CLI.

## Exact generation commands

```powershell
codex app-server generate-ts --out 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\stable\typescript'
codex app-server generate-json-schema --out 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\stable\json-schema'
codex app-server generate-ts --experimental --out 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\experimental\typescript'
codex app-server generate-json-schema --experimental --out 'C:\Users\denko\CodexWork\UPE_v5.6.0_RELEASE\docs\research\generated-app-server-schema\codex-cli-0.144.3\experimental\json-schema'
```

All four commands exited `0` without diagnostic output.

## Generated inventory

The aggregate digest is SHA-256 over UTF-8 lines sorted by relative path, each line formatted as `relative/path|individual_file_sha256` and joined with LF.

| Bundle | Files | Bytes | Aggregate SHA-256 |
|---|---:|---:|---|
| Stable/default TypeScript | 598 | 322,075 | `b212b90f6e7f0aa22ba5c17ee1c2485a0fcd6ee4da022ec8b0cdea09fca6654b` |
| Stable/default JSON Schema | 267 | 2,720,160 | `7b237405b396e1f1d6a95dbad4c7dbae92540b722ccf970cd0fcc1dc149e41ae` |
| Experimental TypeScript | 671 | 377,094 | `b5cdb364733456354ed5d246118ff6e302232b8c9e51e8f939bb7e3587bd1c4f` |
| Experimental JSON Schema | 337 | 3,159,797 | `62b678122d5ae98150638806c26fc9e4389a1217c5651aac8f86fef74d104716` |

Validation inspected 604 JSON files with 0 parse failures and 1,269 TypeScript files with 0 empty files.

## Experimental and unsupported-for-v0 labeling

Everything under `experimental\` was generated only with `--experimental`. It is evidence of an exposed installed-version surface, not a stability or support commitment, and must be treated as unsupported for the v0 architecture unless later official/runtime evidence explicitly promotes it.

Relative to the default bundle, experimental-only types include fuzzy-file-search sessions and v2 collaboration-mode, current-time, environment, memory-reset, process, remote-control, background-terminal, elicitation, thread-items, thread-memory-mode, realtime, thread-search, thread-settings, and thread-turn-list surfaces. Common aggregate schemas also differ when experimental methods are enabled. No adapter behavior should be inferred from names alone.

## Boundary of this capture

No App Server daemon, initialize handshake, thread, turn, approval, or event-order smoke test was run. No adapter was built. The schema artifacts establish only what CLI `0.144.3` can generate on this machine.
