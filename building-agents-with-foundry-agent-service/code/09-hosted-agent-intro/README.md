# 09 — From Prompt Agent to Hosted Agent 🚀

You've now built eight Prompt agents. Why would you ever need anything else?

## The two-minute decision matrix

| Question | Prompt agent | Hosted agent |
|---|---|---|
| Zero infra, ready in 30 seconds? | ✅ | ❌ (provisions container) |
| Edit in portal, no code? | ✅ | ⚠️ (code change → redeploy) |
| Custom multi-step orchestration logic? | ❌ | ✅ |
| Plug in any framework (Agent Framework, LangGraph, CrewAI, your own)? | ❌ | ✅ |
| Long-running / background workflows? | ⚠️ | ✅ |
| Per-agent Microsoft Entra identity for downstream Azure calls? | ❌ | ✅ |
| Persistent per-session filesystem (uploads, scratch space)? | Limited | ✅ (30-day sessions) |
| Scale to zero when idle, predictable cold start? | n/a (always on demand) | ✅ |
| Activity protocol for Teams / M365 publishing | ✅ | ✅ |
| Invocations protocol (custom JSON payloads, webhooks, AG-UI)? | ❌ | ✅ |

> **Rule of thumb:** start as a **Prompt agent**. Graduate to **Hosted** when the orchestration logic outgrows what you can express in a single system prompt + tool list — or when you need a per-agent identity.

## What stays the same

- Same Foundry project, same RBAC, same observability dashboards.
- Same tools — `web_search`, `code_interpreter`, `file_search`, `MCP`, custom functions — all available.
- Same playground & tracing experience in the portal.
- Same OpenAI-compatible Responses API for clients.

## What changes

| Concept | Prompt agent | Hosted agent (Agent Framework) |
|---|---|---|
| Agent definition | `PromptAgentDefinition(...)` in code or portal | `agent.yaml` + Python `main.py` running `ResponsesHostServer` |
| Custom logic | Tool dispatch loop in your *client* | Runs **inside** the container |
| Deploy | `agents.create_version(...)` | `azd up` (Bicep + ACR build) |
| Compute | Fully managed, invisible | Container on Foundry-managed Micro-VMs |
| Lifecycle | One API call | `azd ai agent run` → `azd deploy` → `azd ai agent show` |

## Side-by-side: the same "stock portfolio" agent

[`prompt_version.py`](./prompt_version.py) is exactly Scenario 03 — kept here for easy comparison.

[`hosted_version/`](./hosted_version/) contains the equivalent **Hosted agent** written with Microsoft Agent Framework: identical function tool, identical instructions, identical behavior — packaged as a container. You can convert your prompt agent / workflows YAML to code using VS Code by following the steps [here](https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/vs-code-agents-workflow-low-code#convert-a-yaml-workflow-to-agent-framework-code)

The diff (in pseudo-form):

```
Prompt agent:
   tools = [FunctionTool(name="get_stock_quote", parameters=...)]
   agents.create_version(definition=PromptAgentDefinition(..., tools=tools))
   # client polls function_call items and dispatches manually

Hosted agent:
   @tool
   def get_stock_quote(symbol: str) -> dict: ...
   agent = Agent(client=FoundryChatClient(...), tools=[get_stock_quote])
   ResponsesHostServer(agent).run()        # container hosts this
```

Same mental model, different runtime contract.

## How to deploy a hosted agent (one-time setup)

```powershell
# 1. Install the azd agent extension
azd ext install azure.ai.agents

# 2. Scaffold from a sample manifest
mkdir my-hosted-agent ; cd my-hosted-agent
azd ai agent init -m <path-to-agent.manifest.yaml>

# 3. Provision Foundry project + ACR + model deployment
azd provision

# 4. Run locally
azd ai agent run
azd ai agent invoke --local "Hello"

# 5. Deploy to Foundry
azd deploy
azd ai agent invoke "Hello"

# 6. Tear down
azd down
```

Full quickstart: <https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent>.

> 💡 **VS Code path:** the **Foundry Toolkit** extension can scaffold, run, debug, and deploy hosted agents from the editor — no shell required.

## 👀 In the portal

After `azd deploy`, your hosted agent appears under **Agents** just like a prompt agent. Click it to:

- **Open in playground** — chat with the deployed container.
- **Container details** — see CPU/memory, restart, view logs.
- **Tracing** — every request flows through App Insights automatically (the platform injects the connection string).

## Where to go next

- ➡️ [10-hosted-research-agent](../10-hosted-research-agent/) — a Deep Research hosted agent.
- ➡️ [11-hosted-multi-agent](../11-hosted-multi-agent/) — multi-agent orchestration in a single container.
