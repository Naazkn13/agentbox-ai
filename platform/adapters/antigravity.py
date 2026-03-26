"""
AgentKit — Platform Adapter: Antigravity (Tier 1 — Full)
Converts SKILL.md → plugin YAML in .antigravity/plugins/
"""

from __future__ import annotations

import os
from pathlib import Path

from platform.adapter import (
    AgentKitConfig, InstallResult, PlatformAdapter,
    Skill, extract_level, register,
)


@register
class AntigravityAdapter(PlatformAdapter):
    PLATFORM_ID   = "antigravity"
    PLATFORM_NAME = "Antigravity"
    TIER = 1

    def detect(self) -> bool:
        import shutil
        return (
            shutil.which("antigravity") is not None
            or (self.project_root / ".antigravity").exists()
        )

    def convert_skill(self, skill: Skill) -> dict:
        level2 = extract_level(skill.content, 2) or skill.level1
        return {
            "name":        f"agentkit-{skill.id}",
            "description": skill.level1,
            "trigger":     {"keywords": skill.keywords or [skill.id]},
            "prompt":      level2,
            "priority":    skill.priority,
            "version":     skill.version,
        }

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        plugins_dir = self.project_root / ".antigravity" / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)

        try:
            import yaml as _yaml
            dumper = _yaml.dump
        except ImportError:
            dumper = _fallback_yaml_dump

        for skill in skills:
            plugin = self.convert_skill(skill)
            plugin_path = plugins_dir / f"agentkit-{skill.id}.yaml"
            plugin_path.write_text(dumper(plugin, default_flow_style=False))
            result.files_written.append(str(plugin_path))

        # Write model routing config
        routing_path = self.project_root / ".antigravity" / "agentkit.yaml"
        routing_path.write_text(dumper({
            "model_routing": {
                "enabled":        config.model_routing_enabled,
                "default_model":  config.default_model,
                "subagent_model": config.subagent_model,
            }
        }, default_flow_style=False))
        result.files_written.append(str(routing_path))

        return result


def _fallback_yaml_dump(data: dict, **kwargs) -> str:
    """Minimal YAML serialiser (no PyYAML dependency)."""
    lines = []
    for k, v in data.items():
        if isinstance(v, dict):
            lines.append(f"{k}:")
            for kk, vv in v.items():
                lines.append(f"  {kk}: {vv}")
        elif isinstance(v, list):
            lines.append(f"{k}:")
            for item in v:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{k}: {v}")
    return "\n".join(lines) + "\n"
