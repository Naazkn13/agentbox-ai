"""
AgentKit — Layer 1: Skill Registry
Loads skills/registry.yaml and provides a query interface for the selector.
"""

import os
import yaml
from functools import lru_cache
from router.models import SkillMeta

# Default registry path — can be overridden via AGENTKIT_HOME env var
_DEFAULT_REGISTRY = os.path.join(
    os.path.dirname(__file__), "..", "skills", "registry.yaml"
)


@lru_cache(maxsize=1)
def _load_registry(registry_path: str) -> list[SkillMeta]:
    """Load and parse skills/registry.yaml. Cached after first load."""
    with open(registry_path, "r") as f:
        data = yaml.safe_load(f)

    skills = []
    for entry in data.get("skills", []):
        skills.append(SkillMeta(
            id=entry["id"],
            name=entry["name"],
            category=entry["category"],
            priority=entry.get("priority", 2),
            path=entry["path"],
            level1_tokens=entry.get("level1_tokens", 50),
            level2_tokens=entry.get("level2_tokens", 500),
            level3_tokens=entry.get("level3_tokens", 2000),
            platforms=entry.get("platforms", ["claude-code"]),
            keywords=entry.get("keywords", []),
            effectiveness=entry.get("effectiveness", 1.0),
            personal_weight=entry.get("personal_weight", 1.0),
        ))
    return skills


class SkillRegistry:
    """Query interface for the skill registry."""

    def __init__(self, registry_path: str | None = None):
        agentkit_home = os.environ.get("AGENTKIT_HOME", "")
        if registry_path:
            self._path = registry_path
        elif agentkit_home:
            self._path = os.path.join(agentkit_home, "skills", "registry.yaml")
        else:
            self._path = os.path.normpath(_DEFAULT_REGISTRY)

    @property
    def _skills(self) -> list[SkillMeta]:
        return _load_registry(self._path)

    def get_by_category(
        self,
        category: str,
        priority: int | None = None,
        platform: str = "claude-code",
    ) -> list[SkillMeta]:
        """
        Return skills matching a category, optionally filtered by priority.
        Results are sorted by: priority ASC, effectiveness DESC, personal_weight DESC.
        """
        results = [
            s for s in self._skills
            if s.category == category
            and platform in s.platforms
            and (priority is None or s.priority == priority)
        ]
        results.sort(key=lambda s: (s.priority, -s.effectiveness, -s.personal_weight))
        return results

    def get_by_id(self, skill_id: str) -> SkillMeta | None:
        """Return a single skill by its ID."""
        for skill in self._skills:
            if skill.id == skill_id:
                return skill
        return None

    def get_all(self, platform: str = "claude-code") -> list[SkillMeta]:
        """Return all skills for a given platform."""
        return [s for s in self._skills if platform in s.platforms]

    def reload(self) -> None:
        """Force a cache reload (useful in long-running processes)."""
        _load_registry.cache_clear()

    def resolve_path(self, skill: SkillMeta) -> str:
        """Resolve the absolute path to a skill's SKILL.md file."""
        agentkit_home = os.environ.get("AGENTKIT_HOME", "")
        if agentkit_home:
            return os.path.join(agentkit_home, skill.path)
        # Relative to the repo root (one level above router/)
        repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(repo_root, skill.path)


# Module-level singleton for convenience
registry = SkillRegistry()
