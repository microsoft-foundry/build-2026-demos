# Browser Automation Tool & Verification Skill

Welcome to the Microsoft Build 2026 Browser Automation Tool & Verification Skill Expert Meet Up Station! We're thrilled to offer this incredible opportunity for you to connect with attendees through engaging one-on-one or small group conversations about the latest Browser Automation tool and `/verify` Copilot CLI skill capabilities. At the Expert Meet Up, you'll have the chance to answer questions and share your expertise, showcase demos and product decks, and keep attendees informed on the newest event updates and product announcements. Each station will be powered by our outstanding MVPs, session speakers, and subject matter experts—ready to deliver insights and spark meaningful discussions.

## Build 2026 Browser Automation Tool & Verification Skill Announcements

* **Browser Automation tool in Foundry Toolbox — Public Preview.** A new built-in Foundry Toolbox tool that provisions remote Chromium browsers (backed by Azure Playwright Workspaces) and exposes them to any hosted agent over a single MCP endpoint. Agents drive the browser through Playwright CLI commands — no per-agent browser plumbing required.
* **Azure Playwright Workspaces — Generally Available.** The managed cloud browser service that powers the Browser Automation tool. Parallel, region-aware browser sessions with live-view URLs and recording capture.
* **`/verify` Copilot CLI skill — public sample available.** An end-to-end app verification pipeline driven from Copilot CLI: verify a running app, author Playwright tests for uncovered flows, classify and heal failing tests. Distributed as a portable `.github/skills/verify/` folder via [`Azure/playwright-workspaces`](https://github.com/Azure/playwright-workspaces/tree/main/samples/app-verification-skills).

## Demo Samples

The three demo samples live in their own repositories so each can evolve with its own maintainers, releases, and CI.

### Sample 1 — BYO Browser Automation Agent

> **Repo:** [`microsoft-foundry/foundry-samples` → `samples/python/hosted-agents/bring-your-own/responses/browser-automation`](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents/bring-your-own/responses/browser-automation)

A **Bring Your Own** hosted agent in Python that talks the Responses protocol directly, built on `azure-ai-agentserver-responses` without an agent framework. The agent uses the Foundry Toolbox MCP to provision remote Chromium browsers and drives them via Playwright CLI. Shows off:

* **Lazy + multi-session browser provisioning** — sessions are only created when the model first needs one; the model can spin up additional named sessions for parallel work.
* **`run_parallel`** across sessions for side-by-side comparisons (e.g. pricing on two sites, fill a form on one tab while polling email on another).
* **On-demand skill loading** via a `load_skill` tool that reads markdown workflow files (`form-filler`, `web-scraper`).
* **Immediate `kill_session`** — the model honours user requests to close sessions right away (single, named, or all).

Reach for this sample when you need raw SDK control over streaming, multi-session lifecycles, or custom tool orchestration that the higher-level framework abstracts away.

### Sample 2 — Microsoft Agent Framework Browser Automation Agent

> **Repo:** [`microsoft-foundry/foundry-samples` → `samples/python/hosted-agents/agent-framework/responses/14-browser-automation-agent`](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents/agent-framework/responses/14-browser-automation-agent)

A hosted agent built with [Microsoft Agent Framework](https://github.com/microsoft/agent-framework) using `ResponsesHostServer` — the smaller, prompt-driven counterpart to Sample 1. Same backend (Foundry Toolbox MCP → Azure Playwright Workspaces → remote Chromium over CDP → Playwright CLI), but a single session and a single base prompt (`prompts/base.md`) covering browser lifecycle, safety, web extraction, and form filling.

Recommended starting point for common single-session browser-automation scenarios — general browsing, web scraping, form filling. Sample 1's README itself points readers here when they don't need its raw-SDK extras.

### Sample 3 — `/verify` Copilot CLI Skill

> **Repo:** [`Azure/playwright-workspaces` → `samples/app-verification-skills`](https://github.com/Azure/playwright-workspaces/tree/main/samples/app-verification-skills)

A Copilot CLI skill, not a hosted agent — a different layer of the stack. Targets developers verifying and maintaining their own web apps from the terminal. Three-phase pipeline driven from a single `/verify` invocation:

1. **App verification** — drives the running app via `playwright-cli`, exercises the core flows, captures snapshots and console errors.
2. **Test authoring** — generates Playwright tests for working flows that aren't already covered.
3. **Test healing** — re-runs the existing suite, classifies each failure as a `stale_test` (a real source change broke the test) or a real `regression` (the app misbehaves), fixes the stale ones, surfaces genuine regressions with evidence.

All test execution runs on Azure Playwright Workspaces cloud browsers, with video and trace artifacts uploaded for inspection. The skill ships as a portable `.github/skills/verify/` folder that Copilot CLI auto-detects on clone — no plugin install. The sample bundles a runnable invoice-processing demo app with the skill pre-wired so reviewers can try it end-to-end in one minute.

## Documentation Links

* Microsoft Foundry — Hosted Agents overview: <https://learn.microsoft.com/azure/foundry/agents/concepts/hosted-agents>
* Microsoft Foundry — Hosted Agents quickstart with `azd`: <https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent?pivots=azd>
* Microsoft Agent Framework: <https://github.com/microsoft/agent-framework>
* Azure Playwright Workspaces documentation: <https://aka.ms/pww/docs>
* Playwright CLI: <https://github.com/microsoft/playwright-cli>
