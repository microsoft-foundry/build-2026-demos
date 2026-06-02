"""Evaluation harness for the Zava Post-Purchase Resolution Desk agent.

Scoring dimensions:
  1. Decision Correctness (40%) - right action per item
  2. Tool Usage (25%)          - right tools, right order, no forbidden calls
  3. Financial Accuracy (25%)  - amounts within tolerance
  4. Communication Quality (10%) - policy citations, next steps
"""
import json
import re


# ---------------------------------------------------------------------------
# 1. Decision Correctness (40%)
# ---------------------------------------------------------------------------

def score_decision_correctness(result: dict, scenario: dict) -> float:
    expected_actions = scenario.get("expected_actions", {})
    if not expected_actions:
        # No item-level actions expected. Pass as long as nothing forbidden was called.
        # (T26 deliberately calls calculate_resolution but forbids submit_resolution; the
        # legacy rule of "any calculate_resolution call = 0" was wrong for that case.)
        tool_names = [tc["name"] for tc in result.get("tool_calls", [])]
        forbidden = set(scenario.get("forbidden_tools", []))
        if forbidden:
            return 0.0 if any(t in forbidden for t in tool_names) else 1.0
        # Backwards-compatible default for older scenarios with neither expected_actions
        # nor forbidden_tools (e.g. T02 status check, T19 ambiguous): no resolution action
        # should be produced.
        if "submit_resolution" not in tool_names and "calculate_resolution" not in tool_names:
            return 1.0
        return 0.0

    response_text = (result.get("response") or "").lower()
    tool_calls = result.get("tool_calls", [])

    actual_actions = _extract_actions(tool_calls)

    score = 0.0
    total = len(expected_actions)

    for item_id, expected in expected_actions.items():
        exp_action = expected.get("action", "")

        # Check structured actions first
        if item_id in actual_actions:
            act_action = actual_actions[item_id]
            if act_action == exp_action:
                score += 1.0
            elif (exp_action in ("refund", "replacement", "store_credit")
                  and act_action in ("refund", "replacement", "store_credit")):
                score += 0.7
            elif exp_action == "deny" and act_action == "deny":
                score += 1.0
            continue

        # Fallback: check response text
        score += _text_score_for_action(response_text, exp_action, item_id)

    return score / total if total > 0 else 1.0


def _extract_actions(tool_calls):
    """Extract item_id -> action from calculate_resolution items arg.

    Skips ``shipping_credit`` because it's a meta-action that can co-exist with a
    real per-item resolution (e.g. T29 issues both a `replacement` and a
    `shipping_credit` for the same item; the shipping credit must not overwrite
    the actual resolution action when scoring decision correctness).
    """
    actions = {}
    for tc in tool_calls:
        if tc["name"] == "calculate_resolution":
            items = tc.get("arguments", {}).get("items", [])
            if isinstance(items, str):
                try:
                    items = json.loads(items)
                except json.JSONDecodeError:
                    continue
            for item in items:
                iid = item.get("item_id", "")
                act = item.get("action", "")
                if iid and act and act != "shipping_credit":
                    actions[iid] = act

        if tc["name"] == "submit_resolution":
            # Also check the result of calculate_resolution for breakdown
            pass

    # Also parse calculate_resolution results for breakdown
    for tc in tool_calls:
        if tc["name"] == "calculate_resolution" and tc.get("result"):
            try:
                res = json.loads(tc["result"])
                for item in res.get("breakdown", []):
                    iid = item.get("item_id", "")
                    act = item.get("action", "")
                    if iid and act and act != "shipping_credit" and iid not in actions:
                        actions[iid] = act
            except (json.JSONDecodeError, TypeError):
                pass

    return actions


