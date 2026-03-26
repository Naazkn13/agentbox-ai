"""
AgentKit — Platform Adapter: Codex CLI (Tier 3 — Basic)
Converts SKILL.md → appended sections in AGENTS.md
"""

from __future__ import annotations

import os
from pathlib import Path

from platform.adapter import (
    AgentKitConfig, InstallResult, PlatformAdapter,
    Skill, extract_level, register,
)

AGENTKIT_MARKER = "<!-- AGENTKIT_SKILLS_START -->"
AGENTKIT_END    = "<!-- AGENTKIT_SKILLS_END -->"
MEMORY_MARKER   = "<!-- AGENTKIT_MEMORY_INJECT -->"


@register
class CodexAdapter(PlatformAdapter):
    PLATFORM_ID   = "codex"
    PLATFORM_NAME = "Codex CLI"
    TIER = 3

    def detect(self) -> bool:
        import shutil
        return (
            bool(os.environ.get("OPENAI_API_KEY"))
            or shutil.which("codex") is not None
            or (self.project_root / "AGENTS.md").exists()
        )

    def convert_skill(self, skill: Skill) -> str:
        level2 = extract_level(skill.content, 2) or skill.level1
        return (
            f"### {skill.name}\n"
            f"**Activate when:** {skill.level1}\n\n"
            f"{level2}\n"
        )

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        agents_path = self.project_root / "AGENTS.md"
        existing    = agents_path.read_text() if agents_path.exists() else ""

        # Remove old AgentKit block if present
        existing = _remove_block(existing, AGENTKIT_MARKER, AGENTKIT_END)

        # Build new AgentKit block
        skills_section = "\n".join(self.convert_skill(s) for s in skills)
        agentkit_block = (
            f"\n{AGENTKIT_MARKER}\n"
            f"## AgentKit Skills\n\n"
            f"{skills_section}\n"
            f"## Project Memory\n"
            f"{MEMORY_MARKER}\n"
            f"{AGENTKIT_END}\n"
        )

        agents_path.write_text(existing.rstrip() + agentkit_block)
        result.files_written.append(str(agents_path))
        return result


def _remove_block(content: str, start: str, end: str) -> str:
    import re
    pattern = re.escape(start) + r".*?" + re.escape(end)
    return re.sub(pattern, "", content, flags=re.DOTALL)
