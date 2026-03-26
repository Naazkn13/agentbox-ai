"""
AgentKit — Layer 1: Progressive Disclosure Engine
Reads SKILL.md files and extracts content at the requested level (1, 2, or 3).
Also decides when to escalate to a deeper level.

SKILL.md level markers:
  <!-- LEVEL 1 START --> ... <!-- LEVEL 1 END -->
  <!-- LEVEL 2 START --> ... <!-- LEVEL 2 END -->
  <!-- LEVEL 3 START --> ... <!-- LEVEL 3 END -->
"""

import re
import os
from router.models import SkillMeta, SkillSelection, RouterOutput, ClassificationResult
from router.registry import SkillRegistry, registry as _default_registry

# Regex to extract level sections from SKILL.md
_LEVEL_PATTERN = re.compile(
    r"<!--\s*LEVEL\s+(\d)\s+START\s*-->(.*?)<!--\s*LEVEL\s+\d\s+END\s*-->",
    re.DOTALL | re.IGNORECASE,
)


def _read_skill_file(path: str) -> str:
    """Read a SKILL.md file, returning empty string if not found."""
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def extract_level(skill_content: str, level: int) -> str:
    """
    Extract the content for a specific level from a SKILL.md string.
    Falls back to the full content (minus front-matter) if markers are absent.
    """
    matches = {int(m.group(1)): m.group(2).strip() for m in _LEVEL_PATTERN.finditer(skill_content)}

    if matches:
        if level in matches:
            return matches[level]
        # Graceful degradation: return next lower level available
        for lvl in sorted(matches.keys(), reverse=True):
            if lvl <= level:
                return matches[lvl]
        return next(iter(matches.values()))

    # No markers — strip YAML front-matter and return the whole body
    body = re.sub(r"^---.*?---\s*", "", skill_content, flags=re.DOTALL).strip()
    return body


def should_escalate(current_level: int, context: dict) -> bool:
    """
    Decide whether to escalate from current_level to current_level+1.

    Context keys (all bool, all optional):
      task_confirmed        — agent has started acting on this task category
      first_tool_in_category— the very first tool call in this category
      edge_case_detected    — unusual or complex variant of the task
      agent_asked_question  — agent emitted a clarifying question
      multiple_files_involved — edit spans multiple files
      error_persists_after_fix— bug not fixed after first attempt
    """
    if current_level >= 3:
        return False

    if current_level == 1:
        return bool(
            context.get("task_confirmed")
            or context.get("first_tool_in_category")
        )

    if current_level == 2:
        return bool(
            context.get("edge_case_detected")
            or context.get("agent_asked_question")
            or context.get("multiple_files_involved")
            or context.get("error_persists_after_fix")
        )

    return False


def load_skill_content(
    selection: SkillSelection,
    reg: SkillRegistry | None = None,
) -> str:
    """
    Load the SKILL.md content at the selection's current disclosure level.
    Mutates selection.content in place and returns the content string.
    """
    r = reg or _default_registry
    path = r.resolve_path(selection.meta)
    raw = _read_skill_file(path)

    if not raw:
        # Graceful fallback: synthesise a minimal Level-1 blurb from metadata
        selection.content = f"**{selection.meta.name}**: {selection.meta.id}"
        return selection.content

    selection.content = extract_level(raw, selection.level)
    return selection.content


def build_injection(
    selections: list[SkillSelection],
    reg: SkillRegistry | None = None,
) -> str:
    """
    Load content for all selected skills and combine into a single
    injection block ready to be prepended to Claude's context.

    Returns the formatted injection string.
    """
    if not selections:
        return ""

    r = reg or _default_registry
    blocks: list[str] = ["## AgentKit — Active Skills\n"]

    for sel in selections:
        content = load_skill_content(sel, reg=r)
        level_label = f"L{sel.level}"
        blocks.append(f"### [{level_label}] {sel.meta.name}\n{content}\n")

    return "\n".join(blocks)


def run_router(
    classification: ClassificationResult,
    selections: list[SkillSelection],
    context: dict | None = None,
    reg: SkillRegistry | None = None,
) -> RouterOutput:
    """
    Full pipeline: take classifier output + selector output → produce RouterOutput.

    Applies escalation logic based on context signals before loading content.
    """
    ctx = context or {}
    r = reg or _default_registry

    for sel in selections:
        if should_escalate(sel.level, ctx):
            sel.level = min(sel.level + 1, 3)

    injected = build_injection(selections, reg=r)
    total_tokens = sum(
        sel.meta.level1_tokens if sel.level == 1
        else sel.meta.level2_tokens if sel.level == 2
        else sel.meta.level3_tokens
        for sel in selections
    )

    return RouterOutput(
        classification=classification,
        selected_skills=selections,
        injected_content=injected,
        total_tokens=total_tokens,
        loaded_skill_ids=[sel.meta.id for sel in selections],
    )
