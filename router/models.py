"""
AgentKit — Layer 1: Skill Router
Dataclasses shared across classifier, selector, and disclosure engine.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ClassificationResult:
    """Output of the Task Classifier."""
    primary_category: str          # e.g., "debugging"
    secondary_category: str        # e.g., "writing-tests" (empty string if none)
    confidence: float              # 0.0–1.0
    matched_keywords: list[str]    # keywords that triggered classification
    fallback_used: bool = False    # True if Haiku was called for ambiguous prompt


@dataclass
class SkillMeta:
    """Metadata for a single skill from the registry."""
    id: str
    name: str
    category: str
    priority: int                  # 1=core, 2=supplemental, 3=reference
    path: str                      # relative path to SKILL.md file
    level1_tokens: int
    level2_tokens: int
    level3_tokens: int
    platforms: list[str]
    keywords: list[str]
    effectiveness: float = 1.0    # 0.0–1.0, from marketplace ratings
    personal_weight: float = 1.0  # adjusted by personal model (Phase 4)


@dataclass
class SkillSelection:
    """A skill selected to be loaded, with its disclosure level."""
    meta: SkillMeta
    level: int = 1                 # current disclosure level (1, 2, or 3)
    content: str = ""             # loaded content at current level


@dataclass
class RouterOutput:
    """Final output of the full skill router pipeline."""
    classification: ClassificationResult
    selected_skills: list[SkillSelection]
    injected_content: str          # ready-to-inject text for Claude's context
    total_tokens: int              # estimated tokens of injected_content
    loaded_skill_ids: list[str] = field(default_factory=list)
