"""
AgentKit — Layer 1: Skill Selector
Picks the optimal 2-5 skills from the registry given classifier output.

Rules:
  - Max 3 skills from primary category (priority 1 first)
  - Max 2 skills from secondary category (only if confidence > 0.5)
  - Never exceed TOKEN_BUDGET tokens at Level 1
  - Never reload an already-loaded skill (session continuity)
  - Total selected: 2–5 skills
"""

from router.models import ClassificationResult, SkillMeta, SkillSelection
from router.registry import SkillRegistry, registry as _default_registry

TOKEN_BUDGET = 5_000   # max tokens from skill L1 content per session turn
MAX_PRIMARY = 3
MAX_SECONDARY = 2
SECONDARY_CONFIDENCE_THRESHOLD = 0.5


def select_skills(
    classification: ClassificationResult,
    currently_loaded: list[str] | None = None,
    platform: str = "claude-code",
    token_budget: int = TOKEN_BUDGET,
    reg: SkillRegistry | None = None,
) -> list[SkillSelection]:
    """
    Select the best 2-5 skills for the given classification.

    Args:
        classification:    Output from classifier.classify()
        currently_loaded:  Skill IDs already in context this session.
        platform:          Target platform (affects skill availability).
        token_budget:      Max Level-1 tokens to inject.
        reg:               SkillRegistry instance (uses module default if None).

    Returns:
        Ordered list of SkillSelection objects ready for the disclosure engine.
    """
    r = reg or _default_registry
    loaded = set(currently_loaded or [])
    candidates: list[SkillMeta] = []

    # ── Step 1: Primary category skills (priority 1 first, then 2) ──────────
    primary_skills = r.get_by_category(
        classification.primary_category, priority=1, platform=platform
    )
    candidates.extend(primary_skills[:MAX_PRIMARY])

    # Fill remaining primary slots with priority-2 if needed
    if len(candidates) < MAX_PRIMARY:
        p2 = r.get_by_category(
            classification.primary_category, priority=2, platform=platform
        )
        candidates.extend(p2[:MAX_PRIMARY - len(candidates)])

    # ── Step 2: Secondary category skills (if confidence warrants it) ────────
    if (
        classification.secondary_category
        and classification.confidence >= SECONDARY_CONFIDENCE_THRESHOLD
        and classification.secondary_category != classification.primary_category
    ):
        secondary_skills = r.get_by_category(
            classification.secondary_category, priority=1, platform=platform
        )
        candidates.extend(secondary_skills[:MAX_SECONDARY])

    # ── Step 3: De-duplicate candidates (preserve order) ────────────────────
    seen: set[str] = set()
    unique_candidates: list[SkillMeta] = []
    for skill in candidates:
        if skill.id not in seen:
            seen.add(skill.id)
            unique_candidates.append(skill)

    # ── Step 4: Apply token budget (Level-1 tokens only) ────────────────────
    selected: list[SkillSelection] = []
    total_tokens = 0

    for skill in unique_candidates:
        # If already loaded in this session, keep it without consuming new budget
        if skill.id in loaded:
            selected.append(SkillSelection(meta=skill, level=1))
            continue

        if total_tokens + skill.level1_tokens <= token_budget:
            selected.append(SkillSelection(meta=skill, level=1))
            total_tokens += skill.level1_tokens

    # Guarantee at least 1 skill even if budget is extremely tight
    if not selected and unique_candidates:
        selected.append(SkillSelection(meta=unique_candidates[0], level=1))

    return selected
