"""
AgentKit — Layer 5: Platform Adapter Base
Base class and registry for all platform adapters.
Each adapter converts universal SKILL.md files → platform-native format.
"""

from __future__ import annotations

import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Skill data model (parsed from SKILL.md)
# ---------------------------------------------------------------------------


@dataclass
class Skill:
    id: str
    name: str
    category: str
    level1: str  # activation trigger (~50 tokens)
    content: str  # full raw SKILL.md content
    platforms: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    priority: int = 5
    level1_tokens: int = 50
    level2_tokens: int = 500
    level3_tokens: int = 2000
    version: str = "1.0.0"
    path: str = ""


@dataclass
class AgentKitConfig:
    model_routing_enabled: bool = True
    default_model: str = "claude-sonnet-4-6"
    subagent_model: str = "claude-haiku-4-5-20251001"
    memory_enabled: bool = True
    quality_gates_enabled: bool = True
    workflow_enforcement: bool = True
    agentkit_home: str = ""
    python_cmd: str = "python3"  # "python3" on Mac/Linux, "python" on Windows


@dataclass
class InstallResult:
    platform: str
    success: bool
    files_written: list[str] = field(default_factory=list)
    error: str = ""


# ---------------------------------------------------------------------------
# Level extraction helpers
# ---------------------------------------------------------------------------

_LEVEL_PATTERN = re.compile(
    r"<!--\s*LEVEL\s+(\d)\s*START\s*-->(.+?)<!--\s*LEVEL\s+\d\s*END\s*-->",
    re.DOTALL | re.IGNORECASE,
)


def extract_level(content: str, level: int) -> str:
    """Extract a LEVEL N section from SKILL.md content."""
    for match in _LEVEL_PATTERN.finditer(content):
        if int(match.group(1)) == level:
            return match.group(2).strip()
    # Fallback: return content between level markers using heading heuristics
    return _fallback_extract(content, level)


def _fallback_extract(content: str, level: int) -> str:
    """Heuristic extraction when HTML comment markers are absent."""
    lines = content.splitlines()
    # Level 1 = first non-frontmatter paragraph
    if level == 1:
        in_front = False
        for i, line in enumerate(lines):
            if line.strip() == "---":
                in_front = not in_front
                continue
            if not in_front and line.strip():
                return line.strip()
    return ""


def parse_skill_file(path: str) -> Optional[Skill]:
    """Parse a SKILL.md file into a Skill object."""
    try:
        content = Path(path).read_text()
    except Exception:
        return None

    # Parse YAML frontmatter
    fm: dict = {}
    fm_match = re.match(r"^---\n(.+?)\n---\n", content, re.DOTALL)
    if fm_match:
        try:
            import yaml

            fm = yaml.safe_load(fm_match.group(1)) or {}
        except Exception:
            pass

    skill_id = fm.get("id", Path(path).stem)
    name = fm.get("name", skill_id.replace("-", " ").title())
    category = fm.get("category", "general")
    level1 = fm.get("level1", extract_level(content, 1) or name)
    platforms = fm.get("platforms", [])
    keywords = fm.get("keywords", [])

    return Skill(
        id=skill_id,
        name=name,
        category=category,
        level1=level1,
        content=content,
        platforms=platforms if isinstance(platforms, list) else [platforms],
        keywords=keywords if isinstance(keywords, list) else [keywords],
        priority=int(fm.get("priority", 5)),
        level1_tokens=int(fm.get("level1_tokens", 50)),
        level2_tokens=int(fm.get("level2_tokens", 500)),
        level3_tokens=int(fm.get("level3_tokens", 2000)),
        version=str(fm.get("version", "1.0.0")),
        path=str(path),
    )


def load_skills(skills_dir: str) -> list[Skill]:
    """Load all skill Markdown files from a directory tree.
    Accepts both `SKILL.md` (spec format) and `<id>.md` (legacy format).
    """
    skills = []
    for root, _, files in os.walk(skills_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            # Skip the registry file and top-level index files
            if fname in ("registry.md", "README.md", "index.md"):
                continue
            skill = parse_skill_file(os.path.join(root, fname))
            if skill:
                skills.append(skill)
    return skills


# ---------------------------------------------------------------------------
# Base adapter
# ---------------------------------------------------------------------------


class PlatformAdapter(ABC):
    """
    Abstract base for all platform adapters.
    Subclasses implement convert_skill() and install().
    """

    PLATFORM_ID: str = ""
    PLATFORM_NAME: str = ""
    TIER: int = 3  # 1=Full, 2=Partial, 3=Basic

    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root or os.getcwd())

    def _write(self, rel_path: str, content: str) -> str:
        """Write content to a path relative to project_root. Returns abs path."""
        abs_path = self.project_root / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_text(content)
        return str(abs_path)

    def _append(self, rel_path: str, content: str, marker: str = "") -> str:
        """Append to a file, skipping if marker already present."""
        abs_path = self.project_root / rel_path
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        existing = abs_path.read_text() if abs_path.exists() else ""
        if marker and marker in existing:
            return str(abs_path)
        abs_path.write_text(existing + "\n" + content if existing else content)
        return str(abs_path)

    @abstractmethod
    def convert_skill(self, skill: Skill) -> str:
        """Convert a Skill to the platform's native format string."""

    @abstractmethod
    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        """Install skills + config for this platform."""

    def uninstall(self) -> InstallResult:
        """Uninstall AgentKit from this platform."""
        return InstallResult(platform=self.PLATFORM_ID, success=True)

    def detect(self) -> bool:
        """Return True if this platform is present in the environment."""
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} platform={self.PLATFORM_ID}>"


# ---------------------------------------------------------------------------
# Adapter registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, type[PlatformAdapter]] = {}


def register(cls: type[PlatformAdapter]) -> type[PlatformAdapter]:
    """Class decorator to register an adapter."""
    _REGISTRY[cls.PLATFORM_ID] = cls
    return cls


def get_adapter(
    platform_id: str, project_root: str | None = None
) -> Optional[PlatformAdapter]:
    cls = _REGISTRY.get(platform_id)
    return cls(project_root) if cls else None


def all_adapters(project_root: str | None = None) -> list[PlatformAdapter]:
    return [cls(project_root) for cls in _REGISTRY.values()]


def detect_platforms(project_root: str | None = None) -> list[PlatformAdapter]:
    """Return adapters for platforms detected in the current environment."""
    return [a for a in all_adapters(project_root) if a.detect()]
