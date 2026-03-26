"""
AgentKit — Platform Adapter: Kilo Code (Tier 2 — Partial)
Converts SKILL.md → .kilo/plugins/*.yaml
"""

from __future__ import annotations

from pathlib import Path

from platform.adapter import (
    AgentKitConfig, InstallResult, PlatformAdapter,
    Skill, extract_level, register,
)


@register
class KiloCodeAdapter(PlatformAdapter):
    PLATFORM_ID   = "kilo-code"
    PLATFORM_NAME = "Kilo Code"
    TIER = 2

    def detect(self) -> bool:
        import shutil
        return (
            shutil.which("kilo") is not None
            or (self.project_root / ".kilo").exists()
        )

    def convert_skill(self, skill: Skill) -> dict:
        level2 = extract_level(skill.content, 2) or skill.level1
        return {
            "id":          f"agentkit-{skill.id}",
            "name":        skill.name,
            "description": skill.level1,
            "keywords":    skill.keywords,
            "prompt":      level2,
        }

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        plugins_dir = self.project_root / ".kilo" / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)

        try:
            import yaml
            for skill in skills:
                plugin = self.convert_skill(skill)
                path   = plugins_dir / f"agentkit-{skill.id}.yaml"
                path.write_text(yaml.dump(plugin, default_flow_style=False))
                result.files_written.append(str(path))
        except ImportError:
            result.error   = "PyYAML not installed — run: pip3 install PyYAML"
            result.success = False

        return result
