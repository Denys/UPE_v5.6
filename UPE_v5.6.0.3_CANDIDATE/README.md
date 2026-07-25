# UPE v5.6.0.3 Candidate — Host-Enforced MCP Review Adapter

This candidate adds a deterministic external review loop to the UPE v5.6.0.x line without modifying the frozen UPE v5.6.0.1 release.

## Version boundary

- `5.6.0.1` remains the current merged, immutable repository release.
- `5.6.0.2` is expected to own the native ChatGPT Work subagent adapter.
- `5.6.0.3` owns the API-hosted fallback and enforcement layer described here.
- This directory is a **candidate overlay**, not a published release. It must not be renamed to `*_RELEASE` or merged as a complete release until the `5.6.0.2` dependency and final package manifest are reconciled.
- The reserved `5.6.1` identifier remains untouched.

## What is implemented

A tool-only MCP server exposes one bounded tool:

`upe_review_and_rework`

The server verifies the supplied frozen candidate hash, then host code performs this exact sequence:

1. Create a fresh read-only reviewer agent and review the frozen candidate.
2. Stop when the UPE exit contract passes.
3. Otherwise create a separate rewriter agent and produce a complete replacement.
4. Create a new fresh reviewer agent for the replacement.
5. Repeat for at most three review rounds.
6. Return the final candidate, every structured review, hashes, stop reason, token usage, and estimated API cost.

The model does not choose the graph. The host does. This is deliberately stricter than asking one manager model to remember that it was supposed to call a reviewer before congratulating itself.

## Guarantees and non-guarantees

### Enforced by code

- SHA-256 binding of the initial frozen candidate.
- Fresh `Agent` instance for each review round.
- Separate reviewer and rewriter instructions and structured output schemas.
- No tools or external-action authority for either specialist.
- Bounded rounds and input size.
- Exact stop rule:
  - no blockers;
  - mandatory-dimension score at least `4/5`;
  - projected median next gain below `2/50`;
  - projected upper next gain at most `3/50`.
- Per-call token usage and dated standard-price estimate.
- Sensitive trace payloads excluded; tracing can be disabled entirely.

### Not guaranteed

- Security-grade isolation. Reviewer and rewriter share one process, API key, provider, and deployment boundary.
- Semantic truth merely because structured output validated.
- Independence from provider-level correlations or shared model priors.
- Automatic publication, GitHub writes, release, deployment, or destructive action.
- Accurate final cost before a real run. The server estimates from reported token usage and a dated price table.

## Layout

- `01_ARCHITECTURE_AND_USE.md` — design, request/response contract, deployment and ChatGPT connection.
- `mcp/` — isolated Python 3.12 MCP + Agents SDK application.
- `validation/STATIC_VALIDATION.md` — checks performed and unresolved runtime evidence.

## Status

`IMPLEMENTED_STATICALLY / LIVE_API_UNVERIFIED / MCP_CLIENT_UNVERIFIED`
