# UPE v5.6.0.2 — Official Source Map

**Verified:** 2026-07-26
**Policy:** These sources support the dated GPT-5.6 runtime profile and skill/tool packaging guidance. Re-check them before claims about current model availability, pricing, limits, product labels, or APIs.

**v5.6.0.1 scope note:** The terminal independent auditor/improver contract is a UPE design requirement introduced by `CORE_CHANGE` CC-5.6.0.1-01, not a claim that every OpenAI surface exposes an independent worker. OAI-07 supports the availability and suitable shape of multi-agent work where exposed; each deployment must still verify actual context separation, authorship, permissions, and read-only scope.

**v5.6.0.2 scope note:** OAI-15 and OAI-16 document subagents and subagent-backed Ultra behavior on supported Work/Codex surfaces. They do not prove that a specific run exposes explicit spawn/result/context controls or a per-child security sandbox. The adapter therefore gates on current-run capability evidence and reports cognitive independence separately from technical isolation.

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
| OAI-15 | https://developers.openai.com/codex/subagents | Explicit/applicable-instruction subagent delegation, visible child threads, returned summaries, and supported Codex hosts |
| OAI-16 | https://developers.openai.com/codex/models | ChatGPT Work web model/effort selection and Ultra’s use of subagents |
| OAI-17 | https://chatgpt.com/overview/ | Public description of Work as a surface for completing multi-step artifact tasks with tools, context, and apps |

## Evidence notes

- OpenAI recommends leaner GPT-5.6 prompts, stating each instruction once and exposing only relevant tools.
- GPT-5.6 reasoning effort, API pro mode, and orchestration are separate controls.
- PTC is best for bounded predictable processing; multiple calls alone are not enough.
- Multi-agent is suitable for independent workstreams and requires final synthesis.
- A multi-agent feature is only a candidate route for UPE’s independent audit; the deployment must separately establish that the worker did not author the candidate, receives a frozen bundle, and cannot mutate the original.
- Current Work/Codex documentation establishes subagent availability on supported routes, while exact callable operations remain runtime evidence.
- Subagent context separation is cognitive isolation; technical candidate immutability, tool restriction, and side-effect prevention require separate evidence.
- Skills use progressive disclosure: discovery metadata first, full instructions and references only when selected.
- The active UPE kernel therefore contains stable interfaces and routing rules, while detailed model facts, examples, and procedures remain outside it.
