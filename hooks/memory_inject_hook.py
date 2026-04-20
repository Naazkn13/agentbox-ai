"""
AgentKit — Memory Inject Hook (cross-platform Python equivalent of memory_inject.sh)
Event: UserPromptSubmit
Purpose: Inject relevant project memory into Claude's context.
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
        if not raw.strip():
            return
        # Pass stdin to the injector
        sys.stdin = __import__("io").StringIO(raw)
        from memory.injector import main as injector_main
        injector_main()
    except Exception:
        pass


if __name__ == "__main__":
    main()
