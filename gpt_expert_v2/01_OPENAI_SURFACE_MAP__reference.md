# OpenAI Surface Map — Reference for This Project

Use this file to keep product surfaces separate. Do not merge them unless the user explicitly asks for a cross-surface comparison.

---

## 1. ChatGPT Projects

### What it is
A project-scoped workspace for related chats, files, and instructions.

### Best for
- long-running advisory work
- shared context across multiple chats
- file-backed research / design / planning
- iterative work where continuity matters

### Typical characteristics
- project instructions
- project files
- project-level continuity / memory behavior
- access to normal ChatGPT tools available in the user's plan/surface

### Do not confuse with
- Custom GPTs
- Codex
- API agents

---

## 2. Custom GPTs

### What it is
A no-code assistant configured inside ChatGPT with:
- instructions
- conversation starters
- knowledge files
- selected capabilities
- either **apps** or **actions** (not both at the same time)

### Best for
- reusable assistants inside ChatGPT
- no-code deployment
- GPT Store / sharing / internal workspace publishing

### Important distinctions
- not the same as a ChatGPT Project
- not the same as an API assistant
- not the same as Codex
- does **not** imply saved memory or cross-chat continuity

### Do not confuse with
- GPT Actions
- Apps/MCP
- API agents
- Codex plugins

---

## 3. GPT Actions

### What it is
A way for a Custom GPT to call external APIs you define.

### Core building blocks
- authentication
- OpenAPI schema
- operation IDs / parameters / endpoints

### Best for
- calling a REST API from a Custom GPT
- retrieving data or triggering workflows in external systems

### Watch-outs
- a GPT can use **apps or actions, not both simultaneously**
- model and workspace restrictions may apply
- domain allowlists / admin restrictions may block execution

### Do not confuse with
- API function calling in your own application
- ChatGPT Apps/MCP
- Codex plugins

---

## 4. ChatGPT Apps / MCP / Developer Mode

### What it is
A way to connect ChatGPT to external tools and data, including MCP-based apps.

### Best for
- user-connected tools
- workspace-enabled tools
- internal data/tools exposed to ChatGPT
- UI-backed or tool-backed integrations
- some write-capable workflows, depending on configuration and permissions

### Key distinctions
- "connectors" was renamed to **apps**
- MCP is the protocol layer
- Apps SDK is the recommended packaging path for ChatGPT apps
- developer mode and full MCP capabilities may be plan/workspace dependent

### Do not confuse with
- GPT Actions
- Codex plugins
- plain API function calling
- generic "plugins" unless the user clearly means Codex plugins

---

## 5. Codex

### What it is
OpenAI's coding agent surface.

### Common surfaces
- Codex app
- Codex CLI
- Codex IDE extension
- Codex Web
- Codex SDK

### Best for
- local codebase work
- code generation, editing, validation
- terminal and repo workflows
- multi-step engineering tasks
- reusable coding workflows

### Codex-specific concepts
- `AGENTS.md`
- `.codex/config.toml`
- project-scoped config layers
- skills
- hooks
- plugins
- MCP configuration
- automations
- subagents

### Do not confuse with
- Custom GPTs
- ChatGPT Projects
- API Agents SDK
- ChatGPT apps

---

## 6. Codex Skills

### What it is
Reusable workflow instructions/resources/scripts for Codex.

### Best for
- repeatable engineering workflows
- domain-specific operating procedures
- context-efficient reuse

### Notes
- skills are an authoring format
- Codex loads metadata first and full instructions when needed
- skills are Codex concepts, not generic ChatGPT project files

---

## 7. Codex Hooks

### What it is
Lifecycle scripts for Codex.

### Best for
- validation
- logging
- policy enforcement
- prompt adaptation
- deterministic automation around Codex turn/tool lifecycle

### Watch-outs
- hooks are not the same as API webhooks
- hooks are a Codex feature, not a ChatGPT Project feature

---

## 8. Codex Plugins

### What it is
Installable workflow bundles for Codex.

### Can include
- skills
- apps
- MCP server configurations

### Best for
- packaging stable reusable Codex workflows
- sharing the same workflow setup across teams/projects

### Do not confuse with
- older generic ChatGPT plugin terminology
- ChatGPT apps
- GPT Actions

---

## 9. OpenAI API

### What it is
The developer platform for building assistants, agents, and product integrations outside ChatGPT.

### Core building blocks
- models
- Responses API
- tools
- function calling
- structured outputs
- conversation state
- compaction
- file search / web search / code interpreter
- Agents SDK
- Agent Builder
- evals / graders / traces

### Best for
- embedding AI into products
- custom orchestration
- external applications
- precise control of tool schemas, state, and evaluation

### Do not confuse with
- ChatGPT Projects
- Custom GPTs
- Codex UI surfaces

---

## 10. Memory and Continuity Layers

Treat "memory" as an overloaded term. Resolve which layer the user means.

### Possible meanings
- ChatGPT saved memory
- ChatGPT project memory
- Custom GPT knowledge files
- action/app authentication state
- API conversation state
- `previous_response_id`
- conversation objects
- server-side compaction
- prompt caching
- Codex durable project memory in files
- agent session memory
- skill metadata vs full skill instructions

### Rule
Never promise persistent memory or cross-session continuity unless the exact surface documents it.

---

## 11. Default triage questions

When the user is ambiguous, identify:

1. **Where should this live?**
   - ChatGPT Project
   - Custom GPT
   - ChatGPT App / MCP
   - Codex
   - API / Agents SDK

2. **What kind of integration is actually needed?**
   - no integration
   - external REST API
   - user-connected app
   - MCP server
   - local codebase / terminal
   - embedded product workflow

3. **What kind of persistence is needed?**
   - none
   - project continuity
   - reusable GPT setup
   - API-side conversation state
   - durable files / repo memory

4. **What side effects are allowed?**
   - read-only
   - controlled writes with confirmation
   - automation / scheduled execution
   - CI/CD / local command execution

---

## 12. Recommended response habit

Before proposing implementation:
- map the user request to the correct surface
- normalize terminology
- identify plan/workspace constraints
- distinguish documented behavior from inference
- recommend the smallest valid setup first
