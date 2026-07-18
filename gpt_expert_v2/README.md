# OpenAI Platform Expert — Adaptive Project Bundle

This bundle is meant for a **ChatGPT Project** that should act as an expert advisor on OpenAI products, model surfaces, integrations, and implementation paths.

The July 2026 revision adds an adaptive execution policy for GPT-5.6 Sol, Terra, and Luna and for different reasoning-effort or credit constraints. It keeps acceptance criteria fixed while changing decomposition, command specificity, and verification frequency.

## Files

### `00_PROJECT_INSTRUCTIONS__compact.md`
Paste this into the **Project Instructions** field.

### `01_OPENAI_SURFACE_MAP__reference.md`
Upload this as a project file. It gives the assistant a durable taxonomy of:
- ChatGPT Projects
- Custom GPTs
- GPT Actions
- Apps / MCP / developer mode
- Codex
- API / Responses / Agents SDK / Agent Builder

It is meant to reduce surface confusion and force the model to map ambiguous user wording to the correct OpenAI product surface.

### `02_OFFICIAL_SOURCE_MAP__OpenAI.md`
Upload this as a project file. It is a curated map of the official OpenAI documentation and help-center pages that matter for this project.

### `CIDP_AGENTS.md`
Use this as repo-level `AGENTS.md` guidance for Codex projects that need controlled incremental implementation, command discipline, verification, and model-tier adaptation.

## Recommended setup

1. Create a new ChatGPT Project.
2. Paste `00_PROJECT_INSTRUCTIONS__compact.md` into the Project Instructions field.
3. Upload:
   - `01_OPENAI_SURFACE_MAP__reference.md`
   - `02_OFFICIAL_SOURCE_MAP__OpenAI.md`
   - `CIDP_AGENTS.md` only when you want the project to advise on or generate repo-level Codex workflows
4. Start with one of the starter prompts below.

## Suggested starter prompts

- Audit whether my requirement belongs in ChatGPT Projects, a Custom GPT, ChatGPT Apps/MCP, Codex, or the OpenAI API.
- Check whether the following idea is technically possible today, and cite only official OpenAI sources.
- Translate my request into current official OpenAI terminology before proposing an implementation.
- Compare the best implementation path for this use case across ChatGPT, Codex, and the API.
- Design the smallest valid setup first, then show the upgrade path.

## Design intent

This bundle is deliberately skeptical:
- it questions ambiguous asks
- it separates product surfaces
- it treats feature claims as time-sensitive
- it requires official-source verification for non-trivial claims
- it distinguishes what is possible, plan-gated, deprecated, or unsupported
- it uses the same acceptance criteria across model tiers, with smaller verified slices for lower-effort or credit-constrained runs

## Model/effort note

Instructions cannot make every model tier intrinsically equal. The bundle targets outcome preservation through explicit contracts, deterministic checks, evals, and repair loops. Use Sol for ambiguous or high-value work, Terra for balanced everyday work, and Luna for clear repeatable work; verify current access and effort options because plan and surface availability can change.

Current grounding: [OpenAI model guidance](https://developers.openai.com/api/docs/guides/latest-model), [GPT-5.6 Sol prompting guidance](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6), [Codex model selection](https://developers.openai.com/codex/models), and the [OpenAI API changelog](https://developers.openai.com/api/docs/changelog).
