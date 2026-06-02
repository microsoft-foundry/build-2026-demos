#!/usr/bin/env python
"""Run the multi-turn student/teacher baseline outside the notebook.

Mirrors §1 + §2 + §3 of `agent_traces_to_sft.ipynb` so the produced
`results/baseline__mt__{student,teacher}__*.json` files are interchangeable
with the cached files the notebook reads back.

Usage:
    python scripts/run_baselines.py --role student
    python scripts/run_baselines.py --role teacher
    python scripts/run_baselines.py --role student --only T21,T25,T28,T30
    python scripts/run_baselines.py --role student --only T01,T02 --merge
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

NB_DIR = Path(__file__).resolve().parents[1]
EVAL_DIR = NB_DIR / "eval"
RESULTS_DIR = NB_DIR / "results"
RESULTS_DIR.mkdir(exist_ok=True)

# The retail-agent-langgraph tools.py is the canonical tool source. It exposes
# - TOOL_FUNCTIONS: raw Python callables (used by this script's chat-completions tool loop)
# - AgentTools.all_tools(): LangChain @tool wrappers (used to derive OpenAI schemas)
# (Historically these came from a sibling Zava-Ignite-RL-Lab/src/zava_tools.py
# which was removed when the agent was moved into src/retail-agent-langgraph/.)
RETAIL_AGENT_SRC = (NB_DIR / "src" / "retail-agent-langgraph").resolve()
if not (RETAIL_AGENT_SRC / "tools.py").exists():
    raise RuntimeError(f"retail-agent tools not found at {RETAIL_AGENT_SRC}")

# Path setup: RETAIL_AGENT_SRC for tools, EVAL_DIR LAST so it wins on `import evaluate`
for p in (str(RETAIL_AGENT_SRC), str(EVAL_DIR)):
    if p in sys.path:
        sys.path.remove(p)
    sys.path.insert(0, p)

load_dotenv(NB_DIR / ".env")

import evaluate as eval_module  # noqa: E402
import evaluate_v2 as eval_module_v2  # noqa: E402
import tools as retail_tools  # noqa: E402  # imports cleanly: no agentserver deps

eval_module = importlib.reload(eval_module)
eval_module_v2 = importlib.reload(eval_module_v2)

# Derive OpenAI function-call schemas from the LangChain @tool wrappers so this
# script stays in sync with whatever the hosted agent binds.
from langchain_core.utils.function_calling import convert_to_openai_tool  # noqa: E402

TOOL_FUNCTIONS = retail_tools.TOOL_FUNCTIONS
TOOL_SCHEMAS = [convert_to_openai_tool(t) for t in retail_tools.AgentTools.all_tools()]

# Mirrors the SYSTEM_PROMPT in zava_agent.py (agent_policy.md). Kept inline so
# this script doesn't need to import the full hosted-agent module.
SYSTEM_PROMPT = (
    "You are Zava's Post-Purchase Resolution Desk agent. Help customers with "
    "returns, exchanges, replacements, cancellations, and shipping disputes. "
    "Use the available tools to verify eligibility and compute resolutions.\n\n"
    + (NB_DIR / "src" / "retail-agent-langgraph" / "agent_policy.md").read_text(encoding="utf-8")
)


def _get_client(model=None):
    # AGENT_* env vars allow pointing the AGENT model at a separate endpoint
    # (e.g. a fine-tuned deployment on a different Azure resource) without
    # disturbing the customer-simulator client which uses OPENAI_BASE_URL.
    api_key = (
        os.environ.get("AGENT_OPENAI_API_KEY")
        or os.environ.get("AZURE_OPENAI_API_KEY")
    )
    base_url = (
        os.environ.get("AGENT_OPENAI_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
    )
    endpoint = (
        os.environ.get("AGENT_AZURE_OPENAI_ENDPOINT")
        or os.environ.get("AZURE_OPENAI_ENDPOINT")
    )
    api_version = os.environ.get("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")

    from openai import AzureOpenAI, OpenAI  # noqa: WPS433

    if base_url:
        client = OpenAI(base_url=base_url, api_key=api_key)
    elif endpoint:
        client = AzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=api_version)
    else:
        raise ValueError("Set OPENAI_BASE_URL or AZURE_OPENAI_ENDPOINT")
    deployment = (
        model
        or os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME")
        or os.environ.get("MODEL", "gpt-4.1-mini")
    )
    return client, deployment


def _run_agent(user_message, *, model, client, max_turns=15, history=None, verbose=False):
    """Stripped-down chat-completions tool-loop (matches Zava's run_agent API)."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    tool_calls_log = []

    for _ in range(max_turns):
        kwargs = dict(model=model, messages=messages, tools=TOOL_SCHEMAS)
        m = (model or "").lower()
        if any(t in m for t in ("o4", "o5", "gpt-5", "rft")):
            kwargs["max_completion_tokens"] = 8192
            # gpt-5.5-1 rejects reasoning_effort when function tools are present
            # on /v1/chat/completions ("use /v1/responses instead"). We always
            # pass tools in this harness, so omit reasoning_effort entirely for
            # gpt-5.5 family. Older o4/o5 models accept the default effort.
            if "gpt-5.5" not in m:
                kwargs["reasoning_effort"] = "high"
        else:
            kwargs["max_tokens"] = 4096
            # Lower temperature for the agent itself to reduce run-to-run
            # variance (FT-v2 was swinging up to 73pp on a single scenario at
            # default temperature). Override via AGENT_TEMPERATURE env var.
            kwargs["temperature"] = float(os.environ.get("AGENT_TEMPERATURE", "0.2"))
            # Pass an explicit seed so the provider can reproduce outputs when it
            # routes to the same model fingerprint. Combined with low temp this
            # is the strongest determinism guarantee Azure OpenAI offers.
            _seed_env = os.environ.get("AGENT_SEED")
            if _seed_env:
                kwargs["seed"] = int(_seed_env)

        response = client.chat.completions.create(**kwargs)
        assistant_msg = response.choices[0].message
        msg_dict = {"role": "assistant", "content": assistant_msg.content}
        if assistant_msg.tool_calls:
            msg_dict["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in assistant_msg.tool_calls
            ]
        messages.append(msg_dict)

        if not assistant_msg.tool_calls:
            return {
                "response": assistant_msg.content,
                "messages": messages,
                "tool_calls": tool_calls_log,
            }

        for tc in assistant_msg.tool_calls:
            fn_name = tc.function.name
            try:
                fn_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                fn_args = {}
            fn = TOOL_FUNCTIONS.get(fn_name)
            if fn:
                try:
                    result = fn(**fn_args)
                except Exception as e:  # noqa: BLE001
                    result = json.dumps({"error": f"Tool error: {e}"})
            else:
                result = json.dumps({"error": f"Unknown tool: {fn_name}"})
            tool_calls_log.append({"name": fn_name, "arguments": fn_args, "result": result})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

    return {
        "response": messages[-1].get("content", "[Max turns reached]"),
        "messages": messages,
        "tool_calls": tool_calls_log,
    }


# Provide the same API the notebook uses: zava_agent.get_client, zava_agent.run_agent
class _ZavaShim:
    get_client = staticmethod(_get_client)
    run_agent = staticmethod(_run_agent)


zava_agent = _ZavaShim()

STUDENT_MODEL = os.environ.get("STUDENT_MODEL", "gpt-4.1-nano")
TEACHER_MODEL = os.environ.get("TEACHER_MODEL", "gpt-5.4")
CUSTOMER_MODEL = os.environ.get("CUSTOMER_MODEL", "gpt-5.4-mini")
AGENT_MAX_TURNS = int(os.environ.get("AGENT_MAX_TURNS", "15"))
EVAL_MAX_ROUNDS = int(os.environ.get("EVAL_MAX_ROUNDS", "10"))

_customer_base_url = os.environ.get("OPENAI_BASE_URL")
_customer_api_key = os.environ.get("AZURE_OPENAI_API_KEY")
_customer_timeout = float(os.environ.get("CUSTOMER_HTTP_TIMEOUT_SEC", "180"))
if not (_customer_base_url and _customer_api_key):
    raise RuntimeError(
        "Set OPENAI_BASE_URL + AZURE_OPENAI_API_KEY in .env (the notebook's "
        "preferred direct-OpenAI customer client setup)."
    )

from openai import OpenAI  # noqa: E402

customer_client = OpenAI(
    base_url=_customer_base_url,
    api_key=_customer_api_key,
    timeout=_customer_timeout,
    max_retries=2,
)

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


def _is_reasoning_model(model: str) -> bool:
    m = (model or "").lower()
    return any(tag in m for tag in ("o4", "o5", "gpt-5", "rft"))


def run_multi_turn_eval_conversation(scenario_user_message, model, *, client=None, verbose=False):
    sys_prompt = EVAL_CUSTOMER_PROMPT.format(scenario=scenario_user_message)
    if client is None:
        client, _ = zava_agent.get_client(model)

    history, transcript = [], []
    final_text, all_tool_calls, rounds_used = "", [], 0
    stop_reason = "max_rounds"

    for round_ix in range(EVAL_MAX_ROUNDS):
        rounds_used = round_ix + 1

        msgs = [{"role": "system", "content": sys_prompt}]
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
        # Customer simulator seed (matches agent seed by default for reproducibility)
        _seed_env = os.environ.get("CUSTOMER_SEED") or os.environ.get("AGENT_SEED")
        if _seed_env:
            kwargs["seed"] = int(_seed_env)

        try:
            cust_resp = customer_client.chat.completions.create(**kwargs)
        except Exception as ce:  # noqa: BLE001
            stop_reason = f"customer_error: {type(ce).__name__}"
            break
        cust_msg = (cust_resp.choices[0].message.content or "").strip()
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
            print(f"  cust:  {cust_msg_clean[:140]}", flush=True)

        try:
            result = zava_agent.run_agent(
                cust_msg_clean,
                model=model,
                client=client,
                history=history,
                max_turns=AGENT_MAX_TURNS,
            )
        except Exception as ae:  # noqa: BLE001
            stop_reason = f"agent_error: {type(ae).__name__}"
            break

        agent_text = result.get("response", "") or ""
        final_text = agent_text
        all_tool_calls.extend(result.get("tool_calls", []) or [])
        transcript.append({"role": "agent", "content": agent_text})
        if verbose:
            print(f"  agent: {agent_text[:140]}", flush=True)

        # Preserve the FULL agent sub-conversation (assistant tool_calls + tool
        # responses + final text) across customer rounds, not just the final
        # assistant text. Otherwise the agent loses memory of tools it already
        # called and re-asks the customer for info it could remember. The
        # returned result["messages"] = [system, ...prev_history, new_user,
        # asst1, tool1..., final_asst], so slicing off the system gives us a
        # complete updated history.
        history = result["messages"][1:]

        if ended:
            stop_reason = "end_token"
            break

    return {
        "response": final_text,
        "messages": transcript,
        "tool_calls": all_tool_calls,
        "stop_reason": stop_reason,
        "rounds": rounds_used,
    }


def make_multi_turn_runner(model_deployment):
    client, _ = zava_agent.get_client(model_deployment)

    def _runner(user_message, *, model=None, client=None, verbose=False):
        return run_multi_turn_eval_conversation(
            user_message,
            model=model_deployment,
            client=_runner._client,
            verbose=verbose,
        )

    _runner._client = client
    return _runner


def _safe_name(s):
    return "".join(c if c.isalnum() or c in ".-_" else "_" for c in s)


def _merge(existing: dict, fresh: dict) -> dict:
    """Merge a partial fresh run (subset of scenarios) into an existing cache."""
    by_id = {r["scenario_id"]: r for r in existing.get("per_scenario", [])}
    for r in fresh["per_scenario"]:
        by_id[r["scenario_id"]] = r
    merged_rows = list(by_id.values())
    n = len(merged_rows)

    def avg(key):
        return round(sum(r.get(key, 0.0) for r in merged_rows) / n, 3) if n else 0

    diff_groups = {}
    for r in merged_rows:
        diff_groups.setdefault(r.get("difficulty", "unknown"), []).append(r)
    diff_summary = {}
    for d, group in diff_groups.items():
        gn = len(group)
        diff_summary[d] = {
            "count": gn,
            "avg_combined": round(sum(r["combined"] for r in group) / gn, 3),
            "avg_decision": round(sum(r["decision_correctness"] for r in group) / gn, 3),
            "avg_tools": round(sum(r["tool_usage"] for r in group) / gn, 3),
            "avg_financial": round(sum(r["financial_accuracy"] for r in group) / gn, 3),
            "avg_communication": round(sum(r["communication_quality"] for r in group) / gn, 3),
        }

    return {
        "model": existing.get("model") or fresh.get("model"),
        "n_scenarios": n,
        "avg_decision_correctness": avg("decision_correctness"),
        "avg_tool_usage": avg("tool_usage"),
        "avg_financial_accuracy": avg("financial_accuracy"),
        "avg_communication_quality": avg("communication_quality"),
        "avg_combined": avg("combined"),
        "by_difficulty": diff_summary,
        "errors": sum(1 for r in merged_rows if r.get("error")),
        "per_scenario": merged_rows,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", choices=["student", "teacher", "ft"], required=True,
                    help="student/teacher use STUDENT_MODEL/TEACHER_MODEL from .env; "
                         "ft requires --model.")
    ap.add_argument("--model", default="",
                    help="Model deployment name. Required for --role ft. "
                         "Overrides STUDENT_MODEL/TEACHER_MODEL for student/teacher.")
    ap.add_argument("--only", default="", help="Comma-separated scenario IDs (e.g. T21,T25,T30)")
    ap.add_argument("--merge", action="store_true", help="Merge --only run into existing baseline cache")
    ap.add_argument("--suffix", default="", help="Suffix appended to output filename (e.g. .pass1)")
    ap.add_argument("--scenarios", default=str(EVAL_DIR / "training_tasks.json"))
    ap.add_argument("--scorer", default="v1", choices=["v1", "v2"],
                    help="Which scorer to use (v2 = hard-set calibrated)")
    ap.add_argument("--results-dir", default="",
                    help="Subdir under results/ to write into (created if missing)")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.role == "ft":
        if not args.model:
            sys.exit("--role ft requires --model <ft-deployment-name>")
        model = args.model
    elif args.model:
        model = args.model
    elif args.role == "student":
        model = STUDENT_MODEL
    else:
        model = TEACHER_MODEL
    label = args.role
    scenarios = json.loads(Path(args.scenarios).read_text())

    if args.only:
        keep = {s.strip() for s in args.only.split(",") if s.strip()}
        scenarios = [s for s in scenarios if s["id"] in keep]
        print(f"--only filter -> running {len(scenarios)} scenarios: {sorted(keep)}", flush=True)
        if not scenarios:
            sys.exit("No scenarios matched --only filter.")

    target_dir = RESULTS_DIR / args.results_dir if args.results_dir else RESULTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    scorer_tag = "" if args.scorer == "v1" else ".v2"
    out_path = target_dir / f"baseline__mt__{label}__{_safe_name(model)}{scorer_tag}{args.suffix}.json"
    print(
        f"Running {label.upper()} baseline | model={model} | "
        f"customer={CUSTOMER_MODEL} | n={len(scenarios)} | rounds<={EVAL_MAX_ROUNDS} | "
        f"agent_max_turns={AGENT_MAX_TURNS} | scorer={args.scorer}\nOutput -> {out_path}",
        flush=True,
    )

    scorer = eval_module_v2 if args.scorer == "v2" else eval_module
    summary = scorer.evaluate_model(
        model,
        scenarios,
        runner=make_multi_turn_runner(model),
        verbose=args.verbose,
    )

    if args.merge and out_path.exists():
        existing = json.loads(out_path.read_text())
        summary = _merge(existing, summary)
        print(f"Merged subset run into existing cache ({len(summary['per_scenario'])} total).", flush=True)

    out_path.write_text(json.dumps(summary, indent=2, default=str))
    scorer.print_eval_summary(summary)
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
