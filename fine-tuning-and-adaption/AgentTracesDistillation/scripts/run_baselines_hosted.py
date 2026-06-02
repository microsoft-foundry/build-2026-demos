#!/usr/bin/env python
"""Run the multi-turn teacher baseline against a HOSTED Foundry agent.

Mirrors `run_baselines.py` but talks to a hosted agent over the Responses API
instead of doing the chat-completions tool loop locally.

Two-phase to avoid 60s App-Insights ingestion wait per scenario:
  Phase A: drive customer<->hosted-agent conversations for all scenarios,
           collect response_ids per scenario.
  Phase B: ONE bulk App Insights KQL fetches tool_calls for ALL response_ids
           in the pass; client-side bucketing maps tool_calls -> scenario.
  Phase C: score each scenario with evaluate_v2.score_scenario.

Usage:
    python scripts/run_baselines_hosted.py --agent demo1-retail-agent-langraph-responses \
        --scenarios eval/training_tasks.json --results-dir v2_hard_demo1 \
        --suffix .pass1
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv

NB_DIR = Path(__file__).resolve().parents[1]
EVAL_DIR = NB_DIR / "eval"
RESULTS_DIR = NB_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# Make eval/ importable for evaluate_v2 + appinsights_tools
sys.path.insert(0, str(EVAL_DIR))
load_dotenv(NB_DIR / ".env")

import evaluate_v2 as eval_module_v2  # noqa: E402
import appinsights_tools as ai_tools  # noqa: E402

eval_module_v2 = importlib.reload(eval_module_v2)
ai_tools = importlib.reload(ai_tools)

from azure.identity import DefaultAzureCredential  # noqa: E402
from azure.ai.projects import AIProjectClient  # noqa: E402
from openai import OpenAI  # noqa: E402

PROJECT_ENDPOINT = (
    os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    or "https://smamgain-tip-aifoundry.services.ai.azure.com/api/projects/smamgain-tip-aiproject"
)
CUSTOMER_MODEL = os.environ.get("CUSTOMER_MODEL", "gpt-5.4-mini")
EVAL_MAX_ROUNDS = int(os.environ.get("EVAL_MAX_ROUNDS", "10"))

# Same prompt and customer client as run_baselines.py so customer behavior is
# byte-identical between AOAI-direct and hosted teacher runs.
EVAL_CUSTOMER_PROMPT = """You are simulating a real customer chatting with a retail support agent. \
Your full situation (the agent does NOT see this — you reveal details on demand):

{scenario}

