# Toolbox Integration

This sample connects to the **Azure AI Foundry Toolbox** via its **MCP
(Model Context Protocol) Streamable HTTP** endpoint. The Toolbox acts as a
single unified gateway to multiple operational tools — the agent makes one
MCP connection, and the Toolbox dispatches calls to individual tools
(inventory, work orders, FoundryIQ knowledge base, status dashboard) behind
the scenes.

```text
Field Ops Agent ──► Foundry Toolbox (single MCP endpoint)
                         │
        ┌────────────────┼──────────────────┬──────────────────┐
        │                │                  │                  │
   Inventory MCP   Work Orders OpenAPI  FoundryIQ KB    Status Dashboard
   (Container App) (Container App)      (AI Search +    (browser automation)
                                         Knowledge Base)
```

## Why one endpoint for many tools?

- **Single auth boundary.** One bearer token (or API key) authenticates the
  agent to every backing tool — no per-tool credential plumbing.
- **Smaller agent context.** Tool schemas are aggregated and surfaced through
  one MCP descriptor, instead of registering N independent SDK clients.
- **Centralized governance.** Tool inventory, allow-lists, and rate limits
  live in the Toolbox configuration, not in agent code.
- **Mix tool types.** The Toolbox can expose MCP servers, OpenAPI services,
  and Azure AI Search knowledge bases under one interface.

## Local mode — `MCPStreamableHTTPTool` with custom auth

In local mode the agent runs in-process and connects directly to the Toolbox
MCP endpoint using `MCPStreamableHTTPTool` from the Agent Framework.

The key integration detail is a custom `httpx.Auth` that mints a fresh
Azure bearer token on every request, including the MCP initialize handshake.
The Toolbox also requires the `Foundry-Features: Toolboxes=V1Preview` header.

```python
# src/fibey/agent/agent.py
import httpx
from agent_framework import MCPStreamableHTTPTool

_TOKEN_SCOPE = "https://ai.azure.com/.default"


class _ToolboxAuth(httpx.Auth):
    """httpx Auth that injects a fresh bearer token for Toolbox MCP."""

    def __init__(self, credential):
        self._credential = credential

    def auth_flow(self, request):
        token = self._credential.get_token(_TOKEN_SCOPE).token
        request.headers["Authorization"] = f"Bearer {token}"
        yield request


def _create_toolbox_mcp(credential) -> MCPStreamableHTTPTool:
    toolbox_url = os.getenv("TOOLBOX_MCP_URL", "")
    if "api-version" not in toolbox_url:
        sep = "&" if "?" in toolbox_url else "?"
        toolbox_url = f"{toolbox_url}{sep}api-version=v1"

    auth_http_client = httpx.AsyncClient(
        auth=_ToolboxAuth(credential),
        headers={"Foundry-Features": "Toolboxes=V1Preview"},
        timeout=120.0,
    )

    return MCPStreamableHTTPTool(
        name="toolbox",
        url=toolbox_url,
        http_client=auth_http_client,
        load_prompts=False,
    )
```

### Gotchas discovered the hard way

1. **`api-version` is required.** The Toolbox MCP endpoint requires
   `?api-version=v1` (not a date-based version). The code auto-appends it
   if missing.
2. **The header must be set on every request,** not just `initialize`.
   That's why we use `httpx.Auth.auth_flow()` rather than a one-shot
   `Authorization` header on the client.
3. **The `Foundry-Features: Toolboxes=V1Preview` header must be present**
   for the Toolbox to expose the V1 preview surface.

## Hosted mode — same MCP tool, platform-provided credential

When the agent is deployed to **Azure AI Foundry Agent Service** (hosted
mode), the same `MCPStreamableHTTPTool` is used. The credential comes from
the platform (chained managed identity + `AzureDeveloperCliCredential`),
and the auth header is injected the same way:

```python
# src/fibey/agent/hosted.py
from azure.identity import (
    AzureDeveloperCliCredential, ChainedTokenCredential,
    ManagedIdentityCredential, get_bearer_token_provider,
)

user_mi = ManagedIdentityCredential(client_id=os.getenv("AZURE_CLIENT_ID"))
azd_cli = AzureDeveloperCliCredential(
    tenant_id=os.getenv("AZURE_TENANT_ID"), process_timeout=60
)
credential = ChainedTokenCredential(user_mi, azd_cli)

token_provider = get_bearer_token_provider(
    credential, "https://ai.azure.com/.default"
)


class ToolboxAuth(httpx.Auth):
    def __init__(self, token_provider):
        self._token_provider = token_provider

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self._token_provider()}"
        yield request


toolbox_http_client = httpx.AsyncClient(
    auth=ToolboxAuth(token_provider),
    headers={"Foundry-Features": "Toolboxes=V1Preview"},
    timeout=120.0,
)

toolbox_mcp_tool = MCPStreamableHTTPTool(
    name="toolbox",
    url=os.environ["TOOLBOX_MCP_URL"],
    http_client=toolbox_http_client,
    load_prompts=False,
)
```

> **Note:** In hosted mode, do **not** use `FoundryChatClient.get_mcp_tool()`
> for the Toolbox — that path doesn't carry the bearer token through the
> MCP initialize handshake. Use `MCPStreamableHTTPTool` with the explicit
> `httpx` client shown above.

### MCP SDK URI workaround

The Foundry Toolbox's Azure AI Search knowledge base returns resource
content where `uri` may be `null` or `""`, which fails pydantic `AnyUrl`
validation in the MCP SDK. The hosted entrypoint patches the SDK models to
accept `str | None`:

```python
import mcp.types

for cls in [
    mcp.types.ResourceContents,
    mcp.types.TextResourceContents,
    mcp.types.BlobResourceContents,
]:
    cls.model_fields["uri"].annotation = str | None
    cls.model_fields["uri"].default = None
    cls.model_fields["uri"].metadata = []

for cls in [
    mcp.types.ResourceContents,
    mcp.types.TextResourceContents,
    mcp.types.BlobResourceContents,
    mcp.types.EmbeddedResource,
    mcp.types.CallToolResult,
]:
    cls.model_rebuild(force=True)
```

## Configuring the Toolbox itself

The Toolbox is created in the Foundry project and configured to dispatch to:

| Backing tool | Toolbox tool type | Backend |
|---|---|---|
| Work Orders | OpenAPI | Container App (`work-orders-api`) |
| Inventory | MCP (HTTP) | Container App (`inventory-mcp`) |
| Knowledge Base | `azure_ai_search` | `foundry-iq-docs-index` (semantic) |
| Status Dashboard | Browser automation | Container App (`status-dashboard`) |

For the AI Search knowledge base, the Toolbox uses a `CognitiveSearch`
connection (with `ApiKey` auth) and the `azure_ai_search` tool type — not
a `RemoteTool` MCP pointer to the KB's `/mcp` endpoint. The latter returns
HTTP 403 when accessed through `ProjectManagedIdentity` auth.

## Where to look in the code

| File | Purpose |
|---|---|
| `src/fibey/agent/agent.py` | Local-mode agent + `_ToolboxAuth` |
| `src/fibey/agent/hosted.py` | Foundry-hosted agent + `ToolboxAuth` + MCP SDK patch |
| `src/fibey/agent/service.py` | Containerapp-mode self-hosted agent service |
| `agent.yaml` | Hosted-agent definition (resources, env vars, protocol) |
| `infra-agent/README.md` | Hosted-agent infra notes |
