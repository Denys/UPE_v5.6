# Architecture and Use Contract

## Decision

Use a **host-enforced Agents SDK workflow exposed through a tool-only MCP server**.

The Responses API Multi-agent beta is optimized for model-directed parallel workstreams. UPE review is a serial state machine with a frozen input, a mandatory review gate, conditional rework, a fresh second review, and explicit stop conditions. Giving that graph back to a root model would trade enforcement for vibes, which is precisely the category of defect UPE is meant to remove.

The implementation also avoids an LLM manager agent. The MCP handler is the manager. It invokes bounded reviewer and rewriter `Agent` instances directly with `Runner.run`, so the call order is application logic rather than a prompt suggestion.

## Runtime graph

```text
ChatGPT / Codex
      |
      | MCP tool call: upe_review_and_rework
      v
MCP host manager
      |
      +-- verify initial SHA-256 and limits
      |
      +-- Reviewer R1 (fresh Agent, no tools, structured output)
      |       |
      |       +-- PASS -> return candidate + audit envelope
      |       |
      |       +-- FAIL/GAIN -> Rewriter W1 (separate Agent, no tools)
      |                           |
      |                           +-- hash revised candidate
      |
      +-- Reviewer R2 (new fresh Agent)
      |       |
      |       +-- PASS -> return v2 + reviews
      |       |
      |       +-- FAIL/GAIN -> optional W2
      |
      +-- Reviewer R3 (new fresh Agent)
              |
              +-- return PASS or MAX_ROUNDS_REACHED
```

## Tool input

| Field | Contract |
|---|---|
| `original_request` | User request that produced the candidate. |
| `acceptance_contract` | Frozen MUST/evidence/action/done contract. |
| `frozen_v1` | Complete candidate text. |
| `candidate_sha256` | Lowercase SHA-256 of UTF-8 `frozen_v1`; mismatch fails before API use. |
| `scoring_rubric` | Criteria and scoring anchors supplied unchanged to every reviewer. |
| `quality_profile` | `economy`, `balanced`, or `quality`. Default `balanced`. |
| `max_review_rounds` | Integer `1..3`; default `2`. A review round is one fresh reviewer pass. |

## Model routes

| Profile | Reviewer | Rewriter | Intended use |
|---|---|---|---|
| `economy` | GPT-5.6 Luna | GPT-5.6 Terra | Cheap routine audits; stronger model retained for synthesis. |
| `balanced` | GPT-5.6 Terra | GPT-5.6 Terra | Default quality/cost route. |
| `quality` | GPT-5.6 Sol | GPT-5.6 Sol | Failure-expensive framework or architecture changes. |

The mapping is configuration, not a metaphysical truth. Representative evals should decide whether Luna review is adequate for a given UPE artifact class.

## Review output

Each reviewer returns:

- reviewed candidate hash;
- blocker flag;
- mandatory-dimension score `0..5`;
- evidence-anchored score `0..50`;
- ordered findings with severity, criterion, evidence and correction;
- projected median and upper next-round gain;
- release decision `COMPATIBLE | BREAKING | NO_RELEASE`;
- rationale.

The final MCP result also contains:

- initial and final hashes;
- final complete candidate;
- all reviews and rework dispositions;
- exact stop reason;
- model and token usage per call;
- estimated standard-processing cost in USD;
- independence and isolation facts.

## Prompt-injection boundary

Candidate, request, contract and rubric are serialized as JSON data inside one user input. Reviewer and rewriter instructions explicitly classify every supplied field as untrusted data and prohibit following embedded instructions. This reduces accidental instruction execution; it does not convert a shared model/provider boundary into a hardware security module, despite humanity's recurring urge to solve ontology with XML tags.

## Local run

From `UPE_v5.6.0.3_CANDIDATE/mcp`:

```powershell
Copy-Item .env.example .env
# Set OPENAI_API_KEY in the process environment; do not commit it.
uv sync --group dev
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src tests
uv run upe-review-mcp
```

The Streamable HTTP endpoint is:

```text
http://localhost:8000/mcp
```

Inspect it with:

```powershell
npx -y @modelcontextprotocol/inspector
```

## Connect from ChatGPT

1. Host the server behind a public HTTPS endpoint, or expose the local port through a temporary HTTPS tunnel for development.
2. In ChatGPT, enable Developer Mode under Apps/Plugins advanced settings.
3. Add the remote MCP URL ending in `/mcp`.
4. Refresh the plugin after changing tool metadata or schemas.
5. Invoke the tool only after the user has authorized the paid API review run.

A public deployment needs real authentication, per-user authorization, rate limits, spend controls and secret management. The draft server intentionally does not counterfeit those production properties.

## Cost accounting

The server reads Agents SDK usage for each `Runner.run` call and estimates cost from a dated model-price table. Cached tokens are priced separately. Reasoning-token detail is reported but not added again because it is already included in output-token billing.

The estimate excludes:

- priority/flex/batch pricing differences;
- regional or contractual price modifiers;
- MCP hosting, tunnel, logging or observability cost;
- future price changes;
- unusually long-context surcharges, which are blocked by conservative text-size limits in this candidate.

## Deployment boundary

This candidate is suitable for local/private evaluation. Before production:

- add OAuth or another authenticated front door;
- bind tenant/project identity server-side;
- enforce per-user and global dollar budgets;
- store only hashes and bounded audit records unless retention is explicitly authorized;
- add request idempotency and durable state if reconnect/resume is required;
- run representative behavioral evals and adversarial prompt-injection cases;
- pin a resolved lockfile and container digest;
- deploy, then verify `/mcp` through the actual ChatGPT client.
