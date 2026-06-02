"""Build a clean, explanatory demo notebook for FT distillation.

Outputs: demo_distillation.ipynb

The notebook walks through the distillation cycle end-to-end in a single linear
narrative, then closes with a live FT-agent showcase that loads pre-generated
conversations from results/eval_result/demo_transcripts.json.

This builder script is idempotent: re-running it overwrites the .ipynb.
"""
from __future__ import annotations

import json
from pathlib import Path

NB_DIR = Path(__file__).resolve().parents[1]
OUT = NB_DIR / "demo_distillation.ipynb"


def md(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "metadata": {},
        "source": text.splitlines(keepends=True) or [""],
    }


def code(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": text.splitlines(keepends=True) or [""],
    }


CELLS: list[dict] = []

# =====================================================================
# 0. Title + overview
# =====================================================================
CELLS.append(md("""# Distilling a production retail agent into a small model

This notebook walks step-by-step through one full **distillation cycle**: taking a
small, cheap model that struggles on hard customer-support scenarios and lifting
its quality to near-teacher level by fine-tuning on traces from the production
agent.

**The cast**
| Role | Model | Why |
|---|---|---|
| **Student** | `gpt-4.1-nano` | Small, cheap, fast — what we want in production. Struggles on hard scenarios out of the box. |
| **Teacher** | `gpt-5.5` (running inside the production retail agent) | Strong reasoning. Produces high-quality traces we can learn from. |
| **Fine-tuned student** | `gpt-4.1-nano` fine-tuned on teacher traces | The hoped-for outcome — student-cost, teacher-quality. |

**The cycle**
1. **Score** — define a single number per scenario so we can compare runs.
2. **Baseline** — measure student and teacher on the same 100 hard scenarios.
3. **Harvest** — turn the teacher's recent production traffic into SFT examples.
4. **Fine-tune** — train the student on those examples.
5. **Re-measure** — re-run the fine-tuned student on the same scenarios and a held-out validation set.
6. **Showcase** — drive the fine-tuned model through 4 representative scenarios end-to-end so you can see the post-training behavior.

All quality numbers are reported as **pass^k @ 0.70**: the fraction of scenarios
where the model meets the quality bar (combined score ≥ 0.70) on **all k of k**
independent attempts. We run 3 passes per role, so `pass^1 / pass^2 / pass^3` are
all reported. `pass^3` is the strictest — every attempt has to pass. We do **not**
report mean combined scores: averaging a 4-dimension score hides whether the
model is reliably crossing the bar or whether it's noisy.
"""))

# =====================================================================
# 1. Setup
# =====================================================================
CELLS.append(md("""## 1. Setup

Paths, environment, and one helper. Nothing here calls a model.
"""))

CELLS.append(code("""import json
import os
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

NB_DIR = Path.cwd()
EVAL_DIR = NB_DIR / "eval"
RESULTS_DIR = NB_DIR / "results" / "eval_result"

load_dotenv(NB_DIR / ".env")

STUDENT_MODEL  = os.environ.get("STUDENT_MODEL", "gpt-4.1-nano")
TEACHER_MODEL  = os.environ.get("TEACHER_MODEL", "gpt-5.5")
FT_MODEL       = os.environ.get("FT_MODEL",      "gpt-4.1-nano-demo1")

print(f"student model: {STUDENT_MODEL}")
print(f"teacher model: {TEACHER_MODEL}")
print(f"fine-tuned:    {FT_MODEL}")
print(f"results live in {RESULTS_DIR.relative_to(NB_DIR)}")
"""))

# =====================================================================
# 2. The scenarios
# =====================================================================
CELLS.append(md("""## 2. The evaluation scenarios

Each scenario is a multi-turn customer conversation with a ground-truth
expected resolution (refund, replace, deny, or clarify). The scenarios are
sorted into **categories** — `long_distracting_context`, `restocking_fee_math`,
`multi_item_mixed_outcomes`, `out_of_scope`, etc. — so we can see which
categories are causing the most pain.

- **Training tasks** (`eval/training_tasks.json`, 80 scenarios) — used to harvest fine-tuning examples.
- **Validation tasks** (`eval/eval_tasks.json`, 20 scenarios) — held out; the fine-tuned model never sees these during training.
"""))

