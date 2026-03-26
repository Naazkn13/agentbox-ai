# Architecture: Layer 1 — Intelligent Skill Router
**Color:** Red (`#f43f5e`)
**Tagline:** The biggest token saver — loads ONLY what you need, when you need it
**Token Impact:** 45,000 → 5,000 tokens/session (89% reduction)

---

## The Problem It Solves

Without a skill router, developers dump everything into CLAUDE.md:
- All 1,234 skills from awesome-claude-code? Loaded on every prompt.
- 20 SKILL.md files you installed? All in context at all times.
- Result: 45,000+ tokens wasted on irrelevant skills per session.

The skill router fixes this by loading ONLY the 2-5 skills that matter for the current task.

---

## Components

### Component 1: Task Classifier

**Purpose:** Analyze the current prompt + file context in real-time to determine what the developer is doing.

**Input:**
- User's prompt (natural language)
- Currently open/modified files (from git status or IDE context)
- Active git branch name (signals feature area)
- Previous tool calls in session (signals ongoing task type)

**Output:**
```python
@dataclass
class ClassificationResult:
    primary_category: str      # e.g., "debugging"
    secondary_category: str    # e.g., "writing-tests"
    confidence: float          # 0.0–1.0
    matched_keywords: list     # which keywords triggered the classification
    skill_ids: list            # ordered list of skill IDs to load
    fallback_used: bool        # True if Haiku was called for ambiguous prompt
```

**Classification strategy (3-tier):**

```
Tier 1: Keyword matching (instant, free)
  → Covers 70% of prompts
  → Regex patterns against prompt + filename + branch name
  → Fast: < 5ms

Tier 2: Semantic heuristics (instant, free)
  → Covers 20% of prompts (more complex language)
  → Scoring based on weighted keyword presence
  → Fast: < 10ms

Tier 3: Haiku fallback (50ms, ~$0.0003)
  → Covers remaining 10% of ambiguous prompts
  → One-shot classification call to Haiku
  → Only triggered when Tier 1+2 confidence < 0.6
```

**Full category list:**
```python
CATEGORIES = {
    "debugging":      ["bug", "error", "exception", "crash", "fix", "broken", "failing", "traceback", "undefined", "null"],
    "writing-tests":  ["test", "spec", "coverage", "tdd", "jest", "pytest", "unit", "integration", "mock", "assert"],
    "designing-ui":   ["ui", "ux", "design", "component", "layout", "style", "css", "figma", "responsive", "animation"],
    "deploying":      ["deploy", "ci", "cd", "docker", "k8s", "kubernetes", "pipeline", "build", "release", "helm"],
    "reviewing-pr":   ["review", "pr", "pull request", "diff", "code review", "feedback", "approve", "merge"],
    "architecting":   ["architect", "design system", "scalab", "pattern", "structure", "microservice", "ddd", "cqrs"],
    "writing-docs":   ["document", "readme", "jsdoc", "docstring", "api docs", "swagger", "openapi spec"],
    "db-work":        ["database", "sql", "query", "migration", "schema", "orm", "postgres", "mysql", "prisma"],
    "api-work":       ["api", "endpoint", "rest", "graphql", "route", "http", "request", "response", "webhook"],
    "refactoring":    ["refactor", "clean", "improve", "optimize", "restructure", "simplify", "dry", "solid"],
    "security":       ["security", "auth", "jwt", "oauth", "xss", "injection", "vuln", "cve", "pentest", "audit"],
    "performance":    ["performance", "slow", "latency", "optimize", "profil", "memory leak", "benchmark", "load"],
    "ai-engineering": ["llm", "prompt", "embedding", "rag", "agent", "token", "fine-tun", "eval", "model"],
}
```

---

### Component 2: Skill Selector

**Purpose:** From the classifier output, select the optimal 2-5 skills to load.

**Selection algorithm:**
```python
def select_skills(
    primary: str,
    secondary: str,
    confidence: float,
    currently_loaded: list,
    token_budget: int = 5000
) -> list[SkillSelection]:

    candidates = []

    # Step 1: Get priority-1 skills for primary category
    primary_skills = registry.get_skills(category=primary, priority=1)
    candidates.extend(primary_skills[:3])  # max 3 from primary

    # Step 2: Get priority-1 skills for secondary category (if confidence > 0.5)
    if confidence > 0.5 and secondary:
        secondary_skills = registry.get_skills(category=secondary, priority=1)
        candidates.extend(secondary_skills[:2])  # max 2 from secondary

    # Step 3: Apply personal model weights (Phase 4 feature)
    if personal_model.is_trained():
        candidates = personal_model.rerank(candidates, primary, secondary)

    # Step 4: Respect token budget — stay within budget at Level 1
    selected = []
    total_tokens = 0
    for skill in candidates:
        if total_tokens + skill.level1_tokens <= token_budget:
            selected.append(skill)
            total_tokens += skill.level1_tokens

    # Step 5: Don't reload already-loaded skills (session continuity)
    selected = [s for s in selected if s.id not in currently_loaded] + \
               [s for s in currently_loaded if s.id in [c.id for c in candidates]]

    return selected
```

