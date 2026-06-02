"""Evaluation harness v2 - calibrated for hard scenarios.

Improvements over v1:
- D1: dereferences `shipping_credit_N` pseudo-keys to real item_id
- D2: over-resolution penalty (items resolved that weren't requested)
- D3: reason-correctness sub-score (within matched action, check reason)
- D6: stricter cross-remedy credit on hard categories where remedy IS the test
- T1: argument-completeness sub-score for check_resolution_policy
- T2: redundancy penalty
- T3: sequencing strictness (calc before submit, all policy_checks before calc)
- T4: per-target-item coverage check
- T6: empty-args detection
- T7: tool argument validity vs prior tool results (catches counter-factuals)
- F1: tighter tolerance (±$0.50 full / ±$2 partial)
- F3: per-item first-correct-match instead of last-writer-wins
- C1: multi-turn comm aggregation (concat all assistant turns)
- C2: expanded _KW_MAP for hard-set policy points
- C4: per-item summary check
- C5: specific $ amount mention check
- NEW dimension weights: Decision 35% / Tool 25% / Financial 20% / Communication 20%

Backward-compatible: same `score_scenario(result, scenario)` signature as v1.
"""
import json
import re
import math

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# Categories where the remedy CHOICE is part of the answer
# (refund vs store_credit, refund vs replacement, etc).
# Cross-remedy partial credit is tightened to 0.4 (vs 0.7 elsewhere).
_REMEDY_CHOICE_CATEGORIES = frozenset({
    "sale_defective_edge",
    "personal_care_opened_sealed",
})

# Categories where the agent should refuse / clarify rather than resolve.
_REFUSAL_CATEGORIES = frozenset({
    "wrong_identity",
    "adversarial_policy_bypass",
    "out_of_scope",
    "ambiguity_clarification",
})


def _parse_tool_arg(args, key, default=None):
    if not isinstance(args, dict):
        return default
    v = args.get(key, default)
    if isinstance(v, str) and v.strip() == "":
        return default
    return v


def _normalize_tool_calls(tool_calls):
    """Ensure each tool call has arguments dict (parse if JSON string)."""
    out = []
    for tc in tool_calls or []:
        args = tc.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except (json.JSONDecodeError, TypeError):
                args = {}
        out.append({
            "name": tc.get("name", ""),
            "arguments": args if isinstance(args, dict) else {},
            "result": tc.get("result"),
        })
    return out


def _parse_calc_result(tc):
    """Parse a calculate_resolution tool call result string into dict."""
    res = tc.get("result")
    if isinstance(res, dict):
        return res
    if isinstance(res, str):
        try:
            return json.loads(res)
        except (json.JSONDecodeError, TypeError):
            return None
    return None


def _gather_assistant_text(result):
    """C1 - aggregate all assistant turns, not just the last."""
    parts = []
    final = result.get("response") or ""
    messages = result.get("messages") or []
    # Accept either "agent" (multi-turn transcript convention used by
    # run_baselines.py + run_baselines_hosted.py) OR "assistant" (chat-completions
    # native role). Without this, a runner that emits "assistant" silently scores
    # 0 on communication because parts stays empty and the fallback `final`
    # captures only the very last "you're welcome"-style agent turn.
    for m in messages:
        if isinstance(m, dict) and m.get("role") in ("agent", "assistant"):
            content = m.get("content") or ""
            if content:
                parts.append(content)
    # Fallback to final response if nothing collected.
    text = " \n ".join(parts) if parts else final
    return text.lower(), text


# ---------------------------------------------------------------------------
# 1. Decision Correctness
# ---------------------------------------------------------------------------

