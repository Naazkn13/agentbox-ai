"""
AgentKit — Platform Adapter: Augment Code (Tier 3 — Basic, skills only)
Writes skill context to .augment/context.md
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
class AugmentAdapter(PlatformAdapter):
    PLATFORM_ID   = "augment"
    PLATFORM_NAME = "Augment Code"
    TIER = 3

    def detect(self) -> bool:
        import shutil
        return (
            shutil.which("augment") is not None
            or (self.project_root / ".augment").exists()
        )

    def convert_skill(self, skill: Skill) -> str:
        level2 = extract_level(skill.content, 2) or skill.level1
        return f"### {skill.name}\n{skill.level1}\n\n{level2}\n"

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        augment_dir = self.project_root / ".augment"
        augment_dir.mkdir(parents=True, exist_ok=True)

        context_path = augment_dir / "context.md"
        existing     = context_path.read_text() if context_path.exists() else ""

        existing = re.sub(
            re.escape(AGENTKIT_MARKER) + r".*?" + re.escape(AGENTKIT_END),
            "",
            existing,
            flags=re.DOTALL,
        ).strip()

        skills_text = "\n".join(self.convert_skill(s) for s in skills)
        block = (
            f"\n{AGENTKIT_MARKER}\n"
            f"## AgentKit Skills\n\n"
            f"{skills_text}\n"
            f"{AGENTKIT_END}\n"
        )

        context_path.write_text((existing + block).strip())
        result.files_written.append(str(context_path))
        return result
