#!/usr/bin/env bash
# AgentKit — Memory Recorder Hook
# Event: PostToolUse
# Purpose: Capture entities from Read/Edit/Bash tool use into the memory graph.
#
# Claude Code passes hook input as JSON on stdin:
# {
#   "session_id": "...",
#   "cwd": "...",
#   "tool_name": "Read|Edit|Bash|Write",
#   "tool_input": {...},
#   "tool_response": "..."
# }

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | $PYTHON -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")

# Only capture for relevant tool types
if [[ ! "$TOOL_NAME" =~ ^(Read|Edit|Write|Bash|MultiEdit)$ ]]; then
  exit 0
fi

AGENTKIT_HOME="${AGENTKIT_HOME:-$(dirname "$(dirname "$(realpath "$0")")")}"

# Run recorder in background — don't block the agent
echo "$INPUT" | $PYTHON "${AGENTKIT_HOME}/memory/recorder.py" &

exit 0