def score_decision_correctness(result, scenario):
    expected_actions = scenario.get("expected_actions", {})
    tool_calls = _normalize_tool_calls(result.get("tool_calls", []))
    tool_names = [tc["name"] for tc in tool_calls]
    forbidden = set(scenario.get("forbidden_tools", []))
    category = scenario.get("category", "")

    # No item-level actions expected.
    if not expected_actions:
        if forbidden:
            return 0.0 if any(t in forbidden for t in tool_names) else 1.0
        if "submit_resolution" not in tool_names and "calculate_resolution" not in tool_names:
            return 1.0
        return 0.0

    # Resolve actual per-item actions/reasons from calc tool call.
    actual = _extract_actions_v2(tool_calls)
    target_items = set(scenario.get("target_items", []))
    cross_remedy_credit = 0.4 if category in _REMEDY_CHOICE_CATEGORIES else 0.7

    response_text, _ = _gather_assistant_text(result)
    response_text = response_text.lower()
    score = 0.0
    total = 0

    for raw_key, expected in expected_actions.items():
        total += 1
        exp_action = expected.get("action", "")
        exp_reason = expected.get("reason", "")

        # D1 - dereference shipping_credit_N pseudo-keys to real item_id.
        is_shipping_credit_key = raw_key.startswith("shipping_credit")
        if is_shipping_credit_key:
            real_iid = expected.get("item_id")
            if real_iid and _has_shipping_credit_for(tool_calls, real_iid):
                score += 1.0
            else:
                # Text fallback.
                score += 0.5 if any(w in response_text for w in ["shipping credit", "$10", "late delivery"]) else 0.0
            continue

        item_id = raw_key
        if item_id in actual:
            act_action = actual[item_id]["action"]
            act_reason = actual[item_id].get("reason", "")
            if act_action == exp_action:
                # D3 - check reason if expected. Half credit if reason wrong.
                if exp_reason and act_reason and exp_reason != act_reason:
                    score += 0.85
                else:
                    score += 1.0
            elif (exp_action in ("refund", "replacement", "store_credit", "exchange")
                  and act_action in ("refund", "replacement", "store_credit", "exchange")):
                score += cross_remedy_credit
            elif exp_action == "deny" and act_action == "deny":
                score += 1.0
            continue

        # Fallback: response text scoring.
        score += _text_score_for_action(response_text, exp_action, item_id)

    base = score / total if total > 0 else 1.0

    # D2 - over-resolution penalty.
    if target_items:
        extra_items = set(actual.keys()) - target_items
        # Only penalize if extras were resolved (action != deny is fine to penalize either way).
        penalty = min(0.05 * len(extra_items), 0.30)
        base = max(0.0, base - penalty)

    return base


def _extract_actions_v2(tool_calls):
    """Returns {item_id: {action, reason}} extracted from calc calls."""
    actions = {}
    # From calc arguments (preferred - has reason field).
    for tc in tool_calls:
        if tc["name"] != "calculate_resolution":
            continue
        items = tc["arguments"].get("items", [])
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except (json.JSONDecodeError, TypeError):
                continue
        if not isinstance(items, list):
            continue
        for item in items:
            iid = item.get("item_id", "")
            act = item.get("action", "")
            reason = item.get("reason", "")
            if iid and act and act != "shipping_credit" and iid not in actions:
                actions[iid] = {"action": act, "reason": reason}

    # From calc result breakdown.
    for tc in tool_calls:
        if tc["name"] != "calculate_resolution":
            continue
        res = _parse_calc_result(tc)
        if not res:
            continue
        for item in res.get("breakdown", []):
            iid = item.get("item_id", "")
            act = item.get("action", "")
            if iid and act and act != "shipping_credit" and iid not in actions:
                actions[iid] = {"action": act, "reason": item.get("reason", "")}
    return actions


def _has_shipping_credit_for(tool_calls, real_item_id):
    """Did any calc call include a shipping_credit for this item_id?"""
    for tc in tool_calls:
        if tc["name"] != "calculate_resolution":
            continue
        items = tc["arguments"].get("items", [])
        if isinstance(items, str):
            try:
                items = json.loads(items)
            except (json.JSONDecodeError, TypeError):
                continue
        for item in items if isinstance(items, list) else []:
            if (item.get("action") == "shipping_credit"
                    and item.get("item_id") == real_item_id):
                return True
        res = _parse_calc_result(tc)
        if res:
            for line in res.get("breakdown", []):
                if (line.get("action") == "shipping_credit"
                        and line.get("item_id") == real_item_id):
                    return True
            summary = res.get("summary", {})
            if float(summary.get("total_shipping_credit") or 0) > 0:
                return True
    return False


