# Foundry IQ Cookbook

End-to-end walkthrough that provisions an agentic retrieval pipeline on Azure AI Search and queries it from Python — index → knowledge source → knowledge base → cited answer, all in a single notebook.

## What you'll build

1. A vector + semantic **Search Index** populated with NASA's *Earth at Night* dataset.
2. A **Knowledge Source** pointing at that index.
3. A **Knowledge Base** that pairs the source with an Azure OpenAI chat model and answer synthesis.
4. Two retrievals — a complex multi-part question and a multi-turn follow-up — with the planner's activity trace and citations.
5. A clean teardown that removes every resource the notebook created.

## Prerequisites

- An **Azure AI Search** service in a [region that supports agentic retrieval](https://learn.microsoft.com/azure/search/search-region-support).
- A **Microsoft Foundry** (or Azure OpenAI) resource with two deployments:
  - An embedding model — `text-embedding-3-large` (3072 dims, used here).
  - A chat model — `gpt-4o`, `gpt-4o-mini`, or `gpt-5-mini`.
- Python 3.10+ and admin keys for both services.

## Run it

```powershell
# 1. Create a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Install dependencies (pip.ini wires in the Azure SDK alpha feed)
$env:PIP_CONFIG_FILE = "$PWD\pip.ini"
pip install -r requirements.txt

# 3. Configure credentials
Copy-Item .env.example .env
# ...edit .env with your endpoints and keys

# 4. Open the notebook
jupyter notebook foundry-iq-cookbook.ipynb
```

On macOS/Linux replace the activation and `$env:` syntax with `source .venv/bin/activate` and `export PIP_CONFIG_FILE=$PWD/pip.ini`.

## Files

| File | Purpose |
|---|---|
| `foundry-iq-cookbook.ipynb` | The cookbook — open and run top to bottom. |
| `requirements.txt` | Pinned dependencies, including `azure-search-documents==12.1.0a20260515004` (alpha SDK for the `2026-05-01-preview` API — the surface that backs the upcoming Build 2026 features). |
| `pip.ini` | Adds the Azure SDK public feed so pip can resolve the alpha. |
| `.env.example` | Template for the endpoints and keys the notebook needs. |

## Reference docs

- [Agentic retrieval overview](https://learn.microsoft.com/azure/search/agentic-retrieval-overview)
- [Create a knowledge base](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-create-knowledge-base)
- [Answer synthesis](https://learn.microsoft.com/azure/search/agentic-retrieval-how-to-answer-synthesis)
- [Connect a knowledge base to a Foundry agent](https://learn.microsoft.com/azure/foundry/agents/how-to/foundry-iq-connect)