def _text_score_for_action(text, expected_action, item_id):
    """Score based on response text when structured extraction fails."""
    if expected_action == "deny":
        deny_words = ["deny", "denied", "not eligible", "cannot", "unable",
                      "unfortunately", "final sale", "expired", "ineligible",
                      "not returnable", "cannot be returned"]
        return 0.8 if any(w in text for w in deny_words) else 0.0
    elif expected_action == "refund":
        return 0.7 if any(w in text for w in ["refund", "$", "credit back"]) else 0.0
    elif expected_action == "replacement":
        return 0.7 if any(w in text for w in ["replace", "reship", "send another"]) else 0.0
    elif expected_action == "exchange":
        return 0.7 if any(w in text for w in ["exchange", "swap", "different size"]) else 0.0
    elif expected_action == "store_credit":
        return 0.7 if any(w in text for w in ["store credit", "credit to your account"]) else 0.0
    elif expected_action == "shipping_credit":
        return 0.7 if any(w in text for w in ["shipping credit", "$10", "late delivery"]) else 0.0
    return 0.0


# ---------------------------------------------------------------------------
# 2. Tool Usage (25%)
# ---------------------------------------------------------------------------

def score_tool_usage(result: dict, scenario: dict) -> float:
    actual_tools = [tc["name"] for tc in result.get("tool_calls", [])]
    expected_tools = scenario.get("expected_tools", [])
    forbidden = scenario.get("forbidden_tools", [])

    score = 0.0
    total = 0.0

    # Required tools called
    if expected_tools:
        unique_expected = list(dict.fromkeys(expected_tools))
        for tool in unique_expected:
            total += 1.0
            if tool in actual_tools:
                score += 1.0
            else:
                score += 0.0
    else:
        total += 1.0
        score += 1.0 if not actual_tools else 0.5

    # Forbidden tools avoided
    for tool in forbidden:
        total += 1.0
        if tool not in actual_tools:
            score += 1.0

    # Order: first expected tools should come before later ones
    if len(expected_tools) >= 2:
        total += 1.0
        order_ok = True
        for i in range(len(expected_tools) - 1):
            t1, t2 = expected_tools[i], expected_tools[i + 1]
            if t1 == t2:
                continue
            idx1 = [j for j, t in enumerate(actual_tools) if t == t1]
            idx2 = [j for j, t in enumerate(actual_tools) if t == t2]
            if idx1 and idx2 and min(idx1) > min(idx2):
                order_ok = False
                break
        score += 1.0 if order_ok else 0.3

    # Argument correctness — supports multi-order scenarios via `valid_order_ids`.
    # For single-order scenarios (the default), order_id alone defines the valid set.
    total += 1.0
    order_id = scenario.get("order_id")
    valid_order_ids = set(scenario.get("valid_order_ids", []))
    if order_id:
        valid_order_ids.add(order_id)
    target_items = scenario.get("target_items", [])
    checks = 0
    passed = 0
    for tc in result.get("tool_calls", []):
        args = tc.get("arguments", {})
        if "order_id" in args and valid_order_ids:
            checks += 1
            if args["order_id"] in valid_order_ids:
                passed += 1
        if tc["name"] == "check_resolution_policy" and "item_id" in args and target_items:
            checks += 1
            if args["item_id"] in target_items:
                passed += 1
    score += (passed / checks) if checks > 0 else 0.5

    return score / total if total > 0 else 1.0


# ---------------------------------------------------------------------------
# 3. Financial Accuracy (25%)
# ---------------------------------------------------------------------------

