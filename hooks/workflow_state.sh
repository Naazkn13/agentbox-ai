#!/usr/bin/env bash
# AgentKit — Layer 4: Workflow State Hook
# Event: UserPromptSubmit
#
# Injects a brief workflow status reminder at the top of each turn so
# Claude always knows where it is in the Research→Plan→Execute→Review→Ship pipeline.
# Also detects explicit workflow commands in the prompt.

set -euo pipefail
# Cross-platform Python: $PYTHON on Linux/macOS, python on Windows
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "python3")

AGENTKIT_HOME="${AGENTKIT_HOME:-$(cd "$(dirname "$0")/.." && pwd)}"
PROJECT_ROOT="${AGENTKIT_PROJECT:-$(pwd)}"

INPUT=$(cat)

PROMPT=$(echo "$INPUT" | $PYTHON -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('prompt', ''))
" 2>/dev/null || echo "")

PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]')

# ── Handle explicit workflow commands in the prompt ─────────────────────────
if echo "$PROMPT_LOWER" | grep -qE "agentkit workflow (approve|reset|status|skip)"; then
  if echo "$PROMPT_LOWER" | grep -q "approve"; then
    $PYTHON "$AGENTKIT_HOME/workflow/enforcer.py" approve 2>/dev/null || true
  elif echo "$PROMPT_LOWER" | grep -q "reset"; then
    $PYTHON "$AGENTKIT_HOME/workflow/enforcer.py" reset 2>/dev/null || true
  fi
fi

# ── Get current workflow state ───────────────────────────────────────────────
STATE=$($PYTHON -c "
import sys
sys.path.insert(0, '$AGENTKIT_HOME')
from workflow.enforcer import WorkflowEnforcer
e = WorkflowEnforcer('$PROJECT_ROOT')
print(e.current_state())
" 2>/dev/null || echo "IDLE")

# ── Inject state hint (only for non-IDLE states) ─────────────────────────────
if [ "$STATE" != "IDLE" ]; then
  HINT=""
  case "$STATE" in
    RESEARCH)
      HINT="[AgentKit] Workflow: RESEARCH phase. Read relevant files before writing a plan."
      ;;
    PLAN)
      HINT="[AgentKit] Workflow: PLAN phase. Write your implementation plan to .agentkit/current_plan.md, then it will be approved."
      ;;
    EXECUTE)
      HINT="[AgentKit] Workflow: EXECUTE phase. Implement the plan. Quality gates will run after each edit."
      ;;
    REVIEW)
      HINT="[AgentKit] Workflow: REVIEW phase. Review output and ensure all quality gates pass before shipping."
      ;;
    SHIP)
      HINT="[AgentKit] Workflow: SHIP phase. Commit changes and create the PR."
      ;;
  esac

  if [ -n "$HINT" ]; then
    $PYTHON -c "
import json
print(json.dumps({'system_prompt_suffix': '$HINT'}))
"
  fi
fi

exit 0
