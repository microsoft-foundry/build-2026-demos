"""
Scenario 12 — Hosted Agent + Foundry Toolbox

A Microsoft Agent Framework hosted agent that pulls its tools from a
Foundry **Toolbox** (a centrally-managed, MCP-compatible tool registry
in your Foundry project) instead of declaring them inline.

Run locally:
    azd ai agent run
    azd ai agent invoke --local "What tools do you have?"

Deploy:
    azd deploy
"""

import logging
import os

import httpx
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class _ResilientResponsesHostServer(ResponsesHostServer):
    """Workaround for an alpha bug in `agent_framework_foundry_hosting`.

    The built-in `_handle_inner_agent` calls `await context.get_history()`
    unconditionally on every request. When the platform issues the request
    with `store=true` + a real `conversation.id` (as the foundry-extension
    deploy path does), the history fetch can raise inside the SDK, which
    bubbles up as a platform-level `server_error`. Until that's fixed
    upstream, defensively wrap `get_history` so a transient failure
    degrades to "no prior turns" instead of failing the whole request.
    """

    async def _handle_inner_agent(self, request, context):  # type: ignore[override]
        original_get_history = context.get_history

        async def safe_get_history():
            try:
                return await original_get_history()
            except Exception as ex:  # noqa: BLE001
                logger.warning(
                    "context.get_history() failed (%s); proceeding with no history.",
                    ex,
                )
                return []

        context.get_history = safe_get_history  # type: ignore[method-assign]
        async for item in super()._handle_inner_agent(request, context):
            yield item


def resolve_toolbox_endpoint() -> str:
    """Build the MCP endpoint URL for the Toolbox configured in this project."""
    project_endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"].rstrip("/")
    toolbox_name = os.environ["TOOLBOX_NAME"]
    return f"{project_endpoint}/toolboxes/{toolbox_name}/mcp?api-version=v1"


class ToolboxAuth(httpx.Auth):
    """Injects a fresh bearer token on every request to the Toolbox."""

    def __init__(self, token_provider):
        self._get_token = token_provider

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self._get_token()}"
        yield request


def main():
    # Sync `main()` + `server.run()` (mirrors the 03-mcp pattern). Entering
    # the MCPStreamableHTTPTool context async at startup would do a network
    # `initialize` + `tools/list` against the Toolbox before the HTTP server
    # is bound; on the platform's deploy path, `/readiness` is probed within
    # ~90 s of container start. If the MCP handshake is still in flight,
    # readiness never returns 200 and the platform raises 424
    # session_not_ready. Letting the Agent enter the tool context lazily on
    # first request avoids the race.
    credential = DefaultAzureCredential()

    token_provider = get_bearer_token_provider(
        credential, "https://ai.azure.com/.default"
    )

    http_client = httpx.AsyncClient(
        auth=ToolboxAuth(token_provider),
        headers={"Foundry-Features": "Toolboxes=V1Preview"},
        timeout=120.0,
    )

    toolbox = MCPStreamableHTTPTool(
        name=os.environ["TOOLBOX_NAME"],
        url=resolve_toolbox_endpoint(),
        http_client=http_client,
        load_prompts=False,
    )

    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=credential,
    )

    agent = Agent(
        client=client,
        instructions=(
            "You are a friendly assistant. You have access to whatever tools "
            "are configured in the Foundry Toolbox. Pick the right tool for "
            "the job and keep answers brief."
        ),
        tools=toolbox,
        default_options={"store": False},
    )

    _ResilientResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
