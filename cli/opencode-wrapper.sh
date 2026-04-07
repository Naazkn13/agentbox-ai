#!/usr/bin/env bash
# AgentKit — OpenCode launcher wrapper
# Prints the AgentKit banner in the terminal BEFORE OpenCode's TUI starts,
# so users always see AgentKit is active when they open OpenCode.
#
# Usage: add this to your shell config:
#   alias opencode='bash /path/to/agentkit/cli/opencode-wrapper.sh'
# Or install globally:
#   agentkit init   (automatically adds alias to ~/.zshrc / ~/.bashrc)

AGENTKIT_HOME="${AGENTKIT_HOME:-$(dirname "$(dirname "$(realpath "$0")")")}"
OPENCODE_BIN="${OPENCODE_BIN:-$(which opencode 2>/dev/null || echo opencode)}"

# Print banner to the raw terminal (before TUI takes over)
python3 "$AGENTKIT_HOME/hooks/render_dashboard.py" banner \
  --platform "opencode" 2>/dev/null || true

echo ""
echo "  Starting OpenCode..."
echo ""

# Small pause so user sees the banner before TUI clears the screen
sleep 0.8

# Hand off to the real opencode binary
exec "$OPENCODE_BIN" "$@"
