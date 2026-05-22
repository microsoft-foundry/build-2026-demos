# ASSERT Model Eval Cookbook

Runnable notebook for the model eval and benchmarking booth track: shortlist models with Foundry Leaderboards, then compare two candidates on a LangGraph travel-planner scenario using ASSERT.

## What you'll run

1. Install ASSERT from `microsoft/ASSERT` with the LangGraph and OpenTelemetry extras.
2. Load Azure OpenAI settings from `.env`.
3. Write a compact travel-planner eval spec and ASSERT YAML config.
4. Run the same scenario against `gpt-5.4-mini` and `gpt-5.4`.
5. Compare judged pass rate, token use, and cost per judged pass.
6. Inspect one failed verdict with the judge rationale and cited conversation turn.

## Prerequisites

- Python 3.11+.
- Azure OpenAI or Microsoft Foundry model deployments for the two candidate models.
- Access to the deployment names you put in `.env`.

## Run it

```powershell
# 1. Create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials
Copy-Item .env.example .env
# ...edit .env with your endpoint, key, deployment names, and optional prices

# 4. Open the notebook
jupyter notebook assert-model-eval-cookbook.ipynb
```

On macOS/Linux replace the activation and copy commands with `source .venv/bin/activate` and `cp .env.example .env`.

## Files

| File | Purpose |
|---|---|
| `assert-model-eval-cookbook.ipynb` | The walkthrough — open and run top to bottom. |
| `requirements.txt` | Notebook runtime plus ASSERT from `microsoft/ASSERT`. |
| `.env.example` | Template for Azure OpenAI settings and optional pricing inputs. |

## Reference docs

- [ASSERT source](https://github.com/microsoft/ASSERT)
- [Compare models using the model leaderboard](https://learn.microsoft.com/en-us/azure/foundry/how-to/benchmark-model-in-catalog)
- [Model benchmarks and leaderboards in Microsoft Foundry](https://learn.microsoft.com/en-us/azure/foundry/concepts/model-benchmarks)
