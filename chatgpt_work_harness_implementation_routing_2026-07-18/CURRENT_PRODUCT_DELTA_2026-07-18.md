# Current Product Delta — 18 July 2026

This file corrects volatile surface/model facts in earlier research notes. It is runtime evidence, not a stable harness invariant.

## 1. Work continuity changed after the original launch notes

As of the 16 July 2026 desktop update, **cloud Work conversations sync across web, mobile, and desktop**. Local conversations still remain on the computer, and Codex remains a separate view with separate history.

**Routing consequence:** a cloud Work research/specification thread can move among devices, but local repository state and local Work conversations must still be handed off through explicit files/evidence. Do not use conversation sync as the harness database.

Source: https://help.openai.com/en/articles/6825453-chatgpt-release-notes

## 2. Web Work versus local Work versus Codex

- Work web/mobile runs in the cloud and can use uploaded/project/connected context.
- Work web/mobile cannot directly access files on the user's computer.
- Desktop Work can use local files and desktop apps with explicit permission.
- Codex remains the dedicated software-development surface for local folders, repositories, terminals, commands, tests, and developer tools.

**Routing consequence:** this project has no mandatory Local Work task at present. Research/specification/review stays in Work web; repository/runtime work goes directly to local Codex.

Source: https://help.openai.com/en/articles/20001275/

## 3. Pro is not “one notch above Max”

In standard ChatGPT, GPT-5.6 Sol powers Medium, High, and Very High, while **Pro uses GPT-5.6 Sol Pro**, a separate highest-capability option for difficult tasks and longer workflows. The API model catalog lists Sol reasoning efforts through `max`.

**Terminology used in this package:**

- `sol_high` means the default strong execution route.
- `sol_max_or_highest_exposed` means Max where the surface exposes it, otherwise the highest exposed Sol effort.
- `sol_pro` means GPT-5.6 Sol Pro in ChatGPT/Work for difficult indivisible judgment.

Never treat Sol Pro, API `max`, or orchestration such as Ultra as interchangeable controls.

Sources:
- https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt
- https://developers.openai.com/api/docs/models

## 4. Codex minimum versions to verify locally

Current official GPT-5.6 guidance lists these minimum Codex versions:

- ChatGPT desktop app, Codex mode: `26.707.30751`
- Codex CLI: `0.144.0`

These are not assumptions that the local machine satisfies. Task `C-102` must record the installed versions and mark the result PASS, FAIL, or UNKNOWN.

Source: https://help.openai.com/en/articles/20001354-gpt-56-in-chatgpt

## 5. Plugin note

Plugins can package skills, apps, and templates and are available on ChatGPT web and desktop, including Work and Codex. This does **not** make a Work plugin a v0 runtime requirement. Plugin/skill packaging remains supporting work until the core single-agent harness passes representative evaluations.

Source: https://help.openai.com/en/articles/6825453-chatgpt-release-notes
