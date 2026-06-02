#!/usr/bin/env python
"""Drive teacher traffic for SFT data collection.

Differs from run_baselines_hosted.py in two ways:
  1. The FIRST customer turn is the LITERAL scenario.user_message — this
     preserves adversarial context (long distracting story, counter-factual
     claim, multi-item, policy-bypass attempt, etc.) that the existing persona
     simulator strips when it opens with a vague "Hi I need help with my X".
  2. No scoring. We just need diverse traces flowing to App Insights so the
     data-gen worker can harvest them as SFT rows.

Usage:
    python scripts/drive_teacher_traffic.py \
        --scenarios eval/training_tasks.json --seed 1 --suffix s1

Parallel:
    Launch multiple instances with different --seed values.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

NB_DIR = Path(__file__).resolve().parents[1]
load_dotenv(NB_DIR / ".env")

from azure.identity import DefaultAzureCredential  # noqa: E402
from azure.ai.projects import AIProjectClient  # noqa: E402
from openai import OpenAI  # noqa: E402

PROJECT_ENDPOINT = (
    os.environ.get("AZURE_AI_PROJECT_ENDPOINT")
    or "https://smamgain-tip-aifoundry.services.ai.azure.com/api/projects/smamgain-tip-aiproject"
)
CUSTOMER_MODEL = os.environ.get("CUSTOMER_MODEL", "gpt-5.4-mini")
MAX_ROUNDS = int(os.environ.get("EVAL_MAX_ROUNDS", "8"))

# Persona for FOLLOW-UP turns only. First turn is the literal scenario text.
PERSONA_PROMPT = """You are simulating a customer chatting with a retail support agent. \
Your full situation (the agent does NOT see this — reveal only what's asked):

{scenario}

Style rules:
- You ALREADY sent your opening message; the agent has now replied. Continue the conversation.
- When the agent asks clarifying questions (order ID, item, reason, status, email), \
share the matching detail from your situation.
- Do NOT volunteer policy reasoning or restocking math. Let the agent decide.
- If the agent proposes a resolution and asks you to confirm, say YES.
- If the agent has DENIED with a clear final policy reason, accept gracefully.
- ONLY output the literal token [END] on its own line AFTER the agent has FINALIZED \
(given a confirmation/reference number, said "submitted/processed", or explicitly DENIED \
with a final reason they have repeated). A clarifying question, a quoted refund amount \
awaiting confirmation, or "would you like me to proceed?" is NOT a finalization.
- Never call tools. Replies under ~3 short sentences."""


def _make_customer_client() -> OpenAI:
    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if not (base_url and api_key):
        raise RuntimeError("Set OPENAI_BASE_URL + AZURE_OPENAI_API_KEY in .env")
    return OpenAI(base_url=base_url, api_key=api_key,
                  timeout=float(os.environ.get("CUSTOMER_HTTP_TIMEOUT_SEC", "120")),
                  max_retries=2)


def _is_reasoning(m: str) -> bool:
    m = (m or "").lower()
    return any(t in m for t in ("o4", "o5", "gpt-5", "rft"))


def customer_follow_up(client: OpenAI, scenario_text: str, transcript: list, seed: int) -> str:
    msgs = [{"role": "system", "content": PERSONA_PROMPT.format(scenario=scenario_text)}]
    for entry in transcript:
        role = "user" if entry["role"] == "agent" else "assistant"
        msgs.append({"role": role, "content": entry["content"]})
    kwargs = dict(model=CUSTOMER_MODEL, messages=msgs, seed=seed)
    if _is_reasoning(CUSTOMER_MODEL):
        kwargs["max_completion_tokens"] = 300
    else:
        kwargs["max_tokens"] = 200
        kwargs["temperature"] = 0.0
    return (client.chat.completions.create(**kwargs).choices[0].message.content or "").strip()


def drive_one(agent_client, customer_client, scenario: dict, seed: int, verbose: bool) -> dict:
    transcript = []
    response_ids = []
    previous_response_id: Optional[str] = None
    stop_reason = "max_rounds"

    # ---- Round 1: LITERAL scenario.user_message ----
    opening = scenario["user_message"]
    transcript.append({"role": "customer", "content": opening})
    if verbose:
        print(f"  cust[1]: {opening[:120]}", flush=True)
    try:
        resp = agent_client.responses.create(input=opening)
    except Exception as ae:  # noqa: BLE001
        return {"transcript": transcript, "response_ids": [], "stop_reason": f"agent_error_r1: {type(ae).__name__}: {str(ae)[:200]}"}
    previous_response_id = resp.id
    response_ids.append(resp.id)
    agent_text = resp.output_text or ""
    transcript.append({"role": "agent", "content": agent_text})
    if verbose:
        print(f"  agent[1]: {agent_text[:120]}", flush=True)

    # ---- Rounds 2..N: persona follow-up ----
    for round_ix in range(2, MAX_ROUNDS + 1):
        try:
            cust_msg = customer_follow_up(customer_client, scenario["user_message"], transcript, seed)
        except Exception as ce:  # noqa: BLE001
            stop_reason = f"customer_error: {type(ce).__name__}"
            break
        ended = "[END]" in cust_msg
        cust_clean = cust_msg.replace("[END]", "").strip()
        if not cust_clean:
            stop_reason = "end_token" if ended else "empty_customer_reply"
            break
        transcript.append({"role": "customer", "content": cust_clean})
        if verbose:
            print(f"  cust[{round_ix}]: {cust_clean[:120]}", flush=True)
        try:
            resp = agent_client.responses.create(input=cust_clean, previous_response_id=previous_response_id)
        except Exception as ae:  # noqa: BLE001
            stop_reason = f"agent_error: {type(ae).__name__}: {str(ae)[:200]}"
            break
        previous_response_id = resp.id
        response_ids.append(resp.id)
        agent_text = resp.output_text or ""
        transcript.append({"role": "agent", "content": agent_text})
        if verbose:
            print(f"  agent[{round_ix}]: {agent_text[:120]}", flush=True)
        if ended:
            stop_reason = "end_token"
            break

    return {"transcript": transcript, "response_ids": response_ids, "stop_reason": stop_reason}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", default="demo1-retail-agent-langraph-responses")
    ap.add_argument("--scenarios", default=str(NB_DIR / "eval" / "training_tasks.json"))
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--suffix", default="")
    ap.add_argument("--only", default="", help="Comma-separated scenario IDs")
    ap.add_argument("--start", type=int, default=0, help="Start index (for slicing)")
    ap.add_argument("--end", type=int, default=None, help="End index exclusive")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    if args.only:
        keep = {s.strip() for s in args.only.split(",") if s.strip()}
        scenarios = [s for s in scenarios if s["id"] in keep]
    if args.end is None:
        args.end = len(scenarios)
    scenarios = scenarios[args.start:args.end]

    out_dir = NB_DIR / "results" / "traffic_logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"traffic__{args.agent}__seed{args.seed}{args.suffix}.json"

    print(f"[seed={args.seed}] Driving {len(scenarios)} scenarios -> {out_path}", flush=True)

    cred = DefaultAzureCredential()
    pc = AIProjectClient(endpoint=PROJECT_ENDPOINT, credential=cred, allow_preview=True)
    agent_client = pc.get_openai_client(agent_name=args.agent)
    customer_client = _make_customer_client()

    results = []
    t_start = time.time()
    for i, scenario in enumerate(scenarios, 1):
        t0 = time.time()
        try:
            conv = drive_one(agent_client, customer_client, scenario, args.seed, args.verbose)
            err = None
        except Exception as e:  # noqa: BLE001
            conv = {"transcript": [], "response_ids": [], "stop_reason": f"exception: {type(e).__name__}: {str(e)[:200]}"}
            err = str(e)
        results.append({
            "scenario_id": scenario["id"],
            "scenario_category": scenario.get("category"),
            "scenario_order_id": scenario.get("order_id"),
            "seed": args.seed,
            "response_ids": conv["response_ids"],
            "n_rounds": len(conv["transcript"]) // 2,
            "stop_reason": conv["stop_reason"],
            "error": err,
        })
        print(f"[seed={args.seed} {i}/{len(scenarios)}] {scenario['id']} {scenario.get('category','')[:25]:<25}: "
              f"{len(conv['transcript'])//2}r ({conv['stop_reason'][:30]}) {len(conv['response_ids'])}rid in {time.time()-t0:.1f}s", flush=True)
        # Save incrementally so partial work is not lost
        out_path.write_text(json.dumps(results, indent=2))
    print(f"[seed={args.seed}] DONE {len(results)} scenarios in {(time.time()-t_start)/60:.1f} min. "
          f"Total response_ids: {sum(len(r['response_ids']) for r in results)}", flush=True)


if __name__ == "__main__":
    main()