def _text_score_for_action(text, expected_action, item_id):
    if expected_action == "deny":
        deny_words = ["deny", "denied", "not eligible", "cannot", "unable",
                      "unfortunately", "final sale", "expired", "ineligible",
                      "not returnable", "cannot be returned"]
        return 0.8 if any(w in text for w in deny_words) else 0.0
    if expected_action == "refund":
        return 0.7 if any(w in text for w in ["refund", "$", "credit back"]) else 0.0
    if expected_action == "replacement":
        return 0.7 if any(w in text for w in ["replace", "reship", "send another"]) else 0.0
    if expected_action == "exchange":
        return 0.7 if any(w in text for w in ["exchange", "swap", "different size"]) else 0.0
    if expected_action == "store_credit":
        return 0.7 if any(w in text for w in ["store credit", "credit to your account"]) else 0.0
    if expected_action == "shipping_credit":
        return 0.7 if any(w in text for w in ["shipping credit", "$10", "late delivery"]) else 0.0
    return 0.0


# ---------------------------------------------------------------------------
# 2. Tool Trajectory
# ---------------------------------------------------------------------------

# Args we consider "required for correctness" on check_resolution_policy.
_POLICY_CHECK_ARGS = ("tier", "request_type", "days_since_delivery")
_POLICY_CHECK_OPTIONAL_FLAGS = ("is_sealed", "is_defective", "is_late_delivery")


def score_tool_usage(result, scenario):
    tool_calls = _normalize_tool_calls(result.get("tool_calls", []))
    actual_tools = [tc["name"] for tc in tool_calls]
    expected_tools = scenario.get("expected_tools", [])
    forbidden = scenario.get("forbidden_tools", [])

    score = 0.0
    total = 0.0

    # Required tools called.
    if expected_tools:
        unique_expected = list(dict.fromkeys(expected_tools))
        for tool in unique_expected:
            total += 1.0
            if tool in actual_tools:
                score += 1.0
    else:
        total += 1.0
        score += 1.0 if not actual_tools else 0.5

    # Forbidden tools avoided.
    for tool in forbidden:
        total += 1.0
        if tool not in actual_tools:
            score += 1.0

    # T3 - sequencing strictness.
    seq_ok = _check_sequencing(actual_tools, expected_tools)
    total += 1.0
    score += 1.0 if seq_ok else 0.3

    # Argument correctness - order_id/item_id.
    total += 1.0
    order_id = scenario.get("order_id")
    valid_order_ids = set(scenario.get("valid_order_ids", []))
    if order_id:
        valid_order_ids.add(order_id)
    target_items = scenario.get("target_items", [])
    checks = 0
    passed = 0
    for tc in tool_calls:
        args = tc["arguments"]
        if "order_id" in args and valid_order_ids:
            checks += 1
            if args["order_id"] in valid_order_ids:
                passed += 1
        if tc["name"] == "check_resolution_policy" and "item_id" in args and target_items:
            checks += 1
            if args["item_id"] in target_items:
                passed += 1
    score += (passed / checks) if checks > 0 else 0.5

    # T1 - arg completeness on check_resolution_policy.
    total += 1.0
    score += _arg_completeness_score(tool_calls)

    # T4 - per-target-item coverage on check_resolution_policy.
    if target_items:
        total += 1.0
        score += _item_coverage_score(tool_calls, target_items)

    # T6 - empty-args detection.
    total += 1.0
    empty_arg_count = sum(
        1 for tc in tool_calls
        if tc["name"] in ("check_resolution_policy", "calculate_resolution", "submit_resolution")
        and not tc["arguments"]
    )
    if not tool_calls:
        score += 0.5
    elif empty_arg_count == 0:
        score += 1.0
    else:
        score += max(0.0, 1.0 - 0.3 * empty_arg_count)

    # T7 - tool argument validity vs prior tool results.
    total += 1.0
    score += _arg_validity_score(tool_calls)

    base = score / total if total > 0 else 1.0

    # T2 - redundancy penalty (multiplicative, capped).
    base *= _redundancy_multiplier(actual_tools, expected_tools)

    return max(0.0, min(1.0, base))


