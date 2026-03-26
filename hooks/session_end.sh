#!/usr/bin/env bash
# AgentKit — Session End Hook
# Event: Stop
# Purpose: Compress the session into a handoff document using Haiku.
#          Handoff is saved to .agentkit/handoff.md in the project dir.
#
# Claude Code Stop hook stdin:
# {
#   "session_id": "...",
#   "cwd": "...",
#   "hook_event_name": "Stop"
# }

set -euo pipefail

INPUT=$(cat)

AGENTKIT_HOME="${AGENTKIT_HOME:-$(dirname "$(dirname "$(realpath "$0")")")}"

echo "$INPUT" | python3 "${AGENTKIT_HOME}/memory/handoff.py" generate

exit 0
