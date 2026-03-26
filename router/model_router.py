"""
AgentKit — Layer 3: Auto Model Router
Every turn, classify task complexity → route to the cheapest model that can handle it.

Price ladder (2026):
  Haiku  $0.25/$1.25 per M tokens   → simple tasks, ALL subagents
  Sonnet $3.00/$15.00 per M tokens  → standard coding (80% of tasks)
  Opus   $15.00/$75.00 per M tokens → complex architecture, security audits

Combined with Haiku subagents this cuts costs ~60% vs default (Sonnet for everything).
"""

import os
import sys
import json
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Model constants
# ---------------------------------------------------------------------------

MODEL_HAIKU  = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS   = "claude-opus-4-6"

MODEL_RATES: dict[str, dict[str, float]] = {
    MODEL_HAIKU:  {"input": 0.00000025, "output": 0.00000125},
    MODEL_SONNET: {"input": 0.000003,   "output": 0.000015},
    MODEL_OPUS:   {"input": 0.000015,   "output": 0.000075},
}

# ---------------------------------------------------------------------------
# Complexity signals
# ---------------------------------------------------------------------------

SIMPLE_SIGNALS: list[str] = [
    # Read-only operations
    "find", "search", "list files", "show me", "what is", "where is",
    "read", "look at", "open", "which file", "print", "display",
    # Trivial edits
    "rename", "format", "fix typo", "update comment", "add space",
    "change the name", "update the label", "fix the spelling",
    # Quick lookups
    "what does", "explain this line", "what's the type of",
    "what is the value", "show the output", "how many",
]

COMPLEX_SIGNALS: list[str] = [
    # System design
    "architect", "design system", "design the", "how should we structure",
    "what's the best approach for", "trade-off", "pros and cons",
    "scalab", "high availability", "distributed",
    # Security
    "security audit", "vulnerability", "penetration", "threat model",
    "attack surface", "exploit", "cve", "owasp",
    # Performance
    "performance audit", "profile the", "benchmark", "optimize across",
    "root cause of the slow", "memory leak analysis",
    # Large-scale changes
    "migrate entire", "refactor the whole", "analyze all files",
    "across the codebase", "system-wide",
    # Deep reasoning
    "why is this happening", "root cause of", "investigate why",
    "diagnose", "what could cause", "intermittent",
]


@dataclass
class RoutingContext:
    is_subagent: bool = False
    has_code_context: bool = False   # True if prompt references specific files/functions
    prompt_length: int = 0


@dataclass
class RoutingDecision:
    model: str
    tier: str            # "simple" | "standard" | "complex"
    reason: str
    subagent_model: str = MODEL_HAIKU   # always Haiku for subagents


# ---------------------------------------------------------------------------
# Core routing logic
# ---------------------------------------------------------------------------

def route_model(prompt: str, context: RoutingContext | None = None) -> RoutingDecision:
    """
    Classify prompt complexity and return the appropriate model.

    Rules (in priority order):
      1. Subagents → always Haiku (non-negotiable, 15x cheaper)
      2. Complex signals detected → Opus
      3. 2+ simple signals → Haiku
      4. Short prompt with no code context → Haiku
      5. Default → Sonnet
    """
    ctx = context or RoutingContext(prompt_length=len(prompt))
    prompt_lower = prompt.lower()

    # Rule 1: Subagents always use Haiku
    if ctx.is_subagent:
        return RoutingDecision(
            model=MODEL_HAIKU,
            tier="simple",
            reason="subagent — always Haiku",
        )

    # Rule 2: Complex signals → Opus
    complex_hits = [s for s in COMPLEX_SIGNALS if s in prompt_lower]
    if complex_hits:
        return RoutingDecision(
            model=MODEL_OPUS,
            tier="complex",
            reason=f"complex signals: {', '.join(complex_hits[:3])}",
        )

    # Rule 3: 2+ simple signals → Haiku
    simple_hits = [s for s in SIMPLE_SIGNALS if s in prompt_lower]
    if len(simple_hits) >= 2:
        return RoutingDecision(
            model=MODEL_HAIKU,
            tier="simple",
            reason=f"simple signals: {', '.join(simple_hits[:3])}",
        )

    # Rule 4: Short prompt, no code context → Haiku
    if len(prompt) < 80 and not ctx.has_code_context:
        return RoutingDecision(
            model=MODEL_HAIKU,
            tier="simple",
            reason="short prompt, no code context",
        )

    # Default: Sonnet handles 80% of coding tasks well
    return RoutingDecision(
        model=MODEL_SONNET,
        tier="standard",
        reason="standard coding task",
    )


def cost_for_turn(model: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate the dollar cost for a single turn."""
    rates = MODEL_RATES.get(model, MODEL_RATES[MODEL_SONNET])
    return input_tokens * rates["input"] + output_tokens * rates["output"]


def savings_vs_baseline(
    actual_model: str,
    input_tokens: int,
    output_tokens: int,
    baseline_model: str = MODEL_SONNET,
) -> float:
    """How much was saved vs using the baseline model (default Sonnet)."""
    actual   = cost_for_turn(actual_model, input_tokens, output_tokens)
    baseline = cost_for_turn(baseline_model, input_tokens, output_tokens)
    return max(0.0, baseline - actual)


# ---------------------------------------------------------------------------
# CLI entry point — called by model_router_hook.sh
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AgentKit model router")
    parser.add_argument("--prompt",     required=True)
    parser.add_argument("--is-subagent", default="false")
    parser.add_argument("--has-code-context", default="false")
    args = parser.parse_args()

    ctx = RoutingContext(
        is_subagent=args.is_subagent.lower() == "true",
        has_code_context=args.has_code_context.lower() == "true",
        prompt_length=len(args.prompt),
    )

    decision = route_model(args.prompt, ctx)
    print(json.dumps({
        "model":          decision.model,
        "tier":           decision.tier,
        "reason":         decision.reason,
        "subagent_model": decision.subagent_model,
    }))
