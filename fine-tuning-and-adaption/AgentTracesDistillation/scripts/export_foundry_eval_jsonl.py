"""Convert the curated 80-train / 20-validation task sets into JSONL files
that can be consumed by Azure AI Foundry Evaluations.

Output format follows the conventions of `azure.ai.evaluation.evaluate()`:
each row is a flat JSON object with stable column names. The same files can
also be uploaded to the Foundry Portal "Evaluations" UI as a test dataset.

Columns produced
----------------
    query                  : str   -- the initial customer message (single-turn seed)
    ground_truth           : str   -- compact, human-readable expected outcome string
                                       (for built-in evaluators that expect ground_truth)
    expected_tools         : list  -- ordered list of tool names the agent must call
    forbidden_tools        : list  -- tools that must NOT be called
    expected_actions       : dict  -- per-line-item action map (refund / replace / etc.)
    expected_amounts       : dict  -- numeric truth (refund totals, restocking, credits)
    policy_points          : list  -- policy keywords that must surface in reasoning
    expected_resolution    : str   -- the canonical resolution summary
    order_id               : str
    target_items           : list
    category               : str
    difficulty             : str
    sid                    : str   -- stable scenario id ("H036" / "HE012")
    task_id                : str   -- positional id ("1".."80")
    name                   : str   -- human-readable label
    context                : str   -- JSON-stringified metadata for prompted graders
    conversation           : list  -- single-message seed in OpenAI chat format
                                       ([{"role":"user","content":<query>}])

Usage
-----
    python scripts/export_foundry_eval_jsonl.py
        --out-dir eval/foundry

This writes:
    eval/foundry/foundry_eval_train_80.jsonl
    eval/foundry/foundry_eval_validation_20.jsonl
    eval/foundry/README.md    -- short note on field semantics + sample evaluator code

Notes
-----
- The repo's internal scorer (scripts/score_v2.py) uses richer logic than the
  built-in Foundry evaluators (tool-call ordering, amount math, action-map
  matching). Built-in evals such as IntentResolution / TaskAdherence will work
  out of the box, but for full parity with `run_baselines.py` you'd register a
  custom evaluator that consumes the same JSONL rows.
- The 80/20 split is sourced from results/v2_FIXED/{train,heldout}/curated_*_sids.json
  and re-derived against eval/training_tasks.json + eval/eval_tasks.json (which already
  honor that split today). If you re-partition via reselect_and_reslice.py, just
  rerun this script against the new tasks files.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EVAL_DIR = REPO_ROOT / "eval"


def _short_ground_truth(t: dict) -> str:
    """Compact one-line ground-truth string for evaluators that want a single
    reference response. Includes the resolution summary plus the canonical
    refund total for grounded comparison."""
    parts = []
    if t.get("expected_resolution_summary"):
        parts.append(t["expected_resolution_summary"])
    amounts = t.get("expected_amounts") or {}
    if "total_resolution" in amounts:
        parts.append(f"Total resolution: ${amounts['total_resolution']:.2f}.")
    if t.get("expected_tools"):
        parts.append(f"Required tools: {', '.join(t['expected_tools'])}.")
    return " ".join(parts).strip()


def _convert(task: dict) -> dict:
    """Project one repo-format task into a Foundry-eval-friendly flat row."""
    query = task.get("user_message", "")
    row = {
        "query": query,
        "ground_truth": _short_ground_truth(task),
        # full structured truth for custom / programmatic evaluators
        "expected_tools": task.get("expected_tools", []),
        "forbidden_tools": task.get("forbidden_tools", []),
        "expected_actions": task.get("expected_actions", {}),
        "expected_amounts": task.get("expected_amounts", {}),
        "policy_points": task.get("policy_points", []),
        "expected_resolution": task.get("expected_resolution_summary", ""),
        # identifiers
        "order_id": task.get("order_id", ""),
        "target_items": task.get("target_items", []),
        "category": task.get("category", ""),
        "difficulty": task.get("difficulty", ""),
        "sid": task.get("original_id") or task.get("sid") or task.get("id", ""),
        "task_id": str(task.get("id", "")),
        "name": task.get("name", ""),
        # extras useful for prompt-grader evaluators (Foundry Portal accepts strings)
        "context": json.dumps(
            {
                "category": task.get("category", ""),
                "policy_points": task.get("policy_points", []),
                "expected_amounts": task.get("expected_amounts", {}),
            },
            ensure_ascii=False,
        ),
        # for conversation-style evaluators (e.g. IntentResolution) seed turn 1
        "conversation": [{"role": "user", "content": query}],
    }
    return row


def _write_jsonl(rows: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"wrote {len(rows):3d} rows -> {out_path.relative_to(REPO_ROOT)}")


README_TEMPLATE = """# Foundry-eval JSONL exports

