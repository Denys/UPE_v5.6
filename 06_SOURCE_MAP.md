# UPE v5.6.0 — Official Source Map

**Verified:** 2026-07-18  
**Policy:** These sources support the dated GPT-5.6 runtime profile and skill/tool packaging guidance. Re-check them before claims about current model availability, pricing, limits, product labels, or APIs.

| ID | Official source | Used for |
|---|---|---|
| OAI-01 | https://openai.com/index/gpt-5-6/ | GPT-5.6 family, Sol/Terra/Luna positioning, Work/Codex/API availability, Ultra and multi-agent launch context, artifact/reference fidelity |
| OAI-02 | https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt | Standard ChatGPT reasoning choices, Sol/Sol Pro mapping, Terra/Luna product separation |
| OAI-03 | https://developers.openai.com/api/docs/guides/latest-model | GPT-5.6 API model guidance, effort, pro mode, lean prompting, autonomy boundaries, PTC, migration testing |
| OAI-04 | https://developers.openai.com/api/docs/models | Current API model catalog and aliases |
| OAI-05 | https://developers.openai.com/api/docs/guides/tools | Built-in tools, functions, remote MCP, tool-search and PTC overview |
| OAI-06 | https://developers.openai.com/api/docs/guides/tools-tool-search | Deferred tool discovery and context reduction |
| OAI-07 | https://developers.openai.com/api/docs/guides/responses-multi-agent | GPT-5.6 multi-agent beta and suitable task shapes |
| OAI-08 | https://developers.openai.com/api/docs/guides/tools-connectors-mcp | MCP/connectors and deferred loading |
| OAI-09 | https://developers.openai.com/api/docs/guides/tools-skills | API skill format and versioned bundle definition |
| OAI-10 | https://developers.openai.com/codex/build-skills | Codex skill folder layout, trigger descriptions, scripts/references/assets |
| OAI-11 | https://developers.openai.com/blog/eval-skills | Skill trigger/non-trigger evaluation and definition-of-done discipline |
| OAI-12 | https://developers.openai.com/codex/customization/overview | Progressive disclosure for skills |
| OAI-13 | https://developers.openai.com/api/docs/guides/migrate-to-responses | Responses API tools and agentic loop capabilities |
| OAI-14 | https://developers.openai.com/api/docs/guides/tools-computer-use | Computer-use safety and untrusted UI content |

## Evidence notes

- OpenAI recommends leaner GPT-5.6 prompts, stating each instruction once and exposing only relevant tools.
- GPT-5.6 reasoning effort, API pro mode, and orchestration are separate controls.
- PTC is best for bounded predictable processing; multiple calls alone are not enough.
- Multi-agent is suitable for independent workstreams and requires final synthesis.
- Skills use progressive disclosure: discovery metadata first, full instructions and references only when selected.
- The active UPE kernel therefore contains stable interfaces and routing rules, while detailed model facts, examples, and procedures remain outside it.
