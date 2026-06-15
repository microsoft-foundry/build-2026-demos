# Foundry Control Plane

Welcome to the Microsoft Build 2026 Foundry Control Plane Expert Meet Up Station! We're thrilled to offer this incredible opportunity for you to connect with attendees through engaging one-on-one or small group conversations about the latest Foundry Control Plane innovations. At the Expert Meet Up, you'll have the chance to answer questions and share your expertise, showcase demos and product decks, and keep attendees informed on the newest event updates and product announcements. Each station will be powered by our outstanding MVPs, session speakers, and subject matter experts—ready to deliver insights and spark meaningful discussions.

## Build 2026 Foundry Control Plane Announcements

The agentic platform shift isn't just about building fast — it's about *building, operating, optimizing, observing, and securing* agents in one seamless flow, from laptop to production. These are the Build 2026 launches most relevant to operating and governing agents at scale:

- **Agent 365 for local agents** — Extends **Entra, Defender, and Purview** into a single control plane to observe, govern, and secure agents across your estate — *regardless of where they're hosted or what framework they're built on*. This is the enterprise control plane story for agent operations. ([Build blog](https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work/))
- **Microsoft IQ — Generally Available** — The context layer that grounds agents in both world knowledge and enterprise knowledge, now GA across GitHub Copilot, Microsoft Foundry, and Copilot Studio. Includes **Work IQ** (workplace intelligence; APIs GA June 16), **Fabric IQ** (semantic layer over structured data), **Foundry IQ** (retrieval planning), and the new **Web IQ** (model-agnostic, MCP-native real-world grounding at ~2.5x the speed of the next-best alternative). ([Build blog](https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work/))
- **Open, end-to-end trust stack for agents** — Two open-source projects anchor framework-agnostic agent governance:
  - **Agent Control Specification (ACS)** — an open spec + reference implementation for the *runtime governance layer*. A portable manifest defining **where, when, and how** policies are evaluated and enforced across the full agent lifecycle, independent of framework, runtime, or policy engine. A new module within the Agent Governance Toolkit. ([ACS announcement](https://commandline.microsoft.com/agent-control-specification-runtime-governance/))
  - **ASSERT** (Adaptive Spec-driven Scoring for Evaluation and Regression Testing) — turns natural-language behavior specs into executable eval pipelines: auto-generating test scenarios, datasets, metrics, and scorecards, then running them against your model, app, or agent. ([ASSERT announcement](https://commandline.microsoft.com/assert-written-intent-executable-evals/) · [repo](https://github.com/responsibleai/ASSERT))
- **Agent Governance Toolkit (AGT)** — Policy enforcement, identity, sandboxing, and SRE for autonomous agents. One `pip install`, any framework. Intercepts every tool call, message, and delegation in deterministic code *before* the model's intent reaches the wire — making denied actions structurally impossible, not just unlikely. ([AGT repo](https://github.com/microsoft/agent-governance-toolkit))
- **Codename MDASH** — A multi-model agentic security system that deploys 100+ agents to find exploitable bugs by reasoning about data flow, business logic, and exploit chains — with context-aware fixes delivered directly in the Defender Portal. ([Build blog](https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work/))
- **Frontier Tuning (private preview)** — Applies reinforcement learning *within your compliance boundary* so agents learn how the business actually works, sharpening as they operate. ([Build blog](https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work/))

## Why a Control Plane? The three operating questions

For attendees asking *"why do I need this?"* — the Agent Governance Toolkit frames it as three questions every operator must answer once agents act autonomously:

1. **Is this action allowed?** An agent with `send_email` and `query_database` access should not be able to `drop_table`. OAuth scopes and IAM roles control which services an agent can *reach* — not what it *does* once connected.
2. **Which agent did this?** When five agents share one API key, *"an agent did it"* is not an incident response.
3. **Can you prove what happened?** Auditors need tamper-evident records of every decision: what policy was active, what was requested, and why it was allowed or denied.

Reminder: Prompt-level safety ("please follow the rules") is *not* a control surface — it's a polite request to a stochastic system. OWASP LLM01:2025 confirms there are no fool-proof prompt-injection defenses, and adaptive attacks report up to **100% success rate** against frontier models. A real control plane enforces in deterministic code, not in the prompt. ([AGT repo](https://github.com/microsoft/agent-governance-toolkit))

## Related Build 2026 Sessions & Labs

| Code | Session | Repo |
|------|---------|------|
| BRK241 | From prototype to production: build and run agents at scale | [aka.ms/build26/BRK241](https://aka.ms/build26/BRK241) |
| BRK243 | Claw and Agent Harness in Microsoft Foundry | [aka.ms/build26/BRK243](https://aka.ms/build26/BRK243) |
| DEM361 | Understand and fix Agent Framework apps with observability and evals | [aka.ms/build26/DEM361](https://aka.ms/build26/DEM361) |
| DEM333 | How Foundry integrates with open-source frameworks and tools | [aka.ms/build26/DEM333](https://aka.ms/build26/DEM333) |

Full list: **[Build 2026 Next Steps — Agents & Apps](https://microsoft.github.io/build26-next-steps/agents-apps/)**

Other Recommended:

### Observe & Operate

| Code | Type | Title |
|------|------|-------|
| BRK252 | Breakout | From observability to ROI for AI agents |
| LAB540 | Lab | Observe, optimize & protect hosted agents |
| LTG429 | Lightning | Debug & operate agents with Azure Monitor |
| LTG451 | Lightning | Agentic FinOps: cost & quality in Foundry |

### Govern & Control Plane

| Code | Type | Title |
|------|------|-------|
| BRK251 | Breakout | Secure, enterprise-ready agents with Agent 365 |
| OD840 | Pre-recorded | Enable enterprise agents with Agent 365 SDK |
| OD831 | Pre-recorded | Govern models, tools & agents with API Management |
| LTG467 | Lightning | Secure AI agents: AI Gateway, tools & trust |

### Guardrails, Evals & Trust

| Code | Type | Title |
|------|------|-------|
| BRK250 | Breakout | Govern open-source AI agents, any framework |
| LTG430 | Lightning | Shield your agents: universal control layer |
| TT682 | Table Talk | Trusted AI built for production |
| DEM369 | Demo | Responsible AI: principles to engineering |


## Documentation & Resource Links

- **Foundry Control Plane:** https://aka.ms/FoundryControlPlane
- **Agent Governance Toolkit:** https://github.com/microsoft/agent-governance-toolkit · [Docs](https://microsoft.github.io/agent-governance-toolkit) · [PyPI](https://pypi.org/project/agent-governance-toolkit/)
- **Agent Control Specification (ACS):** https://commandline.microsoft.com/agent-control-specification-runtime-governance/
- **ASSERT:** https://github.com/responsibleai/ASSERT · [Announcement](https://commandline.microsoft.com/assert-written-intent-executable-evals/)
- **Agent 365 / Secure local agents:** https://aka.ms/Build2026/SecureLocalAgents
- **Build 2026 keynote recap:** https://blogs.microsoft.com/blog/2026/06/02/microsoft-build-2026-be-yourself-at-work/
- **Build 2026 Next Steps — Agents & Apps:** https://microsoft.github.io/build26-next-steps/agents-apps/
