"""
AgentKit — Platform Adapter: Gemini CLI (Tier 2 — Partial)
Converts SKILL.md → system prompt extension in .gemini/config.yaml
"""

from __future__ import annotations

import os
from pathlib import Path

from platform.adapter import (
    AgentKitConfig, InstallResult, PlatformAdapter,
    Skill, extract_level, register,
)


@register
class GeminiCLIAdapter(PlatformAdapter):
    PLATFORM_ID   = "gemini-cli"
    PLATFORM_NAME = "Gemini CLI"
    TIER = 2

    def detect(self) -> bool:
        import shutil
        return (
            bool(os.environ.get("GEMINI_API_KEY"))
            or shutil.which("gemini") is not None
            or (self.project_root / ".gemini").exists()
        )

    def convert_skill(self, skill: Skill) -> str:
        level2 = extract_level(skill.content, 2) or skill.level1
        return f"**{skill.name}** (activate when: {skill.level1})\n{level2}\n"

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        gemini_dir = self.project_root / ".gemini"
        gemini_dir.mkdir(parents=True, exist_ok=True)

        # Build system prompt extension
        skills_text = "\n\n".join(self.convert_skill(s) for s in skills)
        analytics_block = self._build_analytics_block()
        system_prompt = (
            f"## AgentKit — Skill Instructions\n\n{skills_text}\n\n"
            f"{analytics_block}"
        )

        # Write GEMINI.md (system prompt extension file)
        gemini_md = gemini_dir / "GEMINI.md"
        gemini_md.write_text(system_prompt)
        result.files_written.append(str(gemini_md))

        # Write config.yaml
        config_path = gemini_dir / "config.yaml"
        existing: dict = {}
        if config_path.exists():
            try:
                import yaml
                existing = yaml.safe_load(config_path.read_text()) or {}
            except Exception:
                pass

        existing["system_prompt_file"] = ".gemini/GEMINI.md"
        if config.model_routing_enabled:
            existing["model"] = config.default_model

        try:
            import yaml
            config_path.write_text(yaml.dump(existing, default_flow_style=False))
        except ImportError:
            # Fallback: write minimal YAML manually
            config_path.write_text(
                f"system_prompt_file: .gemini/GEMINI.md\n"
                f"model: {config.default_model}\n"
            )
        result.files_written.append(str(config_path))

        return result

    def _build_analytics_block(self) -> str:
        try:
            import subprocess
            import sys
            agentkit_home = str(Path(__file__).parent.parent.parent)
            res = subprocess.run(
                [sys.executable, str(Path(agentkit_home) / "hooks" / "render_dashboard.py"),
                 "analytics-md", "--days", "7"],
                capture_output=True, text=True, timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return "<!-- AGENTKIT_ANALYTICS_START -->\n## AgentKit Analytics\nRun `agentkit analytics` in terminal.\n<!-- AGENTKIT_ANALYTICS_END -->"
