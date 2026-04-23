"""
AgentKit — Model Router Hook (cross-platform Python equivalent of model_router_hook.sh)
Event: UserPromptSubmit
Purpose: Route to optimal model (Haiku/Sonnet/Opus) and set thinking budget.
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
        return

    prompt = data.get("prompt", "")
    session_id = data.get("session_id", "unknown")
    is_subagent = data.get("is_subagent", False)

    agentkit_home = os.environ.get("AGENTKIT_HOME", _REPO_ROOT)
    data_dir = os.path.join(agentkit_home, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Run model router
    try:
        from router.model_router import route_model
        result = route_model(prompt, is_subagent)
    except Exception:
        result = {"model": "claude-sonnet-4-6", "tier": "standard", "reason": "fallback"}

    model = result.get("model", "claude-sonnet-4-6")
    tier = result.get("tier", "standard")

    # Run thinking budget tuner
    try:
        from router.thinking_budget import tune_budget
        thinking = tune_budget(prompt)
    except Exception:
        thinking = {"budget_tokens": 8192, "tier": "moderate"}

    thinking_tokens = thinking.get("budget_tokens", 8192)

    # Persist env vars for downstream hooks
    env_file = os.path.join(data_dir, f"env_{session_id}.sh")
    with open(env_file, "a") as f:
        f.write(f"export AGENTKIT_MODEL='{model}'\n")
        f.write(f"export AGENTKIT_TIER='{tier}'\n")
        f.write(f"export AGENTKIT_THINKING='{thinking_tokens}'\n")

    # Inject routing hint
    if tier == "complex":
        hint = "[AgentKit] Routing: complex task → Opus-level reasoning. Think carefully before acting."
        print(json.dumps({"system_prompt_suffix": hint}))
    elif tier == "simple":
        hint = "[AgentKit] Routing: simple task → Haiku speed. Be concise and direct."
        print(json.dumps({"system_prompt_suffix": hint}))


if __name__ == "__main__":
    main()
