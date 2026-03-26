"""
AgentKit — Layer 3: Thinking Budget Tuner
Maps task complexity → extended thinking token budget.

Claude's extended thinking:
  0     tokens → no internal scratchpad (fastest, cheapest)
  8,192 tokens → moderate reasoning (most coding tasks)
  32,000 tokens → deep reasoning (architecture, security, root-cause)

Enabling thinking adds latency + cost but dramatically improves
output quality for complex tasks. For trivial tasks it's wasteful.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Budget tiers
# ---------------------------------------------------------------------------

THINKING_OFF      = 0        # trivial tasks — no scratchpad needed
THINKING_MODERATE = 8_192    # standard coding work
THINKING_DEEP     = 32_000   # complex architecture / security / debugging

# Task categories that warrant deep thinking
DEEP_THINKING_CATEGORIES: set[str] = {
    "architecting",
    "security",
    "debugging",       # intermittent bugs, root-cause
}

# Task categories that need no thinking at all
TRIVIAL_CATEGORIES: set[str] = {
    "read-only",
    "formatting",
    "search",
}

# Complexity-signal words that push toward deep thinking (independent of category)
DEEP_THINKING_SIGNALS: list[str] = [
    "root cause", "why is this", "investigate", "diagnose",
    "intermittent", "flaky", "race condition",
    "security audit", "threat model", "vulnerability",
    "architect", "design system", "trade-off", "scalab",
    "memory leak", "performance audit", "benchmark",
]

TRIVIAL_SIGNALS: list[str] = [
    "rename", "format", "fix typo", "add comment",
    "change the name", "update label", "what is", "show me",
    "list", "find", "search",
]


@dataclass
class ThinkingBudget:
    budget_tokens: int
    tier: str          # "off" | "moderate" | "deep"
    reason: str


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def get_thinking_budget(
    prompt: str,
    task_category: str = "",
    force_tier: str | None = None,
) -> ThinkingBudget:
    """
    Determine the extended thinking token budget for this turn.

    Priority:
      1. force_tier override (testing / manual)
      2. Prompt contains deep-thinking signals → deep
      3. Prompt contains trivial signals (2+) → off
      4. Category in DEEP_THINKING_CATEGORIES → deep
      5. Category in TRIVIAL_CATEGORIES → off
      6. Default → moderate
    """
    if force_tier:
        return _forced(force_tier)

    prompt_lower = prompt.lower()

    # Rule 1: deep signals in prompt
    deep_hits = [s for s in DEEP_THINKING_SIGNALS if s in prompt_lower]
    if deep_hits:
        return ThinkingBudget(
            budget_tokens=THINKING_DEEP,
            tier="deep",
            reason=f"deep signals: {', '.join(deep_hits[:2])}",
        )

    # Rule 2: 2+ trivial signals
    trivial_hits = [s for s in TRIVIAL_SIGNALS if s in prompt_lower]
    if len(trivial_hits) >= 2:
        return ThinkingBudget(
            budget_tokens=THINKING_OFF,
            tier="off",
            reason=f"trivial signals: {', '.join(trivial_hits[:2])}",
        )

    # Rule 3: category-based
    if task_category in DEEP_THINKING_CATEGORIES:
        return ThinkingBudget(
            budget_tokens=THINKING_DEEP,
            tier="deep",
            reason=f"deep-thinking category: {task_category}",
        )

    if task_category in TRIVIAL_CATEGORIES:
        return ThinkingBudget(
            budget_tokens=THINKING_OFF,
            tier="off",
            reason=f"trivial category: {task_category}",
        )

    # Default: moderate
    return ThinkingBudget(
        budget_tokens=THINKING_MODERATE,
        tier="moderate",
        reason="standard coding task",
    )


def _forced(tier: str) -> ThinkingBudget:
    mapping = {
        "off":      (THINKING_OFF,      "off"),
        "moderate": (THINKING_MODERATE, "moderate"),
        "deep":     (THINKING_DEEP,     "deep"),
    }
    tokens, label = mapping.get(tier, (THINKING_MODERATE, "moderate"))
    return ThinkingBudget(budget_tokens=tokens, tier=label, reason="forced override")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser(description="AgentKit thinking budget tuner")
    parser.add_argument("--prompt",    required=True)
    parser.add_argument("--category",  default="")
    parser.add_argument("--force-tier", default=None,
                        choices=["off", "moderate", "deep"])
    args = parser.parse_args()

    budget = get_thinking_budget(args.prompt, args.category, args.force_tier)
    print(json.dumps({
        "budget_tokens": budget.budget_tokens,
        "tier":          budget.tier,
        "reason":        budget.reason,
    }))
