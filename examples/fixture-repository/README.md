# Deterministic fixture repository

This directory contains the committed seed for canonical task `C-305`. The seed is ordinary,
inspectable source: it does not contain Git metadata, credentials, generated state, or harness
lifecycle behavior.

`scripts/bootstrap.sh` copies `seed/` into the ignored `.fixture-output/repository/` directory,
initializes a one-commit Git repository, and uses a fixed local identity and timestamp. Re-running
bootstrap safely replaces only that marked output directory and produces the same initial commit.
The ignored `.fixture-output.owner` marker is adjacent to the removable directory so interrupted
cleanup cannot erase its recovery authority.

Bootstrap and both verification scripts share a Windows-native path guard. Before deletion or
execution it rejects reparse points, validates the marker, and proves the generated repository is
exactly the `repository/` child of the owned output directory.

The fixture deliberately has two contracts:

- the baseline classifies positive and zero values and passes;
- negative-number classification is intentionally unimplemented and provides a stable repair task.

From PowerShell on the supported Windows-native target, invoke the scripts with Git Bash:

```powershell
& 'C:\Program Files\Git\usr\bin\bash.exe' scripts/bootstrap.sh
& 'C:\Program Files\Git\usr\bin\bash.exe' scripts/verify-fast.sh
& 'C:\Program Files\Git\usr\bin\bash.exe' scripts/verify-full.sh
```

The known negative cases are explicit and return exit code `1`:

```powershell
& 'C:\Program Files\Git\usr\bin\bash.exe' scripts/verify-fast.sh --known-failure
& 'C:\Program Files\Git\usr\bin\bash.exe' scripts/verify-full.sh --known-failure
```

The generated repository and owner marker are disposable local test data. The committed `seed/`
remains the source of truth; neither ignored path may be staged.
