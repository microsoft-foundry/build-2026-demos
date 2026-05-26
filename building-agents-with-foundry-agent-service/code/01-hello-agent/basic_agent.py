"""
Scenario 01 — Hello, Agent

The smallest possible Microsoft Foundry agent: a model + a prompt,
plus a two-turn conversation that proves it remembers context.
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
    # 1) Create (or new-version) a Prompt agent
    agent = project_client.agents.create_version(
        agent_name="HelloAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions="You are a friendly assistant that answers concisely.",
        ),
    )
    print(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})")

    # 2) Start a conversation
    conversation = openai_client.conversations.create(
        items=[{"type": "message", "role": "user",
                "content": "What is the size of France in square miles?"}],
    )
    print(f"Created conversation (id: {conversation.id})")

    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}

    response = openai_client.responses.create(conversation=conversation.id, extra_body=agent_ref)
    print(f"Response: {response.output_text}")

    # 3) Follow-up turn — agent remembers we were talking about France
    openai_client.conversations.items.create(
        conversation_id=conversation.id,
        items=[{"type": "message", "role": "user", "content": "And what is the capital city?"}],
    )
    response = openai_client.responses.create(conversation=conversation.id, extra_body=agent_ref)
    print(f"Response: {response.output_text}")

    # 4) Clean up so we don't accumulate test versions in the project
    openai_client.conversations.delete(conversation_id=conversation.id)
    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("Agent deleted")
