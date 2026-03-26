#!/usr/bin/env bash
# AgentKit — Layer 3: Model Router Hook
# Event: UserPromptSubmit
#
# Reads the Claude Code hook JSON from stdin, extracts the user prompt,
# runs model_router.py to classify complexity, then injects the routing
# decision as a system hint and writes env vars for downstream hooks.
#
# Outputs to stdout: JSON with optional system_prompt injection.

set -euo pipefail

AGENTKIT_HOME="${AGENTKIT_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA_DIR="$AGENTKIT_HOME/data"
mkdir -p "$DATA_DIR"

# ── Read stdin ──────────────────────────────────────────────────────────────
INPUT=$(cat)

# Extract fields via python3 (jq may not be installed)
SESSION_ID=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('session_id', 'unknown'))
" 2>/dev/null || echo "unknown")

PROMPT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('prompt', ''))
" 2>/dev/null || echo "")

IS_SUBAGENT=$(echo "$INPUT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
# Heuristic: subagent prompts come from Agent tool invocations
print('true' if d.get('is_subagent', False) else 'false')
" 2>/dev/null || echo "false")

# ── Run model router ─────────────────────────────────────────────────────────
ROUTER_OUT=$(python3 "$AGENTKIT_HOME/router/model_router.py" \
    --prompt "$PROMPT" \
    --is-subagent "$IS_SUBAGENT" \
    2>/dev/null || echo '{"model":"claude-sonnet-4-6","tier":"standard","reason":"fallback"}')

MODEL=$(echo "$ROUTER_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['model'])")
TIER=$(echo  "$ROUTER_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['tier'])")
REASON=$(echo "$ROUTER_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['reason'])")

# ── Run thinking budget tuner ────────────────────────────────────────────────
THINKING_OUT=$(python3 "$AGENTKIT_HOME/router/thinking_budget.py" \
    --prompt "$PROMPT" \
    2>/dev/null || echo '{"budget_tokens":8192,"tier":"moderate","reason":"fallback"}')

THINKING_TOKENS=$(echo "$THINKING_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['budget_tokens'])")
THINKING_TIER=$(echo   "$THINKING_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['tier'])")

# ── Persist env vars for other hooks ────────────────────────────────────────
ENV_FILE="$DATA_DIR/env_${SESSION_ID}.sh"
# Append (don't overwrite — skill_router_hook.py may have written already)
{
  echo "export AGENTKIT_MODEL='$MODEL'"
  echo "export AGENTKIT_TIER='$TIER'"
  echo "export AGENTKIT_THINKING='$THINKING_TOKENS'"
} >> "$ENV_FILE"

# ── Inject a brief routing hint into the system prompt ──────────────────────
# This tells Claude which model it "should" behave like (informational only —
# actual model switching requires the API caller to pass the model field).
HINT=""
if [ "$TIER" = "complex" ]; then
  HINT="[AgentKit] Routing: complex task → Opus-level reasoning. Think carefully before acting."
elif [ "$TIER" = "simple" ]; then
  HINT="[AgentKit] Routing: simple task → Haiku speed. Be concise and direct."
fi

if [ -n "$HINT" ]; then
  python3 -c "
import json, sys
print(json.dumps({'system_prompt_suffix': '$HINT'}))
"
fi

exit 0
