#!/usr/bin/env bash
# Upload FoundryIQ docs to blob storage and configure the full AI Search + FoundryIQ pipeline.
# Usage: ./scripts/setup-knowledge-base.sh [foundry-resource-group] [foundry-account-name] [foundry-project-name]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DOCS_DIR="$REPO_ROOT/services/foundry-iq-docs/docs"

CONTAINER_NAME="foundry-iq-docs"
INDEX_NAME="foundry-iq-docs-index"
DATASOURCE_NAME="foundry-iq-docs-ds"
INDEXER_NAME="foundry-iq-docs-indexer"
KB_NAME="fibey-field-ops-kb"
KS_NAME="fibey-field-ops-ks"
CONNECTION_NAME="kb-fibey-field-ops-kb"

SEARCH_API_VERSION="2024-07-01"
KNOWLEDGE_API_VERSION="2026-04-01"
FOUNDRY_CONNECTION_API_VERSION="2025-10-01-preview"
SEARCH_INDEX_DATA_READER_ROLE_ID="1407120a-92aa-4202-b7e9-c0e197c71c8f"

FOUNDRY_RESOURCE_GROUP="${1:-${FOUNDRY_RESOURCE_GROUP:-}}"
FOUNDRY_ACCOUNT_NAME="${2:-${FOUNDRY_ACCOUNT_NAME:-}}"
FOUNDRY_PROJECT_NAME="${3:-${FOUNDRY_PROJECT_NAME:-}}"

if [ -z "${AZURE_RESOURCE_GROUP:-}" ]; then
  echo "AZURE_RESOURCE_GROUP must be set before running this script."
  exit 1
fi

if [ -z "$FOUNDRY_PROJECT_NAME" ] && [ -n "${FOUNDRY_PROJECT_ENDPOINT:-}" ]; then
  FOUNDRY_PROJECT_NAME="${FOUNDRY_PROJECT_ENDPOINT##*/}"
fi

# Resolve resource names from azd outputs
echo "Reading azd outputs..."
STORAGE_ACCOUNT=$(azd env get-value storageAccountName 2>/dev/null || \
  az storage account list -g "${AZURE_RESOURCE_GROUP}" --query "[0].name" -o tsv)
SEARCH_SERVICE=$(azd env get-value searchServiceName 2>/dev/null || \
  az search service list -g "${AZURE_RESOURCE_GROUP}" --query "[0].name" -o tsv)
SEARCH_ENDPOINT="https://${SEARCH_SERVICE}.search.windows.net"
MCP_ENDPOINT="${SEARCH_ENDPOINT}/knowledgebases/${KB_NAME}/mcp"

if [ -z "$STORAGE_ACCOUNT" ] || [ -z "$SEARCH_SERVICE" ]; then
  echo "Could not resolve storage account or search service from azd outputs or Azure CLI."
  exit 1
fi

SEARCH_RESOURCE_ID=$(az search service show \
  --service-name "$SEARCH_SERVICE" \
  --resource-group "${AZURE_RESOURCE_GROUP}" \
  --query id -o tsv)

STORAGE_CONNECTION_STRING=$(az storage account show-connection-string \
  --name "$STORAGE_ACCOUNT" \
  --query connectionString -o tsv)

SEARCH_ADMIN_KEY="${AZURE_SEARCH_ADMIN_KEY:-}"
if [ -z "$SEARCH_ADMIN_KEY" ]; then
  SEARCH_ADMIN_KEY=$(az search admin-key show \
    --service-name "$SEARCH_SERVICE" \
    --resource-group "${AZURE_RESOURCE_GROUP}" \
    --query primaryKey -o tsv)
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)

if [ -z "$FOUNDRY_RESOURCE_GROUP" ] || [ -z "$FOUNDRY_ACCOUNT_NAME" ]; then
  echo "FOUNDRY_RESOURCE_GROUP and FOUNDRY_ACCOUNT_NAME must be set (or passed as the first two arguments)."
  exit 1
fi

