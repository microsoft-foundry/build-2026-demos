"""
Scenario 06 — Web Search (Bing grounding)

A news-briefing agent that streams its answer and prints citations.

NOTE: Web Search uses Grounding with Bing. See README.md for terms.
"""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    PromptAgentDefinition,
    WebSearchTool,
    WebSearchApproximateLocation,
)

load_dotenv()

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ["FOUNDRY_MODEL_NAME"]

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):
    tool = WebSearchTool(
        user_location=WebSearchApproximateLocation(
            country="US", city="Seattle", region="WA",
        ),
    )

    agent = project_client.agents.create_version(
        agent_name="NewsBriefingAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions=(
                "You are a tech-news briefer. Summarize the most recent and "
                "credible information from the web. Always cite your sources."
            ),
            tools=[tool],
        ),
    )
    print(f"Agent created (version {agent.version})\n")

    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}
    citations: list[str] = []

    with openai_client.responses.create(
        input="Give me a 5-bullet briefing on the latest Microsoft Foundry agent announcements.",
        tool_choice="required",
        extra_body=agent_ref,
        stream=True,
    ) as stream:
        print("[stream open]\n")
        for event in stream:
            if event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
            elif event.type == "response.output_item.done":
                if getattr(event.item, "type", "") == "message":
                    for part in getattr(event.item, "content", []) or []:
                        for ann in getattr(part, "annotations", []) or []:
                            if getattr(ann, "type", "") == "url_citation":
                                citations.append(ann.url)
            elif event.type == "response.completed":
                print("\n\n[stream complete]")

    if citations:
        print("\n🔗 Citations:")
        for url in dict.fromkeys(citations):  # de-dup, preserve order
            print(f"  - {url}")

    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("\nAgent deleted")
