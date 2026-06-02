"""Fetch tool_calls from Application Insights for a hosted-agent response.id.

The Foundry hosted agent runtime emits one App Insights `request` per
``responses.create()`` whose ``customDimensions['gen_ai.response.id']`` is the
client-visible ``caresp_…`` id. Underneath that request, every container-side
tool invocation is a `dependency` span with operation_name == 'execute_tool'
and customDimensions for ``gen_ai.tool.name`` / ``gen_ai.tool.call.arguments``
/ ``gen_ai.tool.call.result``. They are all correlated by ``operation_Id``.

This module returns a list shaped like the local agents' ``tool_calls`` so that
``eval/evaluate.py:score_scenario`` works unchanged.
"""
from __future__ import annotations

import json
import os
import subprocess
import time
from typing import Optional

import requests


APP_INSIGHTS_APP_ID = os.environ.get(
    "APP_INSIGHTS_APP_ID", "28096dc1-3744-48ca-b49b-660e2fa76e2e",
)


def _bearer() -> str:
    # az on Windows is az.cmd; need shell=True to resolve
    out = subprocess.check_output(
        "az account get-access-token --resource https://api.applicationinsights.io --query accessToken -o tsv",
        shell=True, text=True,
    ).strip()
    return out


def _kql(query: str, token: Optional[str] = None) -> list[list]:
    tok = token or _bearer()
    r = requests.post(
        f"https://api.applicationinsights.io/v1/apps/{APP_INSIGHTS_APP_ID}/query",
        headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
        json={"query": query}, timeout=60,
    )
    r.raise_for_status()
    tables = r.json().get("tables", [])
    return tables[0]["rows"] if tables else []


def _operation_id_for_response(response_id: str, window_min: int = 60,
                                token: Optional[str] = None) -> Optional[str]:
    q = f"""
    requests
    | where timestamp > ago({window_min}m)
    | where tostring(customDimensions['gen_ai.response.id']) == '{response_id}'
    | project operation_Id
    | take 1
    """
    rows = _kql(q, token=token)
    return rows[0][0] if rows else None


def _tool_calls_for_operation(operation_id: str, window_min: int = 60,
                               token: Optional[str] = None) -> list[dict]:
    q = f"""
    dependencies
    | where timestamp > ago({window_min}m)
    | where operation_Id == '{operation_id}'
    | where tostring(customDimensions['gen_ai.operation.name']) == 'execute_tool'
    | project ts=timestamp,
              name=tostring(customDimensions['gen_ai.tool.name']),
              args=tostring(customDimensions['gen_ai.tool.call.arguments']),
              result=tostring(customDimensions['gen_ai.tool.call.result'])
    | order by ts asc
    """
    rows = _kql(q, token=token)
    out = []
    for _ts, name, args_str, result_str in rows:
        try:
            args = json.loads(args_str) if args_str else {}
        except json.JSONDecodeError:
            args = {"_raw": args_str}
        # Normalize hosted-agent ToolMessage envelope to match local raw-payload shape.
        # LangChain wraps tool results as {"name": ..., "tool_call_id": ..., "content": {...payload...}};
        # evaluate.py expects `result` to be a JSON string of the raw payload (no envelope).
        normalized = _unwrap_tool_result(result_str)
        out.append({"name": name, "arguments": args, "result": normalized})
    return out


def _unwrap_tool_result(result_str: str) -> str:
    """Hoist `content` to top level if the result is a LangChain ToolMessage envelope.

    Local-agent tool results are raw JSON payloads (e.g. {"order_id":..., "summary":{...}}).
    Hosted-agent tool results captured via OpenTelemetry come wrapped as
    {"name": "...", "tool_call_id": "...", "content": {...raw payload...}}.
    Normalize to the unwrapped form so eval/evaluate.py works identically on both.
    """
    if not result_str:
        return result_str
    try:
        parsed = json.loads(result_str)
    except (json.JSONDecodeError, TypeError):
        return result_str
    if (
        isinstance(parsed, dict)
        and set(parsed.keys()) >= {"name", "content"}
        and "tool_call_id" in parsed
    ):
        content = parsed["content"]
        # content may itself be a JSON string or already a dict
        if isinstance(content, str):
            return content
        return json.dumps(content)
    return result_str


def fetch_tool_calls(response_ids: list[str], *, wait_sec: int = 60,
                     window_min: int = 60) -> list[dict]:
    """Aggregate tool_calls across one or more response.id values (in order).

    ``wait_sec`` lets App Insights ingest spans (typically 30–60s). Call this
    after the conversation has finished.
    """
    if wait_sec > 0:
        time.sleep(wait_sec)
    token = _bearer()
    all_calls = []
    for rid in response_ids:
        op_id = _operation_id_for_response(rid, window_min=window_min, token=token)
        if not op_id:
            continue
        all_calls.extend(_tool_calls_for_operation(op_id, window_min=window_min, token=token))
    return all_calls


if __name__ == "__main__":
    import sys
    rids = sys.argv[1:]
    calls = fetch_tool_calls(rids, wait_sec=0)
    print(json.dumps(calls, indent=2)[:4000])
    print(f"\n{len(calls)} tool calls.")
