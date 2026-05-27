# [DRAFT] Agent Tools & Integrations

Check out the Microsoft Build 2026 Agent Tools & Integrations Expert content!

At the Expert Meet Up, you'll have the chance to answer questions and share your expertise, showcase demos and product decks, and keep attendees informed on the newest event updates and product announcements for Microsoft Foundry.

I'd like to keep track of feedback, all up questions in this doc too: [link]
thanks, Q

## Build 2026 Agent Tools & Integrations Announcements

* **Toolboxes in Foundry are now in public preview.** Toolboxes are reusable, centrally managed bundles of tools (APIs, MCP servers, custom connectors) that any AI agent can consume through a single MCP-compatible endpoint. Build once, consume everywhere — no more duplicating tool integrations across agents.
* **Unified MCP endpoint per Toolbox.** Each Toolbox exposes one endpoint that agents in any framework (Microsoft Agent Framework, GitHub Copilot SDK, LangGraph, and more) can call. Wiring up individual tools for every agent is no longer necessary.
* **Centralized authentication and governance.** Toolboxes support OAuth and Microsoft Entra Identity out of the box. IT teams can enforce policies, govern tool usage, and gain observability from a single control plane — agents no longer store credentials individually.
* **Lifecycle management built in.** When you update a Toolbox, all consuming agents automatically benefit without refactoring their own connections.
* **Supported tool types at preview.** Web Search, Azure AI Search, File Search, Code Interpreter, custom MCP endpoints, OpenAPI services,agent-to-agent (A2A) flows, and skills.
* **Language, framework agnostic.** Any agent that can call an MCP endpoint — whether built in Python, .NET, Java, or C# — can use a Toolbox.
* **Govern capabilities on the roadmap.** centralized analytics and controls (Govern) are coming. Build, discover and Consume are live now.
* **Content Understanding Studio now supports GPT-5.2 across 12 regions.** Expanded beyond East US 2 to include East US, Australia East, Japan East, North Europe, South Central US, Southeast Asia, Sweden Central, UK South, West Europe, West US, and West US 3.
* **Content Understanding integrates with the Azure AI Agent Framework (preview).** Install `agent-framework-azure-contentunderstanding` from PyPI to add document extraction capabilities directly to your agents.
* **Prebuilt analyzers playground in the Foundry portal.** Explore Content Understanding capabilities without writing any code, directly in the Foundry portal experience.

## What Are Foundry Toolboxes?

Think of Toolboxes as the package manager for agent tools. Instead of every team rebuilding the same integrations for every agent, a Toolbox packages tools together, configures authentication once, and makes the bundle available to any agent with a single endpoint.

**Real-world example:** Onboarding a new employee requires Entra ID provisioning, GitHub access, cloud resource setup, and Teams messaging. Without Toolboxes, every HR/IT agent wires these up individually. With a Toolbox, you package them all, authenticate once, and any agent can consume the bundle instantly.

**Core value pillars:**

| Pillar | What it means |
|--------|---------------|
| **Build** | Package tools (MCP servers, OpenAPI, connectors) into a reusable Toolbox |
| **Consume** | Agents call one MCP endpoint to access all tools in the bundle |
| **Discover** | Search and find approved tools across your organization (coming soon) |
| **Govern** | Centralized policies, analytics, and compliance controls (coming soon) |

## Demo Flow

The station demo is centered in the **Microsoft Foundry Playground** at [ai.azure.com/nextgen](https://ai.azure.com/nextgen). Two parallel flows showcase complementary capabilities:

---

### Toolbox & Tools

Demonstrate how Toolboxes are created, configured, and consumed directly in the Foundry portal.

**What to show:**

**Building a toolbox in Foundry Portal**

1. Navigate to the Tools page in your Foundry project: [ai.azure.com/nextgen/{project}/build/tools](https://ai.azure.com/nextgen/projectname/build/tools)
2. Create or open an existing Toolbox — show the bundled tools (MCP servers, OpenAPI endpoints, connectors).
3. Walk through authentication setup (Entra Identity, OAuth) and how it applies to all tools in the bundle at once.
4. Show an agent consuming the Toolbox via its single MCP endpoint — highlight that no per-tool wiring is needed.
5. Optionally show adding/removing a tool and how consuming agents pick up the change automatically.

**Building a toolbox in Foundry Toolkit in VS Code**

1. Open VS Code and sign in to your Foundry account using the Foundry Toolkit extension.
2. In the Foundry Toolkit panel, select your **Foundry Hub** and **Project**.
3. Expand **Toolboxes** and select **Create Toolbox**.
4. Name the toolbox (for example: `build-demo-toolbox`) and choose the region/project target.
5. Add tools to the toolbox:
	* Add one or more built-in tools (for example Web Search, Azure AI Search, File Search, Code Interpreter).
	* Add custom integrations as needed (OpenAPI, MCP endpoint, agent-to-agent flow, or skills).
6. Configure authentication for each tool (Entra ID/OAuth/connection settings) and validate that each connector shows a healthy status.
7. Save and publish the toolbox.
8. Open the toolbox details and copy the unified MCP endpoint.
9. In your sample agent project, configure that MCP endpoint as the tool source.
10. Run the agent and verify it can invoke multiple tools from the same toolbox endpoint.
11. Return to the toolbox, add or update a tool, and re-run the agent to show lifecycle updates without rewiring each tool.

**Key talking points:**
* One endpoint, many tools — simplifies agent development.
* Centralized auth and governance — IT stays in control.
* Framework-agnostic — works with any MCP-compatible agent.

---

### Content Understanding

Demonstrate how Content Understanding turns unstructured documents into structured, agent-ready data.

**What to show:**

1. Open Content Understanding in the Foundry portal: [Content Understanding Playground](https://ai.azure.com/nextgen/[project]/build/models/ai-services/Azure-AI-Content-Understanding/playground)
2. Upload example documents (invoices, contracts, reports) — [download sample documents here](<!-- TODO: insert link to sample documents -->).
3. Walk through how the service extracts structured fields, tables, and entities from the uploaded content.
4. Show how the extracted output can be consumed by agents as a tool — completing the loop back to Toolboxes.
5. Alternatively, use the standalone Content Understanding Studio: [contentunderstanding.ai.azure.com](https://contentunderstanding.ai.azure.com/home)

**Key talking points:**
* Turns messy documents into clean, structured data agents can act on.
* Works across document types out of the box — no custom training required for common formats.
* Integrates naturally as a tool within a Toolbox for end-to-end agent workflows.

**Sample documents:** [Download demo documents](<!-- TODO: insert link to sample documents -->)

---

### Documentation Links

More will be announced on the day of Build 2026.

* <https://devblogs.microsoft.com/foundry/introducing-toolboxes-in-foundry/>
* <https://aka.ms/foundry-toolboxes>

## Agent Tools and Integrations Sessions

* [From zero to teammate in 25 minutes: Build a Teams agent live](https://build.microsoft.com/en-US/sessions/DEM332?source=sessions)
* [Build agents where work happens: chats, channels, and meetings in Microsoft Teams](https://build.microsoft.com/en-US/sessions/DEM334?source=sessions)
