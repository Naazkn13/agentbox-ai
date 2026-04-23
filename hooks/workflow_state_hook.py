"""
AgentKit — Workflow State Hook (cross-platform Python equivalent of workflow_state.sh)
Event: UserPromptSubmit
Purpose: Inject workflow state hint and handle workflow commands.
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
    prompt_lower = prompt.lower()
    project_root = os.environ.get("AGENTKIT_PROJECT", os.getcwd())

    # Handle explicit workflow commands
    if "agentkit workflow" in prompt_lower:
        try:
            from workflow.enforcer import WorkflowEnforcer
            enforcer = WorkflowEnforcer(project_root)
            if "approve" in prompt_lower:
                enforcer.approve_plan()
            elif "reset" in prompt_lower:
                enforcer.reset()
        except Exception:
            pass

    # Get current state
    try:
        from workflow.enforcer import WorkflowEnforcer
        enforcer = WorkflowEnforcer(project_root)
        state = enforcer.current_state()
    except Exception:
        state = "IDLE"

    # Inject state hint
    hints = {
        "RESEARCH": "[AgentKit] Workflow: RESEARCH phase. Read relevant files before writing a plan.",
        "PLAN": "[AgentKit] Workflow: PLAN phase. Write your implementation plan to .agentkit/current_plan.md, then it will be approved.",
        "EXECUTE": "[AgentKit] Workflow: EXECUTE phase. Implement the plan. Quality gates will run after each edit.",
        "REVIEW": "[AgentKit] Workflow: REVIEW phase. Review output and ensure all quality gates pass before shipping.",
        "SHIP": "[AgentKit] Workflow: SHIP phase. Commit changes and create the PR.",
    }

    hint = hints.get(state)
    if hint:
        print(json.dumps({"system_prompt_suffix": hint}))


if __name__ == "__main__":
    main()
