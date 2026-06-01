---
name: work-order-preparation
description: Prepare for a work order by fetching the WO details and checking stock availability for all required parts. Use when the technician wants to get ready for a job, check if parts are available for a WO, or asks "what do I need for WO-XXX".
---

# Work Order Preparation

Use this skill when the technician wants to prepare for a work order — checking that
all required parts are available before heading to the job site.

## When to Use

- "What do I need for WO-007?"
- "Check parts for WO-003"
- "Am I ready for my next job?"
- "Prepare for WO-010"
- "Are the parts available for WO-007?"

## Tools Used by This Skill

This skill uses **two** capabilities from the Foundry Toolbox:

| Capability | Prefixed tool name |
|---|---|
| Get the work order | `work_orders___get_work_order_work_orders__work_order_id__get` |
| Check stock for the parts list | `inventory___check_stock_batch` |

### Step 0: Discover tools (REQUIRED before first call this turn)

If either tool isn't already visible in your tool list, run **one** combined `tool_search` with **`limit: 10`**:

```
tool_search({"query": "work order parts stock inventory", "limit": 10})
```

**Never** run two separate searches — one combined query with `limit: 10` returns all needed tools, and they stay callable for the rest of the turn.

## Step-by-Step Instructions

### Step 1: Fetch the Work Order

Call `work_orders___get_work_order_work_orders__work_order_id__get` via `call_tool` with `{"work_order_id": "WO-XXX"}`.

Extract the `parts_needed` list — each entry has a `part_id` and `quantity`.

If the work order has no `parts_needed`, skip to Step 3 and note that no parts
are listed for this WO.

### Step 2: Check Stock for All Parts

Call `inventory___check_stock_batch` via `call_tool` with `{"part_ids": [<all part_ids>]}` in a single call.
This returns stock status for every part at once — do NOT call `check_stock` individually.

Compare the required quantity against the available stock for each part.

Classify each part:
- ✅ **Ready** — stock ≥ required quantity
- ⚠️ **Partial** — some stock available but less than required
- ❌ **Unavailable** — out of stock

### Step 3: Present the Preparation Checklist

**CRITICAL: You MUST use this exact structure with headers and a table. Never output
a plain paragraph. This is a multi-source response that combines work order data
and inventory data — use visual separators between sections.**

```
### 📋 Work Order — WO-007

**Fiber Splice Repair** | 🟡 In Progress | 🔴 Critical
**Location:** 456 Industrial Pkwy, Building C
**Technician:** Mike Chen | **Due:** 2025-06-15

---

### 📦 Parts Checklist

| Part | Need | Available | Status | Location |
|------|------|-----------|--------|----------|
| SC Connector (FIB-012) | 2 | 342 | ✅ Ready | WH-A1 |
| Splice Tray (FIB-045) | 1 | 0 | ❌ Unavailable | — |

---

### ⚠️ Summary

**1 of 2 parts ready** — Cannot fully proceed.
FIB-045 (Splice Tray) is out of stock. Check with supply chain for alternatives.
```

**Overall status logic:**
- All parts ready → _"✅ All parts available — you're good to go!"_
- Some parts missing → _"⚠️ Cannot fully proceed — {N} part(s) unavailable."_
- No parts listed → _"ℹ️ No parts listed for this work order."_

### Step 4: Offer Next Steps

Based on the preparation result:
- All ready: _"Want me to pull up any procedures for this type of job?"_
- Parts missing: _"Want me to search for alternative parts or update the WO?"_
- No parts: _"Should I add parts to this work order?"_

## What NOT to Do

- ❌ Do not skip the stock check — always verify each part
- ❌ Do not mark a part as ready without checking actual stock
- ❌ Do not use the knowledge base for this skill (that's field-briefing)
- ❌ Do not guess part availability
