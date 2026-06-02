"""Retail-agent LangGraph + Hosted Agent entry point.

Two ways to use this module:

1. **As a Foundry hosted-agent entry point** (azd deploy / `python main.py`).
   Requires AZURE_OPENAI_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME env vars.
   The module-level `app` is the ResponsesAgentServerHost the runtime starts.

2. **As a local library for evaluation**. Import `run_agent(...)` and the
   `SYSTEM_PROMPT` from this module to drive the same LangGraph + tools in
   process. `run_agent` returns a dict shaped like
   ``{"response": str, "messages": list, "tool_calls": list[{name, arguments, result}]}``
   so it plugs straight into the shared eval harness (eval/evaluate.py).
"""
import asyncio
import json
import logging
import os
import uuid

from azure.ai.agentserver.responses import (
    CreateResponse,
    ResponseContext,
    ResponseEventStream,
    ResponsesAgentServerHost,
    ResponsesServerOptions,
)
from azure.ai.agentserver.responses.models import (
    MessageContentInputTextContent,
    MessageContentOutputTextContent,
)
from azure.ai.agentserver.responses.store._foundry_errors import FoundryResourceNotFoundError
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from langchain_azure_ai.callbacks.tracers import enable_auto_tracing
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode

from tools import AgentTools

logger = logging.getLogger(__name__)

_POLICY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agent_policy.md")
try:
    with open(_POLICY_PATH, encoding="utf-8") as _f:
        _AGENT_POLICY = _f.read()
except FileNotFoundError:
    _AGENT_POLICY = ""

SYSTEM_PROMPT = (
    "You are Zava's Post-Purchase Resolution Desk agent. "
    "Help customers with returns, exchanges, replacements, cancellations, and shipping disputes. "
    "Use the available tools to verify eligibility and compute resolutions.\n\n"
    + _AGENT_POLICY
)


# ---------------------------------------------------------------------------
# Auto-tracing — emits OTel spans for every AzureChatOpenAI call + every
# LangGraph node. The Foundry data-gen worker reads these from App Insights.
#
# Required RBAC: the Foundry project's system-assigned managed identity must
# have "Log Analytics Reader" on the App Insights resource so the data-gen
# worker can query the traces. Without it, the worker silently returns 0 rows
# and produces an empty traces.jsonl. Grant once via:
#   az role assignment create --assignee <foundry-mi-principal-id> \
#       --role "Log Analytics Reader" --scope <appinsights-resource-id>
# ---------------------------------------------------------------------------
enable_auto_tracing(
    enable_content_recording=True,
    trace_all_langgraph_nodes=True,
    provider_name="azure_openai",
    auto_configure_azure_monitor=False,
)


# ---------------------------------------------------------------------------
# LangGraph builder + per-(endpoint, deployment) cache so each run_agent call
# doesn't rebuild the graph.
#
# Auth precedence (matches the rest of this lab):
#   1. AZURE_OPENAI_API_KEY env var   -> key auth (works around tenant RBAC blocks)
#   2. token_provider                  -> managed identity / DefaultAzureCredential
# ---------------------------------------------------------------------------
def build_graph(azure_endpoint, azure_deployment, token_provider, tools):
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    llm_kwargs = dict(
        azure_endpoint=azure_endpoint,
        azure_deployment=azure_deployment,
        api_version="2025-03-01-preview",
    )
    if api_key:
        llm_kwargs["api_key"] = api_key
    else:
        llm_kwargs["azure_ad_token_provider"] = token_provider
    llm = AzureChatOpenAI(**llm_kwargs)
    llm_with_tools = llm.bind_tools(tools)

    def chatbot(state: MessagesState):
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
        return {"messages": [llm_with_tools.invoke(messages)]}

    def route_tools(state: MessagesState):
        last = state["messages"][-1]
        if hasattr(last, "tool_calls") and last.tool_calls:
            return "tools"
        return END

    graph_ = StateGraph(MessagesState)
    graph_.add_node("chatbot", chatbot)
    graph_.add_node("tools", ToolNode(tools=tools))
    graph_.add_edge(START, "chatbot")
    graph_.add_conditional_edges("chatbot", route_tools, {"tools": "tools", END: END})
    graph_.add_edge("tools", "chatbot")
    return graph_.compile()