CELLS.append(code("""train_scenarios = json.loads((EVAL_DIR / "training_tasks.json").read_text(encoding="utf-8"))
val_scenarios   = json.loads((EVAL_DIR / "eval_tasks.json").read_text(encoding="utf-8"))

print(f"training tasks:   {len(train_scenarios)}")
print(f"validation tasks: {len(val_scenarios)}")
print()
print("Example scenario:")
ex = train_scenarios[0]
print(f"  id:         {ex['id']}")
print(f"  category:   {ex['category']}")
print(f"  user_msg:   {ex['user_message'][:120]}...")
print(f"  expected:   {ex['expected_resolution_summary']}")
"""))

# =====================================================================
# 3. Scoring
# =====================================================================
CELLS.append(md("""## 3. How a scenario is scored

A scorer (`eval/evaluate_v2.py`) grades the agent on four dimensions and combines them into a single 0–1 number. A scenario **passes** when its combined score reaches **0.70**.

| Dimension | Weight | What it checks |
|---|---:|---|
| **Decision correctness** | 35% | Right action and reason per line item, no over-resolution |
| **Tool trajectory**      | 25% | Right tools called in the right order; no forbidden tools |
| **Financial accuracy**   | 20% | Refund / restocking amounts within tolerance |
| **Communication**        | 20% | Specific amounts, per-item summary, policy keywords |

The weights and the 0.70 bar are calibrated on a separate set of scenarios; this
notebook reuses them.

The cell below runs the scorer **live** on one real cached conversation (the
FT model on validation scenario `HE027`, a restocking-fee math case) so the
dimension breakdown is concrete, not abstract.
"""))

CELLS.append(code("""import sys
sys.path.insert(0, str(EVAL_DIR))
from evaluate_v2 import score_scenario  # noqa: E402

# Pull one cached conversation (FT model on validation/HE027) and the full
# scenario spec, then score it the same way the eval pipeline does.
demo_blob = json.loads((RESULTS_DIR / "demo_transcripts.json").read_text(encoding="utf-8"))
demo = demo_blob["demos"][0]                # validation sid=HE027, restocking_fee_math
scenarios = json.loads((EVAL_DIR / "eval_tasks.json").read_text(encoding="utf-8"))
scenario = next(s for s in scenarios if s["name"] == demo["name"])

# evaluate_v2.score_scenario expects a result dict with:
#   response: final assistant text
#   messages: list of {role, content} turns ("agent" or "assistant" both accepted)
#   tool_calls: list of {name, arguments, result}
ft = demo["ft"]
result = {
    "response":   ft["final_response"],
    "messages":   ft["transcript"],
    "tool_calls": ft["tool_calls"],
}

scores = score_scenario(result, scenario)

print(f"scenario:  {scenario['name']}  ({scenario['category']})")
print(f"customer:  {scenario['user_message'][:90]}...")
print(f"model:     {demo_blob['ft_model']}")
print(f"tools run: {[tc['name'] for tc in ft['tool_calls']]}")
print()
print(f"  decision_correctness  : {scores['decision_correctness']:.3f}  (weight 0.35)")
print(f"  tool_usage            : {scores['tool_usage']:.3f}  (weight 0.25)")
print(f"  financial_accuracy    : {scores['financial_accuracy']:.3f}  (weight 0.20)")
print(f"  communication_quality : {scores['communication_quality']:.3f}  (weight 0.20)")
print(f"  ------------------------------")
print(f"  combined              : {scores['combined']:.3f}    "
      f"{'PASS' if scores['combined'] >= 0.70 else 'FAIL'} @ tau=0.70")
"""))

# =====================================================================
# 4. Helper: load cached results
# =====================================================================
CELLS.append(md("""## 4. Loading the cached eval runs

Every cell in the 3×3×2 evaluation matrix (3 roles × 3 passes × 2 sets) is on
disk under `results/eval_result/{train,validation}/`. The notebook does not
re-run the eval — it loads the cached JSON.
"""))

