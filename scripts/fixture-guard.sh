#!/usr/bin/env bash

# Shared Windows-native containment checks for the generated C-305 fixture.

readonly FIXTURE_OWNER_MARKER_VALUE="upe-c305-fixture-output-v1"
FIXTURE_GUARD_ERROR=""

fixture_guard_error() {
  FIXTURE_GUARD_ERROR="$1"
  return 1
}

fixture_guard_to_windows_path() {
  local path="$1"
  local drive remainder

  if [[ "$path" =~ ^/([A-Za-z])/(.*)$ ]]; then
    drive="${BASH_REMATCH[1]}"
    remainder="${BASH_REMATCH[2]//\//\\}"
    printf '%s:\\%s\n' "$drive" "$remainder"
    return 0
  fi
  if [[ "$path" =~ ^([A-Za-z]):/(.*)$ ]]; then
    drive="${BASH_REMATCH[1]}"
    remainder="${BASH_REMATCH[2]//\//\\}"
    printf '%s:\\%s\n' "$drive" "$remainder"
    return 0
  fi
  cygpath -w "$path"
}

fixture_guard_validate_layout() {
  local fixture_root="$1"
  local output_root="$2"
  local fixture_repository="$3"
  local owner_marker="$4"
  local fixture_windows output_windows repository_windows marker_windows
  local guard_output

  command -v cygpath >/dev/null 2>&1 \
    || fixture_guard_error "Git Bash path conversion utility 'cygpath' is unavailable" \
    || return 1
  command -v powershell.exe >/dev/null 2>&1 \
    || fixture_guard_error "Windows PowerShell is unavailable" \
    || return 1

  fixture_windows="$(fixture_guard_to_windows_path "$fixture_root")" \
    || fixture_guard_error "cannot resolve fixture root" \
    || return 1
  output_windows="$(fixture_guard_to_windows_path "$output_root")" \
    || fixture_guard_error "cannot resolve fixture output" \
    || return 1
  repository_windows="$(fixture_guard_to_windows_path "$fixture_repository")" \
    || fixture_guard_error "cannot resolve generated repository" \
    || return 1
  marker_windows="$(fixture_guard_to_windows_path "$owner_marker")" \
    || fixture_guard_error "cannot resolve owner marker" \
    || return 1

  if guard_output="$(
    FIXTURE_GUARD_ROOT="$fixture_windows" \
    FIXTURE_GUARD_OUTPUT="$output_windows" \
    FIXTURE_GUARD_REPOSITORY="$repository_windows" \
    FIXTURE_GUARD_MARKER="$marker_windows" \
      powershell.exe -NoLogo -NoProfile -NonInteractive -Command '
        $ErrorActionPreference = "Stop"
        $comparison = [System.StringComparison]::OrdinalIgnoreCase

        function Full-Path([string] $Path) {
          return [System.IO.Path]::GetFullPath($Path).TrimEnd("\")
        }

        function Fail-Guard([string] $Message) {
          [Console]::Error.WriteLine($Message)
          exit 10
        }

        function Find-Item([string] $Path) {
          $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
          if ($null -ne $item) {
            return $item
          }
          $parent = [System.IO.Path]::GetDirectoryName($Path)
          if (-not [System.IO.Directory]::Exists($parent)) {
            return $null
          }
          $leaf = [System.IO.Path]::GetFileName($Path)
          return Get-ChildItem -LiteralPath $parent -Force -ErrorAction Stop |
            Where-Object { $_.Name.Equals($leaf, [System.StringComparison]::OrdinalIgnoreCase) } |
            Select-Object -First 1
        }

        function Check-Item(
          [string] $Path,
          [string] $Expected,
          [string] $Label,
          [bool] $MustBeDirectory
        ) {
          $item = Find-Item $Path
          if ($null -eq $item) {
            return $null
          }
          if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            Fail-Guard "$Label path is a reparse point: $Path"
          }
          if ($MustBeDirectory -and -not $item.PSIsContainer) {
            Fail-Guard "$Label path is not a directory: $Path"
          }
          if (-not $MustBeDirectory -and $item.PSIsContainer) {
            Fail-Guard "$Label path is not a regular file: $Path"
          }
          $resolved = Full-Path $item.FullName
          if (-not $resolved.Equals($Expected, $comparison)) {
            Fail-Guard "$Label path resolved outside its exact expected location: $resolved"
          }
          return $item
        }

        $fixture = Full-Path $env:FIXTURE_GUARD_ROOT
        $output = Full-Path $env:FIXTURE_GUARD_OUTPUT
        $repository = Full-Path $env:FIXTURE_GUARD_REPOSITORY
        $marker = Full-Path $env:FIXTURE_GUARD_MARKER
        $expectedOutput = Full-Path ([System.IO.Path]::Combine($fixture, ".fixture-output"))
        $expectedRepository = Full-Path ([System.IO.Path]::Combine($expectedOutput, "repository"))
        $expectedMarker = Full-Path ([System.IO.Path]::Combine($fixture, ".fixture-output.owner"))

        if (-not $output.Equals($expectedOutput, $comparison)) {
          Fail-Guard "fixture output path is not the exact owned output location"
        }
        if (-not $repository.Equals($expectedRepository, $comparison)) {
          Fail-Guard "generated repository path is not the exact owned repository location"
        }
        if (-not $marker.Equals($expectedMarker, $comparison)) {
          Fail-Guard "owner marker path is not the exact adjacent marker location"
        }

        $fixtureItem = Check-Item $fixture $fixture "fixture root" $true
        if ($null -eq $fixtureItem) {
          Fail-Guard "fixture root is missing: $fixture"
        }
        $outputItem = Check-Item $output $expectedOutput "fixture output" $true
        $repositoryItem = Check-Item $repository $expectedRepository "generated repository" $true
        $null = Check-Item $marker $expectedMarker "owner marker" $false

        if ($null -ne $repositoryItem) {
          if ($null -eq $outputItem) {
            Fail-Guard "generated repository exists without its owned output parent"
          }
          $resolvedParent = Full-Path $repositoryItem.Parent.FullName
          if (-not $resolvedParent.Equals($expectedOutput, $comparison)) {
            Fail-Guard "generated repository is not exactly inside the owned output"
          }
        }
      ' 2>&1
  )"; then
    FIXTURE_GUARD_ERROR=""
    return 0
  fi

  guard_output="${guard_output//$'\r'/}"
  [[ -n "$guard_output" ]] || guard_output="Windows fixture path inspection failed"
  fixture_guard_error "$guard_output"
}

fixture_guard_require_owner() {
  local owner_marker="$1"
  local marker_value

  [[ -f "$owner_marker" ]] || fixture_guard_error "fixture owner marker is missing" || return 1
  marker_value="$(<"$owner_marker")"
  [[ "$marker_value" == "$FIXTURE_OWNER_MARKER_VALUE" ]] \
    || fixture_guard_error "fixture owner marker is invalid" \
    || return 1
}

fixture_guard_require_initialized() {
  local fixture_root="$1"
  local output_root="$2"
  local fixture_repository="$3"
  local owner_marker="$4"

  fixture_guard_validate_layout \
    "$fixture_root" "$output_root" "$fixture_repository" "$owner_marker" \
    || return 1
  fixture_guard_require_owner "$owner_marker" || return 1
  [[ -d "$output_root" ]] || fixture_guard_error "fixture output directory is missing" || return 1
  [[ -d "$fixture_repository" ]] \
    || fixture_guard_error "generated fixture repository is missing" \
    || return 1
}
