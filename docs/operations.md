# Harness operations

## Operational status

This guide describes the implementation at `origin/main`
`b1d1a9be9669eb16f6d86e906c4b42b75a2e99e6`, observed on 2026-07-27.

The usable packaged command is the read-only `doctor`. The CLI also parses
`init`, `research`, `run`, `status`, `events`, `resume`, `pause`, `cancel`,
`evaluate`, and `cleanup`, but the default executor deliberately returns exit
code 69 because C-506 integration is not implemented. Do not interpret the
presence of a command name as an operational runtime.

## Prerequisites and setup

Use Windows-native PowerShell in a clean, task-specific Git worktree.

Required:

- Python 3.12 or newer (`pyproject.toml` and doctor minimum);
- the `uv` executable on `PATH` for doctor;
- Git with worktree support; and
- Codex only when checking or later using the App Server adapter.

`py -3 -m uv` is sufficient for the development commands below, but doctor
probes `uv --version` directly. If the module is installed but the executable is
not on `PATH`, development validation can pass while doctor correctly reports
the validator runtime unavailable.

From the repository root:

```powershell
py -3 -m uv sync --group dev --locked
py -3 -m uv lock --check
py -3 -m uv run python -c "import harness; print(harness.__version__)"
py -3 -m uv run harness doctor
```

Global CLI options precede the subcommand:

```powershell
py -3 -m uv run harness --json doctor
py -3 -m uv run harness --config C:\harness\config.json doctor --timeout 5
```

Without a config, doctor uses the current directory as the repository and
`.harness-state\harness.sqlite3` as the database path. An absent config is a
`SKIP`, not a failure.

## Credential-free configuration

The default config path is `.harness\config.json`. The complete contract is
[`config.schema.json`](../schemas/config.schema.json). A minimal safe example is:

```json
{
  "schema_version": "1.0.0",
  "paths": {
    "repository_root": "C:\\projects\\target",
    "worktree_root": "D:\\harness\\worktrees",
    "host_state_root": "E:\\harness\\state"
  },
  "provider": {
    "adapter": "fake",
    "model": null,
    "reasoning_effort": null
  },
  "limits": {
    "max_iterations": 20,
    "max_elapsed_seconds": 3600,
    "max_input_tokens": null,
    "max_output_tokens": null,
    "max_total_tokens": null,
    "max_cost": null,
    "max_external_actions": 0
  },
  "retry": {
    "max_transient_retries": 2,
    "identical_failure_limit": 2,
    "no_progress_iteration_limit": 3,
    "initial_backoff_seconds": 0.5,
    "maximum_backoff_seconds": 8.0,
    "backoff_multiplier": 2.0,
    "jitter_ratio": 0.25
  },
  "validation": {
    "default_timeout_seconds": 120,
    "max_output_bytes": 1048576
  },
  "policy": {
    "network_enabled": false,
    "allowed_hosts": [],
    "docker_enabled": false
  }
}
```

The three roots must be absolute local-drive Windows paths and must not overlap.
UNC/device paths, traversal, expansions, globs, reserved names, ADS syntax, and
trailing dots/spaces are rejected. Keep credential values out of the file.

## Doctor procedure

Run doctor before any runtime or recovery work. It performs bounded,
shell-free, read-only checks in stable order:

- Python minimum and exact observed version;
- config presence and validity;
- exact Codex version;
- `codex app-server --help` availability through that Codex version;
- Git availability;
- repository status and cleanliness;
- worktree support;
- `uv` and configured validator entry points;
- SQLite location and read/integrity access;
- repository/state-directory permissions;
- Docker only when configured; and
- provider credential presence only, never values.

Text output ends in `USABLE` or `UNUSABLE`. JSON output contains the same fixed
summaries. Exit 0 means no check is `FAIL`; exit 69 means one or more checks
failed. `SKIP` does not make the report unusable.

Doctor intentionally treats a dirty repository as a failure. Preserve and
identify the changes; do not reset or clean them to manufacture a passing
result. In the C-410 candidate worktree, doctor returned exit 69 because the
four new documents made the worktree intentionally dirty and because `uv` was
not a standalone command on `PATH`; Python, Codex `0.144.3`, App Server
availability, Git/worktrees, SQLite `3.50.4`, permissions, and the fake-provider
credential boundary passed or skipped as designed.

## Current command behavior

| Command | Current behavior |
|---|---|
| `doctor` | Implemented read-only diagnostics |
| `init`, `research`, `run` | Parsed and dispatched only through an injected runtime executor; unavailable by default |
| `status`, `events` | Parsed with `run_id`; unavailable by default |
| `resume`, `pause`, `cancel` | Parsed with `run_id`; unavailable by default |
| `evaluate` | Parsed with `run_id`; unavailable by default |
| `cleanup` | Parsed with `run_id`; unavailable by default and performs no cleanup |

The fake adapter, orchestrator, validator, state store, evaluator policy, and
security policy are library components exercised by tests. There is no
packaged end-to-end executor that connects them.

## Approvals and consequential actions

Read, transform, and draft action classes are non-consequential in the approval
taxonomy. A local write still remains subject to the assigned-worktree path
boundary. Commit, push, PR create/update, merge, release, deployment, visibility
change, external message, purchase, production mutation, destructive action,
secret handling, other external write, and high-consequence actions require an
exact trusted-host approval.

