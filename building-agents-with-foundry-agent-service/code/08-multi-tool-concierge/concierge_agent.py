"""
Scenario 08 — Travel Concierge (Capstone)

A single Prompt agent equipped with FOUR tools:
  1) WebSearchTool      — live web data (weather, neighborhoods)
  2) FunctionTool ×2    — book_flight, get_exchange_rate (mocked)
  3) CodeInterpreterTool — produces a budget chart
  4) FileSearchTool     — loyalty profile / preferences

We execute the multi-turn tool-call loop until the agent stops asking
for tool calls and returns a natural-language itinerary.
"""

import os
import json
import random
from pathlib import Path
from dotenv import load_dotenv
from openai.types.responses.response_input_param import FunctionCallOutput, ResponseInputParam
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    WebSearchTool,
    WebSearchApproximateLocation,
    FunctionTool,
    CodeInterpreterTool,
    FileSearchTool,
)

load_dotenv()

# ---- Mock business APIs ---------------------------------------------------

def book_flight(origin: str, destination: str, depart_date: str, return_date: str) -> dict:
    random.seed(hash((origin, destination, depart_date)) & 0xFFFF)
    return {
        "confirmation": f"AB{random.randint(10000, 99999)}",
        "origin": origin,
        "destination": destination,
        "depart_date": depart_date,
        "return_date": return_date,
        "total_usd": round(random.uniform(800, 1400), 2),
        "carrier": "SkyAlliance",
    }

def get_exchange_rate(base: str, quote: str) -> dict:
    rates = {("USD", "JPY"): 156.2, ("USD", "EUR"): 0.92, ("USD", "GBP"): 0.78}
    rate = rates.get((base.upper(), quote.upper()), 1.0)
    return {"base": base, "quote": quote, "rate": rate}

DISPATCH = {"book_flight": book_flight, "get_exchange_rate": get_exchange_rate}

book_flight_tool = FunctionTool(
    name="book_flight",
    description="Book a round-trip flight. Returns a confirmation code and total price.",
    parameters={
        "type": "object",
        "properties": {
            "origin": {"type": "string", "description": "Origin airport IATA code, e.g. SEA"},
            "destination": {"type": "string", "description": "Destination IATA code, e.g. HND"},
            "depart_date": {"type": "string", "description": "YYYY-MM-DD"},
            "return_date": {"type": "string", "description": "YYYY-MM-DD"},
        },
        "required": ["origin", "destination", "depart_date", "return_date"],
        "additionalProperties": False,
    },
    strict=True,
)

fx_tool = FunctionTool(
    name="get_exchange_rate",
    description="Get the current FX rate from a base currency to a quote currency.",
    parameters={
        "type": "object",
        "properties": {
            "base":  {"type": "string", "description": "ISO 4217, e.g. USD"},
            "quote": {"type": "string", "description": "ISO 4217, e.g. JPY"},
        },
        "required": ["base", "quote"],
        "additionalProperties": False,
    },
    strict=True,
)

# ---- Run -------------------------------------------------------------------

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ["FOUNDRY_MODEL_NAME"]
profile_path = Path(__file__).resolve().parent / "traveler_profile.md"

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):
    # Index the traveler profile
    vector_store = openai_client.vector_stores.create(name="TravelerProfile")
    with open(profile_path, "rb") as f:
        openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id, file=f,
        )

    agent = project_client.agents.create_version(
        agent_name="ConciergeAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions=(
                "You are Alex's travel concierge. You have four toolkits:\n"
                "  - file_search: read the traveler's profile (loyalty, preferences, allergies).\n"
                "  - web_search: look up live destination info (weather, neighborhoods).\n"
                "  - book_flight: book the round trip.\n"
                "  - get_exchange_rate: convert the budget to local currency.\n"
                "  - code_interpreter: produce a daily-budget chart at the end.\n"
                "Always read the profile first. Respect preferences (no red-eyes, "
                "vegetarian, window seat). Conclude with a friendly day-by-day itinerary."
            ),
            tools=[
                FileSearchTool(vector_store_ids=[vector_store.id]),
                WebSearchTool(user_location=WebSearchApproximateLocation(
                    country="US", city="Seattle", region="WA")),
                book_flight_tool,
                fx_tool,
                CodeInterpreterTool(),
            ],
        ),
    )
    print(f"ConciergeAgent created (version {agent.version})\n")

    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}
    conversation = openai_client.conversations.create(
        items=[{"type": "message", "role": "user", "content": (
            "Plan me a 3-day Tokyo trip departing March 14, 2027 returning March 17, "
            "with a $2,500 budget. Then produce a pie chart breaking the budget into "
            "flight / hotel / food / activities."
        )}],
    )

    # Tool-call loop: keep round-tripping function results until the model is done
    response = openai_client.responses.create(
        conversation=conversation.id, extra_body=agent_ref,
    )

    MAX_TURNS = 6
    for turn in range(MAX_TURNS):
        outputs: ResponseInputParam = []
        for item in response.output:
            if item.type == "function_call" and item.name in DISPATCH:
                args = json.loads(item.arguments)
                print(f"🔧 turn {turn}: {item.name}({args})")
                result = DISPATCH[item.name](**args)
                outputs.append(FunctionCallOutput(
                    type="function_call_output",
                    call_id=item.call_id,
                    output=json.dumps(result),
                ))
        if not outputs:
            break  # no more function calls to satisfy
        response = openai_client.responses.create(
            input=outputs,
            previous_response_id=response.id,
            extra_body=agent_ref,
        )

    print("\n🧳 Final itinerary:\n")
    print(response.output_text)

    # Cleanup
    openai_client.vector_stores.delete(vector_store_id=vector_store.id)
    openai_client.conversations.delete(conversation_id=conversation.id)
    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("\nCleaned up")
