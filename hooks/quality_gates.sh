#!/usr/bin/env bash
# AgentKit — Layer 4: Quality Gates Hook
# Event: PostToolUse (matcher: Edit|Write|MultiEdit)
#
# Runs syntax → lint → types → tests on the edited file.
# Prints results inline. Does NOT block (exit 0 always) — acts as a reminder,
# not a hard block, so Claude can read the output and self-correct.
# Set AGENTKIT_GATES_BLOCK=true to make failures block the next tool call.

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

AGENTKIT_HOME="${AGENTKIT_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
BLOCK_ON_FAILURE="${AGENTKIT_GATES_BLOCK:-false}"

# ── Extract the file that was edited ────────────────────────────────────────
INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | $PYTHON -c "
import sys, json
d = json.load(sys.stdin)
inp = d.get('tool_input', {})
for key in ('file_path', 'path'):
    if key in inp:
        print(inp[key])
        break
" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Only check source files — skip generated files, lock files, configs, etc.
EXT="${FILE_PATH##*.}"
case "$EXT" in
  py|ts|tsx|js|jsx|go|rs) ;;
  *) exit 0 ;;
esac

# Skip test files themselves triggering further checks (infinite loop guard)
if [[ "$FILE_PATH" == *"test_"* ]] || [[ "$FILE_PATH" == *"_test."* ]] || [[ "$FILE_PATH" == *".test."* ]] || [[ "$FILE_PATH" == *".spec."* ]]; then
  # Still run syntax check on test files
  if [ "$EXT" = "py" ]; then
    $PYTHON -m py_compile "$FILE_PATH" 2>&1 && echo "✓ syntax ($FILE_PATH)" || echo "✗ syntax ($FILE_PATH)"
  fi
  exit 0
fi

# ── Run quality gates via Python ─────────────────────────────────────────────
OUTPUT=$($PYTHON "$AGENTKIT_HOME/workflow/quality_gates.py" "$FILE_PATH" 2>&1)
EXIT_CODE=$?

echo "$OUTPUT"

# Update workflow state if all gates passed
if [ $EXIT_CODE -eq 0 ]; then
  $PYTHON "$AGENTKIT_HOME/workflow/enforcer.py" on-edit "$FILE_PATH" 2>/dev/null || true
fi

# Block or warn based on config
if [ $EXIT_CODE -ne 0 ] && [ "$BLOCK_ON_FAILURE" = "true" ]; then
  exit 2   # exit 2 = block in Claude Code hooks
fi

exit 0
