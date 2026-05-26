"""
Scenario 05 — File Search (RAG)

Indexes a product catalog into a Foundry-managed vector store,
then asks the agent grounded questions. Citations are printed so
you can see exactly which file backed each answer.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition, FileSearchTool

load_dotenv()

endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
model = os.environ["FOUNDRY_MODEL_NAME"]

asset = Path(__file__).resolve().parent.parent / "assets" / "product_info.md"

QUESTIONS = [
    "How long is the warranty on the TrailMaster X4 Tent?",
    "What is your return policy?",
    "Which product is the lightest and how much does it cost?",
]

with (
    DefaultAzureCredential() as credential,
    AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
    project_client.get_openai_client() as openai_client,
):
    # 1) Build a vector store and upload the catalog
    vector_store = openai_client.vector_stores.create(name="ContosoCatalog")
    print(f"Vector store created (id: {vector_store.id})")

    with open(asset, "rb") as f:
        openai_client.vector_stores.files.upload_and_poll(
            vector_store_id=vector_store.id, file=f,
        )
    print("File uploaded")

    # 2) Create the agent
    agent = project_client.agents.create_version(
        agent_name="ContosoSupportAgent",
        definition=PromptAgentDefinition(
            model=model,
            instructions=(
                "You are a Contoso Outdoor support agent. Answer ONLY from the "
                "attached catalog. If something isn't covered, say so and offer "
                "to escalate to human support."
            ),
            tools=[FileSearchTool(vector_store_ids=[vector_store.id])],
        ),
    )
    print(f"Agent created (version {agent.version})\n")

    agent_ref = {"agent_reference": {"name": agent.name, "type": "agent_reference"}}
    conversation = openai_client.conversations.create()

    # 3) Ask a few grounded questions
    for q in QUESTIONS:
        openai_client.conversations.items.create(
            conversation_id=conversation.id,
            items=[{"type": "message", "role": "user", "content": q}],
        )
        response = openai_client.responses.create(
            conversation=conversation.id, extra_body=agent_ref,
        )
        print(f"Q: {q}")
        print(f"A: {response.output_text}")

        # Show citations
        for out in response.output:
            if getattr(out, "type", None) == "message":
                for part in getattr(out, "content", []):
                    for ann in getattr(part, "annotations", []) or []:
                        if getattr(ann, "type", "") == "file_citation":
                            print(f"   📎 cite: file_id={ann.file_id}")
        print()

    # 4) Cleanup
    openai_client.vector_stores.delete(vector_store_id=vector_store.id)
    openai_client.conversations.delete(conversation_id=conversation.id)
    project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
    print("Cleaned up")
