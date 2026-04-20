"""
AgentKit — Thinking Budget Hook (cross-platform Python equivalent of thinking_budget.sh)
Event: UserPromptSubmit
Purpose: Inject thinking budget hint based on task complexity.
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

    session_id = data.get("session_id", "unknown")
    agentkit_home = os.environ.get("AGENTKIT_HOME", _REPO_ROOT)
    env_file = os.path.join(agentkit_home, "data", f"env_{session_id}.sh")

    thinking_tier = "moderate"
    if os.path.exists(env_file):
        try:
            with open(env_file) as f:
                for line in f:
                    if "AGENTKIT_THINKING_TIER=" in line:
                        thinking_tier = line.split("=", 1)[1].strip().strip("'\"")
        except Exception:
            pass

    if thinking_tier == "deep":
        hint = "[AgentKit] Deep reasoning mode: take time to explore multiple approaches and verify your reasoning before committing."
        print(json.dumps({"system_prompt_suffix": hint}))
    elif thinking_tier == "off":
        hint = "[AgentKit] Trivial task: respond directly without over-thinking."
        print(json.dumps({"system_prompt_suffix": hint}))


if __name__ == "__main__":
    main()
