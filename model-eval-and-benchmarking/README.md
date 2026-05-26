# Model Eval & Benchmarking

Narrow the model list with public benchmarks. Decide with scenario-specific eval evidence.

Models change weekly. Your scenario, your spec, and your eval evidence are the stable layer. The Foundry catalog gives you the menu; this booth shows you how to **narrow** with public benchmarks, then **decide** with your own scenarios.

This repo is your follow-up kit from the //Build 2026 booth.

## The two-part workflow

| Stage | Question | Tool | Type |
|---|---|---|---|
| **1. Narrow** | "Which 2-3 models should I even try?" | Foundry Model Leaderboards | UI-only, no code |
| **2. Decide** | "Which one actually works on MY scenario?" | ASSERT (Adaptive Eval) | Code-first, notebook included |

## Part 1 — Narrow with Foundry Model Leaderboards (UI)

Start in the Foundry model catalog when you need a shortlist backed up industry-standard benchmarks. Use leaderboards and side-by-side comparison to filter by category, quality, safety, throughput, and cost before you spend time wiring models into your app. The booth demo showed the leaderboard entry point, quality vs safety/cost/throughput trade-off charts, and scenario leaderboards for narrowing a candidate set.

→ **Open the leaderboards:** https://aka.ms/model-leaderboards

Documentation:
- [Compare models using the model leaderboard](https://learn.microsoft.com/en-us/azure/foundry/how-to/benchmark-model-in-catalog)
- [Model benchmarks and leaderboards in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/concepts/model-benchmarks)
- [Microsoft Foundry Models overview](https://learn.microsoft.com/en-us/azure/foundry/concepts/foundry-models-overview)

What you get: a filtered shortlist by category, quality, throughput, and cost. Public benchmarks tell you what a model *can* do, not whether it works for your team's workflow.

## Part 2 — Decide with ASSERT on YOUR scenario (code)

Once you have 2-3 candidates, test them against the behavior your users actually need in the context of your specific use case. ASSERT is a spec-driven, scenario-specific eval harness: write a spec, generate targeted test cases, execute your target, then inspect judged evidence. For this booth, the target is a prompt agent (hosted model + system prompt + simulated tools) so the comparison isolates the model choice.

- **Walkthrough:** [`assert-model-eval-cookbook/assert-model-eval-cookbook.ipynb`](./assert-model-eval-cookbook/assert-model-eval-cookbook.ipynb)
- **Source:** https://github.com/microsoft/ASSERT

What you'll do in the notebook: define a one-page travel-planner spec, run the same prompt agent (hosted model + system prompt + simulated tools) against **gpt-5.4-mini vs gpt-5.4**, compare quality plus cost per judged pass, and read the evidence behind a failed case.

## Was this useful?

File issues on `microsoft/ASSERT`. Visit the booth team if you're at //Build.
