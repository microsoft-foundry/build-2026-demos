# Copilot Instructions — Fibey Field Ops

## Architecture

This repository is a **fiber optics field operations** demo built on Azure AI Foundry Hosted Agents and the Foundry Toolbox. The agent helps field technicians with four tool domains:
- **Inventory MCP** — parts lookup, stock levels, and part details
- **Work Orders API** — view, create, and update work orders
- **FoundryIQ** — splicing procedures, safety protocols, troubleshooting docs
- **Browser automation / status dashboard** — network and service status checks

```text
React UI → FastAPI Gateway → Field Ops Agent → Foundry Toolbox → 4 operational tools
```

- **Backend**: Python 3.12+, FastAPI, Microsoft Agent Framework
- **Frontend**: React + TypeScript + Vite + Tailwind CSS
- **Infra**: Azure Bicep + azd

## Repository structure

```text
src/fibey/gateway/          # FastAPI gateway and streaming API
src/fibey/agent/            # Agent definition, hosted entrypoint, system prompt
ui/                         # React frontend
services/inventory-mcp/     # MCP inventory service
services/work-orders-api/   # FastAPI work order service
services/status-dashboard/  # Static HTML status dashboard
services/foundry-iq-docs/   # Markdown knowledge base content for FoundryIQ
infra/                      # Azure infrastructure definitions
scripts/                    # Setup and dev helpers
```

## Build & run

```bash
# Setup root app + UI deps
./scripts/setup.sh

# Run gateway + UI
./scripts/start-dev.sh

# Gateway only
uv run uvicorn fibey.gateway.api_server:app --reload --port 8080

# Agent CLI only
uv run python -m fibey.agent.main

# Frontend only
cd ui && npm run dev

# Inventory MCP
cd services/inventory-mcp && uv sync && uv run python server.py

# Work Orders API
cd services/work-orders-api && uv sync && uv run python server.py

# Status dashboard (simple local serve)
cd services/status-dashboard/public && python -m http.server 8003

# Frontend production build
cd ui && npm run build
```

## Key patterns

### Streaming SSE protocol
The gateway streams chat responses from `POST /api/chat` and emits assistant text, activity updates, citations, errors, and done events.

### Agent mode
`AGENT_MODE` controls execution:
- `local` — agent runs in-process and connects to the toolbox directly
- `hosted` — gateway proxies to the Foundry-hosted agent

### Activity sidebar
The UI activity sidebar is a core demo feature. Keep tool names and status updates understandable for field operations scenarios.

### Toolbox integration
The agent connects to the Foundry Toolbox via `MCPStreamableHTTPTool` (local) or `FoundryChatClient.get_mcp_tool()` (hosted). Auth uses Azure credentials and the Cognitive Services scope.

### Service expectations
- `services/inventory-mcp/` serves streamable HTTP MCP on port `8001`
- `services/work-orders-api/` serves FastAPI on port `8002`
- `services/status-dashboard/` serves static status content on port `8003`
- `services/foundry-iq-docs/docs/` contains markdown uploaded to blob storage separately for FoundryIQ ingestion

### Coding conventions
- Keep agent prompts in `src/fibey/agent/prompts/`
- Keep gateway and agent logic separate deployable concerns
- Use Tailwind utilities in the UI; avoid introducing separate component CSS files
- Use `.env` / `.env.example` for local configuration
