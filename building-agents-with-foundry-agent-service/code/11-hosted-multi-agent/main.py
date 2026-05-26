"""
Scenario 11 — Hosted Multi-Agent Triage

A single hosted container runs four agents:
  - triage   : router (decides which specialist to hand off to)
  - billing  : answers from a policy snippet
  - technical: runs a diagnostic function
  - sales    : uses hosted web search for current promotions

The triage agent decides; specialists execute. All four live in the same
Python process and share the FoundryChatClient.
"""

import os
import random
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient, HostedWebSearchTool
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field
from typing_extensions import Annotated

load_dotenv()


BILLING_POLICY = """\
Refund policy:
- Customers may request a full refund within 90 days of purchase.
- Double-billing issues are auto-resolved within 3-5 business days.
- For invoices over $500, a manager review is required (please escalate).
"""


@tool(approval_mode="never_require")
def lookup_policy(
    topic: Annotated[str, Field(description="Topic such as 'refund' or 'double-charge'")],
) -> str:
    """Return the relevant billing policy snippet."""
    return BILLING_POLICY


@tool(approval_mode="never_require")
def run_product_diagnostic(
    product: Annotated[str, Field(description="Product name e.g. 'TrailMaster X4 Tent'")],
    issue: Annotated[str, Field(description="Short issue description")],
) -> dict:
    """Pretend-call to a diagnostic service. Returns a triage code + steps."""
    random.seed(hash((product, issue)) & 0xFFFF)
    return {
        "case_id": f"CS{random.randint(100000, 999999)}",
        "severity": random.choice(["low", "medium", "high"]),
        "suggested_steps": [
            "Verify the issue can be reproduced.",
            "Inspect for visible defects against the warranty checklist.",
            "If under warranty, ship a replacement; otherwise offer 20% discount on repair.",
        ],
    }


def build_agents(client: FoundryChatClient) -> dict[str, Agent]:
    billing = Agent(
        client=client, name="billing",
        instructions=(
            "You handle billing questions. Always call lookup_policy first, "
            "then answer concisely and warmly. Escalate to a human if the "
            "policy says manager review is required."
        ),
        tools=[lookup_policy],
        default_options={"store": False},
    )
    technical = Agent(
        client=client, name="technical",
        instructions=(
            "You are a senior product-support engineer. Call "
            "run_product_diagnostic, then walk the customer through the steps."
        ),
        tools=[run_product_diagnostic],
        default_options={"store": False},
    )
    sales = Agent(
        client=client, name="sales",
        instructions=(
            "You are a sales rep. Use web search to find current Contoso "
            "Outdoor promotions and recommend a product."
        ),
        tools=[HostedWebSearchTool()],
        default_options={"store": False},
    )
    return {"billing": billing, "technical": technical, "sales": sales}


# ---- Triage tools that delegate to specialist agents ----------------------

SPECIALISTS: dict[str, Agent] = {}


@tool(approval_mode="never_require")
def handoff_to_billing(
    user_message: Annotated[str, Field(description="The user's full message")],
) -> str:
    """Send a billing-related question to the Billing specialist."""
    return SPECIALISTS["billing"].run(user_message).output_text  # type: ignore[attr-defined]


@tool(approval_mode="never_require")
def handoff_to_technical(
    user_message: Annotated[str, Field(description="The user's full message")],
) -> str:
    """Send a technical-support question to the Technical specialist."""
    return SPECIALISTS["technical"].run(user_message).output_text  # type: ignore[attr-defined]


@tool(approval_mode="never_require")
def handoff_to_sales(
    user_message: Annotated[str, Field(description="The user's full message")],
) -> str:
    """Send a sales/promotions question to the Sales specialist."""
    return SPECIALISTS["sales"].run(user_message).output_text  # type: ignore[attr-defined]


TRIAGE_INSTRUCTIONS = """\
You are the front-line triage assistant for Contoso Outdoor support.

For every customer message:
1. Decide whether it is a Billing, Technical, or Sales question.
2. Call EXACTLY ONE of: handoff_to_billing, handoff_to_technical, handoff_to_sales.
3. Return the specialist's answer to the customer verbatim, but prefix
   it with one short empathetic sentence appropriate to the category.

If the question is ambiguous, ask one clarifying question first."""


def main():
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    SPECIALISTS.update(build_agents(client))

    triage = Agent(
        client=client,
        instructions=TRIAGE_INSTRUCTIONS,
        tools=[handoff_to_billing, handoff_to_technical, handoff_to_sales],
        default_options={"store": False},
    )

    ResponsesHostServer(triage).run()


if __name__ == "__main__":
    main()
