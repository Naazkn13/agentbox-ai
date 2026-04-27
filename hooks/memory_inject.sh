#!/usr/bin/env bash
# AgentKit — Memory Inject Hook
# Event: UserPromptSubmit (runs alongside skill_router_hook)
# Purpose: Inject relevant project memory into Claude's context before each turn.
#
# Output to stdout is prepended to Claude's context by Claude Code.

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

INPUT=$(cat)

AGENTKIT_HOME="${AGENTKIT_HOME:-$(dirname "$(dirname "$(realpath "$0")")")}"

# Run injector — output goes to Claude's context
echo "$INPUT" | $PYTHON "${AGENTKIT_HOME}/memory/injector.py"

exit 0