**Skill registry entry** (`skills/registry.yaml`):
```yaml
- id: debugging-python
  name: Python Debugger
  category: debugging
  priority: 1              # 1=core, 2=supplemental, 3=reference
  path: skills/debugging/python-debugger.md
  level1_tokens: 45
  level2_tokens: 480
  level3_tokens: 2100
  platforms: [claude-code, cursor, codex, gemini-cli]
  keywords: [python, traceback, exception, AttributeError, TypeError]
  personal_weight: 1.0    # adjusted by personal model in Phase 4
  effectiveness: 0.87     # from marketplace ratings
```

---

### Component 3: Progressive Disclosure Engine

**Purpose:** Skills load in layers — only go deeper when the task demands it.

**Three levels:**

```
Level 1 — Trigger Description (50 tokens)
  Purpose: Let the agent KNOW a skill exists and when to use it
  Content: skill name + one-line activation condition
  Loaded:  Always, for all selected skills
  Example:
    "Python Debugger: Activate for Python errors, exceptions, tracebacks, assertion failures."

Level 2 — Core Instructions (400-600 tokens)
  Purpose: The actual rules and patterns the agent needs
  Content: numbered instructions, key rules, common patterns
  Loaded:  When task is confirmed to be in this category
  Trigger: Agent begins a task in the skill's domain
  Example:
    "1. Read full traceback before touching code
     2. Identify root cause, not symptoms
     3. Check variable state at the error line..."

Level 3 — Full Reference (1500-2500 tokens)
  Purpose: Deep reference for complex or unusual cases
  Content: full patterns, examples, edge cases, anti-patterns
  Loaded:  Only when agent explicitly needs depth
  Trigger: Complex debugging, edge case, agent asks clarifying question
  Example:
    "### Common Python Error Patterns
     AttributeError: object has no attribute X
     → Check: is the object None? Is the attribute spelled correctly?
     → Fix: add None guard, or check type before attribute access..."
```

**SKILL.md file structure:**
```markdown
---
id: debugging-python
name: Python Debugger
category: debugging
level1: "For Python errors, exceptions, and tracebacks"
level1_tokens: 45
level2_tokens: 480
level3_tokens: 2100
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
## Python Debugger
Activate for: Python errors, exceptions, assertion failures, stack traces, AttributeError, TypeError, KeyError, ImportError.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Core Instructions

1. **Read the full traceback top-to-bottom** before touching any code. The root cause is rarely at the bottom line.
2. **Identify root cause, not symptoms.** Check variable state at the actual error, not just the line that errored.
3. **Use targeted logging:** `print(f"DEBUG: {var=}")` before the error line. Confirm assumptions before fixing.
4. **Check for None before accessing attributes.** 90% of AttributeErrors are None objects.
5. **Never suppress exceptions** with bare `except: pass`. Always log the error at minimum.
6. **After fixing, reproduce the original error first** to confirm you understand it.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Reference

### Common Python Error Patterns

**AttributeError: 'NoneType' object has no attribute 'X'**
- Root cause: Object is None when you expect an instance
- Check: the function/query returning this object
- Fix: Add None guard (`if obj is None: ...`) or use Optional typing

**KeyError: 'X'**
- Root cause: Accessing dict key that doesn't exist
- Fix: Use `.get('key', default)` instead of `['key']`
- Or: Check `'key' in dict` before accessing

**ImportError: cannot import name 'X' from 'Y'**
- Check: module path, circular imports, __init__.py exports
- Common: circular import — restructure into separate utils module

**RecursionError: maximum recursion depth exceeded**
- Add `if base_case: return` at top of recursive function
- Consider iterative approach for deep recursion

### Debugging Tools
```python
# breakpoint() — built-in debugger (Python 3.7+)
breakpoint()  # drops into pdb

# pdb commands: n(ext), s(tep), c(ontinue), p(rint), l(ist), q(uit)

# Rich traceback (pip install rich)
from rich.traceback import install
install(show_locals=True)

# Structured logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug(f"Processing {item=}, {state=}")
```
<!-- LEVEL 3 END -->
```

