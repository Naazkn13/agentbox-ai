"""
AgentKit — Cost Dashboard Hook (cross-platform Python equivalent of cost_dashboard.sh)
Event: PostToolUse
Purpose: Log token costs and refresh status line.
"""

import json
import os
import subprocess
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return

    session_id = data.get("session_id", "unknown")
    usage = data.get("usage", {})
    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    agentkit_home = os.environ.get("AGENTKIT_HOME", _REPO_ROOT)
    data_dir = os.path.join(agentkit_home, "data")
    os.makedirs(data_dir, exist_ok=True)

    # Load env vars
    env_file = os.path.join(data_dir, f"env_{session_id}.sh")
    model = "claude-sonnet-4-6"
    platform = "claude-code"
    skills = ""
    if os.path.exists(env_file):
        try:
            with open(env_file) as f:
                for line in f:
                    if "AGENTKIT_MODEL=" in line:
                        model = line.split("=", 1)[1].strip().strip("'\"")
                    elif "AGENTKIT_PLATFORM=" in line:
                        platform = line.split("=", 1)[1].strip().strip("'\"")
                    elif "AGENTKIT_SKILLS=" in line:
                        skills = line.split("=", 1)[1].strip().strip("'\"")
        except Exception:
            pass

    render_script = os.path.join(agentkit_home, "hooks", "render_dashboard.py")

    # Log if we have token counts
    if input_tokens > 0 or output_tokens > 0:
        try:
            subprocess.run(
                [sys.executable, render_script, "log",
                 "--model", model,
                 "--input", str(input_tokens),
                 "--output", str(output_tokens),
                 "--session-id", session_id,
                 "--platform", platform,
                 "--skills", skills],
                capture_output=True, timeout=10,
            )
        except Exception:
            pass

    # Refresh status line
    try:
        r = subprocess.run(
            [sys.executable, render_script, "status", "--session-id", session_id],
            capture_output=True, text=True, timeout=10,
        )
        if r.returncode == 0 and r.stdout.strip():
            try:
                d = json.loads(r.stdout.strip())
                status = d.get("status_line", "")
                with open(os.path.join(data_dir, "status_line.txt"), "w") as f:
                    f.write(status)
            except Exception:
                pass
    except Exception:
        pass


if __name__ == "__main__":
    main()
