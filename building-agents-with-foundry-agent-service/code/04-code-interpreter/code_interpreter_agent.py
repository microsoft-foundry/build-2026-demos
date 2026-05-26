"""
Scenario 04 — Code Interpreter

The agent receives a sales CSV and writes Python to analyze it.
We print both the code it wrote and the final natural-language answer.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    CodeInterpreterTool,
    AutoCodeInterpreterToolParam,
)

load_dotenv()

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ["FOUNDRY_MODEL_NAME"]

csv_path = Path(__file__).resolve().parent.parent / "assets" / "sales_2026_q1.csv"

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):
    # Upload the CSV into the agent runtime
    with open(csv_path, "rb") as f:
        uploaded = openai_client.files.create(file=f, purpose="assistants")
    print(f"Uploaded {csv_path.name} (file id: {uploaded.id})")

    # Code Interpreter tool with the file attached as a container input
    code_tool = CodeInterpreterTool(
        container=AutoCodeInterpreterToolParam(file_ids=[uploaded.id]),
    )

    agent = project_client.agents.create_version(
        agent_name="SalesAnalystAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions=(
                "You are a data analyst. Use the Code Interpreter tool to answer "
                "questions about the attached CSV. Always show your reasoning and "
                "summarize findings in plain English."
            ),
            tools=[code_tool],
        ),
        description="Analyzes uploaded sales data and produces charts.",
    )
    print(f"Agent created (version {agent.version})")

    conversation = openai_client.conversations.create()
    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}

    response = openai_client.responses.create(
        conversation=conversation.id,
        input=(
            "Which product had the highest total revenue in Q1, and what was the "
            "month-over-month growth rate? Also produce a bar chart of revenue per product."
        ),
        extra_body=agent_ref,
        tool_choice="required",
    )

    # Extract the Python the agent wrote
    code = next(
        (out.code for out in response.output if out.type == "code_interpreter_call"),
        "<no code captured>",
    )
    print("\n🐍 Code the agent wrote:\n")
    print(code)

    print("\n📈 Agent answer:\n")
    print(response.output_text)

    # Cleanup
    openai_client.files.delete(uploaded.id)
    openai_client.conversations.delete(conversation_id=conversation.id)
    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("\nCleaned up")
