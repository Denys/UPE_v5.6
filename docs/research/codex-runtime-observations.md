# C-102 Codex Runtime Observations

**Captured:** 2026-07-18T18:58:11.3504065+02:00
**Status:** PASS for inventory; WSL-native Codex remains FAIL

## Host and WSL identity

| Surface | Observed result | Finding |
|---|---|---|
| Windows host | Windows 11 Home, version/build `10.0.22621`, 64-bit | PASS |
| WSL | WSL `2.7.10.0`; kernel `6.18.33.2-2`; default distribution `Ubuntu`; default version `2` | PASS |
| WSL OS | Ubuntu `24.04.3 LTS` (Noble), kernel `6.18.33.2-microsoft-standard-WSL2`, x86_64 | PASS |

## Development tools

| Component | Windows observation | WSL observation | Finding |
|---|---|---|---|
| Python | `Python 3.14.3`; launcher also exposes 3.13, 3.12, 3.11, and 3.9 | `/usr/bin/python3` → `Python 3.12.3` | PASS; project compatibility UNKNOWN because no implementation manifest exists |
| uv | `uv 0.11.25 (1fc7de7c4 2026-06-26 x86_64-pc-windows-msvc)` | `uv 0.9.25` | PASS |
| Git | `git version 2.53.0.windows.1` | `git version 2.43.0` | PASS |
| Git worktree | `git worktree -h` exposed add/list/lock/move/prune/remove/repair/unlock | WSL Git exposes worktree support | PASS |
| Codex CLI | `codex-cli 0.144.3` at `C:\Users\denko\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` | Windows npm shim resolves at `/mnt/c/Users/denko/AppData/Roaming/npm/codex`, then fails with exit `126`: `exec: node: Permission denied` | Windows PASS; WSL FAIL |
| Codex desktop | App package `OpenAI.Codex` version `26.715.3651.0` | Not applicable | PASS |
| ChatGPT desktop classic | App package `OpenAI.ChatGPT-Desktop` version `1.2026.190.0` | Not applicable | Observed; no supplied minimum maps to this package numbering |
| App Server | Help and both schema generators exit `0`; the installed CLI labels App Server and generators `[experimental]` | WSL invocation blocked by the missing native Node/Codex toolchain | Windows PASS; WSL FAIL |
| Docker | No Dockerfile or Compose configuration; not materially required for this evidence pass | Not run | NOT APPLICABLE |

The WSL blocker is exact: the distribution has no native Node/Codex installation, inherits a Windows npm Codex shim, and cannot execute it. Current App Server evidence therefore comes from the usable Windows Codex CLI. This does not prove a WSL-native harness runtime is ready.

## Required minimum comparison

| Surface | Installed | Supplied minimum | Finding |
|---|---:|---:|---|
| Codex desktop mode | `26.715.3651.0` | `26.707.30751` | PASS (`[version]` comparison returned `True`) |
| Codex CLI | `0.144.3` | `0.144.0` | PASS (`[version]` comparison returned `True`) |

The standalone CLI executable SHA-256 is `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`.

## Commands

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture | Format-List
wsl.exe --version
wsl.exe --status
wsl.exe --list --verbose
wsl.exe -d Ubuntu --exec sh -lc 'echo DISTRIBUTION=Ubuntu; . /etc/os-release; echo PRETTY_NAME=$PRETTY_NAME; uname -srmo; python3 --version; uv --version 2>&1 || true; git --version; printf "codex_path="; command -v codex || echo MISSING; if command -v codex >/dev/null 2>&1; then timeout 5s codex --version; echo codex_exit=$?; fi'
py -0p
py -3 --version
uv --version
git --version
git worktree -h
codex --version
codex app-server --help
codex app-server generate-ts --help
codex app-server generate-json-schema --help
Get-AppxPackage | Where-Object { $_.Name -match 'ChatGPT|OpenAI|Codex' -or $_.PackageFullName -match 'ChatGPT|OpenAI|Codex' } | Select-Object Name,Version,PackageFullName,InstallLocation | Format-List
```