CELLS.append(code("""def _file(role: str, k: int) -> str:
    if role == "student":
        return f"baseline__mt__student__{STUDENT_MODEL}.v2.pass{k}.json"
    if role == "ft":
        return f"baseline__mt__ft__{FT_MODEL}.v2.pass{k}.json"
    # teacher's deployment is reported under its hosted agent name
    return "baseline__mt__teacher__demo1-retail-agent-langraph-responses.v2.pass{k}.json".format(k=k)


def load_runs(set_name: str, role: str) -> list[dict]:
    runs = []
    for k in (1, 2, 3):
        path = RESULTS_DIR / set_name / _file(role, k)
        runs.append(json.loads(path.read_text(encoding="utf-8")))
    return runs


# Smoke-test: how many rows in each cell?
for set_name in ("train", "validation"):
    for role in ("student", "teacher", "ft"):
        ns = [len(r["per_scenario"]) for r in load_runs(set_name, role)]
        print(f"  {set_name:<10} {role:<8} pass1/2/3 sizes: {ns}")
"""))

# =====================================================================
# 5. Pass^k aggregator
# =====================================================================
CELLS.append(md("""## 5. The pass^k aggregator

`pass^k @ tau` for a scenario is 1 if every one of its k passes scored at or above `tau`,
else 0. We average across all scenarios to get the headline number.
"""))

CELLS.append(code("""TAU = 0.70

def pass_k_at(set_name: str, role: str, tau: float = TAU) -> dict:
    runs = load_runs(set_name, role)
    by_sid = defaultdict(list)
    for run in runs:
        for ps in run["per_scenario"]:
            by_sid[ps["scenario_id"]].append(ps.get("combined", 0.0))
    n = len(by_sid)
    p1 = sum(1 for scores in by_sid.values() if scores[0] >= tau) / n
    p2 = sum(1 for scores in by_sid.values() if all(s >= tau for s in scores[:2])) / n
    p3 = sum(1 for scores in by_sid.values() if all(s >= tau for s in scores[:3])) / n
    return {"n": n, "pass^1": p1, "pass^2": p2, "pass^3": p3}


print(f"{'set':<11} {'role':<8} {'n':>3}  {'p^1':>5}  {'p^2':>5}  {'p^3':>5}")
print("-" * 44)
for set_name in ("train", "validation"):
    for role in ("student", "teacher", "ft"):
        s = pass_k_at(set_name, role)
        print(f"{set_name:<11} {role:<8} {s['n']:>3}  "
              f"{s['pass^1']:>5.2f}  {s['pass^2']:>5.2f}  {s['pass^3']:>5.2f}")
"""))

# =====================================================================
# 6. Headline lift
# =====================================================================
CELLS.append(md("""## 6. Headline: how much did fine-tuning lift the student?

The interesting comparison is **student vs fine-tuned student**: same base model,
same cost-per-token. The teacher is shown as a reference ceiling.

Two metrics per pass^k row:

- **ft lift** = `ft - student`, in percentage points. Absolute gain from fine-tuning.
- **headroom recovered** = `(ft - student) / (teacher - student)`. Fraction of the
  student → teacher gap that fine-tuning closed. 1.000 means FT matched the teacher;
  values >1.000 mean FT exceeded it. Undefined when the student already matches the
  teacher (`n/a`).
"""))

CELLS.append(code("""def lift_table(set_name: str) -> None:
    s = pass_k_at(set_name, "student")
    f = pass_k_at(set_name, "ft")
    t = pass_k_at(set_name, "teacher")
    print(f"\\n=== {set_name.upper()} ({s['n']} scenarios) ===")
    print(f"{'metric':<8} {'student':>8} {'ft':>8} {'teacher':>8}   {'ft lift':>9}   {'headroom':>10}")
    for key in ("pass^1", "pass^2", "pass^3"):
        ds_pp = (f[key] - s[key]) * 100
        gap = t[key] - s[key]
        headroom = f"{(f[key] - s[key]) / gap:>+10.3f}" if gap > 0 else f"{'n/a':>10}"
        print(f"{key:<8} {s[key]:>8.2f} {f[key]:>8.2f} {t[key]:>8.2f}   {ds_pp:>+7.1f}pp   {headroom}")


lift_table("train")
lift_table("validation")
"""))

# =====================================================================
# 6b. Visual: grouped bar chart of pass^k for student / FT / teacher
# =====================================================================
CELLS.append(md("""### Visualizing the lift

The same numbers as a grouped bar chart, so the **student &rarr; FT** uplift is
visually obvious against the teacher ceiling.
"""))

