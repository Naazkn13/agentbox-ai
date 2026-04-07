"""
AgentKit — Layer 3: Cost Dashboard
Logs per-turn cost to a JSONL file and renders a compact status line
that Claude Code can display in its status bar.

Usage modes:
  python3 render_dashboard.py log   --model MODEL --input N --output N [--session-id S] [--platform P] [--skills S1,S2]
  python3 render_dashboard.py status [--session-id S]
  python3 render_dashboard.py report [--days N]
  python3 render_dashboard.py analytics [--days N]
  python3 render_dashboard.py analytics-md [--days N]

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
    platform: str = "",
    skill_ids: list[str] | None = None,
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
        "platform":      platform or "claude-code",
        "skill_ids":     skill_ids or [],
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
# Analytics dashboard (terminal + markdown)
# ---------------------------------------------------------------------------

_BLOCK_CHARS = " ▁▂▃▄▅▆▇█"
_W = 62  # total box width (inner)


def _bar(value: int, max_value: int, width: int = 10) -> str:
    if max_value == 0:
        return " " * width
    filled = round(value / max_value * width)
    return "█" * filled + " " * (width - filled)


def _sparkline(values: list[float]) -> str:
    if not values or max(values) == 0:
        return "─" * len(values)
    mx = max(values)
    return "".join(_BLOCK_CHARS[round(v / mx * (len(_BLOCK_CHARS) - 1))] for v in values)


def _box_line(left: str, right: str, lw: int, rw: int) -> str:
    return f"║  {left:<{lw}}  ║  {right:<{rw}}  ║"  # noqa: E501


def full_analytics(days: int = 7) -> str:
    records = _read_log(max_age_days=days)

    total_cost   = sum(r.get("cost_usd", 0) for r in records)
    total_saved  = sum(r.get("saved_usd", 0) for r in records)
    total_turns  = len(records)

    # Unique sessions
    sessions = len({r.get("session_id", "") for r in records if r.get("session_id")})

    pct_saved = 100 * total_saved / (total_cost + total_saved + 1e-9)

    # Model breakdown
    model_counts: dict[str, int] = {}
    for r in records:
        short = SHORT_NAMES.get(r.get("model", MODEL_SONNET), "Other")
        model_counts[short] = model_counts.get(short, 0) + 1
    max_model = max(model_counts.values(), default=1)

    # Daily cost (last `days` days, day 0 = oldest)
    now_ts = int(time.time())
    daily: list[float] = []
    for d in range(days - 1, -1, -1):
        lo = now_ts - (d + 1) * 86400
        hi = now_ts - d * 86400
        daily.append(sum(r.get("cost_usd", 0) for r in records if lo <= r.get("ts", 0) < hi))

    spark = _sparkline(daily)
    import datetime as _dt
    today_wd = _dt.date.today().weekday()  # 0=Mon
    day_chars = "MTWTFSS"
    spark_label = "".join(day_chars[(today_wd - days + 1 + i) % 7] for i in range(days))

    # Top skills
    skill_counts: dict[str, int] = {}
    for r in records:
        for sid in r.get("skill_ids", []):
            skill_counts[sid] = skill_counts.get(sid, 0) + 1
    top_skills = sorted(skill_counts.items(), key=lambda x: -x[1])[:4]
    max_skill = max((v for _, v in top_skills), default=1)

    # Platform breakdown
    platform_counts: dict[str, int] = {}
    for r in records:
        p = r.get("platform", "claude-code")
        platform_counts[p] = platform_counts.get(p, 0) + 1
    top_platforms = sorted(platform_counts.items(), key=lambda x: -x[1])[:4]
    max_platform = max((v for _, v in top_platforms), default=1)

    LW, RW = 22, 28  # left/right column widths

    lines: list[str] = []
    mid  = "╠" + "═" * (LW + 4) + "╬" + "═" * (RW + 4) + "╣"
    bot  = "╚" + "═" * (LW + 4) + "╩" + "═" * (RW + 4) + "╝"
    htop = "╔" + "═" * (LW + RW + 10) + "╗"
    hbot = "╠" + "═" * (LW + 4) + "╦" + "═" * (RW + 4) + "╣"

    title = f"AgentKit Analytics — Last {days} Days"
    lines.append(htop)
    lines.append(f"║  {title:^{LW + RW + 6}}  ║")
    lines.append(f"║  Sessions: {sessions:<4} Turns: {total_turns:<5} Cost: ${total_cost:.4f}   Saved: ${total_saved:.4f} ({pct_saved:.0f}%)  ║")
    lines.append(hbot)

    # Headers
    lines.append(_box_line("Model Breakdown", f"Daily Cost ({spark_label})", LW, RW))
    lines.append(_box_line("─" * LW, "─" * RW, LW, RW))

    model_rows = list(model_counts.items())
    spark_rows = [f"  {spark}  max ${max(daily):.4f}"]

    max_rows = max(len(model_rows), 1)
    for i in range(max_rows):
        if i < len(model_rows):
            name, cnt = model_rows[i]
            bar = _bar(cnt, max_model, 8)
            left = f"{name:<6} {bar} {cnt}"
        else:
            left = ""
        right = spark_rows[i] if i < len(spark_rows) else ""
        lines.append(_box_line(left, right, LW, RW))

    lines.append(mid)
    lines.append(_box_line("Top Skills", "Platform Usage", LW, RW))
    lines.append(_box_line("─" * LW, "─" * RW, LW, RW))

    max_sl_rows = max(len(top_skills), len(top_platforms), 1)
    for i in range(max_sl_rows):
        if i < len(top_skills):
            sid, cnt = top_skills[i]
            bar = _bar(cnt, max_skill, 6)
            left = f"{sid[:14]:<14} {bar} {cnt}"
        else:
            left = ""
        if i < len(top_platforms):
            pname, cnt = top_platforms[i]
            bar = _bar(cnt, max_platform, 8)
            right = f"{pname[:12]:<12} {bar} {cnt}"
        else:
            right = ""
        lines.append(_box_line(left, right, LW, RW))

    lines.append(bot)

    if not records:
        lines.append("  No data yet. Run some sessions first.")
    else:
        lines.append("  Tip: agentkit analytics --days 30  for monthly view")

    return "\n".join(lines)


def analytics_summary_md(days: int = 7) -> str:
    """Compact markdown analytics block for injection into platform config files."""
    records = _read_log(max_age_days=days)

    if not records:
        return (
            "<!-- AGENTKIT_ANALYTICS_START -->\n"
            "## AgentKit Analytics\nNo sessions logged yet.\n"
            "<!-- AGENTKIT_ANALYTICS_END -->"
        )

    total_cost  = sum(r.get("cost_usd", 0) for r in records)
    total_saved = sum(r.get("saved_usd", 0) for r in records)
    total_turns = len(records)
    sessions    = len({r.get("session_id", "") for r in records if r.get("session_id")})
    pct_saved   = 100 * total_saved / (total_cost + total_saved + 1e-9)

    model_counts: dict[str, int] = {}
    for r in records:
        short = SHORT_NAMES.get(r.get("model", MODEL_SONNET), "Other")
        model_counts[short] = model_counts.get(short, 0) + 1
    model_str = ", ".join(f"{k}×{v}" for k, v in sorted(model_counts.items()))

    skill_counts: dict[str, int] = {}
    for r in records:
        for sid in r.get("skill_ids", []):
            skill_counts[sid] = skill_counts.get(sid, 0) + 1
    top_skills = sorted(skill_counts.items(), key=lambda x: -x[1])[:5]
    skills_str = ", ".join(f"{s}({n})" for s, n in top_skills) or "none"

    platform_counts: dict[str, int] = {}
    for r in records:
        p = r.get("platform", "claude-code")
        platform_counts[p] = platform_counts.get(p, 0) + 1
    platforms_str = ", ".join(f"{p}:{n}" for p, n in sorted(platform_counts.items(), key=lambda x: -x[1]))

    import datetime as _dt
    generated = _dt.datetime.now().strftime("%Y-%m-%d %H:%M")

    return (
        f"<!-- AGENTKIT_ANALYTICS_START -->\n"
        f"## AgentKit Usage Analytics (last {days} days)\n"
        f"_Updated: {generated}_\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Sessions | {sessions} |\n"
        f"| Turns | {total_turns} |\n"
        f"| Total Cost | ${total_cost:.4f} |\n"
        f"| Saved vs Sonnet | ${total_saved:.4f} ({pct_saved:.0f}%) |\n"
        f"| Models | {model_str} |\n"
        f"| Platforms | {platforms_str} |\n"
        f"| Top Skills | {skills_str} |\n\n"
        f"Run `agentkit analytics` in terminal for full dashboard.\n"
        f"<!-- AGENTKIT_ANALYTICS_END -->"
    )


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
    p_log.add_argument("--platform",   default="")
    p_log.add_argument("--skills",     default="", help="Comma-separated skill IDs")

    # status sub-command
    p_status = sub.add_parser("status", help="Render status line")
    p_status.add_argument("--session-id", default="")

    # report sub-command
    p_report = sub.add_parser("report", help="Print weekly cost report")
    p_report.add_argument("--days", type=int, default=7)

    # analytics sub-command (full terminal dashboard)
    p_analytics = sub.add_parser("analytics", help="Full usage analytics dashboard")
    p_analytics.add_argument("--days", type=int, default=7)

    # analytics-md sub-command (markdown for platform injection)
    p_analytics_md = sub.add_parser("analytics-md", help="Markdown analytics summary for platform injection")
    p_analytics_md.add_argument("--days", type=int, default=7)

    args = parser.parse_args()

    if args.cmd == "log":
        skill_list = [s.strip() for s in args.skills.split(",") if s.strip()] if args.skills else []
        record = log_turn(
            model=args.model,
            input_tokens=args.input,
            output_tokens=args.output,
            session_id=args.session_id,
            task_category=args.category,
            platform=args.platform,
            skill_ids=skill_list,
        )
        print(json.dumps(record))

    elif args.cmd == "status":
        line = render_status_line(session_id=args.session_id)
        print(json.dumps({"status_line": line}))

    elif args.cmd == "report":
        print(weekly_report(days=args.days))

    elif args.cmd == "analytics":
        print(full_analytics(days=args.days))

    elif args.cmd == "analytics-md":
        print(analytics_summary_md(days=args.days))
