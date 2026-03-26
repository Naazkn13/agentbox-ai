"""
AgentKit — Skill Router Hook
Triggered by Claude Code on UserPromptSubmit.

Reads JSON from stdin (Claude Code hook format), runs the full
classifier → selector → disclosure pipeline, and prints the
skill injection block to stdout (Claude sees this as context).

Claude Code hook stdin format:
{
  "session_id": "...",
  "transcript_path": "...",
  "cwd": "...",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "the user's prompt text"
}
"""

import sys
import os
import json
import subprocess

# Resolve repo root so imports work regardless of cwd
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from router.classifier import classify
from router.selector import select_skills
from router.disclosure import run_router
from router.registry import SkillRegistry


def _get_modified_files(cwd: str) -> list[str]:
    """Get list of files currently modified or staged in the repo."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]
        # Also grab staged files
        result2 = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        staged = [f.strip() for f in result2.stdout.splitlines() if f.strip()]
        return list(set(files + staged))
    except Exception:
        return []


def _get_branch(cwd: str) -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _load_session_state(session_id: str) -> dict:
    """Load persisted session state (currently loaded skills, etc.)."""
    state_file = os.path.join(_REPO_ROOT, "data", f"session_{session_id}.json")
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                return json.load(f)
        except Exception:
            pass
    return {"loaded_skill_ids": [], "turn_count": 0}


def _save_session_state(session_id: str, state: dict) -> None:
    """Persist session state between hook invocations."""
    os.makedirs(os.path.join(_REPO_ROOT, "data"), exist_ok=True)
    state_file = os.path.join(_REPO_ROOT, "data", f"session_{session_id}.json")
    try:
        with open(state_file, "w") as f:
            json.dump(state, f)
    except Exception:
        pass


def main() -> None:
    # Read hook input from Claude Code
    try:
        raw = sys.stdin.read()
        hook_data = json.loads(raw) if raw.strip() else {}
    except Exception:
        hook_data = {}

    prompt = hook_data.get("prompt", "")
    cwd = hook_data.get("cwd", os.getcwd())
    session_id = hook_data.get("session_id", "unknown")

    if not prompt:
        sys.exit(0)

    # Load persisted session state
    state = _load_session_state(session_id)
    currently_loaded = state.get("loaded_skill_ids", [])
    turn_count = state.get("turn_count", 0)

    # Gather context signals
    files = _get_modified_files(cwd)
    branch = _get_branch(cwd)

    # Determine platform (default claude-code)
    platform = os.environ.get("AGENTKIT_PLATFORM", "claude-code")

    # Run the full router pipeline
    reg = SkillRegistry()
    classification = classify(prompt, files=files, branch=branch)
    selections = select_skills(
        classification,
        currently_loaded=currently_loaded,
        platform=platform,
        reg=reg,
    )

    # Build escalation context based on turn count
    escalation_context = {
        "task_confirmed": turn_count > 0,
        "first_tool_in_category": turn_count == 0,
    }

    output = run_router(classification, selections, context=escalation_context, reg=reg)

    # Update and persist session state
    state["loaded_skill_ids"] = output.loaded_skill_ids
    state["turn_count"] = turn_count + 1
    state["last_category"] = classification.primary_category
    _save_session_state(session_id, state)

    # Export loaded skills for forced_eval hook
    skill_ids_str = ",".join(output.loaded_skill_ids)
    # Write to a temp file that forced_eval.sh can read
    env_file = os.path.join(_REPO_ROOT, "data", f"env_{session_id}.sh")
    os.makedirs(os.path.join(_REPO_ROOT, "data"), exist_ok=True)
    with open(env_file, "w") as f:
        f.write(f'AGENTKIT_LOADED_SKILLS="{skill_ids_str}"\n')
        f.write(f'AGENTKIT_TASK_CATEGORY="{classification.primary_category}"\n')
        f.write(f'AGENTKIT_SESSION_ID="{session_id}"\n')

    # Print injected skill content — Claude Code prepends this to context
    if output.injected_content:
        print(output.injected_content)

    # Debug info to stderr (not shown to Claude, only in hook logs)
    print(
        f"[AgentKit] category={classification.primary_category} "
        f"confidence={classification.confidence:.2f} "
        f"skills={skill_ids_str} "
        f"tokens={output.total_tokens}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
