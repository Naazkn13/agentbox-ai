"""
AgentKit — Research Gate Hook (cross-platform Python equivalent of research_gate.sh)
Event: PostToolUse (Read)
Purpose: Track file reads for the RESEARCH→PLAN workflow gate.
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

    if not file_path:
        return

    # Skip .agentkit internal files
    if ".agentkit" in file_path:
        return

    try:
        from workflow.enforcer import WorkflowEnforcer
        project_root = os.environ.get("AGENTKIT_PROJECT", os.getcwd())
        enforcer = WorkflowEnforcer(project_root)
        enforcer.on_file_read(file_path)
    except Exception:
        pass


if __name__ == "__main__":
    main()
