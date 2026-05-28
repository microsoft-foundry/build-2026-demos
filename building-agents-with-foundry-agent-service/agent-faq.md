# Foundry Agents: FAQ

---

## Platform & Positioning

### Microsoft Agent Framework vs Foundry SDK vs Copilot SDKs

| **Option** | **What it is** | **When to recommend** |
|------------|---------------|----------------------|
| **Microsoft Agent Framework** | A general-purpose framework for building agentic applications, especially multi-agent orchestration across local and cloud agents. | Recommend when visitors need multi-agent workflows, heterogenous agents, or want an orchestration layer they can run locally and evolve over time. |
| **Foundry SDK** | A thin client SDK generated from Foundry REST APIs for working with Foundry resources and Agent Service. | Recommend when they want to create/manage agents and do straightforward single-agent runs using Foundry-native capabilities. |
| **Copilot SDKs (M365 / GitHub Copilot)** | SDKs focused on specific surfaces (Microsoft 365 or developer/coding experiences). | Recommend when the target surface is Teams/M365 or coding-agent experiences; Foundry can complement by hosting/operating agents and enabling interop. |

---

### Copilot Studio vs Microsoft Foundry

| **Dimension** | **Copilot Studio** | **Microsoft Foundry** |
|---------------|-------------------|----------------------|
| **Primary experience** | Low-code, SaaS, graphical authoring and orchestration. | PaaS / pro-code platform for building, hosting, and operating agents. |
| **Control** | Faster start, fewer infrastructure decisions. | More control over models, tools, networking, identity, and observability. |
| **Interop** | Can call external agents (including Foundry agents). | Agents can be connected into Copilot Studio; publishing to Teams/M365 is supported (preview/early access depends on feature). |

---

### Copilot Studio vs Foundry?

Copilot Studio is the low-code, fully managed SaaS option—great when you want to build quickly in a visual experience and stay within the Copilot Studio orchestration model. Microsoft Foundry is the pro-code, Azure-native platform—best when you need deeper control over models, tools, networking, identity, and observability, or want to host and operate agents at enterprise scale. If you’re using both, a common pattern is: Copilot Studio as the orchestration and user-facing layer, with specialized Foundry agents connected as external agents for custom reasoning, retrieval, or tool execution.

---

### What is Foundry Agent Service and when should I use it?

Foundry Agent Service is a fully managed platform for building, deploying, and scaling AI agents—it hosts the agent runtime and manages conversations, tool calls, and lifecycle. Use it when you want agents that reliably call tools, maintain state through conversations, and are operated with enterprise security features like Microsoft Entra identity, RBAC, and virtual network isolation. It supports no-code prompt agents for fast starts and code-first hosted agents when you need custom code and frameworks.

---

### Why use Foundry instead of building my own agents?

Foundry reduces the “plumbing” you’d otherwise build yourself: an agent runtime, conversation/session management, tool orchestration, observability, and security integration. It also provides built-in enterprise trust features (identity via Microsoft Entra, RBAC, content filters, and network isolation) and gives you a governed surface to configure tools and monitor behavior. For many teams, the biggest win is getting from prototype to production without building a bespoke platform for scaling, policy, and debugging.

---

## SDKs & APIs

| **Choice** | **Endpoint shape** | **Best for** |
|------------|-------------------|--------------|
| **Foundry SDK** | `{endpoint}/api/projects/<project>` | Foundry features (agents, evals, tools) with Foundry-native capabilities.|
| **OpenAI SDK** | `{endpoint}/openai/v1` | Maximum OpenAI compatibility / OpenAI API surface. |
| **Anthropic SDK** | `{endpoint}/anthropic` | Calling Claude models deployed through Foundry using the Anthropic Messages API. |

`{endpoint}` == `https://<resource>.services.ai.azure.com`

---

### Which SDK should I use (Foundry vs OpenAI vs others)?

Use the Microsoft Agent Framework to build agents especially when you want to coordinate multiple agents (including Foundry agents) or build a heterogenous agent system across local + cloud.  
If you’re primarily building agents and want Foundry-specific capabilities (agent creation, tools catalog integration, evaluations), use the Foundry SDK and the Foundry project endpoint. The Foundry SDK is a lower level library which provides every REST API feature exposed by Agent Service.  
If you already have OpenAI-compatible code or need the broadest OpenAI API surface, use the OpenAI SDK with the /openai/v1 endpoint. If you’re specifically using Claude models deployed through Foundry, use the Anthropic endpoint option described in the SDK overview guidance.