def _check_sequencing(actual, expected):
    """All policy_check before calc, calc before submit, all expected pairs in order."""
    def first_index(tool, lst):
        for i, t in enumerate(lst):
            if t == tool:
                return i
        return None

    if "calculate_resolution" in actual and "submit_resolution" in actual:
        if first_index("calculate_resolution", actual) > first_index("submit_resolution", actual):
            return False
    if "check_resolution_policy" in actual and "calculate_resolution" in actual:
        last_pol = max(i for i, t in enumerate(actual) if t == "check_resolution_policy")
        first_calc = first_index("calculate_resolution", actual)
        if last_pol > first_calc:
            return False

    # Honor expected order pairwise.
    if len(expected) >= 2:
        for i in range(len(expected) - 1):
            t1, t2 = expected[i], expected[i + 1]
            if t1 == t2:
                continue
            idx1 = first_index(t1, actual)
            idx2 = first_index(t2, actual)
            if idx1 is not None and idx2 is not None and idx1 > idx2:
                return False
    return True


def _arg_completeness_score(tool_calls):
    """Average completeness across all check_resolution_policy calls."""
    policy_calls = [tc for tc in tool_calls if tc["name"] == "check_resolution_policy"]
    if not policy_calls:
        return 0.5
    scores = []
    for tc in policy_calls:
        args = tc["arguments"]
        required_present = sum(1 for k in _POLICY_CHECK_ARGS if k in args and args[k] not in (None, ""))
        # Bonus for optional context-aware flags.
        optional_present = sum(1 for k in _POLICY_CHECK_OPTIONAL_FLAGS if k in args)
        s = required_present / len(_POLICY_CHECK_ARGS)
        s = min(1.0, s + 0.05 * optional_present)
        scores.append(s)
    return sum(scores) / len(scores)


def _item_coverage_score(tool_calls, target_items):
    """Every target_item should be checked by check_resolution_policy."""
    checked = set()
    for tc in tool_calls:
        if tc["name"] != "check_resolution_policy":
            continue
        iid = tc["arguments"].get("item_id")
        if iid:
            checked.add(iid)
    if not target_items:
        return 1.0
    hit = len(set(target_items) & checked)
    return hit / len(set(target_items))


def _redundancy_multiplier(actual, expected):
    """Penalize when total tool count exceeds 1.5x expected."""
    if not expected:
        return 1.0
    expected_count = len(expected)
    actual_count = len(actual)
    threshold = max(3, math.ceil(1.5 * expected_count))
    if actual_count <= threshold:
        return 1.0
    excess = actual_count - threshold
    return max(0.70, 1.0 - 0.05 * excess)


def _arg_validity_score(tool_calls):
    """T7 - cross-check args against prior tool results.

    Catches counter-factual claims: agent passing tier='platinum' to
    check_resolution_policy when get_order_details returned tier='gold'.
    """
    # Build truth from prior tool results.
    truth_tier = None
    truth_items_in_order = set()
    seen_order_id = None
    for tc in tool_calls:
        if tc["name"] == "get_order_details":
            res = tc.get("result")
            if isinstance(res, str):
                try:
                    res = json.loads(res)
                except (json.JSONDecodeError, TypeError):
                    res = None
            if isinstance(res, dict):
                truth_tier = (res.get("customer_tier") or res.get("tier")
                              or (res.get("customer") or {}).get("tier"))
                for li in res.get("line_items", []) or res.get("items", []):
                    iid = li.get("item_id") or li.get("line_item_id")
                    if iid:
                        truth_items_in_order.add(iid)
                seen_order_id = res.get("order_id") or seen_order_id

    if not truth_tier and not truth_items_in_order:
        return 0.7  # Not enough data, neutral.

    checks = 0
    passed = 0
    for tc in tool_calls:
        if tc["name"] != "check_resolution_policy":
            continue
        args = tc["arguments"]
        if truth_tier and "tier" in args and args["tier"]:
            checks += 1
            if str(args["tier"]).lower() == str(truth_tier).lower():
                passed += 1
        if truth_items_in_order and "item_id" in args and args["item_id"]:
            checks += 1
            if args["item_id"] in truth_items_in_order:
                passed += 1
    return (passed / checks) if checks > 0 else 0.7


