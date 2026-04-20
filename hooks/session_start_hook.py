"""
AgentKit — Session Start Hook (cross-platform Python equivalent of session_start.sh)
Event: UserPromptSubmit (first turn only)
Purpose: Load the previous session's handoff document into Claude's context.
"""

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    session_id = data.get("session_id", "unknown")
    agentkit_home = os.environ.get("AGENTKIT_HOME", _REPO_ROOT)

    # Only run on the first turn of a session
    state_file = os.path.join(agentkit_home, "data", f"session_{session_id}.json")
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                state = json.load(f)
            if state.get("turn_count", 0) > 1:
                return
        except Exception:
            pass

    # Print banner
    try:
        import subprocess
        py = sys.executable
        res = subprocess.run(
            [py, os.path.join(agentkit_home, "hooks", "render_dashboard.py"),
             "banner", "--platform", "claude-code"],
            capture_output=True, text=True, timeout=10,
        )
        if res.returncode == 0 and res.stdout.strip():
            print(res.stdout.strip())
    except Exception:
        pass

    # Load handoff
    try:
        from memory.handoff import load_handoff
        cwd = data.get("cwd", os.getcwd())
        handoff_path = os.path.join(cwd, ".agentkit", "handoff.md")
        handoff = load_handoff(handoff_path)
        if handoff:
            print("=== AgentKit Session Handoff (from previous session) ===")
            print(handoff)
            print("=========================================================\n")
    except Exception:
        pass


if __name__ == "__main__":
    main()
