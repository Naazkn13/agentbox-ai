#!/usr/bin/env bash
# AgentKit — Layer 4: Research Gate Hook
# Event: PostToolUse (matcher: Read)
#
# Tracks how many files have been read this session.
# Updates the workflow enforcer so RESEARCH→PLAN gate works correctly.

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

AGENTKIT_HOME="${AGENTKIT_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
PROJECT_ROOT="${AGENTKIT_PROJECT:-$(pwd)}"

# ── Extract the file path that was read ─────────────────────────────────────
INPUT=$(cat)

FILE_PATH=$(echo "$INPUT" | $PYTHON -c "
import sys, json
d = json.load(sys.stdin)
inp = d.get('tool_input', {})
print(inp.get('file_path', inp.get('path', '')))
" 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Skip .agentkit internal files — they don't count as research
if [[ "$FILE_PATH" == *".agentkit"* ]]; then
  exit 0
fi

# ── Notify the enforcer ──────────────────────────────────────────────────────
$PYTHON "$AGENTKIT_HOME/workflow/enforcer.py" on-read "$FILE_PATH" 2>/dev/null || true

exit 0