CELLS.append(code("""import matplotlib.pyplot as plt
import numpy as np

ROLES   = ("student", "ft", "teacher")
LABELS  = {"student": "Student (baseline)",
           "ft":      "FT student (after distillation)",
           "teacher": "Teacher (reference ceiling)"}
COLORS  = {"student": "#c0c4cc",  # neutral grey
           "ft":      "#1f77b4",  # blue, the hero
           "teacher": "#2ca02c"}  # green ceiling
METRICS = ("pass^1", "pass^2", "pass^3")
SETS    = (("train", "Train (80 scenarios)"),
           ("validation", "Validation / held-out (20 scenarios)"))

fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
x = np.arange(len(METRICS))
w = 0.26

for ax, (set_name, set_title) in zip(axes, SETS):
    scores = {role: pass_k_at(set_name, role) for role in ROLES}
    for i, role in enumerate(ROLES):
        vals = [scores[role][m] for m in METRICS]
        bars = ax.bar(x + (i - 1) * w, vals, w,
                      label=LABELS[role], color=COLORS[role],
                      edgecolor="white", linewidth=0.6,
                      zorder=3)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width()/2, v + 0.012,
                    f"{v:.2f}", ha="center", va="bottom",
                    fontsize=9, color="#333", zorder=4)

    # FT uplift annotation: arrow from student to ft at pass^3
    s3 = scores["student"]["pass^3"]
    f3 = scores["ft"]["pass^3"]
    t3 = scores["teacher"]["pass^3"]
    gap3 = t3 - s3
    if f3 > s3:
        x_anchor = x[-1] + w * 0.4
        ax.annotate("", xy=(x_anchor, f3), xytext=(x_anchor, s3),
                    arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.8),
                    zorder=5)
        if gap3 > 0:
            headroom_pct = (f3 - s3) / gap3 * 100
            label = f"{headroom_pct:.1f}%\\nheadroom\\nrecovered"
        else:
            label = f"+{(f3-s3)*100:.0f}pp"
        ax.text(x_anchor + 0.04, (s3 + f3)/2,
                label, color="#d62728",
                fontsize=9, fontweight="bold", va="center", zorder=5)

    ax.set_xticks(x)
    ax.set_xticklabels(METRICS)
    ax.set_title(set_title, fontsize=12, pad=10)
    ax.set_ylim(0, 1.08)
    ax.set_yticks(np.linspace(0, 1.0, 6))
    ax.set_yticklabels([f"{v:.0%}" for v in np.linspace(0, 1.0, 6)])
    ax.grid(axis="y", linestyle="--", alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

axes[0].set_ylabel(f"pass^k @ tau={TAU}", fontsize=11)
# Legend goes to the right of the figure so it doesn't overlap the bars
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="center left",
           bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=10)
fig.suptitle("Fine-tuning lifts the student toward the teacher ceiling",
             fontsize=14, fontweight="bold", y=1.02)
fig.tight_layout(rect=(0, 0, 0.84, 1))
plt.show()
"""))

