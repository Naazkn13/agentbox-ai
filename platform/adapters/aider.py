"""
AgentKit — Platform Adapter: Aider (Tier 3 — Basic)
Appends skill conventions to .aider.conf.yml
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from platform.adapter import (
    AgentKitConfig, InstallResult, PlatformAdapter,
    Skill, extract_level, register,
)

AGENTKIT_MARKER = "# --- AgentKit skills start ---"
AGENTKIT_END    = "# --- AgentKit skills end ---"


@register
class AiderAdapter(PlatformAdapter):
    PLATFORM_ID   = "aider"
    PLATFORM_NAME = "Aider"
    TIER = 3

    def detect(self) -> bool:
        import shutil
        return (
            shutil.which("aider") is not None
            or (self.project_root / ".aider.conf.yml").exists()
            or (Path.home() / ".aider.conf.yml").exists()
        )

    def convert_skill(self, skill: Skill) -> str:
        # Aider uses conventions as YAML multi-line strings
        level1 = skill.level1.replace("\n", " ")
        return f"  - \"{skill.name}: {level1}\""

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        conf_path = self.project_root / ".aider.conf.yml"
        existing  = conf_path.read_text() if conf_path.exists() else ""

        # Remove old AgentKit block
        existing = re.sub(
            re.escape(AGENTKIT_MARKER) + r".*?" + re.escape(AGENTKIT_END),
            "",
            existing,
            flags=re.DOTALL,
        ).strip()

        skill_lines = "\n".join(self.convert_skill(s) for s in skills)
        agentkit_block = (
            f"\n{AGENTKIT_MARKER}\n"
            f"conventions:\n"
            f"{skill_lines}\n"
            f"{AGENTKIT_END}\n"
        )

        conf_path.write_text(existing + agentkit_block)
        result.files_written.append(str(conf_path))
        return result
