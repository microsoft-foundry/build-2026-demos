# Foundry Control Plane Booth — Talking Points & Demo Walkthrough

> **Station 4 — Agent Operations & Management**
> Foundry Control Plane (FCP) is the **builder-facing execution and evidence layer** for your
> agent fleet. It connects your agents and resources, observes and improves their behavior, and
> enforces the policies and controls your organization depends on — surfaced in the new
> **Operate** tab in Microsoft Foundry.
>
> Use this doc to run the booth: the one-liner, the four pillars, the demo flow, the screenshots
> to show, and the sessions to push attendees toward. The attendee-facing rolling deck is
> [`foundry-control-plane-booth-deck.pptx`](foundry-control-plane-booth-deck.pptx).

---

## The 15-second pitch

**"One pane of glass for your entire agent fleet."**

When a customer asks about **controls, observability, governance, security, or compliance** on
their agents — Foundry Control Plane is the answer. It works for **Foundry-native agents and
open-source / third-party agents alike**: drill down to a single agent, roll up to the whole org.

---

## The four pillars (what it covers)

| # | Pillar | What it means at the booth |
|---|--------|----------------------------|
| 01 | **Observability** | Traces, evals, and quality & safety signals for every agent. |
| 02 | **Control** | Author and enforce policies, guardrails, and alerts across the fleet. |
| 03 | **Security** | Runtime guardrails, jailbreak detection, and Defender insights. |
| 04 | **Compliance** | Roll up fleet-wide evidence for auditors and regulators. |

---

## Who it's for (lead with the buyer)

Built for **governance stakeholders**, not just builders:

- **CTO** — owns the agent platform and its operational posture.
- **Chief Compliance Officer** — needs auditable evidence across the fleet.
- **CEO / board** — accountable for AI risk at the org level.
- **Regulatory bodies** — the external audience the evidence is produced for.

**Why now:** Agent-specific regulation has arrived — from the **EU AI Act** onward. Companies
must produce compliance evidence across **every layer** of their agent fleet and roll it up for
compliance officers and regulators in a single view. FCP is how you produce that evidence.

---

## How it works — author → enforce → observe → govern

1. **Author** — Create guardrails, policies, and alerts for your fleet.
2. **Enforce** — Apply them at runtime with **Content Moderation** & **Agent Shield**.
3. **Observe** — Collect traces, run evals, monitor quality & safety.
4. **Govern** — Roll everything up into the **FCP dashboard** (the Operate tab).

> Works for Foundry-native agents **and** open-source / third-party agents alike.

---

## Where it fits — FCP × Agent 365

- **Agent 365** = the **enterprise system of record** — fleet-level visibility and governance
  roll-up across the whole organization.
- **Foundry Control Plane** = **agent-level execution & evidence** — traces, evals, runtime
  guardrails, mediation, and evidence at feature depth.
- **The message: integrate, don't replace** — drill down to the agent, roll up to the org.

---

## Demo walkthrough (the Operate tab)

The live surface to show is the **Operate** tab in Microsoft Foundry. Three screens, in order:

### 1. The Operate tab — your fleet at a glance
![Operate tab overview](images/operate-tab.png)

- **Top-line tiles:** agents running (e.g. *35 / 37*), **estimated cost · 7d** (e.g. *$355.05*),
  and **active alerts** (e.g. *14 · 3 high*).
- Policy and security alerts are **ranked by severity** — click any alert to **jump straight
  into the security portal**.
- **Talking point:** "This is the single screen an operations or compliance owner opens in the
  morning — fleet health, spend, and risk in one view."

### 2. Assets · agent view — drill down to any agent
![Per-agent Monitor view](images/agent-monitor.png)

- Per-agent **Monitor** view: **quality & safety evals**, **time-series monitoring**, and
  **red-teaming built in**.
- Every evaluation is **tracked over time** — so you can spot **the day a metric moved**.
- **Talking point:** "When something regresses, you don't guess — you see exactly when the
  metric changed and what shipped around it."

### 3. Coverage — your whole fleet, native and beyond
![Fleet coverage](images/fleet-coverage.png)

- **Native + 3P:** Foundry-native **and** open-source / third-party agents in **one fleet view**.
- **Defender for Cloud:** security recommendations and a **risk level for every agent**.
- **Talking point:** "It's not just the agents you built in Foundry — bring your LangGraph,
  CrewAI, or custom agents under the same governance umbrella."

---

## Booth conversation starters

- *"How do you know your agents are behaving in production today?"*
- *"When the EU AI Act auditor asks for evidence on your agent fleet, where does it come from?"*
- *"What's your spend across all your agents this week — and which one is the most expensive?"*
- *"Do you have open-source or third-party agents you can't currently see or govern?"*

If they nod at **controls, observability, governance, security, or compliance** → that's the FCP
conversation.

---

## Where to send attendees — sessions at Build 2026

Curated from the EMU Tracker (Session Map booth mapping + AI Schedule title/abstract relevance),
grouped by theme. This list is also slide 10 of the booth deck.

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

---

## Closing line

**"Govern your agent fleet with confidence."** Point attendees to the survey QR on the deck to
send direct feedback to the product team, and to <https://aka.ms/FoundryControlPlane> for docs.
