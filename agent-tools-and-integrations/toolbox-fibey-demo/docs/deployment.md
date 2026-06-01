# Deployment

## Overview

Fibey Field Ops supports multiple deployment modes:

1. **Container Apps Mode** (Recommended) - Self-hosted agent in Azure Container Apps
2. **Foundry Hosted Mode** - Uses Foundry's managed agent hosting
3. **Local Development Mode** - For development and testing

This guide focuses on **Container Apps deployment** using `azd`.

## Architecture

The deployment creates resources in a single resource group:

| Component | Azure Service | Source | Purpose |
|-----------|---------------|--------|---------|
| Chat UI | Container App | `ui/` | React frontend with activity sidebar |
| Gateway | Container App | `src/fibey/gateway/` | FastAPI proxy (supports 3 modes) |
| **Agent Service** | **Container App** | **src/fibey/agent/** | **Foundry agent + Toolbox MCP** |
| Work Orders API | Container App | `services/work-orders-api/` | Work order CRUD backend |
| Inventory MCP | Container App | `services/inventory-mcp/` | Inventory MCP server |
| AI Search | Azure AI Search | `services/foundry-iq-docs/` | Knowledge base index |
| Container Registry | ACR | — | Docker image storage |
| Storage Account | Blob Storage | `services/foundry-iq-docs/` | Document storage |
| Log Analytics | Workspace | — | Logging and monitoring |

## Prerequisites

- Azure subscription with Owner or Contributor + RBAC Admin roles
- Azure CLI (`az`) and Azure Developer CLI (`azd`)
- Docker Desktop (for local image builds if needed)
- Access to Azure AI Foundry project with:
  - Deployed Azure OpenAI model (e.g., `gpt-4`)
  - Foundry Toolbox configured
  - AI Search service

## Quick Deployment

```bash
# 1. Clone repository
git clone https://github.com/dbarkol/fibey-agent.git
cd fibey-agent

# 2. Login
az login
azd auth login

# 3. Set required configuration
azd env set FOUNDRY_PROJECT_ENDPOINT "https://<account>.services.ai.azure.com/api/projects/<project>"
azd env set FOUNDRY_MODEL "gpt-4"
azd env set TOOLBOX_MCP_URL "https://<account>.services.ai.azure.com/api/projects/<project>/toolboxes/<name>/mcp"
azd env set AZURE_SEARCH_ENDPOINT "https://<search>.search.windows.net"
azd env set AZURE_SEARCH_INDEX "<index-name>"

# 4. Deploy everything
azd up
```

**Important:** Do NOT include `?api-version=v1` in the `TOOLBOX_MCP_URL`. The agent code automatically appends this.

## Resource group: fibey-agent (externally managed)

This resource group is **not** managed by `azd`. It contains:

| Resource | Purpose |
|----------|---------|
| AI Foundry Project | Hosts the agent runtime |
| Foundry Toolbox | Single MCP endpoint dispatching to 4 tools |
| AI Services | Chat completions model deployment |

See `infra-agent/README.md` for setup instructions and how to capture the
endpoint values needed by the apps environment.

> **Note:** The Toolbox must be configured to point at the Container App
> FQDNs from the `fibey-apps` deployment (inventory-mcp, work-orders-api,
> status-dashboard). This is a manual step in the Foundry portal after
> both resource groups are set up.

## Environment variables

These are set via `azd env set` and injected into the gateway Container App
by the Bicep template:

| Variable | Description | Source |
|----------|-------------|--------|
| `FOUNDRY_PROJECT_ENDPOINT` | AI Foundry project endpoint | fibey-agent RG |
| `FOUNDRY_MODEL` | Model deployment name | fibey-agent RG |
| `TOOLBOX_MCP_URL` | Foundry Toolbox MCP endpoint (versioned URL) | fibey-agent RG |

## FoundryIQ Knowledge Base Setup

The deployed knowledge path is:

```text
services/foundry-iq-docs/docs/
→ Blob Storage container
→ AI Search indexer
→ AI Search index
→ Knowledge Source
→ Knowledge Base
→ MCP endpoint
→ Foundry connection
```

After `azd provision` (or after the infrastructure portion of `azd up`) completes:

1. **Upload documents to blob storage.** This repo already uses `services/foundry-iq-docs/docs/` as the upload source.
2. **Create the search index and indexer.** Run `./scripts/setup-knowledge-base.sh` to create the blob data source, `foundry-iq-docs-index`, semantic configuration `default`, and the indexer that ingests the text-only markdown files.
3. **Create the Knowledge Source.** Use the AI Search REST API with `api-version=2026-04-01` to create `fibey-field-ops-ks` with `kind: searchIndex`, pointing at `foundry-iq-docs-index`.
4. **Create the Knowledge Base.** Use the AI Search REST API with `api-version=2026-04-01` to create `fibey-field-ops-kb`, referencing `fibey-field-ops-ks`. Configure with `low` reasoning effort, `extractiveData` output mode, and a lightweight chat completion model (e.g. `gpt-4o-mini`) for query planning.
5. **Create the Foundry connection.** In the hosted agent AI Services account, create a `CognitiveSearch` connection with `ApiKey` auth pointing at the search service. Use this connection in the Toolbox with `azure_ai_search` tool type.
6. **Assign RBAC.** Grant the AI Services managed identity `Search Index Data Reader` and `Search Index Data Contributor` on the search service.

### Deployed components

| Layer | Name | Resource Group / Scope | Notes |
|-------|------|-------------------------|-------|
| Search service | `<env>-search` | `<resource-group>` | Azure AI Search, Basic SKU |
| Search index | `foundry-iq-docs-index` | Search service | 8 text documents, semantic ranking only, no vectors |
| Semantic config | `default` | `foundry-iq-docs-index` | `titleField=metadata_storage_name`, `contentField=content` |
| Knowledge source | `fibey-field-ops-ks` | AI Search REST API | `kind: searchIndex` via `2026-04-01` |
| Knowledge base | `fibey-field-ops-kb` | AI Search REST API | References `fibey-field-ops-ks` |
| MCP endpoint | `https://<search-service>.search.windows.net/knowledgebases/fibey-field-ops-kb/mcp` | AI Search | Exposed by the knowledge base |
| Foundry connection | `kb-fibey-field-ops-kb` | AI Services account | `RemoteTool` + `ProjectManagedIdentity` |
| RBAC | `Search Index Data Reader` | AI Services managed identity | Required on the search service |

The knowledge base retrieval was validated with semantic `intents` requests against `fibey-field-ops-ks`, returning references and source data:

```json
{
  "intents": [{"search": "How do I splice a fiber optic cable?", "type": "semantic"}],
  "knowledgeSourceParams": [{"knowledgeSourceName": "fibey-field-ops-ks", "kind": "searchIndex", "includeReferences": true, "includeReferenceSourceData": true}]
}
```

> **Note:** `2026-04-01` is the GA API version used here for knowledge sources and knowledge bases.
>
> **Note:** Azure AI Foundry workspaces currently allow up to **120 connections**. This workspace is already at **120/120**, so plan for cleanup or capacity management before adding more connections.

## Notes

- All Container Apps are configured with **minReplicas: 1** to avoid cold starts.
- The FoundryIQ documents are uploaded to blob storage and indexed separately — they are not part of the container deployment.
- The status dashboard can be set to internal-only ingress if browser automation is the only consumer.
- Infrastructure definitions live in `infra/` (Bicep modules). Toolbox registration inside Foundry is an operational step outside this repo.

## Post-Deployment: RBAC Configuration

After deployment, configure managed identity permissions for the agent-service:

```bash
# Get agent-service managed identity principal ID
AGENT_MI_ID=$(az containerapp show \
  --name fibey-apps-agent-service \
  --resource-group <your-resource-group> \
  --query identity.principalId -o tsv)

echo "Agent Service MI: $AGENT_MI_ID"

# Get Azure AI account resource ID (adjust for your subscription/resource group)
AI_ACCOUNT_ID="/subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.CognitiveServices/accounts/<account-name>"

# Assign Cognitive Services User role
az role assignment create \
  --assignee-object-id "$AGENT_MI_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services User" \
  --scope "$AI_ACCOUNT_ID"

# Assign Azure AI Developer role
az role assignment create \
  --assignee-object-id "$AGENT_MI_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Azure AI Developer" \
  --scope "$AI_ACCOUNT_ID"

# Assign Cognitive Services OpenAI User role
az role assignment create \
  --assignee-object-id "$AGENT_MI_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services OpenAI User" \
  --scope "$AI_ACCOUNT_ID"
```

### Foundry RBAC Roles (Reference)

**Note:** Foundry roles were recently renamed. Use role definition IDs (GUIDs) instead of role names:

| Role Name | Role ID (GUID) | Purpose |
|-----------|----------------|---------|
| Foundry User | `53ca6127-db72-4b80-b1b0-d745d6d5456d` | Basic Foundry access |
| Foundry Owner | `c883944f-8b7b-4483-af10-35834be79c4a` | Full Foundry management |
| Foundry Account Owner | `e47c6f54-e4a2-4754-9501-8e0985b135e1` | Account-level management |
| Foundry Project Manager | `eadc314b-1a2d-4efa-be10-5d325db5065e` | Project management |

To assign roles by GUID:
```bash
az role assignment create \
  --assignee-object-id "$AGENT_MI_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "53ca6127-db72-4b80-b1b0-d745d6d5456d" \
  --scope "$AI_ACCOUNT_ID"
```

**Current Implementation:** The Fibey Agent uses Cognitive Services roles (not Foundry-specific roles). This may change if Foundry Toolbox requires specific Foundry roles in future updates.

## Gateway Modes

The gateway supports three deployment modes configured via `AGENT_MODE` environment variable:

### 1. Container App Mode (Current Default)
```bash
AGENT_MODE=containerapp
CONTAINERAPP_AGENT_URL=https://fibey-apps-agent-service...
```
- Self-hosted agent in Container Apps
- Full control over deployment and scaling
- Direct Toolbox MCP integration with api-version=v1
- Managed identity authentication

### 2. Foundry Hosted Mode
```bash
AGENT_MODE=hosted
HOSTED_AGENT_ENDPOINT=https://<account>.services.ai.azure.com/api/projects/<project>
HOSTED_AGENT_NAME=fibey-agent
```
- Uses Foundry's managed agent hosting
- No container management needed
- Requires hosted agent deployment in Foundry project

### 3. Local Mode (Development Only)
```bash
AGENT_MODE=local
```
- Agent runs in-process with gateway
- For local development and testing
- Not suitable for production

## Troubleshooting

### Toolbox MCP Connection Errors

**Symptom:** `400 BadRequest` from Toolbox MCP endpoint during initialization

**Solution:** The Toolbox MCP endpoint requires `api-version=v1` (not date-based versions). The agent code in `src/fibey/agent/agent.py` automatically appends `?api-version=v1` to the `TOOLBOX_MCP_URL`. Verify:

1. `TOOLBOX_MCP_URL` does NOT include `?api-version=...`
2. Agent code includes the URL modification in `_create_toolbox_mcp()` function

Test directly:
```bash
TOKEN=$(az account get-access-token --resource https://ai.azure.com --query accessToken -o tsv)
curl "https://<account>.services.ai.azure.com/api/projects/<project>/toolboxes/<name>/mcp?api-version=v1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Foundry-Features: Toolboxes=V1Preview" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Authentication Errors

**Symptom:** `DefaultAzureCredential failed to retrieve a token`

**Solution:** Verify managed identity has required roles:
```bash
az role assignment list \
  --assignee "$AGENT_MI_ID" \
  --query "[].{role:roleDefinitionName,scope:scope}" \
  --output table
```

### Container App Logs

```bash
# Application logs
az containerapp logs show \
  --name fibey-apps-agent-service \
  --resource-group rg-fibey-westus2 \
  --type console \
  --tail 100

# System logs
az containerapp logs show \
  --name fibey-apps-agent-service \
  --resource-group rg-fibey-westus2 \
  --type system \
  --tail 50
```

### Manual Image Rebuild

If you need to rebuild and redeploy the agent-service:

```bash
# Build for linux/amd64 (required for Container Apps)
docker build --platform linux/amd64 \
  -f Dockerfile.agent-service \
  -t <acr-name>.azurecr.io/fibey-agent-service:latest .

# Push to ACR
az acr login --name <acr-name>
docker push <acr-name>.azurecr.io/fibey-agent-service:latest

# Update container app
az containerapp update \
  --name fibey-apps-agent-service \
  --resource-group rg-fibey-westus2 \
  --image <acr-name>.azurecr.io/fibey-agent-service:latest
```

## Verification

After deployment, test the stack:

```bash
# Test UI
curl https://fibey-apps-ui.<env-subdomain>.azurecontainerapps.io/

# Test agent-service health
curl https://fibey-apps-agent-service.<env-subdomain>.azurecontainerapps.io/api/health

# Test end-to-end chat via gateway
curl -X POST https://fibey-apps-gateway.<env-subdomain>.azurecontainerapps.io/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What tools do you have?","session_id":"test-123"}'
```

## Cleanup

```bash
# Remove all deployed resources
azd down

# Or manually delete resource group
az group delete --name rg-fibey-westus2 --yes --no-wait
```
