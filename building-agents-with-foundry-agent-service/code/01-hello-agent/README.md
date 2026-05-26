# 01 — Hello, Agent 👋

The simplest Microsoft Foundry agent you can build. Three things in ~30 lines:

1. **Connect** to your Foundry project with `AIProjectClient`.
2. **Create** a Prompt agent — just a model + a system prompt.
3. **Chat** with it through a multi-turn conversation.

This is the foundation every later scenario builds on.

## Run it

```powershell
python basic_agent.py
```

Expected output (yours will differ):

```
Agent created (id: ..., name: HelloAgent, version: 1)
Created conversation (id: ...)
Response: France covers approximately 248,573 square miles...
Response: The capital of France is Paris.
Agent deleted
```

## What just happened?

| Step | API | Notes |
|---|---|---|
| Build agent | `project_client.agents.create_version(...)` | Each call snapshots a new *version* |
| Reference agent | `extra_body={"agent_reference": {...}}` | OpenAI-compatible Responses API |
| Multi-turn memory | `openai_client.conversations.create()` | Foundry stores the conversation server-side |

## 👀 View it in the portal

1. Open <https://ai.azure.com> → your project → **Agents**.
2. Click **HelloAgent**. You'll see the instructions and version history.
3. Switch to the **Playground** tab to chat with it directly — no code required.

> 🧪 **Try this:** Change the `instructions` string to give the agent a personality ("You are a snarky pirate"), re-run, and watch the new version appear in the portal.

## Where to go next

➡️ [02-streaming](../02-streaming/) — make responses appear token-by-token like ChatGPT.