def history_to_langchain_messages(history: list) -> list:
    """Convert responses-protocol history items to LangChain messages.

    Round-trips four item types so prior tool-call/result pairs are preserved:
      - ``message`` (role=user)        -> HumanMessage
      - ``message`` (role=assistant)   -> AIMessage(content=...)
      - ``function_call``              -> AIMessage(tool_calls=[...]) (one per call)
      - ``function_call_output``       -> ToolMessage(tool_call_id=..., content=...)

    Function-call items emitted by this agent on a prior turn must reappear as
    ``AIMessage(tool_calls=[...])`` + ``ToolMessage`` pairs so the LLM sees a
    consistent history and does not re-invoke tools it already called.
    """
    messages: list = []
    for item in history:
        item_type = getattr(item, "type", None)

        if item_type == "function_call":
            try:
                args = json.loads(getattr(item, "arguments", "") or "{}")
            except (TypeError, ValueError):
                args = {}
            tool_call = {
                "id": getattr(item, "call_id", None) or getattr(item, "id", None),
                "name": getattr(item, "name", None),
                "args": args,
                "type": "tool_call",
            }
            messages.append(AIMessage(content="", tool_calls=[tool_call]))
            continue

        if item_type == "function_call_output":
            content = getattr(item, "output", "")
            if not isinstance(content, str):
                try:
                    content = json.dumps(content)
                except (TypeError, ValueError):
                    content = str(content)
            messages.append(
                ToolMessage(
                    content=content,
                    tool_call_id=getattr(item, "call_id", None) or "",
                )
            )
            continue

        if hasattr(item, "content") and item.content:
            for content in item.content:
                if isinstance(content, MessageContentOutputTextContent) and content.text:
                    messages.append(AIMessage(content=content.text))
                elif isinstance(content, MessageContentInputTextContent) and content.text:
                    messages.append(HumanMessage(content=content.text))
    return messages


_credential = None
_token_provider = None
_graph_cache = {}


def _ensure_credential():
    global _credential, _token_provider
    if _credential is None:
        _credential = DefaultAzureCredential()
        _token_provider = get_bearer_token_provider(_credential, "https://ai.azure.com/.default")
    return _credential, _token_provider


def get_graph(azure_endpoint=None, azure_deployment=None):
    """Get or build the LangGraph for the given (endpoint, deployment) pair.

    Falls back to AZURE_OPENAI_ENDPOINT / AZURE_AI_MODEL_DEPLOYMENT_NAME env vars
    when arguments are omitted (hosted-agent runtime path)."""
    azure_endpoint = azure_endpoint or os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_deployment = azure_deployment or os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
    if not azure_endpoint or not azure_deployment:
        raise ValueError(
            "Set AZURE_OPENAI_ENDPOINT and AZURE_AI_MODEL_DEPLOYMENT_NAME (or pass them explicitly)."
        )

    key = (azure_endpoint, azure_deployment)
    if key not in _graph_cache:
        _, token_provider = _ensure_credential()
        _graph_cache[key] = build_graph(
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment,
            token_provider=token_provider,
            tools=AgentTools.all_tools(),
        )
    return _graph_cache[key]


# ---------------------------------------------------------------------------
# Local evaluation entry point — same return shape as Zava's run_agent so the
# shared eval harness scores both agents identically.
# ---------------------------------------------------------------------------
def run_agent(
    user_message: str,
    *,
    model=None,
    azure_endpoint=None,
    history=None,
    max_turns: int = 15,
    verbose: bool = False,
):
    """Drive the LangGraph in-process and return the harness-compatible dict.

    Returns
    -------
    dict
        ``{"response": str, "messages": list, "tool_calls": list[{name, arguments, result}]}``
    """
    g = get_graph(azure_endpoint=azure_endpoint, azure_deployment=model)

    lc_messages = []
    if history:
        for h in history:
            role = h.get("role")
            if role == "user":
                lc_messages.append(HumanMessage(content=h.get("content", "")))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=h.get("content", "") or ""))
    lc_messages.append(HumanMessage(content=user_message))

    result = g.invoke(
        {"messages": lc_messages},
        config={"recursion_limit": max(2 * max_turns + 4, 25)},
    )
    out_messages = result["messages"]

    # Collect tool_calls + their tool message results, indexed by tool_call_id.
    pending_calls = {}  # id -> {"name", "arguments"}
    tool_calls_log = []
    for m in out_messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                tc_id = tc.get("id")
                pending_calls[tc_id] = {
                    "name": tc.get("name"),
                    "arguments": tc.get("args", {}),
                }
        elif isinstance(m, ToolMessage):
            entry = pending_calls.pop(m.tool_call_id, {"name": m.name, "arguments": {}})
            entry["result"] = m.content if isinstance(m.content, str) else str(m.content)
            tool_calls_log.append(entry)

    # Any tool calls without a matching result (shouldn't happen, but be safe).
    for tc_id, entry in pending_calls.items():
        entry["result"] = ""
        tool_calls_log.append(entry)

    final_text = ""
    for m in reversed(out_messages):
        if isinstance(m, AIMessage) and m.content:
            final_text = m.content if isinstance(m.content, str) else str(m.content)
            break

    if verbose:
        logger.info("run_agent: %d tool calls, response len=%d", len(tool_calls_log), len(final_text))

    return {
        "response": final_text,
        "messages": out_messages,
        "tool_calls": tool_calls_log,
    }