# =====================================================================
# 7. The distillation pipeline — narrated with concrete artifacts
# =====================================================================
CELLS.append(md("""## 7. How the SFT training data was generated

The fine-tuning data is just **the teacher's own conversation traces**, captured
from the deployed production agent and turned into chat-completion training
examples. No human labeling, no synthetic prompts. Four steps:

### 7a. Drive traffic against the deployed teacher
The teacher (`gpt-5.5`) is wrapped inside a deployed Foundry agent
(`retail-agent-langgraph`) — the same agent customers would hit in production.
We pointed `scripts/drive_teacher_traffic.py` at the hosted endpoint and replayed
the 80 training scenarios through it, several times with different random
seeds. Two design choices matter:

- **Literal-replay first turn.** The customer's opening message is the scenario's
  `user_message` verbatim — adversarial framing intact ("I shouldn't pay a
  restocking fee because the keys aren't what I expected"). The persona simulator
  only kicks in for follow-up turns. This preserves the hard adversarial context
  that a vague "Hi I need help with my keyboard" would strip.
- **No scoring.** The driver only needs traces flowing through App Insights;
  scoring happens later, in a separate eval pass.

### 7b. Harvest traces from telemetry & shape into SFT JSONL

The Foundry agent emits OpenTelemetry to App Insights — one span per tool call,
one span per assistant message. Rather than write our own KQL+join job, we use
the Foundry `DataGenerationJob` API which does exactly this server-side: it
pulls a time window of traces, joins spans by conversation ID, reshapes each
conversation into a chat-completion training example, and emits a train/valid
JSONL pair ready for fine-tuning. Each example is one line:

```
[
  {"role": "system",    "content": "<agent_policy.md, the full instructions>"},
  {"role": "user",      "content": "<customer's opening turn>"},
  {"role": "assistant", "content": null, "tool_calls": [...]},
  {"role": "tool",      "content": "<tool result JSON>",       "tool_call_id": "..."},
  {"role": "assistant", "content": "<reply or null + more tool_calls>"},
  ...
]
```

**The actual code we ran** (from `demo1_agent_distillation.ipynb` §10.1–§10.4 —
shown here as reference; not re-executed in this walkthrough because it requires
Azure login and overwrites the cached SFT data the FT model was trained on):

```python
# §7b.1 — connect to the Foundry project and pick the window
from datetime import datetime, timedelta, timezone
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

ENDPOINT     = "https://smamgain-tip-aifoundry.services.ai.azure.com/api/projects/smamgain-tip-aiproject"
HOSTED_AGENT = "retail-agent-langgraph"
SFT_DIR      = NB_DIR / "results" / "sft_demo1_last24h"
SFT_DIR.mkdir(parents=True, exist_ok=True)

end_dt   = datetime.now(timezone.utc)
start_dt = end_dt - timedelta(hours=24)             # last 24h of teacher traffic

project_client = AIProjectClient(endpoint=ENDPOINT,
                                 credential=DefaultAzureCredential(),
                                 allow_preview=True)
conn = project_client.telemetry.get_application_insights_connection_string()
assert conn, "Project has no App Insights resource attached."
```

```python
# §7b.2 — submit the supervised-finetuning datagen job
from azure.ai.projects.models import (
    DataGenerationJob, DataGenerationJobInputs, DataGenerationJobScenario,
    TracesDataGenerationJobOptions, TracesDataGenerationJobSource,
)

options = TracesDataGenerationJobOptions(max_samples=200, train_split=0.8)
source  = TracesDataGenerationJobSource(agent_name=HOSTED_AGENT,
                                        start_time=int(start_dt.timestamp()))

job = project_client.beta.datasets.create_generation_job(DataGenerationJob(
    inputs=DataGenerationJobInputs(
        name=f"demo1-sft-{int(time.time())}",
        scenario=DataGenerationJobScenario.SUPERVISED_FINETUNING,
        sources=[source], options=options,
    ),
))
print(f"Job created: {job.id} ({job.status})")
```

```python
# §7b.3 — poll until terminal (usually 1–3 minutes for a 24h window)
from azure.ai.projects.models import JobStatus
TERMINAL = {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED}
while job.status not in TERMINAL:
    job = project_client.beta.datasets.get_generation_job(job.id)
    time.sleep(10)
assert job.status == JobStatus.SUCCEEDED, f"datagen failed: {job!r}"
```

```python
# §7b.4 — download outputs (training + validation JSONL + tool_definitions.json)
from azure.ai.projects.models import DataGenerationJobOutputType
aoai = project_client.get_openai_client()
for output in job.result.outputs:
    if output.type != DataGenerationJobOutputType.FILE:
        continue
    dest = SFT_DIR / (output.filename or f"{output.id}.jsonl")
    dest.write_bytes(aoai.files.content(output.id).content)
    print(f"  {output.id} -> {dest.name}  ({dest.stat().st_size:,} bytes)")
```

The worker then runs a small `dedup_and_clean()` pass on the downloaded JSONL
(trace-level dedup by canonical key-map, within-example message dedup, truncate
unanswered tool calls, keep refusal-style examples, inject system prompt + tool
schema) — full implementation in `demo1_agent_distillation.ipynb` §10.5. Output
is `train_sft.jsonl` + `valid_sft.jsonl`, ready for `fine_tuning.jobs.create`.

### 7c. Submit the fine-tuning job
The cleaned `train_sft.jsonl` + `valid_sft.jsonl` were uploaded as a
supervised-finetuning job against `gpt-4.1-nano` on the Sweden Azure OpenAI
resource. The job took roughly 30 minutes and produced a new deployment
(`gpt-4.1-nano-demo1`).

### 7d. Re-evaluate
The full 3×3×2 matrix was re-run against the new deployment with identical
seeds, producing the cached files §4 loaded.

Below: a peek at one actual teacher trace from the cached eval, to make the
"a conversation = a training example" pattern concrete.
"""))

