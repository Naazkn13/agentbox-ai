"""
AgentKit — Platform Adapter: Cursor (Tier 2 — Partial)
Converts SKILL.md Level 2 content → .mdc rule files in .cursor/rules/
"""

from __future__ import annotations

import os
from pathlib import Path

from platform.adapter import (
    AgentKitConfig, InstallResult, PlatformAdapter,
    Skill, extract_level, register,
)

# Map categories → file globs Cursor should activate the rule for
CATEGORY_GLOBS: dict[str, str] = {
    "debugging":    "**/*.py,**/*.ts,**/*.js,**/*.go,**/*.rs",
    "testing":      "**/*.test.*,**/*.spec.*,**/test_*.py,**/*_test.go",
    "ui":           "**/*.tsx,**/*.jsx,**/*.css,**/*.scss",
    "db":           "**/migrations/**,**/*.sql,**/schema.*,**/prisma/**",
    "api":          "**/routes/**,**/api/**,**/endpoints/**",
    "devops":       "**/Dockerfile,**/docker-compose.*,**/*.yaml,**/*.yml",
    "security":     "**/auth/**,**/middleware/**,**/*.env*",
    "refactoring":  "**/*.py,**/*.ts,**/*.js",
    "ai-engineering": "**/*.py",
}


@register
class CursorAdapter(PlatformAdapter):
    PLATFORM_ID   = "cursor"
    PLATFORM_NAME = "Cursor"
    TIER = 2

    def detect(self) -> bool:
        import shutil
        return (
            (Path.home() / ".cursor").exists()
            or (self.project_root / ".cursor").exists()
            or (self.project_root / ".cursorrules").exists()
            or shutil.which("cursor") is not None
        )

    def convert_skill(self, skill: Skill) -> str:
        level2 = extract_level(skill.content, 2)
        if not level2:
            # Fall back to full content minus frontmatter
            level2 = _strip_frontmatter(skill.content)

        globs = CATEGORY_GLOBS.get(skill.category, "**/*")
        return (
            f"---\n"
            f"description: {skill.level1}\n"
            f"globs: {globs}\n"
            f"alwaysApply: false\n"
            f"---\n\n"
            f"# {skill.name}\n\n"
            f"{level2}\n"
        )

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        rules_dir = self.project_root / ".cursor" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        for skill in skills:
            mdc_content = self.convert_skill(skill)
            mdc_path = rules_dir / f"agentkit-{skill.id}.mdc"
            mdc_path.write_text(mdc_content)
            result.files_written.append(str(mdc_path))

        # Write a global AgentKit model-routing rule
        routing_rule = _model_routing_rule()
        routing_path = rules_dir / "agentkit-model-routing.mdc"
        routing_path.write_text(routing_rule)
        result.files_written.append(str(routing_path))

        return result


def _strip_frontmatter(content: str) -> str:
    import re
    return re.sub(r"^---\n.+?\n---\n", "", content, flags=re.DOTALL).strip()


def _model_routing_rule() -> str:
    return """\
---
description: AgentKit model routing guidance
globs: "**/*"
alwaysApply: true
---

# AgentKit — Model Routing

Use the cheapest model that can handle the task:
- **Simple tasks** (search, rename, read): respond directly and concisely
- **Standard tasks** (most coding): standard thoughtful response
- **Complex tasks** (architecture, security audit): think carefully, explore trade-offs

For subagent-style tasks: be concise — imagine you're running on a budget model.
"""
