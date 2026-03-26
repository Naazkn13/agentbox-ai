"""
AgentKit — Layer 3: Cost Dashboard
Logs per-turn cost to a JSONL file and renders a compact status line
that Claude Code can display in its status bar.

Usage modes:
  python3 render_dashboard.py log   --model MODEL --input N --output N [--session-id S]
  python3 render_dashboard.py status [--session-id S]
  python3 render_dashboard.py report [--days N]

Output (status mode):
  {"status_line": "💰 $0.012 | saved $0.031 | Sonnet×4 Haiku×7"}

Log file: $AGENTKIT_HOME/data/costs.jsonl  (one JSON object per line)
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL_HAIKU  = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS   = "claude-opus-4-6"

MODEL_RATES: dict[str, dict[str, float]] = {
    MODEL_HAIKU:  {"input": 0.00000025, "output": 0.00000125},
    MODEL_SONNET: {"input": 0.000003,   "output": 0.000015},
    MODEL_OPUS:   {"input": 0.000015,   "output": 0.000075},
}

SHORT_NAMES = {
    MODEL_HAIKU:  "Haiku",
    MODEL_SONNET: "Sonnet",
    MODEL_OPUS:   "Opus",
}


def _data_dir() -> Path:
    home = os.environ.get("AGENTKIT_HOME", str(Path(__file__).parent.parent))
    d = Path(home) / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cost_log() -> Path:
    return _data_dir() / "costs.jsonl"


# ---------------------------------------------------------------------------
# Log a single turn
# ---------------------------------------------------------------------------

def log_turn(
    model: str,
    input_tokens: int,
    output_tokens: int,
    session_id: str = "",
    task_category: str = "",
) -> dict:
    rates = MODEL_RATES.get(model, MODEL_RATES[MODEL_SONNET])
    cost  = input_tokens * rates["input"] + output_tokens * rates["output"]

    # Savings vs Sonnet baseline
    baseline_rates = MODEL_RATES[MODEL_SONNET]
    baseline_cost  = input_tokens * baseline_rates["input"] + output_tokens * baseline_rates["output"]
    saved = max(0.0, baseline_cost - cost)

    record = {
        "ts":            int(time.time()),
        "session_id":    session_id,
        "model":         model,
        "input_tokens":  input_tokens,
        "output_tokens": output_tokens,
        "cost_usd":      round(cost, 6),
        "saved_usd":     round(saved, 6),
        "task_category": task_category,
    }

    with open(_cost_log(), "a") as f:
        f.write(json.dumps(record) + "\n")

    return record


# ---------------------------------------------------------------------------
# Read log
# ---------------------------------------------------------------------------

def _read_log(max_age_days: int = 30) -> list[dict]:
    log_path = _cost_log()
    if not log_path.exists():
        return []

    cutoff = int(time.time()) - max_age_days * 86400
    records = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if r.get("ts", 0) >= cutoff:
                    records.append(r)
            except json.JSONDecodeError:
                continue
    return records


def _session_records(session_id: str) -> list[dict]:
    return [r for r in _read_log() if r.get("session_id") == session_id]


# ---------------------------------------------------------------------------
# Status line
# ---------------------------------------------------------------------------

def render_status_line(session_id: str = "") -> str:
    """
    Return a compact status string for Claude Code's status bar.
    Example: "$0.012 | saved $0.031 | Sonnet×4 Haiku×7"
    """
    if session_id:
        records = _session_records(session_id)
    else:
        # Fall back to all records in the last hour
        cutoff = int(time.time()) - 3600
        records = [r for r in _read_log(1) if r.get("ts", 0) >= cutoff]

    if not records:
        return "$0.000 | no turns yet"

    total_cost  = sum(r.get("cost_usd", 0) for r in records)
    total_saved = sum(r.get("saved_usd", 0) for r in records)

    model_counts: dict[str, int] = {}
    for r in records:
        m = r.get("model", MODEL_SONNET)
        short = SHORT_NAMES.get(m, m[:6])
        model_counts[short] = model_counts.get(short, 0) + 1

    model_str = " ".join(f"{name}×{cnt}" for name, cnt in sorted(model_counts.items()))

    return f"${total_cost:.3f} | saved ${total_saved:.3f} | {model_str}"


# ---------------------------------------------------------------------------
# Weekly report
# ---------------------------------------------------------------------------

def weekly_report(days: int = 7) -> str:
    records = _read_log(max_age_days=days)
    if not records:
        return f"No cost data for the last {days} days."

    total_cost  = sum(r.get("cost_usd", 0)  for r in records)
    total_saved = sum(r.get("saved_usd", 0) for r in records)
    total_turns = len(records)

    # Per-model breakdown
    model_stats: dict[str, dict] = {}
    for r in records:
        m = r.get("model", MODEL_SONNET)
        s = model_stats.setdefault(m, {"turns": 0, "cost": 0.0, "saved": 0.0})
        s["turns"] += 1
        s["cost"]  += r.get("cost_usd", 0)
        s["saved"] += r.get("saved_usd", 0)

    lines = [
        f"AgentKit Cost Report — last {days} days",
        f"  Total turns : {total_turns}",
        f"  Total cost  : ${total_cost:.4f}",
        f"  Total saved : ${total_saved:.4f}  "
        f"({100*total_saved/(total_cost+total_saved+1e-9):.0f}% vs all-Sonnet baseline)",
        "",
        "  Per-model breakdown:",
    ]
    for model, s in sorted(model_stats.items(), key=lambda x: -x[1]["cost"]):
        short = SHORT_NAMES.get(model, model)
        lines.append(
            f"    {short:8s}  turns={s['turns']:4d}  "
            f"cost=${s['cost']:.4f}  saved=${s['saved']:.4f}"
        )

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AgentKit cost dashboard")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # log sub-command
    p_log = sub.add_parser("log", help="Log a single turn's cost")
    p_log.add_argument("--model",      required=True)
    p_log.add_argument("--input",      type=int, required=True)
    p_log.add_argument("--output",     type=int, required=True)
    p_log.add_argument("--session-id", default="")
    p_log.add_argument("--category",   default="")

    # status sub-command
    p_status = sub.add_parser("status", help="Render status line")
    p_status.add_argument("--session-id", default="")

    # report sub-command
    p_report = sub.add_parser("report", help="Print weekly cost report")
    p_report.add_argument("--days", type=int, default=7)

    args = parser.parse_args()

    if args.cmd == "log":
        record = log_turn(
            model=args.model,
            input_tokens=args.input,
            output_tokens=args.output,
            session_id=args.session_id,
            task_category=args.category,
        )
        print(json.dumps(record))

    elif args.cmd == "status":
        line = render_status_line(session_id=args.session_id)
        print(json.dumps({"status_line": line}))

    elif args.cmd == "report":
        print(weekly_report(days=args.days))
