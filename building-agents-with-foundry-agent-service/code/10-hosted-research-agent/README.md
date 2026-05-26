# 10 — Hosted Agent: Deep Research 🔬

A hosted research agent that plans, gathers, and synthesizes — all inside the container.

**Scenario:** the user asks a broad research question (e.g. *"How is generative AI changing supply-chain forecasting?"*). The agent:

1. **Plans** sub-questions to investigate.
2. **Searches the web** for each one (Foundry's hosted Web Search tool).
3. **Cross-checks** with internal knowledge if the question touches private docs (file_search).
4. **Synthesizes** a final briefing with citations.

This pattern needs more than a single system prompt + tool list — the planning loop benefits from real code. Hence: hosted agent.

## Files

| File | Purpose |
|---|---|
| [main.py](./main.py) | Agent Framework code — single `Agent` with web search + a custom `plan_subquestions` tool |
| [agent.yaml](./agent.yaml) | Hosted-agent manifest (protocol, CPU/mem, env vars) |
| [requirements.txt](./requirements.txt) | Python deps for the container |
| [agent.manifest.yaml](./agent.manifest.yaml) | Scaffolding manifest for `azd ai agent init` |

## Deploy & run

```powershell
mkdir my-research-agent ; cd my-research-agent
azd ai agent init -m ..\10-hosted-research-agent\agent.manifest.yaml
azd up

# Test
azd ai agent invoke "How is generative AI changing supply-chain forecasting?"
```

Then open the Foundry portal → **Agents → research-agent → Open in playground** and ask follow-ups conversationally.

## Why this design

- **Per-agent identity.** The container's managed identity lets the agent call your private Azure Search index, Cosmos DB, or Blob Storage — no connection strings in code.
- **Scale-to-zero.** Idle research agents cost nothing; first request after 15 min has a small cold start.
- **Sessions.** Each user gets a per-session filesystem — perfect for caching downloaded PDFs across turns.

## 👀 In the portal

- **Container details** — see real CPU/memory and the deployed container image tag.
- **Tracing** in App Insights — every `plan_subquestions` call and every `web_search` invocation shows up as a span. The agent's planning chain is visible end-to-end.
- **Playground** — type a question and watch the streaming response.

## Where to go next

➡️ [11-hosted-multi-agent](../11-hosted-multi-agent/) — orchestrate multiple specialist agents in one container.
