"""Smoke test: handle_create emits the correct event sequence for a multi-turn
LangGraph run, including function_call + function_call_output items.

This stubs the LangGraph invoke so we don't hit Azure OpenAI; it just verifies
the event-translation layer in main.handle_create is correct.

Run with: python _smoke_handler_events.py
"""
import asyncio
import json
import sys
import types

# Stub langchain_azure_ai (see test_history_roundtrip.py for context).
_stub_pkg = types.ModuleType("langchain_azure_ai")
_stub_cb = types.ModuleType("langchain_azure_ai.callbacks")
_stub_tr = types.ModuleType("langchain_azure_ai.callbacks.tracers")
_stub_tr.enable_auto_tracing = lambda *a, **kw: None
sys.modules["langchain_azure_ai"] = _stub_pkg
sys.modules["langchain_azure_ai.callbacks"] = _stub_cb
sys.modules["langchain_azure_ai.callbacks.tracers"] = _stub_tr

import os
os.environ.setdefault("AZURE_OPENAI_ENDPOINT", "dummy")
os.environ.setdefault("AZURE_AI_MODEL_DEPLOYMENT_NAME", "dummy")

sys.path.insert(0, os.path.dirname(__file__))

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import main


class FakeGraph:
    """Pretends to be a LangGraph: returns a fixed sequence of messages
    appended to the input.  The handler must emit exactly one function_call,
    one function_call_output, and one message event item."""
    def __init__(self, new_messages):
        self._new = new_messages

    async def ainvoke(self, state):
        return {"messages": state["messages"] + self._new}


class FakeContext:
    response_id = "resp_test_smoke"

    def __init__(self, input_text, history):
        self._input = input_text
        self._history = history

    async def get_input_text(self):
        return self._input

    async def get_history(self):
        return self._history


class FakeRequest:
    """Minimal CreateResponse stand-in - ResponseEventStream only reads .model
    and a few attrs.  We set the bare minimum."""
    model = "gpt-test"
    background = False
    stream = True
    store = True
    conversation = None
    metadata = None


async def _run(handler):
    events = []
    async for ev in handler:
        events.append(ev)
    return events


def _classify(ev):
    return getattr(ev, "type", type(ev).__name__)


def main_smoke():
    new_msgs = [
        AIMessage(
            content="",
            tool_calls=[{
                "id": "call_test_1",
                "name": "get_order_details",
                "args": {"order_id": "O123"},
                "type": "tool_call",
            }],
        ),
        ToolMessage(
            content='{"order_id":"O123","status":"shipped"}',
            tool_call_id="call_test_1",
            name="get_order_details",
        ),
        AIMessage(content="Your order O123 is shipped."),
    ]

    # Monkeypatch get_graph
    main.get_graph = lambda: FakeGraph(new_msgs)

    ctx = FakeContext("look up O123", history=[])
    req = FakeRequest()

    events = asyncio.run(_run(main.handle_create(req, ctx, asyncio.Event())))

    classes = [_classify(ev) for ev in events]
    print(f"Emitted {len(events)} events:")
    for c in classes:
        print(f"  - {c}")

    # Assertions: lifecycle events present
    assert any("created" in c for c in classes), f"missing response.created: {classes}"
    assert any("in_progress" in c for c in classes), f"missing in_progress: {classes}"
    assert any("completed" in c for c in classes), f"missing completed: {classes}"

    # Function call lifecycle: added + arguments + done
    item_added_count = sum(1 for c in classes if "output_item.added" in c)
    item_done_count = sum(1 for c in classes if "output_item.done" in c)
    assert item_added_count == 3, f"expected 3 output_item.added (1 func + 1 func_output + 1 msg), got {item_added_count}"
    assert item_done_count == 3, f"expected 3 output_item.done, got {item_done_count}"

    # Function call args event
    has_args_done = any("function_call_arguments.done" in c for c in classes)
    assert has_args_done, f"missing function_call_arguments.done: {classes}"

    # Verify the function_call item's arguments were correctly serialized
    for ev in events:
        if "function_call_arguments.done" in _classify(ev):
            args_str = getattr(ev, "arguments", "")
            parsed = json.loads(args_str)
            assert parsed == {"order_id": "O123"}, f"wrong args: {parsed}"
            print(f"OK function_call args round-trip: {parsed}")
            break

    # Verify message text
    for ev in events:
        if "output_text.done" in _classify(ev):
            text = getattr(ev, "text", "")
            assert "shipped" in text, f"wrong final text: {text}"
            print(f"OK final message text: {text!r}")
            break

    print("\nAll smoke assertions passed.")


if __name__ == "__main__":
    main_smoke()
