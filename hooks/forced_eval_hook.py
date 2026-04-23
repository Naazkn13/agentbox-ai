"""
AgentKit — Forced Eval Hook (cross-platform Python equivalent of forced_eval.sh)
Event: PreToolUse (Edit|Write|MultiEdit|Bash)
Purpose: Remind Claude to check if any active skill applies before each tool call.
"""

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return

    tool_name = data.get("tool_name", "")
    session_id = data.get("session_id", "")

    if tool_name not in ("Edit", "Bash", "Write", "MultiEdit"):
        return

    agentkit_home = os.environ.get("AGENTKIT_HOME", _REPO_ROOT)
    env_file = os.path.join(agentkit_home, "data", f"env_{session_id}.sh")

    if not os.path.exists(env_file):
        return

    loaded_skills = ""
    task_category = "unknown"
    try:
        with open(env_file) as f:
            for line in f:
                if "AGENTKIT_LOADED_SKILLS=" in line:
                    loaded_skills = line.split("=", 1)[1].strip().strip("'\"")
                elif "AGENTKIT_TASK_CATEGORY=" in line:
                    task_category = line.split("=", 1)[1].strip().strip("'\"")
    except Exception:
        return

    if not loaded_skills:
        return

    print(f"[AgentKit] Before using {tool_name}, check if any active skill applies:")
    print(f"  Active skills: {loaded_skills}")
    print(f"  Task category: {task_category}")
    print("  → Apply the relevant skill's instructions to this action.")


if __name__ == "__main__":
    main()
