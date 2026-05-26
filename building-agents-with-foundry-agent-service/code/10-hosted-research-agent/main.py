"""
Scenario 10 — Hosted Deep Research Agent

A Microsoft Agent Framework hosted agent that:
  - Uses a custom `plan_subquestions` tool to break a topic into 3-5 angles
  - Uses Foundry's hosted Web Search tool to gather evidence
  - Synthesizes a final, cited briefing

Run locally:
    azd ai agent run
    azd ai agent invoke --local "How is generative AI changing supply-chain forecasting?"

Deploy:
    azd deploy
"""

import os
from agent_framework import Agent, tool
from agent_framework.foundry import FoundryChatClient, HostedWebSearchTool
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv
from pydantic import Field
from typing_extensions import Annotated

load_dotenv()


@tool(approval_mode="never_require")
def plan_subquestions(
    topic: Annotated[str, Field(description="The research topic to break down")],
) -> list[str]:
    """Return 3-5 sub-questions that decompose the research topic.

    The model itself will fill this in via tool-result handling — we just
    define the contract here so the agent treats planning as a discrete
    reasoning step that appears in traces.
    """
    return [
        f"What is the current state of {topic}?",
        f"Who are the leading players in {topic}?",
        f"What are the documented benefits of {topic}?",
        f"What are the risks, limitations, or open challenges in {topic}?",
        f"What is the 1-3 year outlook for {topic}?",
    ]


INSTRUCTIONS = """\
You are a senior research analyst.

Workflow for every new topic:
1. Call `plan_subquestions` to get an investigation outline.
2. For each sub-question, call `web_search` and gather 2-3 high-quality sources.
3. Synthesize a briefing with:
   - 5-bullet executive summary
   - One short section per sub-question
   - A 'Sources' list with URL citations
Always cite sources inline with [n] markers."""


def main():
    client = FoundryChatClient(
        project_endpoint=os.environ["FOUNDRY_PROJECT_ENDPOINT"],
        model=os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"],
        credential=DefaultAzureCredential(),
    )

    agent = Agent(
        client=client,
        instructions=INSTRUCTIONS,
        tools=[plan_subquestions, HostedWebSearchTool()],
        default_options={"store": False},
    )

    ResponsesHostServer(agent).run()


if __name__ == "__main__":
    main()
