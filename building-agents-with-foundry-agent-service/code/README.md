# Microsoft Foundry Agents — Build 2026 Demo Pack

A guided, hands-on tour of **Microsoft Foundry Agent Service**. Every scenario is a tiny, runnable Python script with its own README. The pack starts with the simplest possible agent and gradually layers on the most popular built‑in tools, then shows how to graduate from a **Prompt agent** to a **Hosted agent**.

> Each scenario takes < 5 minutes to run. By the end you will have shipped 10+ different agents.

---

## 🎯 What you will learn

| # | Scenario | Tool / Feature | Why it's interesting |
|---|---|---|---|
| 01 | [Hello, Agent](./01-hello-agent/) | Prompt agent basics | Smallest possible agent — 30 lines of code |
| 02 | [Streaming Responses](./02-streaming/) | `stream=True` | Token-by-token UX like ChatGPT |
| 03 | [Function Calling](./03-function-calling/) | `FunctionTool` | A stock-portfolio agent that calls *your* code |
| 04 | [Code Interpreter](./04-code-interpreter/) | `CodeInterpreterTool` | Agent writes & runs Python to analyze sales data |
| 05 | [File Search (RAG)](./05-file-search/) | `FileSearchTool` | Ground the agent in your private documents |
| 06 | [Web Search](./06-web-search/) | `WebSearchTool` | Real-time answers with Bing citations |
| 07 | [MCP Tools](./07-mcp/) | `MCPTool` | Connect any Model Context Protocol server |
| 08 | [Capstone: Travel Concierge](./08-multi-tool-concierge/) | All of the above | One agent, four tools, real itinerary |
| 09 | [Prompt → Hosted: When & Why](./09-hosted-agent-intro/) | Concepts | The migration playbook |
| 10 | [Hosted: Deep Research Agent](./10-hosted-research-agent/) | Agent Framework | Plan→execute loops in a container |
| 11 | [Hosted: Multi-Agent Triage](./11-hosted-multi-agent/) | Agent Framework | Specialist agents handing off work |
| 12 | [Hosted: Foundry Toolbox](./12-hosted-toolbox-agent/) | Agent Framework + Toolbox | Centralized tool registry, MCP-style discovery |

---

## 🛠 Prerequisites

1. **Azure subscription** with access to Microsoft Foundry — sign in at <https://ai.azure.com>.
2. A **Foundry project** with a deployed chat model (e.g. `gpt-4o`, `gpt-4.1`).
   - In the portal: **Foundry → Your project → Models + endpoints → Deploy model**.
3. **Python 3.10+** and the Azure CLI (`az login`).
4. Permission `Azure AI User` (or higher) on the project.

> 🆕 New to Foundry? Follow the [official environment setup guide](https://learn.microsoft.com/azure/foundry/agents/environment-setup) once, then come back here.

---

## ⚡ Quick start

```powershell
# 1. Clone & enter the repo
cd build-2026

# 2. Create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# then edit .env and fill in FOUNDRY_PROJECT_ENDPOINT and FOUNDRY_MODEL_NAME

# 5. Authenticate (DefaultAzureCredential picks this up)
az login

# 6. Run your first agent
python 01-hello-agent\basic_agent.py
```

### Where do I find the endpoint & model name?

| Variable | Where to look in the Foundry portal |
|---|---|
| `FOUNDRY_PROJECT_ENDPOINT` | **Project → Overview → Endpoints → Azure AI Foundry project endpoint** |
| `FOUNDRY_MODEL_NAME` | **Project → Models + endpoints → Deployments → "Name" column** |

---

## 👀 See your agents in the Foundry portal

Every script in this repo creates a *named version* of an agent. While the script is running (and for any agent versions you keep), you can inspect them live:

1. Open <https://ai.azure.com> and select your project.
2. Click **Agents** in the left nav.
3. Find the agent name printed by the script (default: `MyAgent`, `ConciergeAgent`, etc.).
4. Click into it to see:
   - **Setup** — the instructions, model, and tools the script configured.
   - **Playground** — chat with the agent without writing a single line of code.
   - **Tracing** — every model call, tool invocation, and decision the agent made.
   - **Versions** — every script run snapshots a new version.

> 💡 **Tip for the demo booth:** Run a script, then open the portal Playground side‑by‑side. The audience can chat with the *same* agent the code just built.

The scripts in this pack call `agents.delete_version(...)` at the end so they don't litter your project. Comment out that line if you want the agent to persist for portal exploration.

---

## 📁 Repo layout

```
build-2026/
├─ README.md                ← you are here
├─ requirements.txt
├─ .env.example
├─ assets/                  ← shared sample data (CSV, markdown)
├─ 01-hello-agent/
├─ 02-streaming/
├─ ...
├─ 11-hosted-multi-agent/
└─ 12-hosted-toolbox-agent/
```

Every scenario folder follows the same shape:

```
NN-scenario/
├─ README.md     ← what it does, how to run, what to look for in the portal
└─ *.py          ← one focused script, <100 lines
```

---

## 🧭 Recommended walkthrough order

- **First-timer (10 min):** 01 → 02 → 03 → 08 → portal tour
- **Builder track (30 min):** Run all 01–08 in order
- **Architect track (45 min):** Builder track + 09 → 10 → 11

---

## 📚 Authoritative references

- [Microsoft Foundry Agents — Overview](https://learn.microsoft.com/azure/foundry/agents/overview)
- [Tool catalog](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-catalog)
- [Hosted agents quickstart](https://learn.microsoft.com/azure/foundry/agents/quickstarts/quickstart-hosted-agent)
- [Official Python SDK samples](https://github.com/Azure/azure-sdk-for-python/tree/main/sdk/ai/azure-ai-projects/samples/agents)

---

## ⚠️ Notes & costs

- Bing-grounded Web Search has additional terms and may send data outside the Azure compliance boundary — see the [Web Search docs](https://learn.microsoft.com/azure/ai-foundry/agents/how-to/tools/web-search).
- Each agent run consumes model tokens. The included scripts are tiny but loops can add up — review the [Foundry pricing page](https://azure.microsoft.com/pricing/details/ai-foundry/) before doing a live demo at scale.
- Hosted agents (scenarios 10–11) provision additional compute. Stop or delete them after the event.

Happy building! 🚀
