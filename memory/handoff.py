"""
AgentKit — Layer 2: Session Handoff
Compresses each session into a ~500-token handoff document using Haiku.
Cost: ~$0.0015 per session (800 tokens input, 500 output at Haiku rates).

Called by session_end.sh on the Stop event.
Handoff is saved to .agentkit/handoff.md in the project dir.
Loaded at the start of the next session via session_start.sh.
"""

import os
import sys
import json
import time
import sqlite3

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HANDOFF_PROMPT = """\
You are compressing a software development session into a concise handoff document.
The handoff will be loaded at the start of the next session so no context is lost.

Session data:
{session_data}

Write the handoff using EXACTLY this format (max 500 tokens total):

## What We Built
[1-2 sentences: what was accomplished this session]

## Key Decisions Made
- [decision]: [rationale in one line]
[max 5 decisions]

## Current State
- Complete: [comma-separated list]
- In Progress: [comma-separated list or "nothing"]
- Blocked: [comma-separated list or "nothing"]

## Critical Context for Next Session
[3-5 bullet points of the most important things to remember. Be specific — \
include file paths, function names, and exact values where relevant.]

## Files Changed
- [file path]: [what changed in one line]
[max 8 files]
"""


def _gather_session_data(db_path: str, session_id: str) -> str:
    """Pull entities and decisions created this session from the DB."""
    if not os.path.exists(db_path):
        return "No session data recorded."

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    # Recent decisions
    decisions = conn.execute(
        "SELECT title, content, category FROM decisions WHERE session_id = ? ORDER BY created_at DESC LIMIT 10",
        (session_id,),
    ).fetchall()

    # Files touched this session
    files = conn.execute(
        "SELECT name, path, description FROM entities WHERE type = 'file' AND source_session = ? LIMIT 15",
        (session_id,),
    ).fetchall()

    # APIs discovered
    apis = conn.execute(
        "SELECT name, description FROM entities WHERE type = 'api' AND source_session = ? LIMIT 10",
        (session_id,),
    ).fetchall()

    # Commands that worked
    commands = conn.execute(
        "SELECT name, description FROM entities WHERE type = 'command' AND source_session = ? LIMIT 5",
        (session_id,),
    ).fetchall()

    conn.close()

    parts = []
    if decisions:
        parts.append("DECISIONS:")
        for d in decisions:
            parts.append(f"  [{d['category']}] {d['title']}: {d['content'][:150]}")

    if files:
        parts.append("\nFILES TOUCHED:")
        for f in files:
            desc = f["description"] or ""
            parts.append(f"  {f['path'] or f['name']}: {desc[:100]}")

    if apis:
        parts.append("\nAPIs DISCOVERED:")
        for a in apis:
            parts.append(f"  {a['name']}: {a['description'] or ''}")

    if commands:
        parts.append("\nWORKING COMMANDS:")
        for c in commands:
            parts.append(f"  {c['name']}: {c['description'] or ''}")

    return "\n".join(parts) if parts else "Session had no recorded entities or decisions."


def generate_handoff(db_path: str, session_id: str, output_path: str) -> str:
    """
    Generate an AI-compressed handoff document and write it to output_path.
    Returns the handoff text.
    Falls back to a raw summary if the Anthropic API is unavailable.
    """
    session_data = _gather_session_data(db_path, session_id)

    handoff_text = _call_haiku(session_data)

    # Write handoff file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(f"# Session Handoff\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M')}  |  Session: {session_id}\n\n")
        f.write(handoff_text)

    # Mark session as ended in DB
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE sessions SET ended_at = ?, summary = ? WHERE id = ?",
            (int(time.time()), handoff_text[:1000], session_id),
        )
        conn.commit()
        conn.close()

    return handoff_text


def _call_haiku(session_data: str) -> str:
    """Call Haiku to compress session data into a handoff. Falls back to raw summary."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{
                "role": "user",
                "content": HANDOFF_PROMPT.format(session_data=session_data[:3000]),
            }],
        )
        return response.content[0].text.strip()
    except Exception as e:
        # Fallback: structured raw summary without LLM
        return _raw_summary(session_data, str(e))


def _raw_summary(session_data: str, error: str) -> str:
    return f"""## What We Built
Session data captured (AI compression unavailable: {error[:80]})

## Key Decisions Made
See session data below.

## Critical Context for Next Session
Review the captured session data.

## Raw Session Data
{session_data[:800]}
"""


def load_handoff(handoff_path: str, max_age_days: int = 7) -> str:
    """
    Load the handoff document if it exists and is recent enough.
    Returns the handoff text or empty string.
    """
    if not os.path.exists(handoff_path):
        return ""

    age_seconds = time.time() - os.path.getmtime(handoff_path)
    if age_seconds > max_age_days * 86400:
        return ""

    with open(handoff_path) as f:
        return f.read()


# ---------------------------------------------------------------------------
# CLI entry points
# ---------------------------------------------------------------------------

def main_generate() -> None:
    """Called by session_end.sh on Stop event."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    session_id = data.get("session_id", os.environ.get("AGENTKIT_SESSION_ID", "unknown"))
    cwd        = data.get("cwd", os.getcwd())

    db_path      = os.path.join(cwd, ".agentkit", "memory.db")
    handoff_path = os.path.join(cwd, ".agentkit", "handoff.md")

    print(f"[AgentKit] Compressing session {session_id}...", file=sys.stderr)
    text = generate_handoff(db_path, session_id, handoff_path)
    print(f"[AgentKit] Handoff saved to {handoff_path}", file=sys.stderr)
    # Print preview to stderr (not shown to Claude)
    print(text[:300], file=sys.stderr)


def main_load() -> None:
    """Called by session_start hook — prints handoff to stdout so Claude sees it."""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    cwd = data.get("cwd", os.getcwd())
    handoff_path = os.path.join(cwd, ".agentkit", "handoff.md")
    handoff = load_handoff(handoff_path)

    if handoff:
        print("=== AgentKit Session Handoff (from previous session) ===")
        print(handoff)
        print("=========================================================\n")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "generate"
    if cmd == "load":
        main_load()
    else:
        main_generate()
