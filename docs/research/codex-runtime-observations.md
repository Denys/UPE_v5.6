# C-102 Codex Runtime Observations

**Captured:** 2026-07-18T19:42:13.2622869+02:00
**Status:** PASS for bounded inventory; WSL-native Codex is FAIL

## Host and WSL identity

| Surface | Observed result | Finding |
|---|---|---|
| Windows host | Windows 11 Home, version/build `10.0.22621`, 64-bit | PASS |
| WSL platform | WSL `2.7.10.0`; kernel package `6.18.33.2-2`; default distribution `Ubuntu`; default version `2` | PASS |
| WSL OS | Ubuntu `24.04.3 LTS`, kernel `6.18.33.2-microsoft-standard-WSL2`, x86_64 | PASS |

## Development tools

| Component | Windows observation | WSL observation | Finding |
|---|---|---|---|
| Python | `Python 3.14.3` | `Python 3.12.3` | Installed PASS; project compatibility UNKNOWN because no implementation manifest exists |
| uv | `uv 0.11.25 (1fc7de7c4 2026-06-26 x86_64-pc-windows-msvc)` | `uv 0.9.25` | PASS |
| Git | `git version 2.53.0.windows.1` | `git version 2.43.0` | PASS |
| Git worktree | `git worktree -h` lists add/list/lock/move/prune/remove/repair/unlock; help exits `129`, as Git usage help commonly does | WSL Git version is worktree-capable; no mutation attempted | PASS |
| Codex CLI | `codex-cli 0.144.3` at `C:\Users\denko\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` | Resolves the Windows npm shim at `/mnt/c/Users/denko/AppData/Roaming/npm/codex`, then exits `126` with `exec: node: Permission denied` | Windows PASS; WSL FAIL |
| Codex desktop | App package `OpenAI.Codex` version `26.715.3651.0` | Not applicable | PASS |
| ChatGPT desktop classic | App package `OpenAI.ChatGPT-Desktop` version `1.2026.190.0` | Not applicable | Observed; supplied desktop minimum does not use this package numbering |
| App Server | `app-server --help`, `generate-ts --help`, and `generate-json-schema --help` exit `0`; all are labeled `[experimental]` | Blocked by the missing WSL-native Node/Codex toolchain | Windows PASS; WSL FAIL |
| Docker | No Dockerfile or Compose configuration; not materially required | Not run | NOT APPLICABLE |

The exact WSL blocker is a missing native Node/Codex installation combined with an inherited Windows npm shim that WSL cannot execute. App Server evidence therefore comes from the functioning Windows Codex CLI. This does not prove that a WSL-native harness runtime is ready.

## Required minimum comparison

| Surface | Installed | Supplied minimum | Finding |
|---|---:|---:|---|
| Codex desktop mode | `26.715.3651.0` | `26.707.30751` | PASS |
| Codex CLI | `0.144.3` | `0.144.0` | PASS |

The standalone CLI executable SHA-256 is `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`.

## Commands

```powershell
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
```
