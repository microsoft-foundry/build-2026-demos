"""Fibey Agent — Foundry hosted agent entrypoint (Responses protocol).

Follows the foundry-samples 04-foundry-toolbox pattern:
  https://github.com/microsoft-foundry/foundry-samples/tree/main/samples/python/hosted-agents/agent-framework/responses/04-foundry-toolbox

Environment variables:
    FOUNDRY_PROJECT_ENDPOINT          (auto-injected by Foundry hosting)
    AZURE_AI_MODEL_DEPLOYMENT_NAME    set in agent.yaml
    TOOLBOX_NAME                      set in agent.yaml (e.g. fibey-toolbox-linda)
    AZURE_CLIENT_ID / AZURE_TENANT_ID (auto-injected for managed identity)
"""

import asyncio
import logging
import os
from pathlib import Path

import httpx
import mcp.types
from agent_framework import (
    Agent,
    InMemorySkillsSource,
    MCPStreamableHTTPTool,
    SkillsProvider,
)
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import configure_otel_providers
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

from .mcp_skills_source import MCPSkillsSource

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "system_prompt.md"


# ---------------------------------------------------------------------------
# Workaround: Azure AI Search KB MCP can return resource content with
# uri: null/"", which fails pydantic AnyUrl validation in the MCP SDK.
# ---------------------------------------------------------------------------
for _cls in (
    mcp.types.ResourceContents,
    mcp.types.TextResourceContents,
    mcp.types.BlobResourceContents,
):
    _cls.model_fields["uri"].annotation = str | None
    _cls.model_fields["uri"].default = None
    _cls.model_fields["uri"].metadata = []
for _cls in (
    mcp.types.ResourceContents,
    mcp.types.TextResourceContents,
    mcp.types.BlobResourceContents,
    mcp.types.EmbeddedResource,
    mcp.types.CallToolResult,
):
    _cls.model_rebuild(force=True)


class _ResilientResponsesHostServer(ResponsesHostServer):
    """Defensively wrap ``context.get_history`` so a transient failure
    degrades to "no prior turns" instead of failing the whole request.

    Note: the parent method is ``_handle_inner`` (not ``_handle_inner_agent``
    as some older samples suggest); overriding the wrong name silently
    no-ops the workaround.
    """

    async def _handle_inner(self, request, context, cancellation_signal):  # type: ignore[override]
        original_get_history = context.get_history

        async def safe_get_history():
            try:
                return await original_get_history()
            except Exception as ex:  # noqa: BLE001
                logger.warning(
                    "context.get_history() failed (%s); proceeding with no prior history.",
                    ex,
                )
                return []

        context.get_history = safe_get_history  # type: ignore[method-assign]
        async for item in super()._handle_inner(request, context, cancellation_signal):
            yield item


class ToolboxAuth(httpx.Auth):
    """Injects a fresh bearer token on every request."""

    def __init__(self, token_provider):
        self._get_token = token_provider

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        yield request


def resolve_toolbox_endpoint() -> str:
    """Resolve the toolbox MCP endpoint URL from project endpoint + name."""
    project_endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
    toolbox_name = os.environ["TOOLBOX_NAME"]
    return f"{project_endpoint}/toolboxes/{toolbox_name}/mcp?api-version=v1"


def _load_system_prompt() -> str:
    if SYSTEM_PROMPT_PATH.exists():
        return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    return "You are Fibey, a helpful AI assistant for fiber optics field operations."


async def _build_skills_provider(token_provider) -> SkillsProvider | None:
    """Load skills published by the Foundry Toolbox via MCP resources/list."""
    try:
        toolbox_url = resolve_toolbox_endpoint()
        source = MCPSkillsSource(
            url=toolbox_url,
            httpx_auth=ToolboxAuth(token_provider),
            extra_headers={"Foundry-Features": "Toolboxes=V1Preview"},
        )
        skills = await source.get_skills()
        if skills:
            logger.info("Loaded %d skill(s) from toolbox", len(skills))
            return SkillsProvider(InMemorySkillsSource(skills))
        logger.warning("Toolbox returned no skills; running without skills")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to load MCP skills (%s); running without skills", exc)
    return None


def main() -> None:
    """Start the hosted agent server."""
    # Enable OpenTelemetry instrumentation. Foundry hosting auto-injects the
    # OTLP exporter env vars so traces flow to the project's Application
    # Insights and show up in the portal's Tracing tab. Also enables MAF's
    # span emission around chat/tool/skill operations, which is essential for
    # diagnosing a "stream never completes" hang.
    try:
        configure_otel_providers(enable_sensitive_data=True)
        logger.info("OpenTelemetry instrumentation enabled")
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to configure OTEL providers: %s", exc)

    credential = DefaultAzureCredential()
    token_provider = get_bearer_token_provider(
        credential, "https://ai.azure.com/.default"
    )

    project_endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
    model = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
    toolbox_url = resolve_toolbox_endpoint()
    logger.info("Model: %s | Project: %s", model, project_endpoint[:60])
    logger.info("Toolbox MCP URL: %s", toolbox_url)

    http_client = httpx.AsyncClient(
        auth=ToolboxAuth(token_provider),
        headers={"Foundry-Features": "Toolboxes=V1Preview"},
        timeout=120.0,
    )

    toolbox = MCPStreamableHTTPTool(
        name=os.environ["TOOLBOX_NAME"],
        url=toolbox_url,
        http_client=http_client,
        load_prompts=False,
    )

    client = FoundryChatClient(
        project_endpoint=project_endpoint,
        model=model,
        credential=credential,
    )

    # Pre-load skills synchronously at startup so they are ready for the
    # first request (avoids cold-start latency on the readiness probe path).
    skills_provider = asyncio.run(_build_skills_provider(token_provider))

    agent = Agent(
        client=client,
        name="fibey",
        instructions=_load_system_prompt(),
        tools=toolbox,
        context_providers=[skills_provider] if skills_provider else None,
        default_options={"store": False},
    )

    server = _ResilientResponsesHostServer(agent)
    server.run()


if __name__ == "__main__":
    main()
