#!/usr/bin/env bash
# AgentKit — Session End Hook
# Event: Stop
# Purpose: Compress the session into a handoff document using Haiku.
#          Handoff is saved to .agentkit/handoff.md in the project dir.
#
# Claude Code Stop hook stdin:
# {
#   "session_id": "...",
#   "cwd": "...",
#   "hook_event_name": "Stop"
# }

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

INPUT=$(cat)

AGENTKIT_HOME="${AGENTKIT_HOME:-$(dirname "$(dirname "$(realpath "$0")")")}"

echo "$INPUT" | $PYTHON "${AGENTKIT_HOME}/memory/handoff.py" generate

exit 0