---

### Responses API vs Chat Completions?

Think of these as generations of APIs — Chat Completions is the older pattern, while Responses API is the modern foundation for agentic applications.
* Chat Completions API is the legacy interface focused on simple chat-based interactions. It works well for straightforward back-and-forth conversations, but it is limited in handling richer workflows like tool usage, multi-modal inputs, or structured outputs.
* Responses API is the newer, unified API designed for modern AI applications and agents. It supports richer inputs and outputs, integrates natively with tools and agents, and enables more complex workflows like multi-step reasoning and structured responses. 

In practice, Responses API is what Foundry and Agents v2 are built on, and it’s where ongoing investment is happening—the long-term direction for building intelligent, agentic applications.

**Rule of thumb:** Use Chat Completions for simple, legacy chat scenarios—but use Responses API for anything new, especially if you’re building agents, workflows, or production-grade applications.

---

### How do Agent Framework and Foundry SDK work together?

A simple way to explain it: Foundry SDK is how you talk to the Foundry service, and Microsoft Agent Framework is how you structure and orchestrate agentic applications. Many teams create and manage agents in Foundry using the Foundry SDK, then use Agent Framework to orchestrate multiple agents and workflows (including combining local and Foundry-hosted agents). This separation keeps the service integration clean while giving developers a flexible orchestration layer. The Agent Framework internally uses the FOundry SDK for agentic operations.

---

## Getting Started

### How do I build my first agent (portal vs code)?

If you want to get started quickly, use the Foundry portal path: create a prompt agent by writing instructions and adding tools, then test it in the playground. If you prefer code, you can create and run agents using the Foundry SDK or REST APIs with the Foundry project endpoint. When you need custom code execution or a custom framework, the next step is a hosted agent, where you package code as a container and deploy it into the managed runtime.

| **Type** | **What you define** | **Why you’d pick it** |
|----------|--------------------|----------------------|
| **Prompt agent (declarative)** | Instructions + tools (configuration) | Fastest path; service manages compute and scaling. |
| **Workflow agent** | Workflow definition to coordinate steps/agents | When you want explicit workflow logic managed as an agent (public preview). |
| **Hosted agent** | Your containerized code + framework | When you need custom code, custom protocols, or compute control (public preview). |

---

### Prompt agents vs hosted agents?

Prompt agents are the simplest: you define behavior through instructions and tool configuration, and the service handles the runtime.  
Hosted agents are code-first: you bring your own containerized agent code (Agent Framework, LangGraph, or custom), and Foundry handles deployment, identity, scaling, and observability so you can operate it like a managed service.

---

## Hosting & Deployment

### Hosted agents vs prompt agents?

Hosted agents are the right answer when you need to bring your own code or framework, accept custom protocols/webhooks, or control CPU and memory for the runtime. Prompt agents are ideal when your agent logic fits instructions plus tools and you want a fully managed experience without thinking about containers. Both run under the same Foundry control plane story for identity, tools, and observability; the choice is about how much code and runtime control you need.

---

### Hosted agents vs ACA Express?

Hosted Agents are fully managed, while ACA Express gives you more control.
* **Hosted Agents (Foundry)** are a **fully managed runtime for agents**. Foundry handles scaling, execution, identity, security, tool orchestration, and observability out of the box, so you can focus on building agent logic instead of infrastructure. 
* **ACA Express (Azure Container Apps)** is a **lightweight hosting option for your own code**. You bring your own agent implementation (e.g., Agent Framework, LangGraph, or custom logic) and deploy it as a container, with more flexibility but also more responsibility for operations and configuration.

In practice, Hosted Agents are ideal when you want enterprise-grade agents without managing infrastructure, while ACA Express is better when you need custom runtime control or non-Foundry execution patterns.

**Rule of thumb:** Use Hosted Agents for production-ready, managed agent hosting—use ACA Express when you want lower-level control over how your agent is built and runs.

---

### Where do agents run and how do they scale?

Foundry Agent Service includes an Agent Runtime that hosts and scales both prompt and hosted agents, and it manages conversations, tool calls, and lifecycle. For hosted agents, you package your agent as a container image; Foundry deploys it, assigns a Microsoft Entra-based agent identity, and scales execution as needed. For prompt agents, the platform-managed runtime handles scaling automatically as part of the service.

