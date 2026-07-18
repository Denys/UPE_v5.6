# Official OpenAI Source Map for This Project

Use these sources first when answering factual or implementation questions.

---

## ChatGPT surfaces

### Projects
- Help Center: **Projects in ChatGPT**
- Use for: project memory, project files, project instructions, chat movement into projects, tool availability in projects

### Memory / Custom Instructions
- Help Center: **Is memory different from Custom Instructions?**
- Help Center: **Memory FAQ**
- Help Center: **ChatGPT Capabilities Overview**
- Use for: saved memory vs custom instructions vs project behavior

### Custom GPTs
- Help Center: **GPTs in ChatGPT**
- Help Center: **Creating and editing GPTs**
- Use for: GPT configuration, knowledge files, capabilities, editor behavior, version history, limits, sharing

### GPT Actions
- Help Center: **Configuring actions in GPTs**
- Developers docs: **GPT Actions**
- Use for: OpenAPI schema, auth, limitations, action configuration, when to use actions

### Apps / MCP / Developer Mode
- Help Center: **Apps in ChatGPT**
- Help Center: **Developer mode, and MCP apps in ChatGPT [beta]**
- Developers docs: **ChatGPT Developer mode**
- Developers docs: **Apps SDK**
- Developers docs: **Building MCP servers for ChatGPT Apps and API integrations**
- Use for: app terminology, custom apps, MCP servers, developer mode, write actions, workspace/admin gating

---

## Codex surfaces

### Codex overview
- Developers docs: **Codex**
- Use for: product scope, supported client surfaces, plan inclusion, top-level positioning

### CLI / IDE / SDK / Config
- Developers docs: **Codex CLI**
- Developers docs: **Codex IDE extension**
- Developers docs: **Codex SDK**
- Developers docs: **Config basics**
- Developers docs: **Configuration reference**
- Use for: installation, authentication, configuration layers, project-scoped config, programmatic control

### Skills / Hooks / Plugins / MCP / Automations
- Developers docs: **Agent Skills**
- Developers docs: **Hooks**
- Developers docs: **Plugins**
- Developers docs: **Model Context Protocol – Codex**
- Developers docs: **Automations – Codex app**
- Developers docs: **Best practices – Codex**
- Use for: reusable workflows, hook lifecycle, plugin packaging, MCP support, recurring tasks, improvement loops

---

## API platform

### Models and prompting
- Developers docs: [**Models**](https://developers.openai.com/api/docs/models)
- Developers docs: [**All models**](https://developers.openai.com/api/docs/models/all)
- Developers docs: [**Model guidance**](https://developers.openai.com/api/docs/guides/latest-model)
- Developers docs: [**Prompting guidance for GPT-5.6 Sol**](https://developers.openai.com/api/docs/guides/prompt-guidance-gpt-5p6)
- Codex docs: [**Models**](https://developers.openai.com/codex/models)
- OpenAI API: [**Changelog**](https://developers.openai.com/api/docs/changelog)
- Use for: current Sol/Terra/Luna lineup, model IDs, Codex surface labels, API reasoning-effort values, prompting patterns, and release/deprecation status

### Tools / function calling / structured outputs
- Developers docs: **Using tools**
- Developers docs: **Function calling**
- Developers docs: **Structured model outputs**
- Developers docs: **Web search**
- Developers docs: **Code Interpreter**
- Use for: tool taxonomy, JSON-schema tools, response formats, structured output vs function calling, built-in tools

### Agents / workflows / evals
- Developers docs: **Agents SDK**
- Developers docs: **Agent Builder**
- Developers docs: **Evaluate agent workflows**
- Use for: orchestration, state, guardrails, workflow design, visual agent construction, evaluation

### Context / memory / continuity
- Developers docs: **Conversation state**
- Developers docs: **Compaction**
- Developers docs: **Prompt caching**
- Use for: API-side continuity, previous response chaining, compaction, context management

---

## Working rules for this project

1. Prefer the most specific official source for the exact surface in question.
2. If a Help Center page and Developers page disagree:
   - cite both
   - check publication/update date
   - prefer the more specific and more current page
   - state the uncertainty
3. Use blog posts or cookbook entries only when they add practical detail beyond the formal docs.
4. Do not treat third-party blog posts, Reddit threads, or random videos as authoritative for product capability claims.
5. For current model availability, feature gating, deprecations, and release behavior, re-check official docs before answering.
6. Keep Codex UI effort labels separate from API values: for example, Codex may show Light/Extra High while API requests use `low`/`xhigh`; verify the current mapping instead of assuming equivalence.
7. Do not promise equal model-tier quality. Use representative evals, explicit acceptance criteria, and adaptive decomposition to establish whether a lower-cost configuration meets the same target.
