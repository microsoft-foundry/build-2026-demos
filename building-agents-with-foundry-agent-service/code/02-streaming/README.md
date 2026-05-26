# 02 — Streaming Responses ⚡

Same agent as scenario 01, but the response **streams** token-by-token. This is what makes ChatGPT-style UIs feel responsive.

The only change: set `stream=True` and iterate over events.

## Run it

```powershell
python streaming_agent.py
```

You'll see the answer appear gradually instead of all at once.

## Event types worth knowing

| Event | When it fires | Use it for |
|---|---|---|
| `response.created` | Run started | Display "thinking..." indicator |
| `response.output_text.delta` | Each token | Append to UI |
| `response.text.done` | Final assistant message ready | Stop spinner |
| `response.completed` | Whole run finished | Get usage / final state |

When tools are involved you'll also see `response.output_item.added` events for tool calls — useful for showing "🔧 calling get_weather..." in your UI.

## 👀 In the portal

Streaming is a client-side concern; the agent itself looks identical to scenario 01. But if you open **Tracing** on the agent after a run you'll see the same `responses.create` call, with token-by-token latency captured.

## Where to go next

➡️ [03-function-calling](../03-function-calling/) — let your agent call *your* Python code.
