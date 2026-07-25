# UPE Review MCP

A tool-only MCP server that runs a SHA-bound, host-enforced UPE review and rework loop using separate OpenAI Agents SDK reviewer and rewriter agents.

## Why the host owns orchestration

The sequence is deterministic application code:

`verify hash -> fresh review -> conditional rewrite -> fresh review -> bounded stop`

Neither ChatGPT nor an LLM manager is trusted to choose whether the mandatory review happens. The specialists receive no tools and cannot write files, call MCP, publish, or mutate external systems.

## Install and run

```powershell
uv sync --group dev
$env:OPENAI_API_KEY = "..."
$env:OPENAI_AGENTS_DISABLE_TRACING = "1"  # recommended for private candidate text
uv run upe-review-mcp
```

Connect an MCP client to `http://localhost:8000/mcp`.

## Tests

```powershell
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src tests
```

## Tool

### `upe_review_and_rework`

Inputs:

- original request;
- acceptance contract;
- frozen candidate and exact SHA-256;
- scoring rubric;
- quality profile;
- maximum fresh-review rounds.

Returns a structured JSON envelope containing the final complete candidate, every review, rework dispositions, hashes, exit reason, usage and estimated standard API cost.

## Privacy and tracing

Agents SDK tracing is enabled by default upstream. This server always excludes sensitive input/output payloads from traces. Set `OPENAI_AGENTS_DISABLE_TRACING=1` to disable tracing entirely. Candidate text is still sent to the selected OpenAI API models to perform the review and rewrite.

## Production omissions

No OAuth, multi-tenant authorization, durable persistence, distributed idempotency, deployment manifest or live ChatGPT verification is claimed in this candidate.
