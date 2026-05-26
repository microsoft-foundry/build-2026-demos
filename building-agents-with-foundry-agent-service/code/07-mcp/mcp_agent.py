"""
Scenario 07 — MCP Tools

Connect a Foundry agent to a remote MCP server (gitmcp.io serving the
Azure REST API specs repo). Demonstrates the approval handshake that
Foundry enforces for MCP tools by default.
"""

import os
from dotenv import load_dotenv
from openai.types.responses.response_input_param import McpApprovalResponse, ResponseInputParam
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, MCPTool

load_dotenv()

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ["FOUNDRY_MODEL_NAME"]

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):
    mcp_tool = MCPTool(
        server_label="api-specs",
        server_url="https://gitmcp.io/Azure/azure-rest-api-specs",
        require_approval="always",
    )

    agent = project_client.agents.create_version(
        agent_name="MCPAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions=(
                "You can call MCP tools exposed by the 'api-specs' server to "
                "explore the Azure REST API specs repository."
            ),
            tools=[mcp_tool],
        ),
    )
    print(f"Agent created (version {agent.version})")

    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}
    conversation = openai_client.conversations.create()

    # Initial request — will likely produce mcp_approval_request items
    response = openai_client.responses.create(
        conversation=conversation.id,
        input="Summarize the README of the Azure REST API specs repository.",
        extra_body=agent_ref,
    )

    # Auto-approve every MCP call. In production, gate this on human review.
    approvals: ResponseInputParam = []
    for item in response.output:
        if item.type == "mcp_approval_request":
            print(f"🔐 Approval requested for MCP server '{item.server_label}' (id {item.id})")
            approvals.append(McpApprovalResponse(
                type="mcp_approval_response",
                approve=True,
                approval_request_id=item.id,
            ))

    if approvals:
        response = openai_client.responses.create(
            input=approvals,
            previous_response_id=response.id,
            extra_body=agent_ref,
        )

    print("\n🤖 Agent response:\n")
    print(response.output_text)

    openai_client.conversations.delete(conversation_id=conversation.id)
    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("\nAgent deleted")