# ---------------------------------------------------------------------------
# 3. Financial Accuracy
# ---------------------------------------------------------------------------

def score_financial_accuracy(result, scenario):
    expected = scenario.get("expected_amounts", {})
    if not expected:
        return 1.0

    tool_calls = _normalize_tool_calls(result.get("tool_calls", []))
    response_text = result.get("response") or ""

    actual = {}
    summed = {"total_resolution": 0.0, "total_restocking": 0.0,
              "shipping_credit": 0.0, "total_refund": 0.0}
    saw_calc = False

    for tc in tool_calls:
        if tc["name"] != "calculate_resolution":
            continue
        res = _parse_calc_result(tc)
        if not res:
            continue
        saw_calc = True
        summary = res.get("summary", {})
        summed["total_resolution"] += float(summary.get("total_resolution_amount") or 0)
        summed["total_restocking"] += float(summary.get("total_restocking_fees") or 0)
        summed["total_refund"] += float(summary.get("total_refund") or 0)
        summed["shipping_credit"] += float(summary.get("total_shipping_credit") or 0)

        for item in res.get("breakdown", []):
            iid = item.get("item_id", "")
            action = item.get("action", "")
            if action == "shipping_credit":
                actual["shipping_credit"] = item.get("amount", 0)
            else:
                # F3 - first-correct-match instead of last-writer-wins.
                refund_key = f"{iid}_refund"
                restock_key = f"{iid}_restocking_fee"
                expected_refund = expected.get(refund_key)
                expected_restock = expected.get(restock_key)
                cand_refund = float(item.get("net_refund", 0) or 0)
                cand_restock = float(item.get("restocking_fee", 0) or 0)
                if refund_key in expected and refund_key in actual:
                    if (expected_refund is not None
                        and abs(cand_refund - float(expected_refund)) < abs(float(actual[refund_key]) - float(expected_refund))):
                        actual[refund_key] = cand_refund
                else:
                    actual[refund_key] = cand_refund
                if restock_key in expected and restock_key in actual:
                    if (expected_restock is not None
                        and abs(cand_restock - float(expected_restock)) < abs(float(actual[restock_key]) - float(expected_restock))):
                        actual[restock_key] = cand_restock
                else:
                    actual[restock_key] = cand_restock

    if saw_calc:
        for k, v in summed.items():
            actual.setdefault(k, v)
            if v:
                actual[k] = v
        actual.setdefault("shipping_credit", summed["shipping_credit"])

    if not actual:
        return _score_amounts_from_text(response_text, expected)

    # F1 - tightened tolerance.
    full_tol = 0.50
    partial_tol = 2.00
    score = 0.0
    total = 0
    for key, exp_val in expected.items():
        if not isinstance(exp_val, (int, float)):
            continue
        total += 1
        act_val = actual.get(key)
        if act_val is None:
            continue
        diff = abs(float(act_val) - float(exp_val))
        if diff <= full_tol:
            score += 1.0
        elif diff <= partial_tol:
            score += 0.5
        elif diff <= partial_tol * 3:
            score += 0.2

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
# 4. Communication Quality
# ---------------------------------------------------------------------------

