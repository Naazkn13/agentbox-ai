"""
AgentKit — Platform Adapter: Windsurf (Tier 2 — Partial)
Converts SKILL.md → .windsurf/rules.md (Cascade rules format)
"""

from __future__ import annotations

import re
from pathlib import Path

from platform.adapter import (
    AgentKitConfig, InstallResult, PlatformAdapter,
    Skill, extract_level, register,
)

AGENTKIT_MARKER = "<!-- AGENTKIT_START -->"
AGENTKIT_END    = "<!-- AGENTKIT_END -->"


@register
class WindsurfAdapter(PlatformAdapter):
    PLATFORM_ID   = "windsurf"
    PLATFORM_NAME = "Windsurf"
    TIER = 2

    def detect(self) -> bool:
        import shutil
        return (
            shutil.which("windsurf") is not None
            or (self.project_root / ".windsurf").exists()
        )

    def convert_skill(self, skill: Skill) -> str:
        level2 = extract_level(skill.content, 2) or skill.level1
        return f"## {skill.name}\n**When to activate:** {skill.level1}\n\n{level2}\n"

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        windsurf_dir = self.project_root / ".windsurf"
        windsurf_dir.mkdir(parents=True, exist_ok=True)

        rules_path = windsurf_dir / "rules.md"
        existing   = rules_path.read_text() if rules_path.exists() else ""

        # Remove old AgentKit block
        existing = re.sub(
            re.escape(AGENTKIT_MARKER) + r".*?" + re.escape(AGENTKIT_END),
            "",
            existing,
            flags=re.DOTALL,
        ).strip()

        skills_block = "\n\n".join(self.convert_skill(s) for s in skills)
        agentkit_block = (
            f"\n{AGENTKIT_MARKER}\n"
            f"# AgentKit Skills\n\n"
            f"{skills_block}\n"
            f"{AGENTKIT_END}\n"
        )

        rules_path.write_text((existing + agentkit_block).strip())
        result.files_written.append(str(rules_path))
        return result
