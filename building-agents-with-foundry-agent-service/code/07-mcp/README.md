# 07 — MCP Tools 🔌

**Model Context Protocol (MCP)** is an open standard for exposing tools to LLM agents. Foundry can connect to any remote MCP server — your own, a vendor's, or a community one — without you writing custom function-tool glue.

**Scenario:** wire the agent up to [gitmcp.io](https://gitmcp.io), which serves any GitHub repo as an MCP server, and ask it to explain the Azure REST API specs repo.

## Run it

```powershell
python mcp_agent.py
```

## What's interesting

- **`require_approval="always"`** — the agent pauses and emits an `mcp_approval_request` before invoking any tool. Your code (or a human) approves it. This is the safety primitive that makes MCP enterprise-friendly.
- **Zero tool definitions in your code.** The agent discovers what's available from the MCP server's manifest.
- **Server labels** let you wire up *multiple* MCP servers and the agent picks intelligently.

## The approval loop

```
user msg ──► agent
              │
              ├─ emits mcp_approval_request
              ▼
       your code (or human) approves
              │
              ├─ McpApprovalResponse fed back
              ▼
          agent calls MCP tools → final answer
```

## 👀 In the portal

1. **Agents → MCPAgent → Setup → Tools**. The MCP server URL + label are shown.
2. The portal's **Add Tools** catalog exposes built-in MCP servers (e.g. Azure DevOps MCP Server). Try adding one and running the same agent from the playground.

## Production tips

- Use **Microsoft Entra** or **OAuth On-Behalf-Of** authentication for production MCP servers (see [docs](https://learn.microsoft.com/azure/foundry/agents/overview)).
- Consider Foundry **Toolbox** (preview) to curate a stable set of MCP tools across many agents from a single endpoint.

## Where to go next

➡️ [08-multi-tool-concierge](../08-multi-tool-concierge/) — combine *everything* into one agent.