# C2 - expanded keyword map for hard-set policy points.
_KW_MAP = {
    # Existing
    "30-day": ["30 day", "30-day"],
    "15-day": ["15 day", "15-day"],
    "45-day": ["45 day", "45-day"],
    "60-day": ["60 day", "60-day"],
    "restocking": ["restocking", "restock"],
    "defective": ["defective", "defect", "broken", "damaged", "malfunction"],
    "sale": ["sale", "final sale", "clearance", "non-returnable"],
    "lost": ["lost", "missing", "never arrived", "did not arrive"],
    "late delivery": ["late", "delayed", "shipping credit"],
    "shipping credit": ["shipping credit", "$10", "late delivery"],
    "platinum": ["platinum"],
    "gold": ["gold"],
    "halve": ["halved", "half", "7.5%", "7.5"],
    "waive": ["waived", "waive", "no restocking", "no fee", "0%"],
    "exchange": ["exchange", "swap"],
    "out of stock": ["out of stock", "unavailable", "not available"],
    "cancel": ["cancel", "cancellation"],
    "personal care": ["personal care", "opened", "hygiene", "sealed", "unopened"],
    "clarification": ["which item", "clarif", "specify", "which order",
                      "could you", "can you confirm", "please confirm",
                      "to help", "need more"],
    "store credit": ["store credit"],
    "extension": ["extend", "extension", "extra", "additional"],
    "window": ["window", "day", "within", "past the"],
    "deny": ["not eligible", "cannot", "unable", "denied", "unfortunately",
             "i'm sorry", "we're unable", "not able"],
    "eligible": ["eligible", "approved", "within"],
    "refund": ["refund", "money back"],
    "full refund": ["full refund"],
    "replacement": ["replace", "replacement", "reship"],
    # NEW for hard set (C2 expansion)
    "ownership": ["ownership", "not on your", "not your order", "different account",
                  "doesn't belong", "no record"],
    "wrong identity": ["confirm your identity", "different name", "no record",
                       "i don't see", "verify"],
    "out of scope": ["unable to", "cannot help with", "doesn't fall under",
                     "outside", "not something", "not within"],
    "address change": ["address", "update", "change", "shipping address"],
    "which order": ["which order", "order id", "order number", "more than one"],
    "item mismatch": ["that item", "not on", "no record", "different"],
    "actual tier": ["our records show", "you are gold", "you are standard",
                    "actually a", "based on your account"],
    "actual price": ["actual price", "listed at", "shows as", "according to"],
    "loyalty": ["loyalty", "account", "tier"],
    "calculate_resolution required": ["i'll need to calculate", "let me calculate",
                                       "calculating", "quote"],
    "workflow": ["first", "then", "next", "after that", "let me check"],
    "policy": ["policy", "per our", "according to our"],
    "no identity": ["confirm your", "verify your", "your email",
                    "could you share", "more information"],
    "email typo": ["typo", "no record", "didn't find", "couldn't find",
                   "spelling", "double check"],
    "confirm identity": ["confirm", "verify", "email", "identify"],
    "flat $10": ["$10", "10 dollar", "ten dollar"],
    "doesn't fit": ["fit", "doesn't fit", "size", "wrong size"],
    "no longer needed": ["no longer needed", "changed mind", "don't need"],
    "no return requested": ["did not request", "no return", "didn't ask"],
    "processing": ["processing", "submit", "submitted"],
    "customer-caused damage": ["customer", "user error", "not eligible", "caused"],
    "exactly 2 days": ["2 day", "two day"],
    "either or": ["or", "either", "you can choose"],
    "new order": ["place a new", "new order", "fresh order"],
    "delivered": ["delivered", "arrived", "received"],
    "standard": ["standard"],
    "apparel": ["apparel", "clothing", "sweater", "jacket", "pants", "shirt"],
    "electronics": ["electronics", "headphones", "keyboard", "kettle", "lamp", "phone"],
    "sealed": ["sealed", "unopened", "intact"],
    "opened": ["opened", "used", "broken seal"],
    "all-or-nothing": ["all", "both", "every"],
}