CELLS.append(code("""# Peek at a single teacher conversation from the cached eval data.
# (The eval runner stores the same shape we'd harvest from telemetry.)
teacher_pass1 = load_runs("train", "teacher")[0]
sample = next(ps for ps in teacher_pass1["per_scenario"] if ps.get("transcript"))

print(f"scenario_id={sample['scenario_id']}  category={sample['category']}")
print(f"combined_score={sample['combined']:.3f}")
print(f"rounds={sample['rounds']}  tool_calls={len(sample.get('tool_calls') or [])}")
print()
print("--- conversation turns ---")
for i, turn in enumerate(sample["transcript"][:6]):
    content = (turn.get("content") or "").strip().replace("\\n", " ")
    print(f"  [{turn['role']:<8}] {content[:140]}")
print()
print("--- tool calls (in order) ---")
for tc in (sample.get("tool_calls") or [])[:6]:
    args = tc.get("arguments", {})
    result = (tc.get("result") or "")[:100].replace("\\n", " ")
    print(f"  {tc['name']}({json.dumps(args)})")
    print(f"    -> {result}...")
"""))

# =====================================================================
# 8. Live showcase — student vs fine-tuned, side by side
# =====================================================================
CELLS.append(md("""## 8. Side-by-side showcase — student vs fine-tuned model

To build intuition for **what changed** behaviorally, we picked four scenarios
where the FT model substantially outperformed the student in the eval, then
re-ran each scenario twice live — once against the **deployed student endpoint**
(`gpt-4.1-nano`) and once against the **deployed fine-tuned endpoint**
(`gpt-4.1-nano-demo1`). Both runs used the same customer simulator and the same
opening user message; only the agent model differs.

The transcripts in this section were generated by
`scripts/generate_demo_conversations.py` and cached in
`results/eval_result/demo_transcripts.json` — the notebook never hits either
endpoint at render time.
"""))

CELLS.append(code("""DEMOS_PATH = RESULTS_DIR / "demo_transcripts.json"
demos = json.loads(DEMOS_PATH.read_text(encoding="utf-8"))
print(f"Loaded {len(demos['demos'])} demo conversations")
print(f"Student model: {demos['student_model']}")
print(f"FT model:      {demos['ft_model']}")
print(f"Generated:     {demos['generated_at']}")
"""))

# =====================================================================
# 8b. Renderer
# =====================================================================
CELLS.append(md("""### Rendering helper

Each demo has a `student` and an `ft` block, each with its own transcript and
tool calls. The helper renders the scenario context once, then the two
conversations stacked (student first, then FT) for easy visual comparison.
"""))

CELLS.append(code("""from IPython.display import Markdown, display


def _fmt_args(args) -> str:
    if isinstance(args, dict):
        return ", ".join(f"{k}={json.dumps(v, default=str)}" for k, v in args.items())
    return str(args)


def _render_one_side(label: str, model_name: str, side: dict) -> list[str]:
    lines: list[str] = []
    n_tools = len(side.get("tool_calls") or [])
    tool_names = [tc.get("name") for tc in (side.get("tool_calls") or [])]
    lines.append(f"#### {label} — `{model_name}`")
    lines.append(f"_Rounds: {side.get('rounds')}  •  Tool calls: {n_tools}  "
                 f"•  Stop: `{side.get('stop_reason')}`_")
    lines.append("")
    if tool_names:
        lines.append(f"**Tool sequence:** {' → '.join(f'`{t}`' for t in tool_names)}")
        lines.append("")
    lines.append("<details><summary><b>Full transcript</b></summary>")
    lines.append("")
    for turn in side.get("transcript", []):
        speaker = "👤 **Customer**" if turn["role"] == "customer" else "🤖 **Agent**"
        content = (turn.get("content") or "").strip()
        lines.append(f"{speaker}:")
        lines.append("")
        for line in (content.splitlines() or [""]):
            lines.append(f"> {line}")
        lines.append("")
    lines.append("</details>")
    lines.append("")
    return lines


def render_demo(demo: dict, diagnosis_md: str = "") -> None:
    md_lines: list[str] = []
    md_lines.append(f"### {demo['set']}/{demo['scenario_id']} — {demo['headline']}")
    md_lines.append(f"**Category:** `{demo['category']}`")
    md_lines.append("")
    md_lines.append(f"**Customer opens with:**")
    md_lines.append(f"> {demo['scenario']['user_message']}")
    md_lines.append("")
    md_lines.append(f"**Expected resolution:** {demo['scenario']['expected_resolution_summary']}")
    if demo['scenario'].get('expected_amounts'):
        ea = demo['scenario']['expected_amounts']
        if 'total_refund' in ea:
            md_lines.append(f"**Expected refund:** ${ea['total_refund']:.2f}")
    md_lines.append(f"**Expected tools:** `{demo['scenario'].get('expected_tools')}`")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.extend(_render_one_side("Before fine-tuning (student)", demos['student_model'], demo['student']))
    md_lines.extend(_render_one_side("After fine-tuning (FT)",       demos['ft_model'],      demo['ft']))
    if diagnosis_md:
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("#### Why the student failed and the FT model succeeded")
        md_lines.append("")
        md_lines.append(diagnosis_md)
    display(Markdown("\\n".join(md_lines)))
"""))

