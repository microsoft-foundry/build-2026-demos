# 05 — File Search (RAG) 📚

Ground your agent in **your own documents**. The File Search tool indexes files into a managed vector store; the agent retrieves the right chunks at runtime.

**Scenario:** a customer-support agent for the fictional Contoso Outdoor brand. It answers warranty, product, and policy questions strictly from `assets/product_info.md`.

## Run it

```powershell
python file_search_agent.py
```

Sample output:

```
Vector store created (id: vs_...)
File uploaded
Agent created (version 1)
Q: How long is the warranty on the TrailMaster X4 Tent?
A: Lifetime against manufacturing defects.
Q: What is your return policy?
A: 90 days from purchase for a full refund...
```

## What's interesting

- **Citations.** Each response includes `file_citation` annotations pointing back to the source — print them to show provenance.
- **Multiple files.** Upload PDFs, .docx, .md, .txt — anything textual.
- **Hybrid search.** Foundry's vector store uses dense + lexical retrieval by default.

## 👀 In the portal

1. **Agents → ContosoSupportAgent → Setup → Knowledge**. The vector store the script created is attached here.
2. **Playground**: ask "Is the rain jacket warranty longer than the tent's?" — watch the citation chips appear.
3. **Knowledge** tab on the project lets you reuse the same vector store across multiple agents.

## Production tips

- Chunk large files yourself if you need control over boundaries.
- Keep vector stores small & focused; create one per domain instead of one giant catch-all.
- Re-upload + new agent version when source docs change so old conversations still resolve to the version they were trained on.

## Where to go next

➡️ [06-web-search](../06-web-search/) — for facts that change minute-by-minute.