Style rules:
- OPEN with a brief, vague request that mentions the ITEM but withholds the order ID and the specific reason. Example: "Hi, I need help with my [item]."
- When the agent asks clarifying questions (order ID, item id, reason, status), share the relevant info FROM your situation above.
- Do NOT volunteer policy interpretation, restocking math, or what you think you're entitled to. Let the agent figure it out.
- If the agent proposes a resolution and asks you to confirm, say YES.
- If the agent has DENIED with a clear policy reason, accept gracefully — don't argue indefinitely.
- ONLY output the literal token [END] on its own line AFTER the agent has FINALIZED — given a confirmation/reference number, said "submitted/processed", or explicitly DENIED with a final reason that they have repeated. A clarifying question, a quoted refund amount awaiting confirmation, or a "would you like me to proceed?" is NOT a finalization.
- Never call tools. Keep replies under ~3 short sentences."""

_customer_base_url = os.environ.get("OPENAI_BASE_URL")
_customer_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
_customer_timeout = float(os.environ.get("CUSTOMER_HTTP_TIMEOUT_SEC", "180"))
if not (_customer_base_url and _customer_api_key):
    raise RuntimeError("Set OPENAI_BASE_URL + AZURE_OPENAI_API_KEY in .env")

customer_client = OpenAI(
    base_url=_customer_base_url,
    api_key=_customer_api_key,
    timeout=_customer_timeout,
    max_retries=2,
)


def _is_reasoning_model(model: str) -> bool:
    m = (model or "").lower()
    return any(t in m for t in ("o4", "o5", "gpt-5", "rft"))


def _customer_reply(transcript, scenario_user_message):
    msgs = [{"role": "system", "content": EVAL_CUSTOMER_PROMPT.format(scenario=scenario_user_message)}]
    for entry in transcript:
        role = "user" if entry["role"] == "agent" else "assistant"
        msgs.append({"role": role, "content": entry["content"]})
    if not transcript:
        msgs.append({"role": "user", "content": "Open the conversation as the customer."})
    kwargs = dict(model=CUSTOMER_MODEL, messages=msgs)
    if _is_reasoning_model(CUSTOMER_MODEL):
        kwargs["max_completion_tokens"] = 400
    else:
        kwargs["max_tokens"] = 200
        kwargs["temperature"] = 0.0
    _seed_env = os.environ.get("CUSTOMER_SEED") or os.environ.get("AGENT_SEED")
    if _seed_env:
        kwargs["seed"] = int(_seed_env)
    return (customer_client.chat.completions.create(**kwargs).choices[0].message.content or "").strip()


def run_one_hosted_conversation(agent_client, scenario, verbose=False):
    """Drive a single multi-turn conversation against the hosted agent.

    Returns dict: {transcript, response_ids, final_text, stop_reason, rounds}.
    Tool calls are NOT fetched here — done in batch later.
    """
    sys_situation = scenario["user_message"]
    transcript = []
    response_ids: list[str] = []
    previous_response_id: Optional[str] = None
    final_text = ""
    stop_reason = "max_rounds"

    for round_ix in range(1, EVAL_MAX_ROUNDS + 1):
        try:
            cust_msg = _customer_reply(transcript, sys_situation)
        except Exception as ce:  # noqa: BLE001
            stop_reason = f"customer_error: {type(ce).__name__}"
            break
        ended = "[END]" in cust_msg
        cust_msg_clean = cust_msg.replace("[END]", "").strip()
        if not cust_msg_clean and ended:
            stop_reason = "end_token"
            break
        if not cust_msg_clean:
            stop_reason = "empty_customer_reply"
            break

        transcript.append({"role": "customer", "content": cust_msg_clean})
        if verbose:
            print(f"  cust [{round_ix}]: {cust_msg_clean[:140]}", flush=True)

        try:
            kw = dict(input=cust_msg_clean)
            if previous_response_id:
                kw["previous_response_id"] = previous_response_id
            resp = agent_client.responses.create(**kw)
        except Exception as ae:  # noqa: BLE001
            stop_reason = f"agent_error: {type(ae).__name__}: {str(ae)[:200]}"
            break
        previous_response_id = resp.id
        response_ids.append(resp.id)
        agent_text = (resp.output_text or "")
        final_text = agent_text
        transcript.append({"role": "agent", "content": agent_text})
        if verbose:
            print(f"  agent[{round_ix}]: {agent_text[:140]}", flush=True)

        if ended:
            stop_reason = "end_token"
            break

    return {
        "transcript": transcript,
        "response_ids": response_ids,
        "final_text": final_text,
        "stop_reason": stop_reason,
        "rounds": len(transcript) // 2,
    }


def batch_fetch_tool_calls(all_response_ids: list[str], *, wait_sec: int = 60,
                            window_min: int = 360) -> dict:
    """ONE KQL query returning every tool_call grouped by response_id.

    Returns {response_id: [{"name","arguments","result"}, ...]} preserving
    intra-conversation order.
    """
    if not all_response_ids:
        return {}
    if wait_sec > 0:
        print(f"Waiting {wait_sec}s for App Insights ingestion of {len(all_response_ids)} response(s)...", flush=True)
        time.sleep(wait_sec)
    token = ai_tools._bearer()

    # 1) response_id -> operation_Id mapping (one KQL).
    quoted_ids = ",".join(f"'{rid}'" for rid in all_response_ids)
    q_req = f"""
    requests
    | where timestamp > ago({window_min}m)
    | where tostring(customDimensions['gen_ai.response.id']) in ({quoted_ids})
    | project response_id=tostring(customDimensions['gen_ai.response.id']),
              operation_Id
    """
    rows = ai_tools._kql(q_req, token=token)
    rid_to_op: dict[str, str] = {}
    for response_id, op_id in rows:
        rid_to_op[response_id] = op_id

    op_ids = list(rid_to_op.values())
    if not op_ids:
        return {rid: [] for rid in all_response_ids}

    # 2) all execute_tool dependencies under those operation_Ids (one KQL).
    quoted_ops = ",".join(f"'{op}'" for op in op_ids)
    q_dep = f"""
    dependencies
    | where timestamp > ago({window_min}m)
    | where operation_Id in ({quoted_ops})
    | where tostring(customDimensions['gen_ai.operation.name']) == 'execute_tool'
    | project ts=timestamp,
              operation_Id,
              name=tostring(customDimensions['gen_ai.tool.name']),
              args=tostring(customDimensions['gen_ai.tool.call.arguments']),
              result=tostring(customDimensions['gen_ai.tool.call.result'])
    | order by ts asc
    """
    dep_rows = ai_tools._kql(q_dep, token=token)

    op_to_calls: dict[str, list] = {op: [] for op in op_ids}
    for _ts, op_id, name, args_str, result_str in dep_rows:
        try:
            args = json.loads(args_str) if args_str else {}
        except json.JSONDecodeError:
            args = {"_raw": args_str}
        normalized = ai_tools._unwrap_tool_result(result_str)
        op_to_calls.setdefault(op_id, []).append(
            {"name": name, "arguments": args, "result": normalized}
        )

    # Bucket back to response_id in submission order.
    out: dict[str, list] = {}
    for rid in all_response_ids:
        op_id = rid_to_op.get(rid)
        out[rid] = list(op_to_calls.get(op_id, [])) if op_id else []
    return out


def _safe_name(s):
    return "".join(c if c.isalnum() or c in ".-_" else "_" for c in s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="demo1-retail-agent-langraph-responses",
                    help="Hosted Foundry agent name")
    ap.add_argument("--scenarios", default=str(EVAL_DIR / "training_tasks.json"))
    ap.add_argument("--only", default="", help="Comma-separated scenario IDs")
    ap.add_argument("--results-dir", default="v2_hard_demo1",
                    help="Subdir under results/ to write into")
    ap.add_argument("--suffix", default="", help="Suffix appended to output filename (e.g. .pass1)")
    ap.add_argument("--ingest-wait", type=int, default=90,
                    help="Seconds to wait for App Insights ingestion before bulk fetch")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    scenarios = json.loads(Path(args.scenarios).read_text())
    if args.only:
        keep = {s.strip() for s in args.only.split(",") if s.strip()}
        scenarios = [s for s in scenarios if s["id"] in keep]
        print(f"--only filter -> running {len(scenarios)} scenarios: {sorted(keep)}", flush=True)
        if not scenarios:
            sys.exit("No scenarios matched --only filter.")

    target_dir = RESULTS_DIR / args.results_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    out_path = target_dir / f"baseline__mt__teacher__{_safe_name(args.agent)}.v2{args.suffix}.json"

    print(
        f"HOSTED teacher baseline | agent={args.agent} | customer={CUSTOMER_MODEL} | "
        f"n={len(scenarios)} | rounds<={EVAL_MAX_ROUNDS}\nOutput -> {out_path}",
        flush=True,
    )

    # ---- Phase A: run all conversations ------------------------------------
    cred = DefaultAzureCredential()
    pc = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=cred, allow_preview=True)
    agent_client = pc.get_openai_client(agent_name=args.agent)

    per_scenario_meta: dict = {}  # scenario_id -> dict
    all_response_ids: list[str] = []

    phase_a_start = time.time()
    for i, scenario in enumerate(scenarios, 1):
        t0 = time.time()
        try:
            conv = run_one_hosted_conversation(agent_client, scenario, verbose=args.verbose)
            err = None
        except Exception as e:  # noqa: BLE001
            conv = {"transcript": [], "response_ids": [], "final_text": "",
                    "stop_reason": f"exception: {type(e).__name__}", "rounds": 0}
            err = str(e)
        per_scenario_meta[scenario["id"]] = {
            "scenario": scenario,
            "conv": conv,
            "error": err,
        }
        all_response_ids.extend(conv["response_ids"])
        print(
            f"[{i}/{len(scenarios)}] {scenario['id']} {scenario['name'][:40]}: "
            f"{conv['rounds']} rounds ({conv['stop_reason']}) in {time.time()-t0:.1f}s "
            f"({len(conv['response_ids'])} resp_ids)",
            flush=True,
        )
    print(f"\nPhase A done in {(time.time()-phase_a_start)/60:.1f} min. "
          f"Total response_ids: {len(all_response_ids)}", flush=True)

    # ---- Phase B: ONE App Insights query for all tool_calls ----------------
    rid_to_calls = batch_fetch_tool_calls(all_response_ids, wait_sec=args.ingest_wait)
    n_with_calls = sum(1 for v in rid_to_calls.values() if v)
    print(f"Phase B: fetched tool_calls for {n_with_calls}/{len(all_response_ids)} response_ids", flush=True)

    # ---- Phase C: score every scenario -------------------------------------
    results: list[dict] = []
    for scenario_id, meta in per_scenario_meta.items():
        scenario = meta["scenario"]
        conv = meta["conv"]
        # Concatenate tool_calls across all turns of this scenario in order.
        tool_calls = []
        for rid in conv["response_ids"]:
            tool_calls.extend(rid_to_calls.get(rid, []))
        # Use role="agent" so v2 scorer's _gather_assistant_text picks up every
        # agent turn (the scorer also accepts "assistant" after the fix, but we
        # match the AOAI-direct runner's convention for parity).
        result_dict = {
            "response": conv["final_text"],
            "messages": [
                {"role": "user" if e["role"] == "customer" else "agent",
                 "content": e["content"]}
                for e in conv["transcript"]
            ],
            "tool_calls": tool_calls,
        }
        try:
            scores = eval_module_v2.score_scenario(result_dict, scenario)
            scores["error"] = meta["error"]
            scores["response_preview"] = (conv["final_text"] or "")[:200]
            scores["actual_tools"] = [tc["name"] for tc in tool_calls]
            scores["response_ids"] = conv["response_ids"]
            scores["stop_reason"] = conv["stop_reason"]
            scores["rounds"] = conv["rounds"]
            # Preserve raw transcript + tool_calls so a future scorer change
            # can be re-applied without re-running the 300-call conversation.
            scores["transcript"] = conv["transcript"]
            scores["tool_calls"] = tool_calls
        except Exception as e:  # noqa: BLE001
            scores = {
                "scenario_id": scenario["id"],
                "scenario_name": scenario["name"],
                "difficulty": scenario.get("difficulty", "unknown"),
                "category": scenario.get("category", ""),
                "decision_correctness": 0.0, "tool_usage": 0.0,
                "financial_accuracy": 0.0, "communication_quality": 0.0,
                "combined": 0.0, "error": str(e),
                "response_preview": "", "actual_tools": [],
                "response_ids": conv["response_ids"],
                "stop_reason": conv["stop_reason"], "rounds": conv["rounds"],
            }
        results.append(scores)

    n = len(results)
    def avg(key):
        return round(sum(r[key] for r in results) / n, 3) if n else 0

    difficulty_groups: dict = {}
    category_groups: dict = {}
    for r in results:
        difficulty_groups.setdefault(r.get("difficulty", "unknown"), []).append(r)
        category_groups.setdefault(r.get("category", "unknown"), []).append(r)

    def summarize_group(group):
        gn = len(group)
        return {
            "count": gn,
            "avg_combined": round(sum(r["combined"] for r in group) / gn, 3),
            "avg_decision": round(sum(r["decision_correctness"] for r in group) / gn, 3),
            "avg_tools": round(sum(r["tool_usage"] for r in group) / gn, 3),
            "avg_financial": round(sum(r["financial_accuracy"] for r in group) / gn, 3),
            "avg_communication": round(sum(r["communication_quality"] for r in group) / gn, 3),
        }

    summary = {
        "model": args.agent, "scorer_version": "v2", "hosted": True,
        "n_scenarios": n,
        "avg_decision_correctness": avg("decision_correctness"),
        "avg_tool_usage": avg("tool_usage"),
        "avg_financial_accuracy": avg("financial_accuracy"),
        "avg_communication_quality": avg("communication_quality"),
        "avg_combined": avg("combined"),
        "by_difficulty": {d: summarize_group(g) for d, g in difficulty_groups.items()},
        "by_category": {c: summarize_group(g) for c, g in category_groups.items()},
        "errors": sum(1 for r in results if r["error"]),
        "per_scenario": results,
    }
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    eval_module_v2.print_eval_summary(summary)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
