# 08 — Capstone: Travel Concierge 🧳

Everything together. One Prompt agent. Four tools. A real-world workflow.

## Meet the Concierge

> **"Plan me a 3-day Tokyo trip in March 2027 for a $2,500 budget, then make a spending chart."**

The agent must:

1. **Web search** — what's the weather in Tokyo in March? What are top neighborhoods?
2. **Function tool** — `book_flight()` & `get_exchange_rate()` (mocked here; pretend they're real APIs).
3. **Code interpreter** — produce a daily-budget pie chart.
4. **File search** — recall the user's loyalty status & travel preferences from a small profile doc.

This is the pattern most production agents follow: **a single orchestrator + many tools**.

## Run it

```powershell
python concierge_agent.py
```

The script will:
- Spin up a vector store with the traveler profile
- Register two custom functions
- Wire in web search and code interpreter
- Run a single user prompt and execute the tool-call loop until the agent is done

Expected highlights:
- Live web results with citations
- `book_flight` invoked with structured args
- Python code generated for the budget chart
- A final, human-readable itinerary

## Architecture

```
              ┌──────────────────────────────┐
              │      ConciergeAgent          │
              │  (gpt-4o, single instance)   │
              └─────────────┬────────────────┘
                            │
       ┌────────────┬───────┴────────┬──────────────┐
       ▼            ▼                ▼              ▼
  WebSearchTool  FunctionTool×2  CodeInterpreter  FileSearchTool
   (Bing)        (book_flight,   (matplotlib in   (traveler
                  get_fx)         sandbox)         profile.md)
```

## Why this is interesting for a demo booth

- Audience sees a **single prompt** unfold into a multi-tool orchestration.
- Every tool you've seen in 03–07 is here — but composed naturally.
- A small change to `instructions` re-shapes the behavior immediately.

## 👀 In the portal

Open **Agents → ConciergeAgent → Tracing** after a run. You'll see a clean Gantt chart: model → web_search → function → file_search → code_interpreter → model → final. This view alone is worth showing to architects.

## Where to go next

You've maxed out the Prompt agent surface. Time to graduate to code.

➡️ [09-hosted-agent-intro](../09-hosted-agent-intro/) — when & why to move to a Hosted agent.
