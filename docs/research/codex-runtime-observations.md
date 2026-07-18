# C-102 Codex Runtime Observations

**Captured:** 2026-07-18T18:34:41.6551604+02:00  
**Status:** PASS with one WSL-specific blocker

## Host and WSL identity

| Surface | Observed result | Finding |
|---|---|---|
| Windows host | Windows 11 Home, version/build `10.0.22621`, 64-bit | PASS |
| WSL | WSL `2.7.10.0`; kernel `6.18.33.2-2`; default distribution `Ubuntu`; default version `2` | PASS |
| WSL OS | Ubuntu `24.04.3 LTS` (Noble), kernel `6.18.33.2-microsoft-standard-WSL2`, x86_64 | PASS |

## Development tools

| Component | Windows observation | WSL observation | Finding |
|---|---|---|---|
| Python | `py -3 --version` → `Python 3.14.3`; launcher also has 3.13, 3.12, 3.11, and 3.9 | `/usr/bin/python3` → `Python 3.12.3` | PASS; project compatibility is UNKNOWN because no project manifest exists |
| uv | `uv 0.11.25 (1fc7de7c4 2026-06-26 x86_64-pc-windows-msvc)` | `/home/denkov/.local/bin/uv` → `uv 0.9.25` | PASS |
| Git | `git version 2.53.0.windows.1` | `git version 2.43.0` | PASS |
| Git worktree | `git worktree -h` printed the add/list/lock/move/prune/remove/repair/unlock surface | WSL `git worktree -h` printed the worktree surface | PASS; repository-specific use is unavailable because no repository exists |
| Codex CLI | `codex-cli 0.144.3` at `C:\Users\denko\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` | Windows npm shim found at `/mnt/c/Users/denko/AppData/Roaming/npm/codex`, but execution failed with exit `126`: `exec: node: Permission denied` | Windows PASS; WSL FAIL |
| Codex desktop | App package `OpenAI.Codex` version `26.715.3651.0` | Not applicable | PASS |
| ChatGPT desktop classic | App package `OpenAI.ChatGPT-Desktop` version `1.2026.190.0` | Not applicable | Observed; no minimum supplied for this package numbering |
| App Server | `codex app-server --help` exited `0`; both schema generators are exposed and marked `[experimental]` | WSL invocation blocked with Codex shim | Windows PASS; WSL FAIL |
| Docker | No Dockerfile or Compose configuration found; Docker is not materially required for this pass | Not run by instruction | NOT APPLICABLE |

The WSL Codex blocker is specific: no WSL-native `node` or Codex installation was found, while the WSL `PATH` resolves Windows npm shims. The Windows `codex` executable is usable and supplied the generated protocol evidence.

## Required minimum comparison

| Surface | Installed | Supplied minimum | Finding |
|---|---:|---:|---|
| Codex desktop mode | `26.715.3651.0` | `26.707.30751` | PASS (`[version]` comparison returned `True`) |
| Codex CLI | `0.144.3` | `0.144.0` | PASS (`[version]` comparison returned `True`) |

The standalone Windows CLI executable SHA-256 is `e5dcc9f9b08102c58596af85345f689a69fd53a87d8d408bdc0fcdaf99fcf6e3`. The desktop package's bundled resource executable SHA-256 is `20d611ef1c9851f4da1cb4609beb6763904f72275cb91517b2400639ca1c28c4`, but direct execution of that protected WindowsApps path was denied; its CLI version is therefore UNKNOWN. Schema capture is tied to the usable standalone CLI, not inferred from the package resource.

## Principal commands

```powershell
Get-CimInstance Win32_OperatingSystem | Select-Object Caption,Version,BuildNumber,OSArchitecture | Format-List
wsl.exe --version
wsl.exe --status
wsl.exe --list --verbose
wsl.exe -d Ubuntu --exec sh -lc 'echo DISTRIBUTION=Ubuntu; cat /etc/os-release; uname -srmo; printf "python3="; python3 --version 2>&1; printf "python3_path="; command -v python3 || true; printf "uv="; uv --version 2>&1 || true; printf "uv_path="; command -v uv || true; printf "git="; git --version 2>&1; printf "codex="; codex --version 2>&1 || true; printf "codex_path="; command -v codex || true'
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
