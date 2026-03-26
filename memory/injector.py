"""
AgentKit — Layer 2: Smart Context Injector
Builds the memory injection block for Claude's context on each turn.

Budget: max 2,000 tokens of memory context (vs 10,000+ for a full CLAUDE.md).
Only injects nodes relevant to the current task + files being worked on.
"""

import os
import sys
import json

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from memory.graph import KnowledgeGraph, ContextNode

MAX_INJECTION_TOKENS = 2_000
CHARS_PER_TOKEN = 4   # rough approximation: 1 token ≈ 4 characters


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN)


def build_injection(
    db_path: str,
    task_category: str,
    current_files: list[str],
    prompt: str,
    max_tokens: int = MAX_INJECTION_TOKENS,
) -> str:
    """
    Query the knowledge graph and build a memory injection block
    within the token budget.

    Returns a formatted string ready to prepend to Claude's context,
    or an empty string if no relevant memory exists.
    """
    if not os.path.exists(db_path):
        return ""

    graph = KnowledgeGraph(db_path)

    # Extract keywords from prompt for relevance scoring
    keywords = _extract_keywords(prompt)

    # Get scored context nodes
    nodes = graph.get_context_for_task(
        task_category=task_category,
        current_files=current_files,
        prompt_keywords=keywords,
    )

    if not nodes:
        return ""

    # Select nodes within token budget
    selected: list[ContextNode] = []
    total_tokens = 0
    header = "## Project Memory (relevant context)\n\n"
    budget = max_tokens - _estimate_tokens(header)

    # Group by type for a cleaner injection format
    decisions = [n for n in nodes if hasattr(n.entity_or_decision, "category")]
    entities  = [n for n in nodes if not hasattr(n.entity_or_decision, "category")]

    # Decisions first (highest information density)
    for node in decisions:
        cost = _estimate_tokens(node.formatted_text) + 1
        if total_tokens + cost <= budget:
            selected.append(node)
            total_tokens += cost

    # Then entities
    for node in entities:
        cost = _estimate_tokens(node.formatted_text) + 1
        if total_tokens + cost <= budget:
            selected.append(node)
            total_tokens += cost

    if not selected:
        return ""

    # Format output
    lines = [header]

    decision_nodes = [n for n in selected if hasattr(n.entity_or_decision, "category")]
    entity_nodes   = [n for n in selected if not hasattr(n.entity_or_decision, "category")]

    if decision_nodes:
        lines.append("### Decisions & Patterns")
        for n in decision_nodes:
            lines.append(f"- {n.formatted_text}")
        lines.append("")

    if entity_nodes:
        lines.append("### Codebase Knowledge")
        for n in entity_nodes:
            lines.append(f"- {n.formatted_text}")
        lines.append("")

    lines.append(f"*({total_tokens} tokens injected / {max_tokens} budget)*\n")
    return "\n".join(lines)


def _extract_keywords(prompt: str) -> list[str]:
    """Extract meaningful keywords from a prompt for relevance scoring."""
    # Strip common stop words, keep meaningful tokens
    stop_words = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
        "of", "with", "by", "from", "is", "it", "this", "that", "be", "are",
        "was", "were", "have", "has", "can", "will", "do", "does", "i", "my",
        "me", "we", "you", "how", "what", "why", "when", "where", "which",
    }
    words = prompt.lower().replace(",", " ").replace(".", " ").split()
    return [w for w in words if len(w) > 3 and w not in stop_words][:20]


# ---------------------------------------------------------------------------
# CLI entry point — called by memory_inject.sh (UserPromptSubmit hook)
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Reads Claude Code hook JSON from stdin, builds injection block,
    prints it to stdout (Claude sees this as additional context).
    """
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        sys.exit(0)

    prompt      = data.get("prompt", "")
    cwd         = data.get("cwd", os.getcwd())
    session_id  = data.get("session_id", "unknown")

    if not prompt:
        sys.exit(0)

    # Load session state to get task category + loaded skill context
    agentkit_home = os.environ.get("AGENTKIT_HOME", _REPO_ROOT)
    state_file = os.path.join(agentkit_home, "data", f"session_{session_id}.json")
    state: dict = {}
    if os.path.exists(state_file):
        try:
            with open(state_file) as f:
                state = json.load(f)
        except Exception:
            pass

    task_category = state.get("last_category", "api-work")

    # Get currently modified files as context signal
    current_files = _get_modified_files(cwd)

    # DB lives in the project's .agentkit dir
    db_path = os.path.join(cwd, ".agentkit", "memory.db")

    injection = build_injection(
        db_path=db_path,
        task_category=task_category,
        current_files=current_files,
        prompt=prompt,
    )

    if injection:
        print(injection)
        print(f"[AgentKit Memory] Injected memory context", file=sys.stderr)


def _get_modified_files(cwd: str) -> list[str]:
    import subprocess
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=cwd, capture_output=True, text=True, timeout=3,
        )
        return [f.strip() for f in r.stdout.splitlines() if f.strip()]
    except Exception:
        return []


if __name__ == "__main__":
    main()