def score_financial_accuracy(result: dict, scenario: dict) -> float:
    expected = scenario.get("expected_amounts", {})
    if not expected:
        return 1.0

    tool_calls = result.get("tool_calls", [])
    response_text = result.get("response") or ""

    actual = {}
    # Sum totals ACROSS all calculate_resolution calls so multi-order scenarios
    # (e.g. T28: 3 orders, 3 calculate_resolution calls) get a correct total. Per-item
    # entries take the value from whichever call produced that item — last writer wins,
    # which is harmless because each item id only appears in one order's call.
    summed = {"total_resolution": 0.0, "total_restocking": 0.0, "shipping_credit": 0.0, "total_refund": 0.0}
    saw_calc = False
    for tc in tool_calls:
        if tc["name"] == "calculate_resolution" and tc.get("result"):
            try:
                res = json.loads(tc["result"])
            except (json.JSONDecodeError, TypeError):
                continue
            saw_calc = True
            summary = res.get("summary", {})
            summed["total_resolution"] += float(summary.get("total_resolution_amount") or 0)
            summed["total_restocking"] += float(summary.get("total_restocking_fees") or 0)
            summed["total_refund"] += float(summary.get("total_refund") or 0)
            # shipping_credit may be reported in summary OR as a per-item line; both add up.
            summed["shipping_credit"] += float(summary.get("total_shipping_credit") or 0)

            for item in res.get("breakdown", []):
                iid = item.get("item_id", "")
                action = item.get("action", "")
                if action == "shipping_credit":
                    # Already counted in total_shipping_credit; keep last item's amount
                    # for any per-item key reference.
                    actual["shipping_credit"] = item.get("amount", 0)
                else:
                    actual[f"{iid}_refund"] = item.get("net_refund", 0)
                    actual[f"{iid}_restocking_fee"] = item.get("restocking_fee", 0)
    if saw_calc:
        # Overlay summed totals (per-item keys retain breakdown values).
        for k, v in summed.items():
            actual.setdefault(k, v)
            # If the summed total is non-zero, prefer it over any single-call value above.
            if v:
                actual[k] = v
        # shipping_credit fallback: if no per-item entry was added but the summary had one
        actual.setdefault("shipping_credit", summed["shipping_credit"])

    if not actual:
        return _score_amounts_from_text(response_text, expected)

    tolerance = 2.0
    score = 0.0
    total = 0
    for key, exp_val in expected.items():
        if not isinstance(exp_val, (int, float)):
            continue
        total += 1
        act_val = actual.get(key)
        if act_val is not None and abs(float(act_val) - float(exp_val)) <= tolerance:
            score += 1.0
        elif act_val is not None and abs(float(act_val) - float(exp_val)) <= tolerance * 3:
            score += 0.5

    return score / total if total > 0 else 1.0


def _score_amounts_from_text(response_text, expected_amounts):
    total = 0
    found = 0
    for key, val in expected_amounts.items():
        if not isinstance(val, (int, float)) or val == 0:
            continue
        total += 1
        val_str = f"{val:.2f}"
        if val_str in response_text or f"${val_str}" in response_text:
            found += 1
    return found / total if total > 0 else 0.5


# ---------------------------------------------------------------------------
# 4. Communication Quality (10%)
# ---------------------------------------------------------------------------

def score_communication(result: dict, scenario: dict) -> float:
    response = (result.get("response") or "").lower()
    policy_points = scenario.get("policy_points", [])

    if not policy_points:
        return 1.0 if len(response) > 20 else 0.5

    score = 0.0
    total = len(policy_points)

    for point in policy_points:
        keywords = _point_to_keywords(point.lower())
        if any(kw in response for kw in keywords):
            score += 1.0

    return score / total if total > 0 else 1.0


_KW_MAP = {
    "30-day": ["30 day", "30-day"],
    "15-day": ["15 day", "15-day"],
    "45-day": ["45 day", "45-day"],
    "60-day": ["60 day", "60-day"],
    "restocking": ["restocking", "restock"],
    "defective": ["defective", "defect", "broken", "damaged"],
    "sale": ["sale", "final sale", "clearance"],
    "lost": ["lost", "missing", "never arrived"],
    "late delivery": ["late", "delayed", "shipping credit"],
    "shipping credit": ["shipping credit", "$10", "late delivery"],
    "platinum": ["platinum"],
    "gold": ["gold"],
    "halve": ["halved", "half", "7.5%", "7.5"],
    "waive": ["waived", "waive", "no restocking", "no fee", "0%"],
    "exchange": ["exchange", "swap"],
    "out of stock": ["out of stock", "unavailable", "not available"],
    "cancel": ["cancel", "cancellation"],
    "personal care": ["personal care", "opened", "hygiene"],
    "clarification": ["which item", "clarif", "specify", "which order", "could you"],
    "store credit": ["store credit"],
    "extension": ["extend", "extension", "extra", "additional 15"],
    "window": ["window", "day"],
    "deny": ["not eligible", "cannot", "unable", "denied", "unfortunately"],
    "eligible": ["eligible", "approved", "within"],
    "refund": ["refund", "money back"],
    "full refund": ["full refund"],
    "replacement": ["replace", "replacement", "reship"],
}


