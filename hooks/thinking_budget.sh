#!/usr/bin/env bash
# AgentKit — Layer 3: Thinking Budget Hook
# Event: UserPromptSubmit (runs after model_router_hook.sh)
#
# Reads env vars written by model_router_hook.sh, then injects a thinking-
# budget reminder so Claude applies the right level of internal reasoning.
#
# Does NOT change the actual API thinking parameter (that requires the caller);
# instead it injects a lightweight behavioural nudge via the system prompt.

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

AGENTKIT_HOME="${AGENTKIT_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA_DIR="$AGENTKIT_HOME/data"

INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | $PYTHON -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('session_id', 'unknown'))
" 2>/dev/null || echo "unknown")

# Load env vars if available
ENV_FILE="$DATA_DIR/env_${SESSION_ID}.sh"
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
fi

THINKING_TIER="${AGENTKIT_THINKING_TIER:-moderate}"
THINKING_TOKENS="${AGENTKIT_THINKING:-8192}"

# Only inject a hint for non-default tiers
if [ "$THINKING_TIER" = "deep" ]; then
  $PYTHON -c "
import json
hint = '[AgentKit] Deep reasoning mode: take time to explore multiple approaches and verify your reasoning before committing.'
print(json.dumps({'system_prompt_suffix': hint}))
"
elif [ "$THINKING_TIER" = "off" ]; then
  $PYTHON -c "
import json
hint = '[AgentKit] Trivial task: respond directly without over-thinking.'
print(json.dumps({'system_prompt_suffix': hint}))
"
fi
# moderate: no hint needed — default behaviour is fine

exit 0
