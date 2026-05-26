# 04 — Code Interpreter 📊

Give your agent a sandboxed Python runtime. It can:

- Parse files you upload
- Crunch numbers with `pandas` / `numpy`
- Generate charts with `matplotlib`
- Return both the code it wrote *and* the resulting artifacts

**Scenario:** upload a Q1 sales CSV; ask the agent to find the best-performing product and visualize the trend.

## Run it

```powershell
python code_interpreter_agent.py
```

Sample output:

```
Agent created (version 1)
Uploaded sales_2026_q1.csv
🐍 Code the agent wrote:
   import pandas as pd
   df = pd.read_csv(...)
   ...
📈 Agent answer: The top-performing product in Q1 was TrekLite Hiking Boots
   with $558,873 in revenue, growing 25% month-over-month...
```

## Why it's interesting

- **No backend to provision.** The Python sandbox lives inside the agent runtime.
- **Reproducible analysis.** The agent's code is captured in the response — paste it into a notebook and you have a perfect audit trail.
- **Charts in chat.** Returned PNGs are accessible via response annotations (extend the script to download them).

## 👀 In the portal

1. **Agents → SalesAnalystAgent → Playground**. Click 📎 **attach a file**, upload `sales_2026_q1.csv`, and ask "Plot revenue per region over time".
2. The portal renders the chart inline — perfect for a demo screen.
3. **Tracing** shows the `code_interpreter_call` span with the executed code.

## Where to go next

➡️ [05-file-search](../05-file-search/) — RAG over your own documents.
