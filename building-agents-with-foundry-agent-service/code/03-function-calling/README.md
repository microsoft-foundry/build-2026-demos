# 03 — Function Calling 🔧

Give your agent custom Python functions to call. The agent decides **when** to call them, **what arguments** to pass, and **how to use the result**.

**Scenario:** a personal-finance agent that can look up stock quotes and compute portfolio totals. The "lookup" is a mock — but it could just as easily hit Yahoo Finance, a CRM API, or your internal microservice.

## What's interesting

- The agent receives **only the function signature + description** — no implementation. It reasons about which one to call.
- You can register **multiple tools** and the agent will fan out across them.
- `strict=True` forces the model to produce JSON that exactly matches your schema.

## Run it

```powershell
python function_tool_agent.py
```

Sample output:

```
🤖 First turn — model decides to call tools
  → get_stock_quote(symbol='MSFT')
  → get_stock_quote(symbol='NVDA')
  → get_stock_quote(symbol='CRM')
🤖 Second turn — model produces final answer
Your portfolio is worth approximately $48,720. NVDA is the top performer today (+2.1%)...
```

## The control loop

```
user message  ──► agent
                  │
                  ├─ emits function_call items
                  ▼
          your code executes them
                  │
                  ├─ feeds FunctionCallOutput back in
                  ▼
              agent ──► final natural-language answer
```

## 👀 In the portal

1. Open **Agents → PortfolioAgent → Setup**. Your registered tools (get_stock_quote, get_portfolio) are listed.
2. **Playground** lets a non-developer chat with the agent. **Important:** function tools defined in code only execute when *your script* is running — the portal playground can simulate the call request, but you'd need to wire the executor to actually run them. For pure portal demos, use code interpreter / web search / file search.
3. **Tracing** shows each function-call request as a separate span.

## Where to go next

➡️ [04-code-interpreter](../04-code-interpreter/) — let the agent write & run its own Python.
