"""
Scenario 02 — Streaming Responses

Same Hello agent, but tokens stream as they are produced.
"""

import os
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

load_dotenv()

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ["FOUNDRY_MODEL_NAME"]

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):
    agent = project_client.agents.create_version(
        agent_name="StreamingAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a vivid storyteller. Keep answers under 150 words.",
        ),
    )
    print(f"Agent created (version {agent.version})\n")

    conversation = openai_client.conversations.create(
        items=[{"type": "message", "role": "user",
                "content": "Tell me a short, dramatic story about an AI agent that learned to dream."}],
    )

    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}

    with openai_client.responses.create(
        conversation=conversation.id, extra_body=agent_ref, stream=True,
    ) as stream:
        for event in stream:
            if event.type == "response.created":
                print("[stream open]\n", flush=True)
            elif event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
            elif event.type == "response.completed":
                print("\n\n[stream complete]")

    openai_client.conversations.delete(conversation_id=conversation.id)
    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("Agent deleted")