if [ -n "$FOUNDRY_PROJECT_NAME" ]; then
  FOUNDRY_PROJECT_RESOURCE_ID="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${FOUNDRY_RESOURCE_GROUP}/providers/Microsoft.MachineLearningServices/workspaces/${FOUNDRY_ACCOUNT_NAME}/projects/${FOUNDRY_PROJECT_NAME}"
else
  FOUNDRY_PROJECT_RESOURCE_ID=$(az resource list \
    --resource-group "$FOUNDRY_RESOURCE_GROUP" \
    --namespace Microsoft.MachineLearningServices \
    --query "[?type=='Microsoft.MachineLearningServices/workspaces/projects' && contains(id, '/workspaces/${FOUNDRY_ACCOUNT_NAME}/projects/')].id | [0]" \
    -o tsv)
fi

if [ -z "$FOUNDRY_PROJECT_RESOURCE_ID" ]; then
  echo "Could not resolve a Foundry project resource ID. Set FOUNDRY_PROJECT_NAME or FOUNDRY_PROJECT_ENDPOINT."
  exit 1
fi

if [ -z "$FOUNDRY_PROJECT_NAME" ]; then
  FOUNDRY_PROJECT_NAME="${FOUNDRY_PROJECT_RESOURCE_ID##*/}"
fi

FOUNDRY_MI_PRINCIPAL_ID=$(az resource show \
  --ids "$FOUNDRY_PROJECT_RESOURCE_ID" \
  --api-version "$FOUNDRY_CONNECTION_API_VERSION" \
  --query identity.principalId -o tsv)

if [ -z "$FOUNDRY_MI_PRINCIPAL_ID" ]; then
  FOUNDRY_MI_PRINCIPAL_ID=$(az resource show \
    --ids "/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${FOUNDRY_RESOURCE_GROUP}/providers/Microsoft.MachineLearningServices/workspaces/${FOUNDRY_ACCOUNT_NAME}" \
    --api-version "$FOUNDRY_CONNECTION_API_VERSION" \
    --query identity.principalId -o tsv)
fi

if [ -z "$FOUNDRY_MI_PRINCIPAL_ID" ]; then
  echo "Could not resolve the Foundry managed identity principal ID for RBAC assignment."
  exit 1
fi

ROLE_DEFINITION_ID="/subscriptions/${SUBSCRIPTION_ID}/providers/Microsoft.Authorization/roleDefinitions/${SEARCH_INDEX_DATA_READER_ROLE_ID}"
MANAGEMENT_TOKEN=$(az account get-access-token \
  --scope https://management.azure.com/.default \
  --query accessToken -o tsv)

echo ""
echo "Storage Account       : $STORAGE_ACCOUNT"
echo "Search Service        : $SEARCH_SERVICE"
echo "Search Endpoint       : $SEARCH_ENDPOINT"
echo "Foundry Resource Group: $FOUNDRY_RESOURCE_GROUP"
echo "Foundry Account       : $FOUNDRY_ACCOUNT_NAME"
echo "Foundry Project       : $FOUNDRY_PROJECT_NAME"
echo ""

# ─── 1. Upload documents ───────────────────────────────────────────────
echo "=== Uploading documents to blob storage ==="
az storage blob upload-batch \
  --source "$DOCS_DIR" \
  --destination "$CONTAINER_NAME" \
  --account-name "$STORAGE_ACCOUNT" \
  --auth-mode key \
  --overwrite \
  --no-progress
echo "✓ Uploaded $(find "$DOCS_DIR" -maxdepth 1 -type f | wc -l | tr -d ' ') documents"

# ─── 2. Create data source ─────────────────────────────────────────────
echo ""
echo "=== Creating search data source ==="
curl --fail-with-body -sS -X PUT "${SEARCH_ENDPOINT}/datasources/${DATASOURCE_NAME}?api-version=${SEARCH_API_VERSION}" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d "{
    \"name\": \"${DATASOURCE_NAME}\",
    \"type\": \"azureblob\",
    \"credentials\": {
      \"connectionString\": \"${STORAGE_CONNECTION_STRING}\"
    },
    \"container\": {
      \"name\": \"${CONTAINER_NAME}\"
    }
  }" | python3 -m json.tool