---

### How do I monitor/debug agents?

Foundry’s documentation highlights end-to-end tracing, metrics, and Application Insights integration so teams can see what an agent did and why. The Foundry FAQ also calls out OpenTelemetry-based tracing and monitoring via Azure Monitor/App Insights for Agent Service scenarios. For booth conversations, emphasize that observability is built-in so debugging tool calls and agent behavior doesn’t require custom instrumentation from scratch.

---

## Data & Tools

### How do I connect enterprise data (RAG)?

Foundry supports retrieval patterns through tools like File Search and the Azure AI Search tool, which can ground responses in your indexed content. Vector stores back File Search: the service can parse, chunk, embed, and index files so the agent can perform semantic and keyword retrieval. If you want a more managed knowledge base experience, Foundry documentation points to Foundry IQ as the managed enterprise knowledge layer.

---

### What tools are built-in vs custom?

Agent Service includes built-in tools (for example, web search, file search, memory, and code interpreter) and supports custom tools so agents can take real actions. Tools are configured through the Foundry tool catalog, and the platform supports managed authentication patterns, including service-managed credentials and on-behalf-of (OBO) auth for certain tool scenarios. A good booth soundbite is: “Tools are first-class in Foundry—you don’t have to build the tool gateway and auth plumbing yourself.”

---

### How do I integrate APIs and external systems?

Foundry supports API integration through OpenAPI 3.0-specified tools and custom functions, and the FAQ calls out Azure Functions integration as another path for action tools. For standardized integrations, Foundry supports remote MCP servers that can be added through the tool catalog, with configuration that scopes what actions are allowed. Emphasize that the tool configuration + authentication is governed in Foundry so teams can integrate external systems without writing a bespoke integration layer for every agent.

---

## Enterprise & Governance

### How does identity / RBAC work?

Foundry Agent Service integrates with Microsoft Entra identity and role-based access control (RBAC) to manage who can create, manage, and operate agents. The service also supports managed authentication for tools, including service-managed credentials and on-behalf-of (OBO) patterns where applicable. For booth discussions, position this as “enterprise-ready by default,” so customers can align agent operations with existing identity and access models.

---

### VNet / private networking support?

Foundry documentation and FAQ describe private networking capabilities, including bring-your-own virtual network (BYO VNet) and private endpoint support, to meet stricter enterprise network boundaries. The Learn FAQ also explains that subnet delegation is required because Agent Service networking uses Azure Container Apps, and it provides guidance on recommended subnet sizes. A good summary is: “If your enterprise needs network isolation, Foundry has a documented VNet path rather than forcing public endpoints.”

---

### How do I enforce governance across projects?

Governance in Foundry typically starts with project-level RBAC (who can manage agents and tools) and then tool configuration (what actions an agent is allowed to take). Foundry also supports versioning and stable endpoints, so teams can promote a tested version to be “active” without changing the consumer endpoint. For booth talk tracks, connect this to standard SDLC ideas: least-privilege access, controlled tool permissions, and version promotion.

---

## Models & Capabilities

### Which models are supported?

Foundry Agent Service works with many models from the Foundry model catalog, including Azure OpenAI models, Anthropic models, Grok, DeepSeek and additional model collections sold through Foundry. Model and tool availability can vary by region, so the best practice is to verify what’s deployable in the Foundry portal for the customer’s region. In booth terms: “Foundry is multi-model, but model availability follows region constraints.”

---

### Can I swap models without code changes?

The Foundry Agent Service overview explicitly calls out that you can swap models without changing your agent code. The practical caveat is that tool availability can depend on the model and region, so teams should verify compatibility when switching. This is a great “anti-lock-in” story: orchestration logic doesn’t have to be tied to a single model vendor.

---

### What features (tools, reasoning, memory) are supported?

Foundry documentation describes built-in tools (including web search, file search, memory, and code interpreter) plus custom tools and MCP support for extending capabilities. The limits/regions documentation highlights that not all tools are supported in every region, and some tools are in preview depending on the feature. The Foundry FAQ also calls out built-in memory as available in preview and positions it as part of the connected intelligence story.

---

## Lifecycle & DevOps

### How do I manage SDLC / IaC?