def _point_to_keywords(point):
    keywords = []
    for trigger, kws in _KW_MAP.items():
        if trigger in point:
            keywords.extend(kws)
    for word in point.split():
        if len(word) > 4:
            keywords.append(word)
    return keywords if keywords else [point]


# ---------------------------------------------------------------------------
# Combined scoring
# ---------------------------------------------------------------------------

def score_scenario(result: dict, scenario: dict) -> dict:
    decision = score_decision_correctness(result, scenario)
    tools = score_tool_usage(result, scenario)
    financial = score_financial_accuracy(result, scenario)
    communication = score_communication(result, scenario)

    combined = (
        decision * 0.40
        + tools * 0.25
        + financial * 0.25
        + communication * 0.10
    )

    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "difficulty": scenario.get("difficulty", "unknown"),
        "decision_correctness": round(decision, 3),
        "tool_usage": round(tools, 3),
        "financial_accuracy": round(financial, 3),
        "communication_quality": round(communication, 3),
        "combined": round(combined, 3),
    }


# ---------------------------------------------------------------------------
# Full evaluation run
# ---------------------------------------------------------------------------

def evaluate_model(model: str, scenarios: list, *, runner=None, client=None, verbose=False) -> dict:
    """Run all scenarios against a model and return aggregated results.

    Parameters
    ----------
    model : str
        The model deployment name to record on the result.
    scenarios : list
        Scenarios loaded from scenarios_train.json.
    runner : callable, optional
        A function ``(user_message, *, model, client, verbose) -> dict`` that
        returns ``{"response": str, "messages": list, "tool_calls": list}``.
        Defaults to importing ``run_agent`` from a sibling ``zava_agent``
        module (Zava lab compatibility). Pass the retail agent's
        ``main.run_agent`` to score *this* lab's agent with the same rubric.
    client : optional
        Forwarded to ``runner``. Required by the Zava ``run_agent`` for
        ``OpenAI`` clients; ignored by the retail agent's ``run_agent``.
    """
    if runner is None:
        # Backwards-compat default: import Zava lab's run_agent.
        from .zava_agent import run_agent as _run_agent, get_client  # type: ignore
        runner = _run_agent
        if client is None:
            client, model = get_client(model)

    results = []
    for i, scenario in enumerate(scenarios):
        if verbose:
            print(f"  [{i+1}/{len(scenarios)}] {scenario['name']}...")

        try:
            result = runner(
                scenario["user_message"], model=model, client=client, verbose=verbose,
            )
            scores = score_scenario(result, scenario)
            scores["error"] = None
            scores["response_preview"] = (result.get("response") or "")[:200]
            scores["actual_tools"] = [tc["name"] for tc in result.get("tool_calls", [])]
        except Exception as e:
            scores = {
                "scenario_id": scenario["id"],
                "scenario_name": scenario["name"],
                "difficulty": scenario.get("difficulty", "unknown"),
                "decision_correctness": 0.0,
                "tool_usage": 0.0,
                "financial_accuracy": 0.0,
                "communication_quality": 0.0,
                "combined": 0.0,
                "error": str(e),
                "response_preview": "",
                "actual_tools": [],
            }

        results.append(scores)

    n = len(results)
    def avg(key):
        return round(sum(r[key] for r in results) / n, 3) if n else 0

    difficulty_groups = {}
    for r in results:
        difficulty_groups.setdefault(r.get("difficulty", "unknown"), []).append(r)

    difficulty_summary = {}
    for d, group in difficulty_groups.items():
        gn = len(group)
        difficulty_summary[d] = {
            "count": gn,
            "avg_combined": round(sum(r["combined"] for r in group) / gn, 3),
            "avg_decision": round(sum(r["decision_correctness"] for r in group) / gn, 3),
            "avg_tools": round(sum(r["tool_usage"] for r in group) / gn, 3),
            "avg_financial": round(sum(r["financial_accuracy"] for r in group) / gn, 3),
            "avg_communication": round(sum(r["communication_quality"] for r in group) / gn, 3),
        }

    return {
        "model": model,
        "n_scenarios": n,
        "avg_decision_correctness": avg("decision_correctness"),
        "avg_tool_usage": avg("tool_usage"),
        "avg_financial_accuracy": avg("financial_accuracy"),
        "avg_communication_quality": avg("communication_quality"),
        "avg_combined": avg("combined"),
        "by_difficulty": difficulty_summary,
        "errors": sum(1 for r in results if r["error"]),
        "per_scenario": results,
    }


