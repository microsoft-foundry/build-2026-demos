"""Generate live student + FT conversations for the demo notebook.

Picks 4 representative scenarios where the FT model substantially outperformed
the student baseline. For each, runs the SAME scenario twice — once against the
deployed student endpoint (gpt-4.1-nano) and once against the deployed FT
endpoint (gpt-4.1-nano-demo1) — and captures both full conversations.

Outputs: results/eval_result/demo_transcripts.json

The notebook reads this file and renders the side-by-side conversations, so the
notebook itself never needs to hit either endpoint during display.

Run:
  cd Demos/AgentTracesDistillation
  $env:PYTHONIOENCODING="utf-8"
  .\.venv-hosted\Scripts\python.exe scripts\generate_demo_conversations.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

NB_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(NB_DIR / "scripts"))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(NB_DIR / ".env")

# Student endpoint (the non-FT baseline)
student_base = os.environ.get("OPENAI_BASE_URL")
student_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
STUDENT_MODEL = os.environ.get("STUDENT_MODEL", "gpt-4.1-nano")

# FT endpoint (the post-training deployment)
ft_base = os.environ.get("FT_OPENAI_BASE_URL")
ft_key = os.environ.get("FT_OPENAI_API_KEY")
FT_MODEL = os.environ.get("FT_MODEL", "gpt-4.1-nano-demo1")

if not (student_base and student_key):
    raise SystemExit("OPENAI_BASE_URL and OPENAI_API_KEY must be set in .env")
if not (ft_base and ft_key):
    raise SystemExit("FT_OPENAI_BASE_URL and FT_OPENAI_API_KEY must be set in .env")

import run_baselines  # noqa: E402
from openai import OpenAI  # noqa: E402

student_client = OpenAI(base_url=student_base, api_key=student_key)
ft_client = OpenAI(base_url=ft_base, api_key=ft_key)

# === Selected scenarios (data-driven choices from _pick_demo_scenarios2.py) ===
# Each entry: (set, scenario_id, headline) where set is "train" or "validation".
# scenario_id is the integer id used in the source scenarios JSON.
DEMO_PICKS = [
    {
        "set": "validation",
        "id": 7,
        "headline": "Restocking-fee math: gold-tier change of mind on electronics",
        "why": (
            "Pre-FT student averaged 0.54 (sometimes forgot the 15% restocking fee "
            "or applied the wrong tier window). Post-FT averaged 0.90 across 3 passes."
        ),
    },
    {
        "set": "validation",
        "id": 1,
        "headline": "Multi-item cart: refund one, exchange another",
        "why": (
            "Multi-item carts are the toughest category for the student (mean 0.46). "
            "Post-FT averaged 0.85: the model now keeps each line item's resolution "
            "independent instead of forcing a single uniform action."
        ),
    },
    {
        "set": "validation",
        "id": 3,
        "headline": "Sale-priced + defective edge case",
        "why": (
            "Final-sale items are non-returnable except when defective. Student "
            "averaged 0.55 (often refused outright or applied the wrong refund base). "
            "Post-FT averaged 0.85 by checking defect status before applying the "
            "final-sale rule."
        ),
    },
    {
        "set": "train",
        "id": 7,
        "headline": "Out-of-scope request: customer asks about a competitor",
        "why": (
            "The right answer is a polite refusal + redirect. Student averaged 0.59 "
            "(often tried to help anyway, sometimes invoking tools that don't apply). "
            "Post-FT averaged 0.82 and consistently refuses without tool calls."
        ),
    },
]

OUT_PATH = NB_DIR / "results" / "eval_result" / "demo_transcripts.json"


def load_scenarios(set_name: str) -> dict:
    if set_name == "train":
        path = NB_DIR / "eval" / "training_tasks.json"
    else:
        path = NB_DIR / "eval" / "eval_tasks.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {int(s["id"]): s for s in raw}


def run_one(scenario: dict, *, role: str) -> dict:
    """Drive a multi-turn customer <-> agent conversation and return the trace."""
    client = student_client if role == "student" else ft_client
    model = STUDENT_MODEL if role == "student" else FT_MODEL
    print(f"  -> [{role}] scenario id={scenario['id']} ({scenario['category']}) model={model}", flush=True)
    t0 = time.time()
    result = run_baselines.run_multi_turn_eval_conversation(
        scenario_user_message=scenario["user_message"],
        model=model,
        client=client,
        verbose=False,
    )
    elapsed = time.time() - t0
    print(f"     [{role}] done in {elapsed:.1f}s, rounds={result.get('rounds')}, "
          f"stop={result.get('stop_reason')}, tool_calls={len(result.get('tool_calls', []))}",
          flush=True)
    return result


def main() -> None:
    train_scenarios = load_scenarios("train")
    val_scenarios = load_scenarios("validation")

    out = {
        "student_model": STUDENT_MODEL,
        "student_endpoint": student_base,
        "ft_model": FT_MODEL,
        "ft_endpoint": ft_base,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "demos": [],
    }

    for pick in DEMO_PICKS:
        scenarios = train_scenarios if pick["set"] == "train" else val_scenarios
        scenario = scenarios.get(pick["id"])
        if scenario is None:
            print(f"!! scenario {pick['set']}/{pick['id']} not found; skipping", flush=True)
            continue
        print(f"\n=== {pick['set']}/{pick['id']}: {pick['headline']} ===", flush=True)
        student_trace = run_one(scenario, role="student")
        ft_trace = run_one(scenario, role="ft")
        out["demos"].append({
            "set": pick["set"],
            "scenario_id": pick["id"],
            "category": scenario.get("category"),
            "name": scenario.get("name"),
            "headline": pick["headline"],
            "why": pick["why"],
            "scenario": {
                "user_message": scenario.get("user_message"),
                "order_id": scenario.get("order_id"),
                "target_items": scenario.get("target_items"),
                "expected_resolution_summary": scenario.get("expected_resolution_summary"),
                "expected_tools": scenario.get("expected_tools"),
                "policy_points": scenario.get("policy_points"),
                "expected_amounts": scenario.get("expected_amounts"),
            },
            "student": {
                "transcript": student_trace["messages"],
                "tool_calls": student_trace["tool_calls"],
                "rounds": student_trace.get("rounds"),
                "stop_reason": student_trace.get("stop_reason"),
                "final_response": student_trace.get("response"),
            },
            "ft": {
                "transcript": ft_trace["messages"],
                "tool_calls": ft_trace["tool_calls"],
                "rounds": ft_trace.get("rounds"),
                "stop_reason": ft_trace.get("stop_reason"),
                "final_response": ft_trace.get("response"),
            },
        })

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {len(out['demos'])} demos to {OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