# ---------------------------------------------------------------------------
# Hosted-agent runtime: only constructed when running as the entry point.
# (Importing main.py for local evaluation does NOT require AZURE_OPENAI_ENDPOINT.)
# ---------------------------------------------------------------------------
app = ResponsesAgentServerHost(options=ResponsesServerOptions(default_fetch_history_count=20))


async def handle_create(
    request: CreateResponse,
    context: ResponseContext,
    cancellation_signal: asyncio.Event,
):
    """Run the LangGraph and emit ResponseEventStream events.

    Each LangGraph step produces zero or more Responses-protocol output items:
      - ``AIMessage.tool_calls``  -> one ``function_call`` item per tool call
      - ``ToolMessage``           -> one ``function_call_output`` item
      - final ``AIMessage.content`` -> one ``message`` item

    Emitting these as ResponseEventStream items (instead of returning only a
    ``TextResponse(text=...)``) causes the AgentServer to persist them on the
    response object, so ``context.get_history()`` on the next turn returns the
    full prior tool-call / tool-result sequence. ``history_to_langchain_messages``
    round-trips them back into LangChain ``AIMessage(tool_calls=)`` /
    ``ToolMessage`` pairs, preventing the agent from re-investigating across
    turns.
    """
    current_input = await context.get_input_text()
    try:
        history = await context.get_history()
    except FoundryResourceNotFoundError:
        history = []

    lc_messages = history_to_langchain_messages(history)
    lc_messages.append(HumanMessage(content=current_input))

    g = get_graph()
    result = await g.ainvoke({"messages": lc_messages})
    out_messages = result["messages"]

    # Slice off any messages that already existed in history; emit only the
    # NEW messages produced by this invocation so we don't double-persist.
    new_messages = out_messages[len(lc_messages):]

    stream = ResponseEventStream(response_id=context.response_id, request=request)
    yield stream.emit_created()
    yield stream.emit_in_progress()

    emitted_tool_call_ids: set[str] = set()
    final_text = ""

    for msg in new_messages:
        if isinstance(msg, AIMessage):
            for tc in getattr(msg, "tool_calls", None) or []:
                call_id = tc.get("id") or f"call_{uuid.uuid4().hex[:24]}"
                emitted_tool_call_ids.add(call_id)
                try:
                    args_str = json.dumps(tc.get("args", {}) or {})
                except (TypeError, ValueError):
                    args_str = "{}"
                for ev in stream.output_item_function_call(
                    name=tc.get("name", ""),
                    call_id=call_id,
                    arguments=args_str,
                ):
                    yield ev
            content = msg.content
            if isinstance(content, str) and content:
                final_text = content
        elif isinstance(msg, ToolMessage):
            call_id = msg.tool_call_id or ""
            output_str = msg.content if isinstance(msg.content, str) else str(msg.content)
            for ev in stream.output_item_function_call_output(
                call_id=call_id,
                output=output_str,
            ):
                yield ev

    if final_text:
        for ev in stream.output_item_message(text=final_text):
            yield ev

    yield stream.emit_completed()


# Register the handler — different agentserver SDK versions expose this under
# different names. Best-effort registration so this module remains importable
# even when only the local-eval surface (run_agent) is needed.
for _attr in ("response_handler", "create_handler"):
    _decorator = getattr(app, _attr, None)
    if callable(_decorator):
        try:
            _decorator(handle_create)
            break
        except TypeError:
            continue


if __name__ == "__main__":
    app.run()