# ---------------------------------------------------------------------------
# Pretty-print
# ---------------------------------------------------------------------------

def print_eval_summary(summary: dict):
    print(f"\n{'=' * 70}")
    print(f"  Model: {summary['model']}")
    print(f"  Scenarios: {summary['n_scenarios']} | Errors: {summary['errors']}")
    print(f"{'=' * 70}")
    print(f"  Decision Correctness (40%):  {summary['avg_decision_correctness']:.1%}")
    print(f"  Tool Usage (25%):            {summary['avg_tool_usage']:.1%}")
    print(f"  Financial Accuracy (25%):    {summary['avg_financial_accuracy']:.1%}")
    print(f"  Communication Quality (10%): {summary['avg_communication_quality']:.1%}")
    print(f"  Combined Score:              {summary['avg_combined']:.1%}")
    print(f"{'=' * 70}")

    by_diff = summary.get("by_difficulty", {})
    if by_diff:
        print(f"\n  By Difficulty:")
        for d in ["easy", "medium", "hard"]:
            if d in by_diff:
                info = by_diff[d]
                print(
                    f"    {d.upper():<8} ({info['count']:>2} scenarios): "
                    f"{info['avg_combined']:.1%}  "
                    f"[dec={info['avg_decision']:.0%} "
                    f"tool={info['avg_tools']:.0%} "
                    f"fin={info['avg_financial']:.0%} "
                    f"com={info['avg_communication']:.0%}]"
                )

    header = (
        f"\n  {'ID':<5} {'Name':<38} {'Diff':<6} "
        f"{'Dec':>5} {'Tool':>5} {'Fin':>5} {'Com':>5} {'Score':>6}"
    )
    print(header)
    print(f"  {'-'*5} {'-'*38} {'-'*6} {'-'*5} {'-'*5} {'-'*5} {'-'*5} {'-'*6}")

    for r in summary["per_scenario"]:
        flag = "X" if r["error"] else ("!" if r["combined"] < 0.5 else ("~" if r["combined"] < 0.7 else "+"))
        diff_icon = {"easy": "E", "medium": "M", "hard": "H"}.get(r.get("difficulty", ""), "?")
        print(
            f"  {r['scenario_id']:<5} {r['scenario_name'][:38]:<38} "
            f"{diff_icon:<6} "
            f"{r['decision_correctness']:>4.0%} "
            f"{r['tool_usage']:>4.0%} "
            f"{r['financial_accuracy']:>4.0%} "
            f"{r['communication_quality']:>4.0%} "
            f"{r['combined']:>5.1%} {flag}"
        )
