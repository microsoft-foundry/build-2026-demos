"""
The same portfolio agent — but written as a Microsoft Agent Framework
Hosted agent. The function-call dispatch loop you wrote in the prompt
version is now handled by the Agent Framework runtime *inside the
container*. Clients call the agent through the standard OpenAI Responses API.

Run locally:
    azd ai agent run
    azd ai agent invoke --local "What is MSFT trading at today?"

Deploy:
    azd deploy
"""

import os
import random
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field
from typing_extensions import Annotated

load_dotenv()


@tool(approval_mode="never_require")
def get_stock_quote(
    symbol: Annotated[str, Field(description="Ticker symbol like MSFT")],
) -> dict:
    """Get the current price and daily change for a stock ticker."""
    random.seed(hash(symbol) & 0xFFFF)
    return {
        "symbol": symbol,
        "price_usd": round(random.uniform(80, 950), 2),
        "change_pct": round(random.uniform(-3, 3), 2),
    }


def main():
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )
    agent = Agent(
        client=client,
        instructions="You are a personal finance assistant.",
        tools=[get_stock_quote],
        default_options={"store": False},
    )
    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
