#!/usr/bin/env bash
# AgentKit — Forced-Eval Hook
# Event: PreToolUse
# Purpose: Remind Claude to check if any active skill applies before each tool call.
#          This raises skill activation from ~20% to ~84%.
#
# Claude Code passes hook input as JSON on stdin:
# {
#   "session_id": "...",
#   "tool_name": "Edit|Bash|Write|Read|...",
#   "tool_input": {...}
# }

set -euo pipefail

# Read JSON input from stdin
INPUT=$(cat)

# Extract fields with python (available everywhere, no jq dependency)
TOOL_NAME=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_name',''))" 2>/dev/null || echo "")
SESSION_ID=$(echo "$INPUT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('session_id',''))" 2>/dev/null || echo "")

# Only apply for action tools where skills are relevant
if [[ ! "$TOOL_NAME" =~ ^(Edit|Bash|Write|MultiEdit)$ ]]; then
  exit 0
fi

# Load session env (written by skill_router_hook.py)
AGENTKIT_HOME="${AGENTKIT_HOME:-$(dirname "$(dirname "$(realpath "$0")")")}"
ENV_FILE="${AGENTKIT_HOME}/data/env_${SESSION_ID}.sh"

if [ ! -f "$ENV_FILE" ]; then
  exit 0
fi

# Source env to get AGENTKIT_LOADED_SKILLS
# shellcheck source=/dev/null
source "$ENV_FILE"

if [ -z "${AGENTKIT_LOADED_SKILLS:-}" ]; then
  exit 0
fi

# Output the forced-eval reminder — Claude Code shows this to Claude before the tool runs
cat <<EOF
[AgentKit] Before using $TOOL_NAME, check if any active skill applies:
  Active skills: ${AGENTKIT_LOADED_SKILLS}
  Task category: ${AGENTKIT_TASK_CATEGORY:-unknown}
  → Apply the relevant skill's instructions to this action.
EOF

exit 0