echo "✓ Data source created"

# ─── 3. Create search index ────────────────────────────────────────────
echo ""
echo "=== Creating search index ==="
curl --fail-with-body -sS -X PUT "${SEARCH_ENDPOINT}/indexes/${INDEX_NAME}?api-version=${SEARCH_API_VERSION}" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d "{
    \"name\": \"${INDEX_NAME}\",
    \"fields\": [
      {\"name\": \"id\", \"type\": \"Edm.String\", \"key\": true, \"filterable\": true, \"retrievable\": true},
      {\"name\": \"content\", \"type\": \"Edm.String\", \"searchable\": true, \"retrievable\": true},
      {\"name\": \"metadata_storage_path\", \"type\": \"Edm.String\", \"filterable\": true, \"retrievable\": true},
      {\"name\": \"metadata_storage_name\", \"type\": \"Edm.String\", \"filterable\": true, \"retrievable\": true}
    ],
    \"semantic\": {
      \"configurations\": [
        {
          \"name\": \"default\",
          \"prioritizedFields\": {
            \"prioritizedContentFields\": [{\"fieldName\": \"content\"}],
            \"titleField\": {\"fieldName\": \"metadata_storage_name\"}
          }
        }
      ],
      \"defaultConfiguration\": \"default\"
    }
  }" | python3 -m json.tool
echo "✓ Index created"

# ─── 4. Create indexer ─────────────────────────────────────────────────
echo ""
echo "=== Creating search indexer ==="
curl --fail-with-body -sS -X PUT "${SEARCH_ENDPOINT}/indexers/${INDEXER_NAME}?api-version=${SEARCH_API_VERSION}" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d "{
    \"name\": \"${INDEXER_NAME}\",
    \"dataSourceName\": \"${DATASOURCE_NAME}\",
    \"targetIndexName\": \"${INDEX_NAME}\",
    \"fieldMappings\": [
      {
        \"sourceFieldName\": \"metadata_storage_path\",
        \"targetFieldName\": \"id\",
        \"mappingFunction\": {
          \"name\": \"base64Encode\"
        }
      }
    ],
    \"parameters\": {
      \"configuration\": {
        \"parsingMode\": \"default\",
        \"dataToExtract\": \"contentAndMetadata\"
      }
    },
    \"schedule\": null
  }" | python3 -m json.tool
echo "✓ Indexer created"

# ─── 5. Run indexer ────────────────────────────────────────────────────
echo ""
echo "=== Running indexer ==="
curl --fail-with-body -sS -X POST "${SEARCH_ENDPOINT}/indexers/${INDEXER_NAME}/run?api-version=${SEARCH_API_VERSION}" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -H "Content-Length: 0" \
  -w "HTTP %{http_code}"
echo ""
echo "✓ Indexer triggered — documents will be indexed shortly"

# ─── 6. Check status ───────────────────────────────────────────────────
echo ""
echo "=== Checking indexer status ==="
sleep 5
STATUS=$(curl --fail-with-body -sS "${SEARCH_ENDPOINT}/indexers/${INDEXER_NAME}/status?api-version=${SEARCH_API_VERSION}" \
  -H "api-key: ${SEARCH_ADMIN_KEY}")
