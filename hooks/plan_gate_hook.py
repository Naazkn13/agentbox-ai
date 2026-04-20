"""
AgentKit — Plan Gate Hook (cross-platform Python equivalent of plan_gate.sh)
Event: PreToolUse (Edit|Write|MultiEdit)
Purpose: Block coding unless a plan exists and has been approved.
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

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", tool_input.get("path", ""))

    # Allow edits to the plan file itself
    if "current_plan.md" in file_path:
        return

    # Delegate to workflow enforcer
    try:
        from workflow.enforcer import WorkflowEnforcer
        project_root = os.environ.get("AGENTKIT_PROJECT", os.getcwd())
        enforcer = WorkflowEnforcer(project_root)
        ok, msg = enforcer.on_file_edit(file_path)
        if not ok:
            print(msg)
            sys.exit(2)  # exit 2 = block in Claude Code hooks
    except SystemExit:
        raise
    except Exception:
        pass


if __name__ == "__main__":
    main()