Generated by `scripts/export_foundry_eval_jsonl.py` from the curated
80-train / 20-validation task sets.

## Files

- `foundry_eval_train_80.jsonl`       — 80 hard customer scenarios (training partition)
- `foundry_eval_validation_20.jsonl`  — 20 hard heldout scenarios (validation partition)

## Columns

Each row is a flat JSON object. Most evaluators consume only a subset; the
rest is metadata for custom evaluators or analysis.

| column               | type            | purpose |
|----------------------|-----------------|---------|
| `query`              | str             | First user turn (built-in evals + simulators) |
| `ground_truth`       | str             | One-line canonical answer (Relevance, Groundedness, etc.) |
| `conversation`       | list[msg]       | `[{role:user, content:query}]` — seeds multi-turn evaluators |
| `expected_tools`     | list[str]       | Tool names the agent must call (custom tool-call evaluator) |
| `forbidden_tools`    | list[str]       | Tools that must NOT be called |
| `expected_actions`   | dict            | Per-line-item action map (refund/replace/credit/…) |
| `expected_amounts`   | dict            | Numeric truth (refund totals, credits, restocking fees) |
| `policy_points`      | list[str]       | Policy keywords the response must reflect |
| `expected_resolution`| str             | Full free-text canonical resolution summary |
| `order_id`           | str             | Order under discussion |
| `target_items`       | list[str]       | Line-item ids affected |
| `category`/`difficulty` | str          | Stratification labels |
| `sid` / `task_id` / `name` | str       | Stable identifiers |
| `context`            | str (JSON)      | Compact metadata for prompt-graders |

## Quick start: use with `azure-ai-evaluation`

```python
from azure.ai.evaluation import evaluate
from azure.ai.evaluation import IntentResolutionEvaluator, RelevanceEvaluator

# `model_config` points at any Azure OpenAI / Foundry chat model
result = evaluate(
    data="eval/foundry/foundry_eval_validation_20.jsonl",
    target=my_agent_callable,            # (query, conversation) -> {"response": str, "tool_calls": [...]}
    evaluators={
        "intent_resolution": IntentResolutionEvaluator(model_config=judge_cfg),
        "relevance": RelevanceEvaluator(model_config=judge_cfg),
    },
    evaluator_config={
        "intent_resolution": {"column_mapping": {"query": "${data.query}", "response": "${target.response}"}},
        "relevance": {"column_mapping": {"query": "${data.query}", "response": "${target.response}", "ground_truth": "${data.ground_truth}"}},
    },
)
print(result["studio_url"])    # link to Foundry Portal Evaluations tab
```

## Custom evaluator for full parity with `run_baselines.py`

The repo's `scripts/score_v2.py` uses richer logic (tool-call ordering with
substring tolerance, amount math, action-map matching, policy-word coverage).
To get parity inside Foundry, wrap that scorer as a callable evaluator:

```python
class CustomV2Evaluator:
    def __init__(self): pass
    def __call__(self, *, query, response, expected_tools, expected_amounts,
                 expected_actions, policy_points, tool_calls, **_):
        from scripts.score_v2 import score_scenario
        return score_scenario(
            response=response,
            tool_calls=tool_calls,
            expected_tools=expected_tools,
            expected_amounts=expected_amounts,
            expected_actions=expected_actions,
            policy_points=policy_points,
        )

evaluators = {"v2_combined": CustomV2Evaluator()}
```

## Foundry Portal upload

Both JSONLs are valid drop-ins for the Foundry Portal "Evaluations" tab
("Create new evaluation → Upload dataset"). The Portal will auto-detect
`query`, `ground_truth`, `conversation`, and `context` for built-in evaluators.
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default=str(EVAL_DIR / "training_tasks.json"))
    ap.add_argument("--validation", default=str(EVAL_DIR / "eval_tasks.json"))
    ap.add_argument("--out-dir", default=str(EVAL_DIR / "foundry"))
    args = ap.parse_args()

    train_path = Path(args.train).resolve()
    val_path = Path(args.validation).resolve()
    out_dir = Path(args.out_dir).resolve()

    if not train_path.exists():
        raise SystemExit(f"missing train tasks: {train_path}")
    if not val_path.exists():
        raise SystemExit(f"missing validation tasks: {val_path}")

    train_tasks = json.loads(train_path.read_text(encoding="utf-8"))
    val_tasks = json.loads(val_path.read_text(encoding="utf-8"))

    train_rows = [_convert(t) for t in train_tasks]
    val_rows = [_convert(t) for t in val_tasks]

    _write_jsonl(train_rows, out_dir / "foundry_eval_train_80.jsonl")
    _write_jsonl(val_rows, out_dir / "foundry_eval_validation_20.jsonl")

    (out_dir / "README.md").write_text(README_TEMPLATE, encoding="utf-8")
    print(f"wrote README -> {(out_dir / 'README.md').relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
