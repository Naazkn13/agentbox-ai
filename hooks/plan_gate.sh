#!/usr/bin/env bash
# AgentKit — Layer 4: Plan Gate Hook
# Event: PreToolUse (matcher: Edit|Write|MultiEdit)
#
# Blocks coding unless a plan exists and has been approved.
# Allows edits to the plan file itself (.agentkit/current_plan.md).

set -euo pipefail

AGENTKIT_HOME="${AGENTKIT_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
PROJECT_ROOT="${AGENTKIT_PROJECT:-$(pwd)}"
AGENTKIT_DIR="$PROJECT_ROOT/.agentkit"
PLAN_FILE="$AGENTKIT_DIR/current_plan.md"
STATE_FILE="$AGENTKIT_DIR/workflow.json"

# ── Read the file being edited from the hook JSON ───────────────────────────
INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('tool_name', ''))
" 2>/dev/null || echo "")

TOOL_INPUT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
inp = d.get('tool_input', {})
# Check all common path keys
for key in ('file_path', 'path', 'command'):
    if key in inp:
        print(inp[key])
        break
" 2>/dev/null || echo "")

# ── Allow edits to the plan file itself ─────────────────────────────────────
if [[ "$TOOL_INPUT" == *"current_plan.md"* ]]; then
  exit 0
fi

# ── Delegate to workflow enforcer ───────────────────────────────────────────
python3 "$AGENTKIT_HOME/workflow/enforcer.py" on-edit "$TOOL_INPUT" 2>/dev/null
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
  # enforcer printed the block message — exit 2 signals "block" to Claude Code
  exit 2
fi

exit 0
