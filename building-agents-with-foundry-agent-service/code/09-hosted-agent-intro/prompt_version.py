"""
The Scenario 03 portfolio agent, kept here unchanged for direct comparison
with hosted_version/main.py — the same business logic, deployed as a Prompt agent.
"""

import os
import json
import random
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FunctionTool

load_dotenv()


def get_stock_quote(symbol: str) -> dict:
    random.seed(hash(symbol) & 0xFFFF)
    return {"symbol": symbol,
            "price_usd": round(random.uniform(80, 950), 2),
            "change_pct": round(random.uniform(-3, 3), 2)}


quote_tool = FunctionTool(
    name="get_stock_quote",
    description="Get the current price and daily change for a stock ticker.",
    parameters={
        "type": "object",
        "properties": {"symbol": {"type": "string"}},
        "required": ["symbol"],
        "additionalProperties": False,
    },
    strict=True,
)

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ["FOUNDRY_MODEL_NAME"]

with (
    DefaultAzureCredential() as cred,
    AIProjectClient(endpoint=endpoint, credential=cred) as project_client,
    project_client.get_openai_client() as openai_client,
):
    agent = project_client.agents.create_version(
        agent_name="PortfolioPromptAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a personal finance assistant.",
            tools=[quote_tool],
        ),
    )
    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}

    response = openai_client.responses.create(
        input="What is MSFT trading at today?", extra_body=agent_ref,
    )

    outputs: ResponseInputParam = []
    for item in response.output:
        if item.type == "function_call":
            args = json.loads(item.arguments)
            outputs.append(FunctionCallOutput(
                type="function_call_output",
                call_id=item.call_id,
                output=json.dumps(get_stock_quote(**args)),
            ))

    final = openai_client.responses.create(
        input=outputs, previous_response_id=response.id, extra_body=agent_ref,
    )
    print(final.output_text)

    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
