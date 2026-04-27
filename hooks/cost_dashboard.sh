#!/usr/bin/env bash
# AgentKit — Layer 3: Cost Dashboard Hook
# Event: PostToolUse (fires after every tool call that produces token counts)
#
# Reads the PostToolUse JSON from stdin. If it contains token usage data,
# logs the cost to data/costs.jsonl and writes the updated status line to
# data/status_line.txt (read by the Claude Code status bar integration).

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

AGENTKIT_HOME="${AGENTKIT_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
DATA_DIR="$AGENTKIT_HOME/data"
mkdir -p "$DATA_DIR"

INPUT=$(cat)

# Extract fields
SESSION_ID=$(echo "$INPUT" | $PYTHON -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('session_id', 'unknown'))
" 2>/dev/null || echo "unknown")

# Try to get token counts from the hook payload
# Claude Code PostToolUse may include usage in tool_result
INPUT_TOKENS=$(echo "$INPUT" | $PYTHON -c "
import sys, json
d = json.load(sys.stdin)
usage = d.get('usage', {})
print(usage.get('input_tokens', 0))
" 2>/dev/null || echo "0")

OUTPUT_TOKENS=$(echo "$INPUT" | $PYTHON -c "
import sys, json
d = json.load(sys.stdin)
usage = d.get('usage', {})
print(usage.get('output_tokens', 0))
" 2>/dev/null || echo "0")

# Load model, platform, and active skills from env vars written by model_router_hook.sh
ENV_FILE="$DATA_DIR/env_${SESSION_ID}.sh"
MODEL="claude-sonnet-4-6"   # default
PLATFORM="claude-code"
SKILLS=""
if [ -f "$ENV_FILE" ]; then
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  MODEL="${AGENTKIT_MODEL:-claude-sonnet-4-6}"
  PLATFORM="${AGENTKIT_PLATFORM:-claude-code}"
  SKILLS="${AGENTKIT_SKILLS:-}"
fi

# Only log if we have non-zero token counts
if [ "$INPUT_TOKENS" -gt 0 ] || [ "$OUTPUT_TOKENS" -gt 0 ]; then
  $PYTHON "$AGENTKIT_HOME/hooks/render_dashboard.py" log \
    --model      "$MODEL" \
    --input      "$INPUT_TOKENS" \
    --output     "$OUTPUT_TOKENS" \
    --session-id "$SESSION_ID" \
    --platform   "$PLATFORM" \
    --skills     "$SKILLS" \
    > /dev/null 2>&1 || true
fi

# Always refresh the status line file
$PYTHON "$AGENTKIT_HOME/hooks/render_dashboard.py" status \
  --session-id "$SESSION_ID" \
  2>/dev/null | $PYTHON -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('status_line', ''))
except Exception:
    print('')
" > "$DATA_DIR/status_line.txt" 2>/dev/null || true

exit 0
