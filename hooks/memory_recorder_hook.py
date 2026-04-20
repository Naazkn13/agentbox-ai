"""
AgentKit — Memory Recorder Hook (cross-platform Python equivalent of memory_recorder.sh)
Event: PostToolUse (Read|Edit|Write|Bash|MultiEdit)
Purpose: Capture entities from tool events into the memory graph.
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

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Read", "Edit", "Write", "Bash", "MultiEdit"):
        return

    try:
        sys.stdin = __import__("io").StringIO(json.dumps(data))
        from memory.recorder import main as recorder_main
        recorder_main()
    except Exception:
        pass


if __name__ == "__main__":
    main()
