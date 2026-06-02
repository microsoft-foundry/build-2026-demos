"""One-shot helper: pick 10 diverse training scenarios for hosted-agent demo traffic."""
import json

with open('eval/training_tasks.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

priority = [
    'adversarial_policy_bypass', 'wrong_identity', 'out_of_scope', 'counter_factual_claims',
    'tool_sequence_trap', 'restocking_fee_math', 'boundary_date_arithmetic', 'sale_defective_edge',
    'multi_item_mixed_outcomes', 'late_delivery_interactions', 'personal_care_opened_sealed',
    'ambiguity_clarification', 'long_distracting_context'
]
by_cat = {}
for s in d:
    by_cat.setdefault(s['category'], []).append(s)

picks = []
for cat in priority:
    if cat in by_cat:
        s = max(by_cat[cat], key=lambda x: len(x.get('user_message', '')))
        picks.append(s)
        if len(picks) >= 10:
            break

for p in picks:
    um = p['user_message']
    print(f"[{p['category']:30s}] {p['id']}  diff={p['difficulty']}  msg={um[:80]!r}...")

with open('eval/_demo_traffic_10.json', 'w', encoding='utf-8') as f:
    json.dump(picks, f, indent=2, ensure_ascii=False)
print(f"Wrote eval/_demo_traffic_10.json  ({len(picks)} scenarios)")