For hosted agents, the official samples describe a deployment experience that pairs with azd-based workflows, and they emphasize that tracing/observability is available out of the box in sample templates. For production teams, the key message is that Foundry supports a build-test-deploy-monitor lifecycle, and you can operationalize your agent as a managed deployment rather than an ad-hoc script. If you’re asked about IaC specifically, steer people to the Foundry templates and the guidance linked from the docs and samples.

---

### How do I version and promote agents?

Foundry supports versioned agents and stable endpoints, and the publishing guidance explains that end users interact with the stable endpoint while builders can roll out newer versions behind it. This lets teams promote versions in a controlled way and reduce deployment risk—similar to how you’d do releases for microservices. For booth messaging, it’s a clean SDLC soundbite: “test a new version, then switch the active version without changing the client endpoint.”

---

## Regions & Availability

### Which regions are agents available?

Microsoft Learn states that Foundry Agent Service is available in the same regions as the Azure OpenAI Responses API. It also warns that tool availability varies by region and gives examples such as file search not being available in Italy North and Brazil South. The right booth guidance is: confirm your target region, then validate that your required tools and models are supported there.

---

## Migration & Roadmap

### v1 vs v2 (Agents vs Assistants)?

The Foundry FAQ states that the classic experience is built on the Assistants API and is being deprecated, while the next-gen experience is built on the Responses API and is GA as of March 13, 2026. In migration language, older “threads/runs” concepts map to “conversations/responses,” and the newer experience aligns to the Responses API model for modern agent workflows. The recommended guidance is to build new workloads on the Responses-based experience and migrate older Assistants-based workloads to stay on the long-term foundation.

---

### Migration tools and timelines?

Microsoft Learn provides a migration guide and calls out that a migration tool exists to help automate migration from Assistants API to Agents. The public GitHub migration tooling describes a V1→V2 agent migration tool that can list what would be migrated and then migrate when you run it without the list flag. For booth experts, the practical advice is: point customers to the migration guide first, and use the tool when they have many assistants to migrate.

---

## Advanced Scenarios

### Multi-agent orchestration?

Foundry positions itself as open and modular, supporting Microsoft Agent Framework, LangGraph, and open protocols like MCP and A2A. Microsoft Agent Framework is the primary talk track for orchestration: it provides patterns for coordinating multiple agents and can include Foundry-hosted agents as participants. A good booth framing is: “Use Foundry to host and govern the agents; use Agent Framework (or LangGraph) to orchestrate how they collaborate.”

---

### External agents / hybrid architectures?

Foundry’s tool model supports OpenAPI tools, custom functions, and MCP servers so an agent can safely call external systems without hand-building a tool gateway. Copilot Studio also supports connecting to external agents (including Foundry agents) as part of multi-agent solution design. When you talk hybrid, anchor on “standard protocols + governed tool access,” so integrations stay manageable as the agent system grows.

---

### Integration with Copilot / M365?

Foundry provides publishing guidance for making agents available in Microsoft 365 Copilot and Microsoft Teams, using a stable endpoint so end users see a consistent agent while builders roll forward versions. Separately, Copilot Studio provides a “connect to a Microsoft Foundry agent” experience that lets a Copilot Studio agent delegate to a Foundry agent by configuring the Foundry project endpoint and agent identifier. A simple booth message is: “Copilot Studio orchestrates; Foundry provides specialized agents and enterprise runtime; and they can connect when you need both.”

---

## Key references

- Foundry Agent Service overview (Learn): https://learn.microsoft.com/en-us/azure/foundry/agents/overview  
- Foundry Agent Service FAQ (Learn): https://learn.microsoft.com/en-us/azure/foundry/agents/faq  
- SDK & endpoint chooser (Learn): https://learn.microsoft.com/en-us/azure/foundry/how-to/develop/sdk-overview  
- Migrate to the new agents experience (Learn): https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/migrate  
- Limits/quotas/regions (Learn): https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions  
- Hosted agents (Learn): https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents  
- Copilot Studio → connect to Foundry agent (Learn): https://learn.microsoft.com/en-us/microsoft-copilot-studio/add-agent-foundry-agent  
- Publish Foundry agents to M365/Teams (Learn): https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/publish-copilot  
- Migration tool (GitHub): https://github.com/microsoft-foundry/foundry-samples/blob/main/migration/README.md  