echo "$STATUS" | python3 -c "
import json, sys
d = json.load(sys.stdin)
hist = d.get('lastResult', {})
print(f\"Status: {hist.get('status', 'unknown')}\")
print(f\"Items processed: {hist.get('itemsProcessed', 0)}\")
print(f\"Items failed: {hist.get('itemsFailed', 0)}\")
"

# ─── 7. Create knowledge source ────────────────────────────────────────
echo ""
echo "=== Creating knowledge source ==="
curl --fail-with-body -sS -X PUT "${SEARCH_ENDPOINT}/knowledgesources/${KS_NAME}?api-version=${KNOWLEDGE_API_VERSION}" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d "{
    \"name\": \"${KS_NAME}\",
    \"kind\": \"searchIndex\",
    \"description\": \"Knowledge source for Fibey Field Ops FoundryIQ documents.\",
    \"encryptionKey\": null,
    \"searchIndexParameters\": {
      \"searchIndexName\": \"${INDEX_NAME}\",
      \"semanticConfigurationName\": \"default\",
      \"sourceDataFields\": [
        { \"name\": \"metadata_storage_name\" },
        { \"name\": \"metadata_storage_path\" }
      ],
      \"searchFields\": [
        { \"name\": \"content\" }
      ]
    }
  }" | python3 -m json.tool
echo "✓ Knowledge source created"

# ─── 8. Create knowledge base ──────────────────────────────────────────
echo ""
echo "=== Creating knowledge base ==="
curl --fail-with-body -sS -X PUT "${SEARCH_ENDPOINT}/knowledgebases/${KB_NAME}?api-version=${KNOWLEDGE_API_VERSION}" \
  -H "Content-Type: application/json" \
  -H "api-key: ${SEARCH_ADMIN_KEY}" \
  -d "{
    \"name\": \"${KB_NAME}\",
    \"description\": \"Knowledge base for Fibey Field Ops procedures, safety guidance, and troubleshooting docs.\",
    \"knowledgeSources\": [
      { \"name\": \"${KS_NAME}\" }
    ],
    \"encryptionKey\": null
  }" | python3 -m json.tool
echo "✓ Knowledge base created"

# ─── 9. Create Foundry connection ──────────────────────────────────────
echo ""
echo "=== Creating Foundry connection ==="
curl --fail-with-body -sS -X PUT "https://management.azure.com${FOUNDRY_PROJECT_RESOURCE_ID}/connections/${CONNECTION_NAME}?api-version=${FOUNDRY_CONNECTION_API_VERSION}" \
  -H "Authorization: Bearer ${MANAGEMENT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"${CONNECTION_NAME}\",
    \"type\": \"Microsoft.MachineLearningServices/workspaces/connections\",
    \"properties\": {
      \"authType\": \"ProjectManagedIdentity\",
      \"category\": \"RemoteTool\",
      \"target\": \"${MCP_ENDPOINT}\",
      \"isSharedToAll\": true,
      \"audience\": \"https://search.azure.com/\",
      \"metadata\": {
        \"ApiType\": \"Azure\"
      }
    }
  }" | python3 -m json.tool
echo "✓ Foundry connection created"

# ─── 10. Assign RBAC ───────────────────────────────────────────────────
echo ""
echo "=== Assigning Search Index Data Reader RBAC ==="
EXISTING_ASSIGNMENT=$(az role assignment list \
  --assignee-object-id "$FOUNDRY_MI_PRINCIPAL_ID" \
  --scope "$SEARCH_RESOURCE_ID" \
  --query "[?roleDefinitionId=='${ROLE_DEFINITION_ID}'].id | [0]" \
  -o tsv)

if [ -n "$EXISTING_ASSIGNMENT" ]; then
  echo "✓ Search Index Data Reader already assigned"
else
  az role assignment create \
    --assignee-object-id "$FOUNDRY_MI_PRINCIPAL_ID" \
    --assignee-principal-type ServicePrincipal \
    --role "$SEARCH_INDEX_DATA_READER_ROLE_ID" \
    --scope "$SEARCH_RESOURCE_ID" \
    --only-show-errors >/dev/null
  echo "✓ Search Index Data Reader assigned"
fi

echo ""
echo "=== Done ==="
echo "Search endpoint   : ${SEARCH_ENDPOINT}"
echo "Index name        : ${INDEX_NAME}"
echo "Knowledge source  : ${KS_NAME}"
echo "Knowledge base    : ${KB_NAME}"
echo "Foundry connection: ${CONNECTION_NAME}"
echo "MCP endpoint      : ${MCP_ENDPOINT}"
echo ""
echo "Set these in your azd environment:"
echo "  azd env set AZURE_SEARCH_ENDPOINT \"${SEARCH_ENDPOINT}\""
echo "  azd env set KB_NAME \"${KB_NAME}\""
