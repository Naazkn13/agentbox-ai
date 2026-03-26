"""
AgentKit — Layer 3: Smart Compaction
Proactively compact context at logical breakpoints — not reactively at 80%.

Strategy:
  - Score each context element by utility (recency × relevance × type weight)
  - Discard low-utility elements before the context window fills up
  - Summarise discarded tool outputs via Haiku (~$0.0003 per compaction)
  - Trigger at configurable fill %, defaulting to 60% (vs Claude's 80%)

Element type weights:
  system_prompt     1.0   never compact
  user_message      0.9   keep recent, summarise old
  assistant_message 0.8   keep recent, summarise old
  tool_result       0.5   compress aggressively
  tool_use          0.4   compress aggressively
  file_content      0.3   discard after file closes
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPACT_TRIGGER_FILL   = 0.60   # trigger compaction when context is 60% full
DISCARD_SCORE_FLOOR    = 0.15   # elements below this score are discarded
SUMMARY_SCORE_FLOOR    = 0.30   # elements below this (but above discard) get summarised
MAX_KEEP_TOOL_RESULTS  = 5      # keep only the N most recent tool results verbatim

TYPE_WEIGHTS: dict[str, float] = {
    "system_prompt":     1.0,
    "user_message":      0.9,
    "assistant_message": 0.8,
    "tool_result":       0.5,
    "tool_use":          0.4,
    "file_content":      0.3,
}

RECENCY_HALF_LIFE_TURNS = 10    # score halves every N turns


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ContextElement:
    id: str
    type: str                      # one of TYPE_WEIGHTS keys
    content: str
    turn_index: int                # which turn this appeared in
    tokens: int = 0                # estimated token count
    pinned: bool = False           # if True, never compact
    tags: list[str] = field(default_factory=list)


@dataclass
class CompactionResult:
    kept: list[ContextElement]
    summarised: list[ContextElement]
    discarded: list[ContextElement]
    summary_text: str              # Haiku-generated summary of summarised elements
    tokens_freed: int
    tokens_remaining: int


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_element(
    el: ContextElement,
    current_turn: int,
    keyword_hits: int = 0,
) -> float:
    """
    Score = type_weight × recency_factor × (1 + 0.1 × keyword_hits)

    recency_factor decays exponentially with turns since creation.
    """
    if el.pinned:
        return 1.0

    type_weight = TYPE_WEIGHTS.get(el.type, 0.5)
    turns_old   = max(0, current_turn - el.turn_index)
    recency     = 0.5 ** (turns_old / RECENCY_HALF_LIFE_TURNS)

    return type_weight * recency * (1 + 0.1 * keyword_hits)


# ---------------------------------------------------------------------------
# Core compaction
# ---------------------------------------------------------------------------

def smart_compact(
    elements: list[ContextElement],
    context_window_tokens: int,
    current_tokens: int,
    current_turn: int,
    prompt_keywords: list[str] | None = None,
    use_haiku_summary: bool = True,
) -> CompactionResult:
    """
    Decide which context elements to keep, summarise, or discard.

    Returns CompactionResult with the three buckets + a Haiku summary string.
    Call this when: current_tokens / context_window_tokens >= COMPACT_TRIGGER_FILL
    """
    keywords = prompt_keywords or []

    # Score all elements
    scored: list[tuple[float, ContextElement]] = []
    for el in elements:
        hits = sum(1 for kw in keywords if kw.lower() in el.content.lower())
        score = _score_element(el, current_turn, hits)
        scored.append((score, el))

    scored.sort(key=lambda x: x[0], reverse=True)

    kept: list[ContextElement]       = []
    to_summarise: list[ContextElement] = []
    discarded: list[ContextElement]  = []

    # Most recent tool results are always kept verbatim
    tool_result_count = 0

    for score, el in scored:
        if el.pinned or el.type == "system_prompt":
            kept.append(el)
        elif el.type == "tool_result":
            if tool_result_count < MAX_KEEP_TOOL_RESULTS:
                kept.append(el)
                tool_result_count += 1
            elif score >= SUMMARY_SCORE_FLOOR:
                to_summarise.append(el)
            else:
                discarded.append(el)
        elif score >= SUMMARY_SCORE_FLOOR:
            kept.append(el)
        elif score >= DISCARD_SCORE_FLOOR:
            to_summarise.append(el)
        else:
            discarded.append(el)

    # Generate summary
    summary_text = ""
    if to_summarise:
        if use_haiku_summary:
            summary_text = _haiku_summary(to_summarise)
        else:
            summary_text = _raw_summary(to_summarise)

    tokens_freed = sum(el.tokens for el in to_summarise) + sum(el.tokens for el in discarded)
    tokens_remaining = current_tokens - tokens_freed

    return CompactionResult(
        kept=kept,
        summarised=to_summarise,
        discarded=discarded,
        summary_text=summary_text,
        tokens_freed=tokens_freed,
        tokens_remaining=tokens_remaining,
    )


def should_compact(current_tokens: int, context_window_tokens: int) -> bool:
    """Return True if compaction should be triggered now."""
    if context_window_tokens <= 0:
        return False
    return (current_tokens / context_window_tokens) >= COMPACT_TRIGGER_FILL


# ---------------------------------------------------------------------------
# Summarisation
# ---------------------------------------------------------------------------

def _haiku_summary(elements: list[ContextElement]) -> str:
    """Call Haiku to produce a concise summary of old context elements."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        combined = "\n\n---\n\n".join(
            f"[{el.type.upper()} turn={el.turn_index}]\n{el.content[:800]}"
            for el in elements
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{
                "role": "user",
                "content": (
                    "You are a context compressor. Summarise the following conversation "
                    "fragments in ≤200 words, preserving file names, function names, "
                    "decisions made, and key facts. Omit verbatim code.\n\n"
                    + combined
                ),
            }],
        )
        return msg.content[0].text.strip()
    except Exception:
        return _raw_summary(elements)


def _raw_summary(elements: list[ContextElement]) -> str:
    """Fallback: plain text summary without an API call."""
    lines = [f"[COMPACTED — {len(elements)} elements removed]"]
    for el in elements:
        preview = el.content[:120].replace("\n", " ")
        lines.append(f"  [{el.type}@turn{el.turn_index}]: {preview}…")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI entry point (for testing)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser(description="AgentKit smart compaction check")
    parser.add_argument("--current-tokens",  type=int, required=True)
    parser.add_argument("--window-tokens",   type=int, required=True)
    args = parser.parse_args()

    needs = should_compact(args.current_tokens, args.window_tokens)
    fill  = args.current_tokens / args.window_tokens if args.window_tokens else 0
    print(json.dumps({
        "should_compact": needs,
        "fill_pct":       round(fill * 100, 1),
        "trigger_pct":    round(COMPACT_TRIGGER_FILL * 100, 1),
    }))
