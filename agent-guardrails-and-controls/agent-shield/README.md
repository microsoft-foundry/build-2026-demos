# Agent Shield (ACS) — runtime guardrails

**Agent Shield** is the Microsoft Foundry runtime control plane for AI agents. It enforces deterministic, policy-driven guardrails on every agent turn: input filtering, state-machine gates on sensitive tools, multi-stage task-adherence checks, and output redaction. Same agent, same prompt, same model — wrap it in `Shield.from_yaml(...)` and the policy becomes a runtime contract the agent cannot bypass.

## What's in this booth section

This section covers **runtime enforcement**. For the no-code authoring flow (creating these policies in the Foundry portal), see [`../guided-setup/`](../guided-setup/). For measuring whether the guardrails actually changed the outcome on your scenarios, see [`../assert/`](../assert/).

## Demo video

### Agent Shield — bank-manager walkthrough (~X min, no sound)

<video src="./agent-shield-demo.mp4" controls width="100%"></video>

End-to-end demo of Agent Shield enforcing a banking-control policy on a live LangGraph bank-manager agent. The agent has real MCP tools (transfer money, freeze account, read PII), the user pressure-tests it across multiple turns, and the shield gates each sensitive tool call against a YAML policy stack.

What the video walks through:

- The agent's tool surface and the threat model
- The `guardrails.yaml` policy file structure (state machine gates, LLM-based detectors, PII redaction)
- A side-by-side of the unguarded baseline vs. the same agent wrapped in `Shield.from_yaml(...)`
- The audit trail every shield decision generates — every refusal traces back to a specific YAML expression

## Where this fits

| Stage | Capability | Booth folder |
|---|---|---|
| **Author** | No-code guardrail setup in the Foundry portal | [`../guided-setup/`](../guided-setup/) |
| **Enforce** | Runtime control plane (this folder) | `agent-shield/` |
| **Measure** | Scenario-specific eval to prove the trade-off | [`../assert/`](../assert/) |

## Documentation links

- *(TBD — Mike to add docs links after //Build)*

## Was this useful?

Visit the **Agent Guardrails and Controls** booth at //Build 2026, or file issues on the Microsoft Foundry feedback channel.