**Escalation logic** (`router/disclosure.py`):
```python
def should_escalate(current_level: int, context: dict) -> bool:
    if current_level == 1:
        # Escalate to Level 2 when task is confirmed in this domain
        return context.get("task_confirmed") or context.get("first_tool_in_category")
    elif current_level == 2:
        # Escalate to Level 3 when complexity signals detected
        return (
            context.get("edge_case_detected") or
            context.get("agent_asked_question") or
            context.get("multiple_files_involved") or
            context.get("error_persists_after_fix")
        )
    return False
```

---

### Component 4: Forced-Eval Hook

**Purpose:** Ensure skills actually fire when they should. The community discovered skills only activate 20% of the time without this hook. With it: 84%.

**How it works:**
1. `PreToolUse` hook fires before every agent tool call
2. Injects a short reminder: "Check if any active skill applies to this action"
3. Forces the agent to evaluate loaded skills before proceeding

**Why this matters — the math:**
```
Without forced-eval:
  Skill activation rate: 20%
  Sessions where skill helps: 1 in 5
  Token savings per session: 40,000 × 0.20 = 8,000 tokens saved

With forced-eval:
  Skill activation rate: 84%
  Token savings per session: 40,000 × 0.84 = 33,600 tokens saved

Difference: 4.2x more savings from ONE hook
```

**Hook implementation:**
```bash
#!/bin/bash
# hooks/forced_eval.sh
# Event: PreToolUse

LOADED_SKILLS="${AGENTKIT_LOADED_SKILLS:-}"
TOOL_NAME="$1"

# Only apply for tool types where skills are relevant
if [[ "$TOOL_NAME" =~ ^(Edit|Bash|Write)$ ]] && [ -n "$LOADED_SKILLS" ]; then
  echo "[AgentKit] Active skills: ${LOADED_SKILLS}"
  echo "[AgentKit] Check if any skill's instructions apply to this ${TOOL_NAME} action."
fi
```

**Settings registration** (`.claude/settings.json`):
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Bash|Write",
        "hooks": [
          { "type": "command", "command": "bash ${AGENTKIT_HOME}/hooks/forced_eval.sh $CLAUDE_TOOL_NAME" }
        ]
      }
    ]
  }
}
```

---

## Data Flow

```
User types prompt
       ↓
UserPromptSubmit hook fires
       ↓
Task Classifier
  → Keyword matching (Tier 1, 5ms)
  → Heuristic scoring (Tier 2, 10ms)
  → Haiku fallback if needed (Tier 3, 50ms)
       ↓
Skill Selector
  → Query registry for matching skills
  → Apply token budget (max 5,000 tokens at L1)
  → Apply personal model weights (Phase 4)
  → Return 2-5 skill IDs
       ↓
Progressive Disclosure Engine
  → Load Level 1 for all selected skills (~50 tokens each)
  → Export AGENTKIT_LOADED_SKILLS for forced-eval hook
       ↓
Skill content injected into agent context
       ↓
Agent begins task
       ↓
PreToolUse hook (forced-eval)
  → Reminds agent to check active skills
  → Agent reads Level 1, decides if skill applies
  → If applies: requests Level 2 load
       ↓
Agent uses relevant skill instructions
Task completed with 89% fewer skill tokens
```

---

## Token Budget by Scenario

| Scenario | Skills Loaded | L1 | L2 | L3 | Total | Savings vs Naive |
|----------|--------------|----|----|----|----|---------|
| Simple bug fix | 2 (debug, test) | 100 | 480 | 0 | 580 | 44,420 tok |
| Feature implementation | 3 (coding, api, db) | 150 | 1,440 | 0 | 1,590 | 43,410 tok |
| Complex architecture | 4 (arch, security, design, patterns) | 200 | 2,000 | 2,100 | 4,300 | 40,700 tok |
| Naive (load all 50 skills at L2) | 50 | — | 25,000 | 0 | 25,000 | 0 |
| Legacy (dump all to CLAUDE.md) | all | — | — | — | 45,000 | 0 |

---

## Files Owned by This Layer

```
router/
├── classifier.py       # Task classifier (keyword + heuristic + Haiku fallback)
├── selector.py         # Skill selector (registry queries + token budget)
├── disclosure.py       # Progressive disclosure (L1/L2/L3 loading)
├── registry.py         # Registry loader + query interface
└── models.py           # Dataclasses: ClassificationResult, SkillSelection

skills/
├── registry.yaml       # Master skill registry
└── [category]/
    └── [skill].md      # SKILL.md files with L1/L2/L3 sections

hooks/
├── skill_router_hook.sh  # Triggered on UserPromptSubmit
└── forced_eval.sh        # Triggered on PreToolUse
```
