"""Test that `history_to_langchain_messages` losslessly round-trips tool calls.

A previous bug discarded all `function_call` and `function_call_output` items
from Responses-API history, causing the agent to re-invoke tools across turns.
This test asserts that a synthetic multi-turn history with mixed text + tool
calls converts to the correct LangChain message list.

Run with: pytest test_history_roundtrip.py -v
"""
import json
import sys
import types

import pytest

# Stub out langchain_azure_ai (only used for hosted-runtime OTel tracing).
# We can't easily install the full hosted dep stack in this venv because of
# a pip resolver clash with an unrelated 'contentunderstanding' package.
_stub_pkg = types.ModuleType("langchain_azure_ai")
_stub_cb = types.ModuleType("langchain_azure_ai.callbacks")
_stub_tr = types.ModuleType("langchain_azure_ai.callbacks.tracers")
_stub_tr.enable_auto_tracing = lambda *a, **kw: None
sys.modules.setdefault("langchain_azure_ai", _stub_pkg)
sys.modules.setdefault("langchain_azure_ai.callbacks", _stub_cb)
sys.modules.setdefault("langchain_azure_ai.callbacks.tracers", _stub_tr)

from azure.ai.agentserver.responses.models import (
    FunctionToolCallOutput,
    MessageContentInputTextContent,
    MessageContentOutputTextContent,
    OutputItemFunctionToolCall,
    OutputItemMessage,
)
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

# Allow `python test_history_roundtrip.py` from any cwd.
sys.path.insert(0, __file__.rsplit("/", 1)[0])
sys.path.insert(0, __file__.rsplit("\\", 1)[0])

from main import history_to_langchain_messages


def _user_msg(text: str) -> OutputItemMessage:
    return OutputItemMessage(
        role="user",
        content=[MessageContentInputTextContent(text=text)],
    )


def _assistant_msg(text: str) -> OutputItemMessage:
    return OutputItemMessage(
        role="assistant",
        content=[MessageContentOutputTextContent(text=text)],
    )


def _function_call(name: str, call_id: str, args: dict) -> OutputItemFunctionToolCall:
    return OutputItemFunctionToolCall(
        name=name,
        call_id=call_id,
        arguments=json.dumps(args),
    )


def _function_call_output(call_id: str, output: str) -> FunctionToolCallOutput:
    return FunctionToolCallOutput(call_id=call_id, output=output)


def test_empty_history():
    assert history_to_langchain_messages([]) == []


def test_text_only_history():
    history = [
        _user_msg("hi"),
        _assistant_msg("hello, how can I help?"),
        _user_msg("what time is it?"),
    ]
    msgs = history_to_langchain_messages(history)
    assert len(msgs) == 3
    assert isinstance(msgs[0], HumanMessage) and msgs[0].content == "hi"
    assert isinstance(msgs[1], AIMessage) and msgs[1].content == "hello, how can I help?"
    assert isinstance(msgs[2], HumanMessage) and msgs[2].content == "what time is it?"


def test_function_call_round_trips():
    history = [
        _user_msg("Look up order O123"),
        _function_call("get_order_details", "call_abc", {"order_id": "O123"}),
        _function_call_output("call_abc", '{"order_id":"O123","status":"shipped"}'),
        _assistant_msg("Your order O123 is shipped."),
    ]
    msgs = history_to_langchain_messages(history)
    assert len(msgs) == 4

    assert isinstance(msgs[0], HumanMessage)
    assert msgs[0].content == "Look up order O123"

    assert isinstance(msgs[1], AIMessage)
    assert msgs[1].content == ""
    assert len(msgs[1].tool_calls) == 1
    tc = msgs[1].tool_calls[0]
    assert tc["name"] == "get_order_details"
    assert tc["id"] == "call_abc"
    assert tc["args"] == {"order_id": "O123"}

    assert isinstance(msgs[2], ToolMessage)
    assert msgs[2].tool_call_id == "call_abc"
    assert "shipped" in msgs[2].content

    assert isinstance(msgs[3], AIMessage)
    assert msgs[3].content == "Your order O123 is shipped."


def test_multi_turn_with_multiple_tool_calls():
    """The Sofia-Martinez scenario in miniature: turn 1 calls 2 tools, turn 2
    asks a follow-up.  The agent must see ALL prior tool calls + results."""
    history = [
        _user_msg("I want to return order O123"),
        _function_call("get_order_details", "call_1", {"order_id": "O123"}),
        _function_call_output("call_1", '{"status":"delivered","total":50}'),
        _function_call("check_resolution_policy", "call_2", {"reason": "wrong_item"}),
        _function_call_output("call_2", '{"eligible":true,"refund_pct":1.0}'),
        _assistant_msg("You're eligible for a full refund."),
        _user_msg("Great, please process it."),
    ]
    msgs = history_to_langchain_messages(history)
    assert len(msgs) == 7

    # Tool-call AIMessages with empty content
    assert isinstance(msgs[1], AIMessage) and msgs[1].tool_calls[0]["name"] == "get_order_details"
    assert isinstance(msgs[3], AIMessage) and msgs[3].tool_calls[0]["name"] == "check_resolution_policy"

    # ToolMessages match their call_ids
    assert isinstance(msgs[2], ToolMessage) and msgs[2].tool_call_id == "call_1"
    assert isinstance(msgs[4], ToolMessage) and msgs[4].tool_call_id == "call_2"

    # Final assistant text + new user message
    assert isinstance(msgs[5], AIMessage) and "refund" in msgs[5].content
    assert isinstance(msgs[6], HumanMessage) and msgs[6].content == "Great, please process it."


def test_malformed_arguments_falls_back_to_empty_dict():
    bad = OutputItemFunctionToolCall(
        name="tool", call_id="call_x", arguments="not valid json {"
    )
    msgs = history_to_langchain_messages([bad])
    assert len(msgs) == 1
    assert msgs[0].tool_calls[0]["args"] == {}


def test_function_call_without_id_uses_item_id():
    # call_id may be missing; tool_call_id round-trip must still produce a string
    fco = FunctionToolCallOutput(output="{}", call_id="")
    msgs = history_to_langchain_messages([fco])
    assert len(msgs) == 1
    assert isinstance(msgs[0], ToolMessage)
    assert isinstance(msgs[0].tool_call_id, str)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
