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
* **Content Understanding integrates with the Microsoft Agent Framework (preview).** Install `agent-framework-azure-contentunderstanding` from PyPI to add document extraction capabilities directly to your agents.
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

The station demo is centered in the **Microsoft Foundry Playground** at [ai.azure.com/nextgen](https://ai.azure.com/nextgen).

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

## Content Understanding

Demonstrate how **Azure Content Understanding (CU) in Foundry Tools** turns unstructured content — documents, audio, video, images — into structured, agent-ready fields. **CU brings together Azure Document Intelligence and advanced LLM-based multimodal capabilities for extracting information across structured and unstructured content** through a single API and schema-driven experience.

<!-- TODO: add overview screenshot/visual of CU in Foundry -->

**Elevator pitch (10 seconds):** One multimodal **API** that takes any file (PDF, audio, video, image) and returns structured JSON your agent can act on — confidence scores and source grounding included where the analyzer supports them. Layout (OCR → clean markdown) is the highest-volume use case today, especially for RAG.

**Where can I do what?**

| Capability | Foundry (New) | CU Studio | REST API |
|---|---|---|---|
| Layout and OCR/Read | ✅ | ✅ | ✅ |
| Document analyzers (Invoice, Contract, etc.) | ✅ | ✅ | ✅ |
| Audio analyzer (Call center) | ✅ | ✅ | ✅ |
| Video & Image analyzers | ❌ (coming) | ✅ | ✅ |
| Custom analyzers, classifiers & labeling | ❌ | ✅ | ✅ |
| Document-Search analyzer (LLM figure understanding for RAG) | ❌ | ✅ | ✅ |
| GPT-5.2 selection | ❌ (gpt-4.1 family only) | ✅ | ✅ |

### Pre-reqs (set these up ahead of time)

1. A Foundry project on `ai.azure.com` in a region where CU is available (East US, East US 2, West US, West US 3, Sweden Central, Australia East, etc. — see the [region list](https://learn.microsoft.com/azure/ai-services/content-understanding/service-limits#region-support)).
2. **Deploy `gpt-4.1` (or `gpt-4.1-mini`) into the same project.** The Foundry playground dropdown only lists `gpt-4.1` family today. Without a deployment, you can run Layout, but custom uploads for field-extraction analyzers (Invoice, Call center, etc.) will be blocked. Takes ~2 min from the Deployments tab — don't wait until a customer is standing in front of you.
3. Open the Foundry playground gear/settings panel once and confirm your `gpt-4.1` deployment shows up in the dropdown. If it doesn't, the upload step in Flow A will silently block.
4. Grab a couple of sample documents to upload — the [Azure Document Intelligence sample data folder](https://github.com/Azure-Samples/document-intelligence-code-samples/tree/main/Data) is a great source (invoices, receipts, contracts, IDs).

### Demo Flow A — Foundry Playground (prebuilts, ~2 min)

1. Go to <https://ai.azure.com> → click **Build** (top right) → **Models** *or* **Deployments** in the left nav (the tab name is under A/B test today, so you may see either) → **AI Services** tab → select **Content Understanding**. Alternate path: `/discover/models` → search "Content Understanding". All land in the same playground.
2. **Show #1 — Layout (Document modality).** The default sample document loads. On the right, flip between **Content** (markdown, paragraphs, tables) and **Result** (full JSON; markdown lives at `result -> contents -> markdown`). Talking point: *"This is the most-used analyzer in CU — it's what powers RAG pipelines because you get clean markdown plus structure with no LLM call required."* Layout runs on the Foundry resource alone; no GPT deployment needed.
3. **Show #2 — Invoice (Document → Procurements → Invoice).** Sample invoice loads with extracted **fields + confidence scores** on the right. Uploading a fresh invoice (sample or a customer-approved file) is where the GPT-4.1 deployment kicks in — open the gear icon in the right panel to confirm the deployment is selected; you can deploy one inline if you forgot the pre-req.
4. **Show #3 — Call center (Audio modality).** Sample MP3 loads with a transcript in the middle and structured fields (summary, topics, sentiment, etc.) on the right. Great for landing the multimodal point.

▶ **Walkthrough video:** [Foundry Playground — Content Understanding demo](https://microsoft-my.sharepoint.com/:v:/p/kmuthukrishn/cQqp592pKQcnRZUfXm6tMSPZEgUCkWXJ8RC7gXgjpnXTbR4lDg?nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0=) (Microsoft internal, SSO required)

### Customization (only if asked)

Customization, labeling, video & image analyzers, and the LLM-powered **Document-Search** analyzer aren't in Foundry (New) yet — point customers at **CU Studio** (<https://contentunderstanding.ai.azure.com/>). The fastest way to get there is the **Customize in CU Studio** link/button at the top right of any analyzer in the Foundry playground; it carries your project context across so the deployment, region, and resource you set up in Foundry are already wired up on the other side.

* Sign in, use your existing Foundry project, and create a new CU project.
* Build a custom analyzer with **Suggest schema** — upload a sample doc and CU proposes a schema you can edit and run.
* You can reuse the same `gpt-4.1` deployment you created in Foundry — no extra setup. CU Studio also lets you pick **GPT-5.2** for analyzers that benefit from it.
* For documents with figures/charts, mention the **Document-Search analyzer** — a Layout variant that uses an LLM to add figure understanding and image/chart descriptions inline in the markdown output. Best option when you want maximum RAG/agent context from a document with visuals (decks, reports, datasheets).

Recommended: set up a sample custom analyzer in CU Studio ahead of time so you can show it end-to-end in under a minute if it comes up.

### Hooking CU into an agent (bonus, only if asked)

* **Microsoft Agent Framework context provider:** `pip install agent-framework-azure-contentunderstanding` — any file the agent receives is automatically routed through CU before the model sees it. ~10 lines of glue. Point folks at the [PyPI package](https://pypi.org/project/agent-framework-azure-contentunderstanding/).
* **Foundry IQ uses CU under the hood (going GA at Build).** When you create a Foundry IQ knowledge source (e.g., from Azure Blob) and set `contentExtractionMode` to **`standard`**, the ingestion pipeline calls the Content Understanding skill to extract text, chunk semantically across pages, and verbalize images/figures into markdown. Net: every Foundry IQ knowledge base going GA at Build is already a CU customer — great answer for "how does Foundry IQ ingest documents?". See [Foundry IQ overview](https://learn.microsoft.com/azure/ai-foundry/agents/concepts/what-is-foundry-iq) and [blob knowledge source how-to](https://learn.microsoft.com/azure/search/agentic-knowledge-source-how-to-blob).
* **Logic Apps connector for CU as an MCP tool (new).** The new Logic Apps connector for Content Understanding can be surfaced as an **MCP tool**, so any MCP-aware agent (including via a Foundry Toolbox) can invoke CU analyzers as part of a workflow — no custom code required.
* **MarkItDown integration:** newly merged — lets MarkItDown call CU under the hood for richer Markdown conversion than the default extractors. Good "what should I use for RAG ingestion?" answer.

### Known gaps & gotchas (read these so you don't get caught out)

| Gap | Reality today | What to say |
|---|---|---|
| Video & Image modalities in Foundry (New) | Not in the playground yet (Document + Audio only). Both are fully supported via the CU API and in CU Studio. | *"Foundry is catching up to the API — video and image are coming. Today, show video/image demos in CU Studio."* |
| Custom analyzers / labeling in Foundry (New) | Not yet — Foundry is prebuilts-only. | *"Customization lives in CU Studio today; that's why the **Customize in CU Studio** button is right there in the playground."* |
| GPT-5.2 in the Foundry playground dropdown | API and CU Studio support GPT-5.2 (across 12 regions); Foundry playground dropdown is gpt-4.1 / gpt-4.1-mini only for now. | *"4.1 in the playground is fine for demos; production workloads can pick 5.2 via CU Studio or the API."* |
| Deep links to the Foundry CU playground | None today — always start from `ai.azure.com`. | Just navigate live; don't try to paste a URL into the customer's tenant. |

### Rude FAQ

* **"How is this different from Document Intelligence (DI)?"** CU brings together Azure Document Intelligence and advanced LLM-based multimodal capabilities under one umbrella — you can think of DI's strengths as part of the CU experience now, extended to audio, video, and image with schema-driven extraction. Both are in Foundry, both are supported. For new content-to-JSON projects, start with CU.
* **"Why two surfaces (Foundry vs. CU Studio)?"** Foundry (New) = fastest path to "show me what it does" for prebuilts. CU Studio = build, label, and ship your own analyzers, plus video/image/Document-Search and GPT-5.2 selection. They share the same backend and the same API — you're never locked into one UI.
* **"Can I use CU as a tool in my agent?"** Yes — easiest path is the Agent Framework context provider (above). You can also wire CU into an MCP-aware agent via the new Logic Apps connector, or call the REST analyzer endpoint directly from any tool surface (OpenAPI spec → Toolbox → done). And if you're using Foundry IQ, you're already calling CU under the hood when `contentExtractionMode = standard`.
* **"Do I need a GPT deployment to use CU?"** Only for analyzers that do field extraction with custom inputs. Layout (OCR/markdown) runs without one.

**Key talking points (if you only remember three things):**
* One multimodal API across docs, audio, video, image — structured JSON out, confidence scores included.
* Foundry (New) for prebuilts, CU Studio for customization / video / image / Document-Search / GPT-5.2 — same backend, same API.
* Drops into an agent as a tool via the Agent Framework context provider, the new Logic Apps MCP connector, or a direct REST call — and quietly powers Foundry IQ ingestion when `contentExtractionMode = standard`.

**Sample files:** [Azure Document Intelligence sample data folder](https://github.com/Azure-Samples/document-intelligence-code-samples/tree/main/Data) — invoices, receipts, contracts, IDs, and more.

---

### Documentation Links

More will be announced on the day of Build 2026.

* <https://devblogs.microsoft.com/foundry/introducing-toolboxes-in-foundry/>
* <https://aka.ms/foundry-toolboxes>
* Content Understanding Build 2026 blog: <https://aka.ms/content-understanding-build2026>
* Content Understanding overview: <https://learn.microsoft.com/azure/ai-services/content-understanding/overview>
* Content Understanding Studio: <https://contentunderstanding.ai.azure.com/>
* CU Agent Framework provider (PyPI): <https://pypi.org/project/agent-framework-azure-contentunderstanding/>

## Agent Tools and Integrations Sessions

* [From zero to teammate in 25 minutes: Build a Teams agent live](https://build.microsoft.com/en-US/sessions/DEM332?source=sessions)
* [Build agents where work happens: chats, channels, and meetings in Microsoft Teams](https://build.microsoft.com/en-US/sessions/DEM334?source=sessions)
