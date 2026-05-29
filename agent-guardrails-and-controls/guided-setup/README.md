# Guided Guardrails Setup (Foundry portal)

Three Foundry portal walkthroughs covering the **no-code guardrail setup** experience that ships at //Build 2026. Each video shows a complete authoring flow — from picking the guardrail type to attaching it to an agent — in the Microsoft Foundry portal.

## What's covered

| Capability | What it does | When to use |
|---|---|---|
| **Guided guardrail setup** | Walks a developer through creating a guardrail in the Foundry portal — pick the policy type, configure trigger conditions, attach to an agent — without writing YAML or code | Teams that want to ship a controlled agent without a runtime engineer in the loop |
| **Task adherence** | Detects when an agent drifts from the assigned task or workflow boundary — even when the user pressure-tests it across multiple turns | Long-running agents with crisp task scope (banking, support, document review) |
| **Tool moderation** | Inspects each tool invocation against a configured policy — blocks risky calls before they reach the backend | Agents wired to live tools that move money, send messages, or change state |

## Demo videos

### Guided guardrail setup (~X min, no sound)

<video src="./foundry-guided-guardrail-setup.mp4" controls width="100%"></video>

End-to-end walkthrough of creating a guardrail in the Foundry portal — pick the policy template, configure detection thresholds, attach to a target agent, and verify the policy is active.

### Task adherence (~X min, no sound)

<video src="./foundry-task-adherence.mp4" controls width="100%"></video>

Demonstrates how task-adherence detects when an agent strays from its assigned workflow. Includes a side-by-side of the agent's intended task vs. the actual tool calls being attempted, with the guardrail blocking off-task actions.

### Tool moderation (~X min, no sound)

<video src="./foundry-tool-moderation.mp4" controls width="100%"></video>

Shows tool-call moderation in action: an agent attempts a tool invocation that violates the configured policy, the guardrail intercepts the call before execution, and the developer sees the policy hit with a human-readable reason.

## Where this fits

The guided-setup experience pairs with two adjacent capabilities at this booth:

- **[Agent Shield](../agent-shield/)** — the runtime control plane that enforces these policies on every agent turn
- **[ASSERT](../assert/)** — the open-source eval framework that measures whether the guardrails actually changed the outcome on YOUR scenarios

## Documentation links

- *(TBD — Ying to add docs links after //Build)*

## Was this useful?

Visit the **Agent Guardrails and Controls** booth at //Build 2026, or file issues on the Microsoft Foundry feedback channel.
