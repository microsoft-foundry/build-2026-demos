# 12 — Hosted Agent + Foundry Toolbox 🧰

A **Foundry Toolbox** is a centrally-managed, MCP-compatible **tool registry** in your Foundry project. Instead of wiring tools (web search, GitHub MCP, OpenAPI, Azure AI Search, …) into every agent individually, you define them **once** on a Toolbox and let any agent — prompt or hosted — discover them at runtime over a single MCP endpoint.

This scenario shows a hosted Agent Framework agent that does exactly that: it points at a Toolbox URL, and **whatever tools you've configured there become available automatically**.

## Why this is interesting

| Without Toolbox | With Toolbox |
|---|---|
| Each agent redeclares every tool | One Toolbox → many agents reuse it |
| Auth (Entra, OAuth, API keys) configured per-agent | Auth wired once at the Toolbox |
| Tool inventory drifts across teams | Single source of truth, governed centrally |
| Adding a tool = redeploy every agent | Add tool to Toolbox → agents pick it up next run |

## Files

| File | Purpose |
|---|---|
| [main.py](./main.py) | Agent Framework code — connects to the Toolbox MCP endpoint with a bearer token |
| [agent.yaml](./agent.yaml) | Hosted-agent manifest, declares `TOOLBOX_NAME` |
| [agent.manifest.yaml](./agent.manifest.yaml) | `azd ai agent init -m` scaffold (provisions the Toolbox alongside the agent) |
| [requirements.txt](./requirements.txt) | Python deps for the container |

## Prerequisites

You need a **Foundry Toolbox** in your project. You have two ways to get one:

1. **Easy path** — let `azd` create it. The `agent.manifest.yaml` in this folder declares a Toolbox with **Web Search** + **Code Interpreter** built-in tools. `azd provision` will create both the Toolbox and the agent.
2. **Manual path** — create the Toolbox in the Foundry portal (**Project → Tools → Toolboxes → + New**) and pick tools from the catalog. Then set `TOOLBOX_NAME` in `agent.yaml` to match its name.

See the [Toolbox documentation](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/toolbox) for the full catalog (14 scenarios: web search, file search, code interpreter, GitHub MCP, OAuth MCP, Azure AI Search, A2A, OpenAPI, …).

## Deploy & run

```powershell
mkdir my-toolbox-agent ; cd my-toolbox-agent
azd ai agent init -m ..\12-hosted-toolbox-agent\agent.manifest.yaml
azd up

# Try it
azd ai agent invoke "What tools do you have?"
azd ai agent invoke "Search the web for the latest Microsoft Foundry announcements and summarize them."
azd ai agent invoke "Plot a sine wave from 0 to 2π using code_interpreter."
```

The same agent answered three radically different questions — because the **Toolbox** gave it the right tool for each.

## What's in main.py worth noting

- **Bearer-token auth on every MCP call.** `DefaultAzureCredential` produces a token for `https://ai.azure.com/.default`; `ToolboxAuth(httpx.Auth)` injects it into each MCP request. No API keys in the container.
- **Lazy MCP handshake.** The agent enters the `MCPStreamableHTTPTool` context on first request (not at startup) so the platform's `/readiness` probe doesn't race the toolbox handshake.
- **Resilient history fetch.** A tiny `_ResilientResponsesHostServer` wrapper degrades a flaky `get_history()` call to "no prior turns" instead of failing the whole request — a known workaround for the current `agent_framework_foundry_hosting` alpha.

## 👀 In the portal

- **Project → Tools → Toolboxes → `<your-toolbox>`** shows every tool and its auth config; edits propagate to all consuming agents.
- **Project → Agents → `<your-agent>` → Playground** lets you ask *"What tools do you have?"* — the agent introspects the Toolbox and lists them.
- **Tracing** shows each MCP call (`tools/list`, `tools/call`) as its own span, plus the upstream tool execution (e.g. web search latency).

## Where to go next

- ➡️ [11-hosted-multi-agent](../11-hosted-multi-agent/) — combine a Toolbox with multi-agent triage.
- 🔗 [Foundry Toolbox docs](https://learn.microsoft.com/azure/foundry/agents/how-to/tools/toolbox)
- 🔗 [All 14 toolbox scenarios](https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/toolbox/azd) — drop-in `agent.manifest.yaml` examples for each.
