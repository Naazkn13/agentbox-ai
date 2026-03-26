"""
AgentKit CLI — Python installer bridge.
Called by install.js to run the Python platform adapters.
Outputs JSON: { success, filesWritten, error }
"""

from __future__ import annotations

import json
import os
import sys

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True)
    parser.add_argument("--skills",   required=True, help="Comma-separated skill IDs")
    parser.add_argument("--home",     required=True, help="AGENTKIT_HOME path")
    args = parser.parse_args()

    sys.path.insert(0, args.home)

    # Import all adapters so the registry is populated
    from platform.adapter import (
        get_adapter, load_skills, AgentKitConfig,
    )
    # Force adapter registration by importing the package
    import platform.adapters.claude_code
    import platform.adapters.cursor
    import platform.adapters.codex
    import platform.adapters.gemini_cli
    import platform.adapters.antigravity
    import platform.adapters.opencode
    import platform.adapters.aider
    import platform.adapters.windsurf
    import platform.adapters.kilo_code
    import platform.adapters.augment

    adapter = get_adapter(args.platform)
    if not adapter:
        print(json.dumps({
            "success": False,
            "filesWritten": [],
            "error": f"Unknown platform: {args.platform}",
        }))
        sys.exit(1)

    # Load skills from the AgentKit skills directory
    skills_dir = os.path.join(args.home, "skills")
    all_skills = load_skills(skills_dir)
    wanted_ids = set(args.skills.split(","))
    skills     = [s for s in all_skills if s.id in wanted_ids]

    if not skills:
        # Fall back to all skills if none matched
        skills = all_skills

    config = AgentKitConfig(agentkit_home=args.home)
    result = adapter.install(skills, config)

    print(json.dumps({
        "success":      result.success,
        "filesWritten": result.files_written,
        "error":        result.error,
    }))


if __name__ == "__main__":
    main()
