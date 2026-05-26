"""
Scenario 03 — Function Calling

A portfolio agent with two custom tools:
  - get_stock_quote(symbol)
  - get_portfolio(user_id)

The model decides which to call and in what order. We execute the
functions locally and feed results back into the conversation.
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

# ---- Mock business logic --------------------------------------------------

_PORTFOLIO = {
    "demo-user": [
        {"symbol": "MSFT", "shares": 50},
        {"symbol": "NVDA", "shares": 20},
        {"symbol": "CRM",  "shares": 30},
    ]
}

def get_portfolio(user_id: str) -> dict:
    return {"user_id": user_id, "holdings": _PORTFOLIO.get(user_id, [])}

def get_stock_quote(symbol: str) -> dict:
    # Deterministic fake quote so the demo is reproducible
    random.seed(hash(symbol) & 0xFFFF)
    return {
        "symbol": symbol,
        "price_usd": round(random.uniform(80, 950), 2),
        "change_pct": round(random.uniform(-3, 3), 2),
    }

DISPATCH = {"get_portfolio": get_portfolio, "get_stock_quote": get_stock_quote}

# ---- Tool schemas (what the model sees) -----------------------------------

portfolio_tool = FunctionTool(
    name="get_portfolio",
    description="Get the list of stock holdings for a user.",
    parameters={
        "type": "object",
        "properties": {"user_id": {"type": "string", "description": "User identifier"}},
        "required": ["user_id"],
        "additionalProperties": False,
    },
    strict=True,
)

quote_tool = FunctionTool(
    name="get_stock_quote",
    description="Get the current price and daily change for a stock ticker.",
    parameters={
        "type": "object",
        "properties": {"symbol": {"type": "string", "description": "Ticker symbol like MSFT"}},
        "required": ["symbol"],
        "additionalProperties": False,
    },
    strict=True,
)

# ---- Run the agent --------------------------------------------------------

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ["FOUNDRY_MODEL_NAME"]

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):
    agent = project_client.agents.create_version(
        agent_name="PortfolioAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions=(
                "You are a personal finance assistant. When the user asks about their "
                "portfolio, first call get_portfolio, then call get_stock_quote for "
                "each holding, then summarize total value and top mover."
            ),
            tools=[portfolio_tool, quote_tool],
        ),
    )
    print(f"Agent created (version {agent.version})")

    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}

    response = openai_client.responses.create(
        input="How is my portfolio doing today? My user id is demo-user.",
        extra_body=agent_ref,
    )

    # The model may need several tool-call rounds (portfolio → quote per holding →
    # final summary). Loop until it stops asking for function calls.
    MAX_TURNS = 6
    turn = 1
    while turn <= MAX_TURNS:
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            break
        print(f"\n🤖 Turn {turn} — model decided to call:")
        outputs: ResponseInputParam = []
        for item in calls:
            args = json.loads(item.arguments)
            print(f"  → {item.name}({', '.join(f'{k}={v!r}' for k, v in args.items())})")
            result = DISPATCH[item.name](**args)
            outputs.append(FunctionCallOutput(
                type="function_call_output",
                call_id=item.call_id,
                output=json.dumps(result),
            ))
        response = openai_client.responses.create(
            input=outputs,
            previous_response_id=response.id,
            extra_body=agent_ref,
        )
        turn += 1

    print("\n🤖 Final answer:")
    print(response.output_text)

    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("\nAgent deleted")
