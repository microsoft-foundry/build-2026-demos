# ASSERT — measure whether your guardrails actually work

Guardrails answer *"did we block the bad thing?"* — but most AI failures are emergent, scenario-specific, and live in the long tail. **ASSERT** is Microsoft Foundry's open-source eval framework for AI agents and apps. It lets developers write a one-page **behavioral spec** in plain English (what the agent should and should not do), generate scenario-specific test cases, run the same eval against the unguarded and guarded variants, and **see the trade-off** between safety wins and quality cost — per dimension, not as one rolled-up number.

ASSERT is the third leg of this booth: **author → enforce → measure.**

## Why ASSERT belongs in the guardrails-and-controls booth

A guardrail without an eval is a hope. ASSERT lets you:

- **Prove the trade-off before you ship**: run ASSERT on the agent **before** and **after** applying Agent Shield (or any other mitigation), and see exactly which failure modes closed, which costs you paid (e.g., overrefusal), and which axes regressed.
- **Catch the silent regression**: a naive DO-NOT prompt can *look* like it fixed the rolled-up violation rate while making a specific axis (e.g., account-takeover susceptibility) **worse**. Per-dimension scoring catches it; aggregate scoring hides it.
- **Pair with any framework, any model**: ASSERT plugs into 33 agent frameworks via OpenInference auto-instrumentation. Two lines of code for the happy path, no SDK migration.

## Framework-agnostic happy path — travel planner with LangGraph

This demo uses the [travel planner LangGraph example](https://github.com/microsoft/ASSERT/tree/main/examples/phoenix_auto_trace) to show ASSERT working **without any agent-side code changes** — just OpenInference auto-instrumentation streaming traces into ASSERT's judge pipeline.

The happy path is two lines added to your agent's startup:

```python
from openinference.instrumentation.langchain import LangChainInstrumentor
LangChainInstrumentor().instrument()
```

Once that lands, ASSERT picks up every agent invocation through OTel and scores it against your behavioral spec — no SDK adoption, no orchestration rewrite.

## Demo video

### Universal framework support — 2-min walkthrough

<video src="./assert-universal-framework-support.mp4" controls width="100%"></video>

Walks through ASSERT picking up traces from multiple agent frameworks (LangGraph, LangChain, and others in the OpenInference instrumentor set) via the same two-line OpenTelemetry setup — no SDK changes to the agent code.

## Where this fits

| Stage | Capability | Booth folder |
|---|---|---|
| **Author** | No-code guardrail setup in the Foundry portal | [`../guided-setup/`](../guided-setup/) |
| **Enforce** | Agent Shield runtime control plane | [`../agent-shield/`](../agent-shield/) |
| **Measure** | Scenario-specific eval to prove the trade-off (this folder) | `assert/` |

## Resources

- **ASSERT source**: <https://github.com/microsoft/ASSERT>
- **Travel planner LangGraph example**: [`examples/phoenix_auto_trace/`](https://github.com/microsoft/ASSERT/tree/main/examples/phoenix_auto_trace)
- **Writing eval specs**: <https://github.com/microsoft/ASSERT/blob/main/docs/writing-eval-specs.md>
- **Model Eval and Benchmarking booth (sibling)**: [`../../model-eval-and-benchmarking/`](../../model-eval-and-benchmarking/)

## Was this useful?

Visit the **Agent Guardrails and Controls** booth at //Build 2026, or file issues at <https://github.com/microsoft/ASSERT/issues>.