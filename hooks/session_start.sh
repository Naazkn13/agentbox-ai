#!/usr/bin/env bash
# AgentKit — Session Start Hook
# Event: UserPromptSubmit (first turn only — detected by turn_count == 0)
# Purpose: Load the previous session's handoff document into Claude's context.
#
# Output to stdout is shown to Claude as context.

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

INPUT=$(cat)

AGENTKIT_HOME="${AGENTKIT_HOME:-$(dirname "$(dirname "$(realpath "$0")")")}"
SESSION_ID=$(echo "$INPUT" | $PYTHON -c \
  "import sys,json; d=json.load(sys.stdin); print(d.get('session_id','unknown'))" 2>/dev/null || echo "unknown")

# Only run on the first turn of a session
STATE_FILE="${AGENTKIT_HOME}/data/session_${SESSION_ID}.json"
if [ -f "$STATE_FILE" ]; then
  TURN=$($PYTHON -c "import json; print(json.load(open('${STATE_FILE}')).get('turn_count',1))" 2>/dev/null || echo "1")
  if [ "$TURN" -gt 1 ]; then
    exit 0   # Not the first turn — skip handoff injection
  fi
fi

# Print AgentKit startup banner (visible to the AI and user on turn 1)
$PYTHON "${AGENTKIT_HOME}/hooks/render_dashboard.py" banner \
  --platform "claude-code" 2>/dev/null || true

echo "$INPUT" | $PYTHON "${AGENTKIT_HOME}/memory/handoff.py" load

exit 0
