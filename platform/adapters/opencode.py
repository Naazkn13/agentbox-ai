"""
AgentKit — Platform Adapter: OpenCode (Tier 2 — Partial)
Converts SKILL.md → system prompt in .opencode/config.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from platform.adapter import (
    AgentKitConfig,
    InstallResult,
    PlatformAdapter,
    Skill,
    extract_level,
    register,
)

AGENTKIT_MARKER = "<!-- AGENTKIT_START -->"
AGENTKIT_END = "<!-- AGENTKIT_END -->"


@register
class OpenCodeAdapter(PlatformAdapter):
    PLATFORM_ID = "opencode"
    PLATFORM_NAME = "OpenCode"
    TIER = 2

    def detect(self) -> bool:
        import shutil

        return (
            shutil.which("opencode") is not None
            or (self.project_root / ".opencode").exists()
        )

    def convert_skill(self, skill: Skill) -> str:
        level2 = extract_level(skill.content, 2) or skill.level1
        return f"**{skill.name}**: {skill.level1}\n{level2}"

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        global_config = Path.home() / ".opencode.json"
        global_dir = Path.home() / ".opencode"

        cfg: dict = {}
        if global_config.exists():
            try:
                cfg = json.loads(global_config.read_text())
            except Exception:
                pass

        skills_prompt = (
            f"{AGENTKIT_MARKER}\n"
            f"## AgentKit Skills\n\n"
            + "\n\n".join(self.convert_skill(s) for s in skills)
            + f"\n{AGENTKIT_END}"
        )

        existing_prompt = cfg.get("system_prompt", "")
        import re

        existing_prompt = re.sub(
            re.escape(AGENTKIT_MARKER) + r".*?" + re.escape(AGENTKIT_END),
            "",
            existing_prompt,
            flags=re.DOTALL,
        ).strip()

        cfg["system_prompt"] = (existing_prompt + "\n\n" + skills_prompt).strip()
        if config.model_routing_enabled:
            cfg["model"] = config.default_model

        global_config.write_text(json.dumps(cfg, indent=2))
        result.files_written.append(str(global_config))
        return result

    def uninstall(self) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)
        global_config = Path.home() / ".opencode.json"

        if global_config.exists():
            try:
                cfg = json.loads(global_config.read_text())
                existing_prompt = cfg.get("system_prompt", "")
                import re

                cleaned = re.sub(
                    re.escape(AGENTKIT_MARKER) + r".*?" + re.escape(AGENTKIT_END),
                    "",
                    existing_prompt,
                    flags=re.DOTALL,
                ).strip()
                cfg["system_prompt"] = cleaned
                global_config.write_text(json.dumps(cfg, indent=2))
                result.files_written.append(str(global_config))
            except Exception as e:
                result.error = str(e)

        return result
