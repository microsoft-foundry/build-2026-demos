# 11 — Hosted Agent: Multi-Agent Triage 🎛️

A single hosted container that runs three specialist agents and one router:

```
              ┌──────────────────┐
   user ───►  │  Triage agent    │
              │  (router/LLM)    │
              └────────┬─────────┘
            ┌──────────┼──────────┐
            ▼          ▼          ▼
       ┌────────┐ ┌──────────┐ ┌──────────┐
       │Billing │ │Technical │ │ Sales    │
       │ agent  │ │ Support  │ │ agent    │
       └────────┘ └──────────┘ └──────────┘
```

- **Triage** classifies the customer's intent and hands off.
- **Billing** answers refund / invoice questions (file_search over a policy doc).
- **Technical Support** runs diagnostic functions.
- **Sales** uses web search to discuss current promotions.

This is the canonical "intelligent customer support" pattern, and it's a perfect hosted-agent use case — too much orchestration to express in a single system prompt.

## Files

| File | Purpose |
|---|---|
| [main.py](./main.py) | Agent Framework code: 4 agents wired together with a workflow |
| [agent.yaml](./agent.yaml) | Hosted-agent manifest |
| [requirements.txt](./requirements.txt) | Python deps |
| [agent.manifest.yaml](./agent.manifest.yaml) | Scaffold manifest for `azd ai agent init` |

## Deploy & try it

```powershell
mkdir my-triage-agent ; cd my-triage-agent
azd ai agent init -m ..\11-hosted-multi-agent\agent.manifest.yaml
azd up

azd ai agent invoke "I was double-charged on my last invoice."
azd ai agent invoke "My TrailMaster tent's zipper broke after one week."
azd ai agent invoke "Are there any deals on hiking boots this month?"
```

You should see three very different conversational styles — because each specialist has its own instructions and tools.

## 👀 In the portal

- **Tracing** is the killer feature here. Open the agent's trace view and watch a single user message fan out into a triage decision → handoff → specialist invocation. Beautiful for an architecture deep-dive.

## Production tips

- Set `default_options={"store": False}` on each specialist agent — the *outer* hosted agent owns conversation history.
- Use **per-agent identities** (configure in `agent.yaml`) so each specialist only has the downstream Azure permissions it actually needs.
- For more elaborate flows, look at the **Workflow agents** (preview) in Foundry — a YAML/visual builder for the same pattern.

## Where to go next

You've shipped 11 different agents. Now:

- Open every one in the **Foundry portal** and run them from the Playground.
- Try modifying instructions and watch the new **versions** appear automatically.
- Wire **App Insights** dashboards to monitor your hosted agents in production.
- Explore the [tool catalog](https://learn.microsoft.com/azure/foundry/agents/concepts/tool-catalog) — there are more tools (memory, image generation, Fabric, SharePoint, browser automation…) beyond what we covered here.

🎉 Have fun at the demo booth!