def score_communication(result, scenario):
    response_lower, response_orig = _gather_assistant_text(result)
    policy_points = scenario.get("policy_points", [])

    if not policy_points:
        return 1.0 if len(response_lower) > 20 else 0.5

    score = 0.0
    total = len(policy_points)
    for point in policy_points:
        keywords = _point_to_keywords(point.lower())
        if any(kw in response_lower for kw in keywords):
            score += 1.0
    base = score / total if total > 0 else 1.0

    # C4 - per-item summary check.
    target_items = scenario.get("target_items", [])
    if target_items and len(target_items) > 1:
        item_mentions = sum(1 for iid in target_items if iid.lower() in response_lower)
        item_coverage = item_mentions / len(target_items)
        base = 0.75 * base + 0.25 * item_coverage

    # C5 - specific $ amount mention.
    expected_amounts = scenario.get("expected_amounts", {})
    key_amount = expected_amounts.get("total_resolution") or expected_amounts.get("total_refund")
    if key_amount and float(key_amount) > 0:
        amount_str = f"{float(key_amount):.2f}"
        if amount_str in response_orig or amount_str.rstrip("0").rstrip(".") in response_orig:
            base = min(1.0, base + 0.10)
        else:
            base = max(0.0, base - 0.10)

    return max(0.0, min(1.0, base))


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

# Phase 1 weights (no LLM judges yet).
W_DECISION = 0.35
W_TOOL = 0.25
W_FINANCIAL = 0.20
W_COMMUNICATION = 0.20


def score_scenario(result, scenario):
    decision = score_decision_correctness(result, scenario)
    tools = score_tool_usage(result, scenario)
    financial = score_financial_accuracy(result, scenario)
    communication = score_communication(result, scenario)
    combined = (
        decision * W_DECISION + tools * W_TOOL
        + financial * W_FINANCIAL + communication * W_COMMUNICATION
    )
    return {
        "scenario_id": scenario["id"],
        "scenario_name": scenario["name"],
        "difficulty": scenario.get("difficulty", "unknown"),
        "category": scenario.get("category", ""),
        "decision_correctness": round(decision, 3),
        "tool_usage": round(tools, 3),
        "financial_accuracy": round(financial, 3),
        "communication_quality": round(communication, 3),
        "combined": round(combined, 3),
    }


# ---------------------------------------------------------------------------
# Full eval (matches v1 API)
# ---------------------------------------------------------------------------

def evaluate_model(model, scenarios, *, runner=None, client=None, verbose=False):
    if runner is None:
        raise ValueError("evaluate_v2.evaluate_model requires runner=")

    results = []
    for i, scenario in enumerate(scenarios):
        if verbose:
            print(f"  [{i+1}/{len(scenarios)}] {scenario['name']}...", flush=True)
        try:
            result = runner(scenario["user_message"], model=model,
                            client=client, verbose=verbose)
            scores = score_scenario(result, scenario)
            scores["error"] = None
            scores["response_preview"] = (result.get("response") or "")[:200]
            scores["actual_tools"] = [tc["name"] for tc in result.get("tool_calls", [])]
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
            }
        results.append(scores)

    n = len(results)
    def avg(key):
        return round(sum(r[key] for r in results) / n, 3) if n else 0

    difficulty_groups = {}
    for r in results:
        difficulty_groups.setdefault(r.get("difficulty", "unknown"), []).append(r)
    category_groups = {}
    for r in results:
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

    return {
        "model": model, "scorer_version": "v2",
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


def print_eval_summary(summary):
    print(f"\n{'=' * 70}")
    print(f"  Model: {summary['model']}  (scorer v2)")
    print(f"  Scenarios: {summary['n_scenarios']} | Errors: {summary['errors']}")
    print(f"{'=' * 70}")
    print(f"  Decision Correctness ({W_DECISION:.0%}):  {summary['avg_decision_correctness']:.1%}")
    print(f"  Tool Trajectory      ({W_TOOL:.0%}):  {summary['avg_tool_usage']:.1%}")
    print(f"  Financial Accuracy   ({W_FINANCIAL:.0%}):  {summary['avg_financial_accuracy']:.1%}")
    print(f"  Communication        ({W_COMMUNICATION:.0%}):  {summary['avg_communication_quality']:.1%}")
    print(f"  Combined Score:              {summary['avg_combined']:.1%}")
    print(f"{'=' * 70}")
    by_cat = summary.get("by_category", {})
    if by_cat:
        print("\n  By Category:")
        for cat in sorted(by_cat.keys()):
            info = by_cat[cat]
            print(f"    {cat:<30} ({info['count']:>2}): {info['avg_combined']:.1%}")