At dispatch, validate:

- run and action class;
- exact target and normalized arguments/content;
- repository and branch identity;
- decision ID, approving identity, grant status, and expiry;
- one intended effect; and
- current action/target identity.

Denial, expiry, revocation, future decision time, missing record, or any scope
drift stops the effect. Approval policy currently returns decisions only; C-506
must wire them adjacent to actual dispatch.

Provider approval events stop the orchestrator at `APPROVAL_REQUIRED`. It does
not automatically answer the provider or continue the event stream.

## Failure and recovery procedure

### General stop

1. Stop dispatching new provider or external actions.
2. Record repository, branch, worktree, Run, task, transition, and provider
   identities.
3. Preserve the last stable SQLite database, event mirror, referenced evidence,
   and candidate worktree.
4. Classify the stop as blocked, budget exhausted, approval required, failed,
   or cancelled with an explicit reason and next action.
5. Reconcile any `STARTED` or ambiguous non-idempotent action against its target
   before retry.

### Validator failure

- Nonzero exit is a deterministic `FAIL`; repair the smallest evidenced defect.
- Timeout, execution error, malformed result, overflow, or missing evidence is
  `INSUFFICIENT_EVIDENCE`; gather the named evidence or adjust an authorized
  bound.
- Do not invoke a model evaluator to override either condition.
- Inspect referenced stdout/stderr artifacts; structured evidence does not
  embed their contents.

### SQLite and JSONL

- Treat SQLite as authoritative.
- Do not edit the `runs` or `outbox` tables manually.
- Do not truncate a partial or conflicting JSONL file and continue.
- A missing JSONL mirror may be rebuilt by delivering pending authoritative
  outbox rows through `JsonlEventMirror.deliver_pending`.
- Exact replay after fsync/before acknowledgement is deduplicated.
- Preserve corruption evidence and stop on hash, sequence, transition,
  canonical-JSON, or mirror conflicts.

There is no recovery CLI. Cross-process exclusive locking, partial-tail repair,
restart/reconnect, and stopped-run resume are C-503 work.

### Workspace and cleanup

`WorkspaceManager.assign` may inspect and bind a dirty worktree, but cleanup
preparation requires it to be clean. Cleanup requires:

1. the exact task-owned direct-child worktree;
2. matching root/workspace filesystem identity;
3. one unlocked matching Git worktree record;
4. matching HEAD and branch;
5. no staged, unstaged, or untracked paths;
6. a current explicit `CleanupTarget`; and
7. a separate approval plus immediate revalidation.

The current module does not remove worktrees or delete files. Do not substitute
`git clean`, recursive deletion, a glob, or an environment-derived path.

### App Server

The adapter is pinned to Codex CLI `0.144.3` and the accepted generated schema
reference. Unknown/malformed JSON-RPC, identity mismatch, duplicate terminal,
process exit, and compatibility failure stop or fail closed. Provider stderr
contents are not exposed.

PR `#22` merged the C-501 terminal-notification correlation correction into the
current base. C-502 remains blocked until the coordinator records post-merge
revalidation of that correction and separately authorizes the controlled live
App Server smoke. C-410 does not start a real provider.

## Documentation and development validation

From the C-410 worktree, run:

```powershell
py -3 -m uv lock --check
py -3 -m uv run pytest -q tests/unit/test_state.py tests/unit/test_config.py tests/unit/test_fake_adapter.py tests/unit/test_lifecycle.py tests/unit/test_validation.py tests/unit/test_workspace.py tests/unit/test_state_store.py tests/unit/test_events.py tests/unit/test_budgets.py tests/unit/test_retry_policy.py tests/unit/test_evaluation.py tests/unit/test_cli.py tests/unit/test_codex_adapter.py tests/unit/test_approvals.py tests/unit/test_permissions.py
py -3 -m uv run pytest -q
py -3 -m uv run ruff check .
py -3 -m uv run ruff format --check .
py -3 -m uv run mypy --strict src tests
py -3 -m uv run python scripts/validate_work_specifications.py
py -3 -m uv run python scripts/validate_references.py
py -3 -m uv run python scripts/validate_schema.py
py -3 -m uv run python scripts/update_capability_readiness_report.py --check
git diff --check
```

C-410 also requires a local Markdown-link check and a four-output content gate
covering setup, operation, recovery, approvals, limitations, C-501 correction
status, and the C-502 blocker. These checks must be reported with their exact
command and result in the handoff.

## Known limitations

- Only `doctor` is operational from the default CLI.
- The harness is synchronous and single-agent.
- No packaged end-to-end runtime connects orchestration, persistence,
  budget/retry, evaluator, C-501 adapter, and C-505 security.
- C-505 policy performs decisions and redaction but no I/O.
- No real evaluator is implemented.
- No cleanup effect is implemented.
- No restart/reconnect, stopped-run resume, action reconciliation loop, or
  partial JSONL repair is implemented.
- The C-502 live smoke has not been accepted here.
- SQLite does not yet contain Goal, Task, approval, action, or checkpoint
  tables.

See [`state-model.md`](state-model.md),
[`evaluation-plan.md`](evaluation-plan.md), and
[`threat-model.md`](threat-model.md) for the corresponding contracts.
