# Building Agents with Foundry Agent Service

Demo assets for the **Building Agents with Microsoft Foundry Agent Service** track at Build 2026. This folder contains a hands-on code pack plus FAQ references used at the booth.

## What's in here

| Asset | Description |
|---|---|
|[Booth deck](./building-agents-booth-deck.pptx)|Rolling Booth Deck|
| [Agent FAQs](./agent-faq.md) | Booth FAQ on Foundry Agent Service positioning — Agent Framework vs Foundry SDK vs Copilot SDKs, Copilot Studio comparison, SDK/API choices, prompt vs hosted agents, tools, identity, observability, and pricing. |
| [vNet FAQs](./vnet-faq.md) | Booth FAQ on network isolation — BYO VNet/private networking support across prompt, workflow, and hosted agents, traffic flow, GA status, and per-tool considerations. |
| [code/](./code/) | A guided, runnable demo pack — 12 scenarios that walk from a 30-line "Hello, Agent" through built-in tools (function calling, code interpreter, file search, web search, MCP) and graduate to **Hosted agents** (research, multi-agent, toolbox). See the [code README](./code/README.md) for setup and walkthrough order. |

## Quick start for Code

```powershell
cd code
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
az login
python 01-hello-agent\basic_agent.py
```

See [code/README.md](./code/README.md) for the full prerequisites, environment variables, and the recommended walkthrough order (first-timer, builder, and architect tracks).

## Scenario index for Code

The `code/` pack is organized as numbered, self-contained scenarios — each with its own README and a single focused script:

1. [Hello, Agent](./code/01-hello-agent/) — smallest possible prompt agent
2. [Streaming Responses](./code/02-streaming/) — token-by-token output
3. [Function Calling](./code/03-function-calling/) — `FunctionTool` calling your code
4. [Code Interpreter](./code/04-code-interpreter/) — agent writes & runs Python
5. [File Search (RAG)](./code/05-file-search/) — ground on private docs
6. [Web Search](./code/06-web-search/) — real-time answers with Bing
7. [MCP Tools](./code/07-mcp/) — connect any Model Context Protocol server
8. [Capstone: Travel Concierge](./code/08-multi-tool-concierge/) — all tools in one agent
9. [Prompt → Hosted: When & Why](./code/09-hosted-agent-intro/) — migration playbook
10. [Hosted: Deep Research Agent](./code/10-hosted-research-agent/) — plan→execute loops
11. [Hosted: Multi-Agent Triage](./code/11-hosted-multi-agent/) — specialist handoffs
12. [Hosted: Foundry Toolbox](./code/12-hosted-toolbox-agent/) — centralized tool registry

## References

- [Microsoft Foundry Agents — Overview](https://learn.microsoft.com/azure/foundry/agents/overview)
- [Tool catalog](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-catalog)
- [Hosted agents quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)
- [Foundry environment setup](https://learn.microsoft.com/azure/foundry/agents/environment-setup)