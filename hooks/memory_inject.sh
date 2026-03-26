#!/usr/bin/env bash
# AgentKit — Memory Inject Hook
# Event: UserPromptSubmit (runs alongside skill_router_hook)
# Purpose: Inject relevant project memory into Claude's context before each turn.
#
# Output to stdout is prepended to Claude's context by Claude Code.

set -euo pipefail

INPUT=$(cat)

AGENTKIT_HOME="${AGENTKIT_HOME:-$(dirname "$(dirname "$(realpath "$0")")")}"

# Run injector — output goes to Claude's context
echo "$INPUT" | python3 "${AGENTKIT_HOME}/memory/injector.py"

exit 0
