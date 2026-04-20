"""
AgentKit — Session End Hook (cross-platform Python equivalent of session_end.sh)
Event: Stop
Purpose: Compress the session into a handoff document using Haiku.
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
        sys.stdin = __import__("io").StringIO(raw)
        from memory.handoff import main_generate
        main_generate()
    except Exception:
        pass


if __name__ == "__main__":
    main()