# =====================================================================
# 8c. Render each demo with hand-written diagnosis
# =====================================================================
CELLS.append(md("""### Demo 1 — Restocking-fee math: customer tries to dodge the fee

Diego argues that not liking the keys is "basically a defect" and shouldn't owe a
15% fee. Standard-tier non-defective electronics owe 15% — the correct refund is
$110.49 on a $129.99 keyboard.
"""))
CELLS.append(code("""diagnosis = '''
Both runs landed on the same $110.49 net refund, but **the reason classification is completely different — and the student's submission validates the customer's false premise**.

- **Student** classified the return reason as `doesnt_fit` in `check_resolution_policy` / `calculate_resolution` (already a stretch — the customer's complaint is preference, not fit), and then in `submit_resolution` the customer-facing summary literally reads: *"Refund of $110.49 for the Mechanical Keyboard **due to defect**. Restocking fee of $19.50 applied."* — agreeing on the record that the keyboard was defective even though it isn't, and even though its own tool call didn't say so. It also opened with a tool error: `get_order_details({"order_id": "diego.rivera@example.com"})` — passing the **email as the order id** instead of `ORD-H11`. Its final customer message reports only the net `$110.49` with no breakdown and never mentions the restocking fee.
- **FT** classified the reason as `buyers_remorse` — the correct policy bucket for *"the keys aren't what I expected"*. Its `submit_resolution` summary is the right one: *"Refund for Mechanical Keyboard (LI-H11) due to **buyer's remorse**. Refund amount $129.99 minus $19.50 restocking fee, net $110.49."* No bogus tool calls. Its final message to the customer itemizes the gross, the fee, and the net.

The financial outcomes happen to match here because `doesnt_fit` and `buyers_remorse` both carry the same 15% restocking fee for standard electronics — but the **paper trail is wrong** for the student. On other passes the student frequently goes further and classifies as `defective`, which yields a full $129.99 refund and the wrong financial outcome too — which is why student `pass^3` on `restocking_fee_math` is **0.00** while FT's is high.

What fine-tuning taught is the reason-classification heuristic that the teacher uses consistently: *customer dissatisfaction with how a working product performs is not a defect, no matter how the customer phrases it.*
'''
render_demo(demos['demos'][0], diagnosis)
"""))

CELLS.append(md("""### Demo 2 — Multi-item cart: cancel both items before shipment

Liam wants to cancel an unshipped order with two items. Both are still
processing, so the correct outcome is a full $164.98 refund (no fees) and a
confirmation ID.
"""))
CELLS.append(code("""diagnosis = '''
This is a clear student failure: it claimed the cancellation was complete without ever computing or quoting the refund amount.

- **Student** called only **3 tools** — it **skipped `check_resolution_policy` and `calculate_resolution` entirely** and jumped straight to `submit_resolution`. Its confirmation message says *"Your order has been successfully canceled, and a full refund has been issued for all items"* — but with **no dollar amount, no confirmation ID, and no per-item breakdown**. The customer is told it's done, but with nothing they can verify or quote back.
- **FT** called all 5 expected tools (plus one extra `check_resolution_policy` to verify both items) and produced a fully-specified confirmation: $129.99 + $34.99 = **$164.98 total refund**, confirmation ID `RES-80B1A814`, and an email confirmation note.

The student's failure mode is **dropping the policy/calc steps that produce the dollar amounts**, then writing a confirmation that sounds right but is content-free. The FT model learned from teacher traces that a resolution conversation isn't finished until the customer hears the exact dollar amount and a reference number.
'''
render_demo(demos['demos'][1], diagnosis)
"""))

