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

Demonstrate how **Azure AI Content Understanding (CU)** turns unstructured content — documents, audio, video, images — into structured, agent-ready fields. The story is **Foundry Playground first** (prebuilt analyzers, zero code) → **CU Studio** (customize when prebuilts aren't enough).

**Elevator pitch (10 seconds):** One multimodal **API** that takes any file (PDF, audio, video, image) and returns structured JSON your agent can act on — confidence scores and source grounding included where the analyzer supports them. The **Foundry playground** today covers Document + Audio (video/image are coming); for video, image, and customization, jump to **CU Studio**. Layout (OCR → clean markdown) is the highest-volume use case today, especially for RAG.

**Why a customer should care:** CU replaces the one-off OCR/parser/transcription/glue code teams write for every new content type. One API, one schema, JSON out — drops straight into an agent or workflow.

#### Pre-reqs (do this **before** your booth shift)

1. A Foundry project on `ai.azure.com` in a region where CU is available (East US, East US 2, West US, West US 3, Sweden Central, Australia East, etc. — see the [region list](https://learn.microsoft.com/azure/ai-services/content-understanding/service-limits#region-support)).
2. **Deploy `gpt-4.1` (or `gpt-4.1-mini`) into the same project.** The Foundry playground dropdown only lists `gpt-4.1` family today. Without a deployment, you can run Layout, but custom uploads for field-extraction analyzers (Invoice, Call center, etc.) will be blocked. Takes ~2 min from the Deployments tab — don't wait until a customer is standing in front of you.
3. Bookmark **CU Studio**: <https://contentunderstanding.ai.azure.com/> — you'll jump to it from the playground for the customization story. Sign in once before your shift so you don't burn time on auth in front of a customer.
4. **Pre-rehearse the custom analyzer flow in CU Studio** (Demo Flow B below) and leave a pre-built custom analyzer + classifier saved in your project. Creating one live in under a minute is tight; opening a pre-built one is bulletproof.
5. Open the Foundry playground gear/settings panel once and confirm your `gpt-4.1` deployment shows up in the dropdown. If it doesn't, the upload step in Flow A will silently block.
6. Optional: have 1–2 sanitized sample files (an invoice, a call recording, a contract) on your laptop. **Don't upload a customer's actual files unless they explicitly confirm the content is non-sensitive and OK to send to the demo tenant.** Default to our samples.

#### Demo Flow A — Foundry Playground (prebuilts, ~2 min)

> Foundry doesn't expose a deep link to a specific analyzer today, so navigate from the top of `ai.azure.com` every time.

1. Go to <https://ai.azure.com> → click **Build** (top right) → **Models** in the left nav → **AI Services** tab → select **Content Understanding**. (Alternate path: **Deployments** → **AI Services** → **Content Understanding**, or `/discover/models` → search "Content Understanding". All land in the same playground.)
2. **Show #1 — Layout (Document modality).** The default sample document loads. On the right, flip between **Content** (markdown, paragraphs, tables) and **Result** (full JSON; markdown lives at `result -> contents -> markdown`). Talking point: *"This is the most-used analyzer in CU — it's what powers RAG pipelines because you get clean markdown plus structure with no LLM call required."* Layout runs on the Foundry resource alone; no GPT deployment needed.
3. **Show #2 — Invoice (Document → Procurements → Invoice).** Sample invoice loads with extracted **fields + confidence scores** on the right. Uploading a fresh invoice (sample or a customer-approved file) is where the GPT-4.1 deployment kicks in — open the gear icon in the right panel to confirm the deployment is selected; you can deploy one inline if you forgot the pre-req.
4. **Show #3 — Call center (Audio modality).** Sample MP3 loads with a transcript in the middle and structured fields (summary, topics, sentiment, etc.) on the right. Great for landing the multimodal point.

#### Demo Flow B — Customize in CU Studio (~2 min)

When a customer asks *"can I extract my custom fields?"* or *"can I classify into my own categories?"*, pivot to CU Studio. **Default to opening your pre-built analyzer; only build live if you've rehearsed it.**

1. From the Foundry playground, click **Customize in CU Studio** (top right of the playground). This carries your project context over.
2. **Custom extract:** open your pre-built custom analyzer, show the schema, run it on a sample, point at the extracted fields + confidence. If time permits, demo the **Suggest** button: upload a sample doc → click **Suggest** → CU proposes a schema from the file content. Great "wow" moment.
3. **Custom classifier:** open your pre-built classifier (e.g., routes incoming docs into invoice vs. contract vs. receipt). Mention it can chain into an extract analyzer for end-to-end routing.
4. Land the point: once published, every custom analyzer is callable via the same CU REST API as the prebuilts — no migration when you graduate from prebuilt to custom.

**If something breaks live:** fall back to the Foundry playground's built-in Layout + Invoice samples and verbally describe the customization story using a CU Studio screenshot. The samples never fail.

#### Hooking CU into an agent (bonus, only if asked)

* **Microsoft Agent Framework context provider:** `pip install agent-framework-azure-contentunderstanding` — any file the agent receives is automatically routed through CU before the model sees it. ~10 lines of glue. Point folks at the [PyPI package](https://pypi.org/project/agent-framework-azure-contentunderstanding/).
* **MarkItDown integration:** newly merged — lets MarkItDown call CU under the hood for richer Markdown conversion than the default extractors. Good "what should I use for RAG ingestion?" answer.

#### Known gaps & gotchas (read these so you don't get caught out)

| Gap | Reality today | What to say |
|---|---|---|
| Video & Image modalities in Foundry playground | Not in the playground yet (Document + Audio only). Both are fully supported via the CU API and in CU Studio. | *"Foundry playground is catching up to the API — video and image are coming. Today, show video/image demos in CU Studio."* |
| Custom analyzers in Foundry playground | Not yet — Foundry is prebuilts-only. | *"Customization lives in CU Studio today; that's why the **Customize in CU Studio** button is right there in the playground."* |
| GPT-5.2 in the Foundry playground dropdown | API supports GPT-5.2 (across 12 regions), playground dropdown is GPT-4.1 / 4.1-mini only for now. | *"4.1 in the playground is fine for demos; production workloads can pick 5.2 via the API."* |
| Deep links to the playground | None today — always start from `ai.azure.com`. | Just navigate live; don't try to paste a URL into the customer's tenant. |

#### Rude FAQ

* **"How is this different from Document Intelligence (DI)?"** Both are part of Foundry. DI is GA and remains the right choice for existing document workloads — keep using it. CU is the newer, **multimodal**, schema-driven experience: docs **+ audio + video + image** through one API, with built-in customization. For greenfield content-to-JSON projects (especially anything beyond docs), start with CU; for established DI pipelines, no need to migrate.
* **"Why two surfaces (Foundry vs. CU Studio)?"** Foundry playground = fastest path to "show me what it does" for prebuilts. CU Studio = build, label, and ship your own analyzers. They share the same backend and the same API — you're never locked into one UI.
* **"Can I use CU as a tool in my agent?"** Yes — easiest path is the Agent Framework context provider (above). You can also call the REST analyzer endpoint directly from any tool surface (OpenAPI spec → Toolbox → done).
* **"Do I need a GPT deployment to use CU?"** Only for analyzers that do field extraction with custom inputs. Layout (OCR/markdown) runs without one.

**Key talking points (if you only remember three things):**
* One multimodal API across docs, audio, video, image — structured JSON out, confidence scores included.
* Foundry playground for prebuilts, CU Studio for customization — same backend, same API.
* Drops into an agent as a tool via the Agent Framework context provider in ~10 lines.

**Sample files:** <!-- TODO: insert link to sample documents (invoices, call-center mp3, contract) once hosted -->

---

### Documentation Links

More will be announced on the day of Build 2026.

* <https://devblogs.microsoft.com/foundry/introducing-toolboxes-in-foundry/>
* <https://aka.ms/foundry-toolboxes>
* Content Understanding overview: <https://learn.microsoft.com/azure/ai-services/content-understanding/overview>
* Content Understanding Studio: <https://contentunderstanding.ai.azure.com/>
* CU Agent Framework provider (PyPI): <https://pypi.org/project/agent-framework-azure-contentunderstanding/>

## Agent Tools and Integrations Sessions

* [From zero to teammate in 25 minutes: Build a Teams agent live](https://build.microsoft.com/en-US/sessions/DEM332?source=sessions)
* [Build agents where work happens: chats, channels, and meetings in Microsoft Teams](https://build.microsoft.com/en-US/sessions/DEM334?source=sessions)
