#!/usr/bin/env python
"""Run full pass^k evaluation matrix for the demo deck.

Runs N_PASSES (default 3) evaluations of {student, teacher-hosted, ft} on
{training_tasks.json, eval_tasks.json}, writes per-pass scoring JSON into
``results/demo_results/{train,validation}/``, and emits ``summary.json``
with aggregate pass^1 / pass^2 / pass^3 (tau=0.70) for every cell.

Usage:
    python scripts/run_demo_eval.py                # all 18 runs
    python scripts/run_demo_eval.py --skip-existing  # resume after a crash

The intent is to produce the canonical numbers cited in the demo notebook
(``demo1_agent_distillation.ipynb``).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from math import comb
from pathlib import Path

NB_DIR = Path(__file__).resolve().parents[1]
EVAL_DIR = NB_DIR / "eval"
RESULTS_DIR = NB_DIR / "results"
DEMO_DIR = RESULTS_DIR / "demo_result"
OUT_NAME = "demo_result"
SCRIPTS_DIR = NB_DIR / "scripts"

try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(NB_DIR / ".env")
except Exception:
    pass

SEEDS = [7, 17, 27]
TAU = 0.70
STUDENT_MODEL = os.environ.get("STUDENT_MODEL", "gpt-4.1-nano")
FT_MODEL = os.environ.get("FT_MODEL", "gpt-4.1-nano-demo1")
HOSTED_AGENT = os.environ.get("HOSTED_AGENT_NAME", "demo1-retail-agent-langraph-responses")

TASK_SETS = [
    ("train",      EVAL_DIR / "training_tasks.json"),
    ("validation", EVAL_DIR / "eval_tasks.json"),
]


def _safe(s: str) -> str:
    return s.replace("/", "-").replace(":", "-")


def _expected_path(set_label: str, role: str, seed_ix: int) -> Path:
    out_dir = DEMO_DIR / set_label
    if role == "student":
        name = f"baseline__mt__student__{_safe(STUDENT_MODEL)}.v2.pass{seed_ix+1}.json"
    elif role == "ft":
        name = f"baseline__mt__ft__{_safe(FT_MODEL)}.v2.pass{seed_ix+1}.json"
    else:  # teacher (hosted)
        name = f"baseline__mt__teacher__{_safe(HOSTED_AGENT)}.v2.pass{seed_ix+1}.json"
    return out_dir / name


def _direct_cmd(role: str, model: str, set_label: str, scenarios: Path, seed_ix: int) -> list[str]:
    return [
        sys.executable, "-u", str(SCRIPTS_DIR / "run_baselines.py"),
        "--role", role,
        "--model", model,
        "--scenarios", str(scenarios),
        "--scorer", "v2",
        "--results-dir", f"{OUT_NAME}/{set_label}",
        "--suffix", f".pass{seed_ix+1}",
    ]


def _hosted_cmd(set_label: str, scenarios: Path, seed_ix: int) -> list[str]:
    return [
        sys.executable, "-u", str(SCRIPTS_DIR / "run_baselines_hosted.py"),
        "--agent", HOSTED_AGENT,
        "--scenarios", str(scenarios),
        "--results-dir", f"{OUT_NAME}/{set_label}",
        "--suffix", f".pass{seed_ix+1}",
    ]


def _run_job(label: str, cmd: list[str], log_path: Path, seed: int):
    env = os.environ.copy()
    env["AGENT_SEED"] = str(seed)
    env["CUSTOMER_SEED"] = str(seed)
    env["PYTHONIOENCODING"] = "utf-8"
    # FT runs need to point AGENT_* at the FT endpoint
    if "ft" in label.lower() and "ft__" in str(cmd):
        pass  # handled by caller
    print(f"[run] {label}  seed={seed}  log={log_path.name}", flush=True)
    t0 = time.time()
    with open(log_path, "w", encoding="utf-8") as fh:
        result = subprocess.run(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                cwd=NB_DIR)
    dt = (time.time() - t0) / 60
    if result.returncode != 0:
        print(f"  FAILED in {dt:.1f} min — see {log_path}", flush=True)
        return False
    print(f"  done in {dt:.1f} min", flush=True)
    return True


def _pass_at_k(scores: list[float], k: int, tau: float = TAU) -> float:
    n = len(scores)
    c = sum(1 for s in scores if s >= tau)
    if c < k:
        return 0.0
    return comb(c, k) / comb(n, k)


def _aggregate(paths: list[Path]) -> dict:
    """Aggregate per-scenario pass^k across N passes."""
    by_sid: dict[str, list[float]] = {}
    avgs: list[dict] = []
    for p in paths:
        d = json.loads(p.read_text(encoding="utf-8"))
        avgs.append({
            "pass": p.name,
            "avg_combined":      d.get("avg_combined", 0),
            "avg_decision":      d.get("avg_decision_correctness", 0),
            "avg_tools":         d.get("avg_tool_usage", 0),
            "avg_financial":     d.get("avg_financial_accuracy", 0),
            "avg_communication": d.get("avg_communication_quality", 0),
            "n_scenarios":       d.get("n_scenarios", 0),
        })
        for r in d.get("per_scenario", []):
            by_sid.setdefault(r["scenario_id"], []).append(r.get("combined", 0))
    n = len(by_sid)
    metrics = {f"pass^{k}": sum(_pass_at_k(v, k) for v in by_sid.values()) / n if n else 0.0
               for k in (1, 2, 3)}
    return {
        "n_scenarios": n,
        "tau": TAU,
        "metrics": {k: round(v, 4) for k, v in metrics.items()},
        "per_pass": avgs,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-existing", action="store_true",
                    help="Skip a pass whose output JSON already exists")
    ap.add_argument("--only", default="",
                    help="Comma-separated subset of {student,teacher,ft} to run")
    ap.add_argument("--out-name", default="demo_result",
                    help="Subfolder name under results/ for this run "
                         "(default: demo_result)")
    args = ap.parse_args()

    global DEMO_DIR, OUT_NAME
    OUT_NAME = args.out_name
    DEMO_DIR = RESULTS_DIR / OUT_NAME

    only = {x.strip() for x in args.only.split(",") if x.strip()}
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    for s, _ in TASK_SETS:
        (DEMO_DIR / s).mkdir(exist_ok=True)
        (DEMO_DIR / s / "logs").mkdir(exist_ok=True)

    # Build job list — order: cheap first (student, ft) then hosted teacher last
    jobs: list[tuple] = []
    for set_label, scenarios in TASK_SETS:
        for role in ("student", "ft", "teacher"):
            if only and role not in only:
                continue
            for i, seed in enumerate(SEEDS):
                out_path = _expected_path(set_label, role, i)
                jobs.append((set_label, role, seed, i, scenarios, out_path))

    print(f"Plan: {len(jobs)} job(s)")
    for j in jobs:
        marker = "(cached)" if args.skip_existing and j[5].exists() else ""
        print(f"  - {j[0]:<10} {j[1]:<7} pass{j[3]+1} seed={j[2]}  {marker}")
    print()

    failures = []
    for set_label, role, seed, i, scenarios, out_path in jobs:
        log_name = f"{role}.pass{i+1}.log"
        log_path = DEMO_DIR / set_label / "logs" / log_name
        if args.skip_existing and out_path.exists():
            print(f"[skip] {set_label} {role} pass{i+1} — cached", flush=True)
            continue

        # Build env per job (FT uses a different endpoint)
        env = os.environ.copy()
        env["AGENT_SEED"] = str(seed)
        env["CUSTOMER_SEED"] = str(seed)
        env["PYTHONIOENCODING"] = "utf-8"
        if role == "ft":
            env["AGENT_OPENAI_BASE_URL"] = (
                os.environ.get("AGENT_OPENAI_BASE_URL")
                or os.environ.get("FT_OPENAI_BASE_URL", "")
            )
            env["AGENT_OPENAI_API_KEY"] = (
                os.environ.get("AGENT_OPENAI_API_KEY")
                or os.environ.get("FT_OPENAI_API_KEY", "")
            )
            assert env["AGENT_OPENAI_API_KEY"], "Missing FT_OPENAI_API_KEY"

        if role == "teacher":
            cmd = _hosted_cmd(set_label, scenarios, i)
        elif role == "student":
            cmd = _direct_cmd("student", STUDENT_MODEL, set_label, scenarios, i)
        else:
            cmd = _direct_cmd("ft", FT_MODEL, set_label, scenarios, i)

        print(f"[run] {set_label}/{role} pass{i+1} seed={seed}  log={log_name}", flush=True)
        t0 = time.time()
        with open(log_path, "w", encoding="utf-8") as fh:
            result = subprocess.run(cmd, env=env, stdout=fh, stderr=subprocess.STDOUT,
                                    cwd=NB_DIR)
        dt = (time.time() - t0) / 60
        if result.returncode != 0:
            print(f"  FAILED in {dt:.1f} min — see {log_path}", flush=True)
            failures.append((set_label, role, i+1))
        else:
            print(f"  done in {dt:.1f} min  -> {out_path.name}", flush=True)

    # ---- Aggregate summary --------------------------------------------------
    print("\n=== Aggregating summary ===", flush=True)
    summary = {"tau": TAU, "seeds": SEEDS, "by_set": {}}
    for set_label, _ in TASK_SETS:
        cell = {}
        for role in ("student", "teacher", "ft"):
            paths = [_expected_path(set_label, role, i) for i in range(len(SEEDS))]
            paths = [p for p in paths if p.exists()]
            if not paths:
                cell[role] = {"error": "no passes available"}
                continue
            cell[role] = _aggregate(paths)
        # uplift FT - student
        if "metrics" in cell.get("ft", {}) and "metrics" in cell.get("student", {}):
            cell["uplift_ft_vs_student"] = {
                k: round(cell["ft"]["metrics"][k] - cell["student"]["metrics"][k], 4)
                for k in ("pass^1", "pass^2", "pass^3")
            }
        summary["by_set"][set_label] = cell

    summary_path = DEMO_DIR / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote {summary_path}", flush=True)

    # Console table
    print(f"\n{'='*72}")
    print(f"DEMO RESULTS — pass^k at combined >= {TAU}, seeds={SEEDS}")
    print(f"{'='*72}")
    for set_label, _ in TASK_SETS:
        cell = summary["by_set"][set_label]
        print(f"\n{set_label.upper()} TASKS")
        print(f"  {'role':<10}  {'n':>3}  {'pass^1':>7}  {'pass^2':>7}  {'pass^3':>7}")
        for role in ("student", "teacher", "ft"):
            c = cell.get(role, {})
            m = c.get("metrics", {})
            if not m:
                print(f"  {role:<10}  N/A")
                continue
            print(f"  {role:<10}  {c['n_scenarios']:>3}  "
                  f"{m['pass^1']*100:>6.1f}%  {m['pass^2']*100:>6.1f}%  {m['pass^3']*100:>6.1f}%")
        if "uplift_ft_vs_student" in cell:
            u = cell["uplift_ft_vs_student"]
            print(f"  {'FT-Student':<10}  -    "
                  f"{u['pass^1']*100:>+6.1f}pp  {u['pass^2']*100:>+6.1f}pp  {u['pass^3']*100:>+6.1f}pp")

    if failures:
        print(f"\n!! {len(failures)} pass(es) failed: {failures}")
        sys.exit(1)


if __name__ == "__main__":
    main()