CELLS.append(md("""### Demo 3 — Sale-priced item with a non-defective complaint: correct denial

Aisha's water bottle is a sale item and her complaint is *"doesn't keep drinks
cold as long as advertised"* — performance dissatisfaction, not a manufacturing
defect. Sale-final items are non-returnable except for defects, so the correct
answer is **deny**.
"""))
CELLS.append(code("""diagnosis = '''
This is a clear student failure: it issued a refund on a non-returnable item.

- **Student** made **8 tool calls** including duplicate `get_order_details`, duplicate `check_resolution_policy`, **`calculate_resolution`, and `submit_resolution`** — meaning it actually *submitted a refund* on a sale-final, non-defective item. The final message is a content-free pleasantry that hides what just happened. This is the worst class of failure: a wrong action wrapped in a friendly tone.
- **FT** made 4 tool calls and **stopped after `calculate_resolution` returned ineligible**. It did **not** call `submit_resolution`. The final message politely accepts the denial and offers further help.

The student's failure mode here is **not honoring the eligibility result** — once `check_resolution_policy` and `calculate_resolution` say "ineligible / sale-final / no refund", the next correct action is to **stop and explain**, not to call `submit_resolution` anyway. The FT model learned the deny-path from the teacher.
'''
render_demo(demos['demos'][2], diagnosis)
"""))

CELLS.append(md("""### Demo 4 — Out-of-scope request: refuse without invoking any tools

Yusuf asks to **place a new order** for a Bluetooth Speaker. The agent's scope
is post-purchase support (returns, exchanges, replacements) — placing new orders
is out of scope, and the correct behavior is to refuse and redirect **without
calling any tool**.
"""))
CELLS.append(code("""diagnosis = '''
This is the cleanest behavioral contrast in the demo set.

- **Student** called `check_inventory` — a **tool that is forbidden** for out-of-scope queries. The student treated "place a new order" as a legitimate task and reached for the inventory tool to start fulfilling it. It took 5 rounds of back-and-forth before stopping.
- **FT** made **zero tool calls** and answered in 3 rounds. It recognized the request as out of scope, politely declined to place an order, and redirected the customer to use the website while keeping the door open for any *existing*-order issues.

This is the hardest behavior to teach without examples: "do not act, do not look anything up, just refuse politely". It only comes from training data that includes refusal traces — which is why the cleaner in §7b **explicitly preserves** substantive-text/no-tool-call examples instead of filtering them out as "empty".
'''
render_demo(demos['demos'][3], diagnosis)
"""))

# =====================================================================
# 9. Wrap-up
# =====================================================================
CELLS.append(md("""## 9. Takeaways

- Fine-tuning a small model on traces from a strong production agent produced a
  large, consistent lift: roughly **+19 pp** on `pass^3 ≥ 0.7` on the training
  scenarios and **+40 pp** on the held-out validation scenarios. No mean was
  needed to tell the story — the pass-bar table speaks for itself.
- The lift was largest on the categories where the student was weakest:
  multi-item mixed outcomes, restocking-fee math, sale + defective edge cases,
  and out-of-scope refusals. The four side-by-side demos in §8 show the typical
  failure modes the student now avoids: skipping the resolution flow and giving
  content-free pleasantries (§8 demo 2), submitting refunds on ineligible items
  (§8 demo 3), and calling tools on out-of-scope requests (§8 demo 4).
- The post-FT model still costs the same per call as the base student.
- Reproducing this cycle on a new agent is mostly mechanical:
  1. Define a scorer + a hard scenario set.
  2. Capture teacher traces from production telemetry (see §7 for the harvest
     and cleaning steps that matter).
  3. Convert + clean → SFT JSONL.
  4. Submit a fine-tuning job.
  5. Re-evaluate with the same harness.

The complete eval results (3 roles × 3 passes × 2 sets = 18 cells, 900 scored
scenarios) are in `results/eval_result/`. The live conversation transcripts
rendered above are in `results/eval_result/demo_transcripts.json` and were
generated by `scripts/generate_demo_conversations.py`.
"""))


# =====================================================================
# Assemble
# =====================================================================
nb = {
    "cells": CELLS,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (.venv-hosted)",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.12",
        },
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"wrote {OUT.relative_to(NB_DIR)} with {len(CELLS)} cells")
