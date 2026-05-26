# 06 — Web Search 🌐

When the answer needs to be **fresh**, ground the agent in the live web. Foundry's Web Search tool uses Grounding with Bing under the hood and returns **URL citations** alongside the answer.

**Scenario:** a tech-news briefer that summarizes the latest from a topic of your choice.

## Run it

```powershell
python web_search_agent.py
```

Sample output (citations will vary):

```
[stream open]
Microsoft Build 2026 announced several major Foundry updates...
[stream complete]

🔗 Citations:
  - https://techcommunity.microsoft.com/...
  - https://learn.microsoft.com/azure/foundry/...
```

## ⚠️ Terms & data flow

Web Search uses Grounding with Bing, which has additional costs and terms.

- [Grounding terms of use](https://www.microsoft.com/bing/apis/grounding-legal-enterprise)
- [Privacy statement](https://go.microsoft.com/fwlink/?LinkId=521839&clcid=0x409)

Customer queries flow to Bing — review with your compliance team before enabling in regulated workloads.

## 👀 In the portal

1. **Agents → NewsBriefingAgent → Setup → Tools**. You'll see Web Search listed.
2. **Playground**: ask "What were the top announcements at Microsoft Build 2026?"
3. Citation chips show source URLs inline.

## Where to go next

➡️ [07-mcp](../07-mcp/) — plug in *any* MCP server as a tool.
