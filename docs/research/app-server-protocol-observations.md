# C-103 App Server Protocol Observations

**Captured:** 2026-07-18T19:42:13.2622869+02:00
**Status:** PASS for installed-version schema inspection; runtime handshake not attempted

## Generator identity

- Codex CLI: `codex-cli 0.144.3`
- Executable: `C:\Users\denko\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`
- Executable SHA-256: `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`
- `codex app-server --help`, `generate-ts --help`, and `generate-json-schema --help` each exited `0`.
- The installed CLI explicitly labels App Server and both schema generators `[experimental]`.

## Tracked installed-version surface

The corrected repository contains the generated surface at:

`C:\Users\denko\CodexWork\UPE_5.6\docs\research\generated-app-server-schema\codex-cli-0.144.3`

| Bundle | Files | Empty files | Validation |
|---|---:|---:|---|
| Non-`--experimental` TypeScript | 598 | 0 | PASS |
| Non-`--experimental` JSON Schema | 267 | 0 | PASS |
| `--experimental` TypeScript | 671 | 0 | PASS |
| `--experimental` JSON Schema | 337 | 0 | PASS |

All 604 tracked JSON files parse successfully.

## Direct capture comparison

The direct four-bundle capture retained from this session is at:

`C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806`

It was produced with:

```powershell
codex app-server generate-ts --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\typescript'
codex app-server generate-json-schema --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\default\json-schema'
codex app-server generate-ts --experimental --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\typescript'
codex app-server generate-json-schema --experimental --out 'C:\Users\denko\AppData\Local\Temp\upe-c103-codex-0.144.3-1784393795806\experimental\json-schema'
```

All four generator commands exited `0`. The retained capture and corrected-repository artifacts have identical relative file sets and counts.

Because the corrected checkout uses CRLF, raw bytes differ across all generated text files. After LF normalization:

- both TypeScript bundles have zero differences;
- both JSON bundles have zero parsed-object differences;
- each JSON bundle has one text difference in `codex_app_server_protocol.v2.schemas.json`, limited to object-key ordering.

No tracked schema was regenerated or rewritten during the corrected-target refresh.

## Experimental and unsupported-for-v0 labeling

The repository directory named `stable` means only “generated without `--experimental`.” It is not an API stability guarantee because CLI `0.144.3` labels the entire App Server surface experimental.

Everything under `experimental` was emitted only with `--experimental` and is unsupported for v0 architecture commitments unless later official/runtime evidence promotes it. Experimental-only names do not establish runtime behavior, ordering, persistence, or recovery semantics.

## Boundary

No App Server daemon, initialize handshake, thread, turn, approval, reconnect, or event-order smoke test was run. No adapter was built. This evidence proves only the TypeScript/JSON schema surface emitted by the installed CLI and inspected in the corrected repository.
