# Phase 1: Core Plugin
**Timeline:** Weeks 1–4
**Goal:** Ship the foundational plugin — skill router, model routing, cost dashboard, one-command install. This alone delivers the biggest token savings and proves the core value proposition.

---

## Deliverables Checklist

- [ ] Skill Router: task classifier + progressive disclosure loader
- [ ] Curated skill library: 50 battle-tested skills organized by role
- [ ] Forced-eval hook (84% activation rate)
- [ ] Token cost dashboard hook (real-time $/session in status line)
- [ ] Auto model routing: Haiku → Sonnet → Opus by complexity
- [ ] MAX_THINKING_TOKENS auto-tuning
- [ ] Claude Code plugin format
- [ ] Cursor plugin format
- [ ] `npx agentkit init` one-command installer

---

## Week 1: Skill Router Core

### 1.1 Task Classifier
**File:** `router/classifier.py`

Classifies the current task from the incoming prompt + file context. Must run fast (< 50ms) — it's called on every agent turn.

**Task categories to detect:**
```
debugging        → load: debugging, logging, error-handling skills
writing-tests    → load: testing, tdd, coverage skills
designing-ui     → load: ui-ux, design-system, accessibility skills
deploying        → load: devops, ci-cd, docker, k8s skills
reviewing-pr     → load: code-review, security, performance skills
architecting     → load: system-design, patterns, ddd skills
writing-docs     → load: documentation, markdown, api-docs skills
db-work          → load: sql, orm, migrations, optimization skills
api-work         → load: rest, graphql, openapi, auth skills
refactoring      → load: clean-code, patterns, solid skills
```

**Implementation approach:**
- Use keyword + regex matching on the prompt (fast, free, no LLM call)
- Fallback: lightweight LLM call to Haiku for ambiguous prompts (< $0.001)
- Output: task category + confidence score + list of matched skill IDs

```python
# router/classifier.py
import re
from dataclasses import dataclass
from typing import Optional

TASK_PATTERNS = {
    "debugging": [r"\b(bug|error|exception|crash|fix|broken|failing|traceback)\b"],
    "writing-tests": [r"\b(test|spec|coverage|tdd|jest|pytest|unit|integration)\b"],
    "designing-ui": [r"\b(ui|ux|design|component|layout|style|css|figma|responsive)\b"],
    "deploying": [r"\b(deploy|ci|cd|docker|k8s|kubernetes|pipeline|build|release)\b"],
    "reviewing-pr": [r"\b(review|pr|pull request|diff|code review|feedback)\b"],
    "architecting": [r"\b(architect|design|system|scalab|pattern|structure|microservice)\b"],
    "db-work": [r"\b(database|sql|query|migration|schema|orm|postgres|mysql|mongo)\b"],
    "api-work": [r"\b(api|endpoint|rest|graphql|route|http|request|response)\b"],
    "refactoring": [r"\b(refactor|clean|improve|optimize|restructure|simplify)\b"],
}

@dataclass
class ClassificationResult:
    category: str
    confidence: float
    skill_ids: list[str]
    fallback_used: bool = False
```

### 1.2 Skill Selector
**File:** `router/selector.py`

Maps task category → skill IDs → skill files. Loads ONLY 2–5 skills per task.

**Skill registry format** (`skills/registry.yaml`):
```yaml
skills:
  - id: debugging-python
    category: debugging
    path: skills/debugging/python-debugger.md
    level1_tokens: 45      # trigger description
    level2_tokens: 480     # core instructions
    level3_tokens: 2100    # full references + examples
    platforms: [claude-code, cursor, codex]
    priority: 1            # lower = higher priority

  - id: tdd-workflow
    category: writing-tests
    path: skills/testing/tdd-workflow.md
    level1_tokens: 52
    level2_tokens: 510
    level3_tokens: 1980
    platforms: [claude-code, cursor, codex, gemini-cli]
    priority: 1
```

**Selection logic:**
1. Get top-3 category matches from classifier
2. Select priority-1 skills for primary category (max 3)
3. Select priority-1 skills for secondary category (max 2)
4. Never exceed 5 skills total, 5,000 tokens total at Level 1

### 1.3 Progressive Disclosure Engine
**File:** `router/disclosure.py`

Skills load in 3 levels. Start at Level 1 always. Escalate only if task complexity requires it.

```
Level 1 (50 tokens):   skill name + one-line trigger description
Level 2 (500 tokens):  core instructions + key rules
Level 3 (2000 tokens): full references + examples + edge cases
```

**Escalation triggers:**
- Level 1 → Level 2: agent asks a clarifying question about the skill domain
- Level 2 → Level 3: task involves an edge case or the agent explicitly requests more detail

**Token budget per session:**
```
Level 1 only (5 skills):   ~250 tokens
Level 2 for 3 skills:      ~1,500 tokens
Level 3 for 1 skill:       ~2,000 tokens
Total realistic:           ~3,750 tokens vs 45,000 (loading all)
Savings:                   ~41,250 tokens per session
```

---

## Week 2: Hooks System

### 2.1 Forced-Eval Hook
**File:** `hooks/forced_eval.sh`

The single most impactful hook. Without it, skills activate only 20% of the time. With it: 84%.

**How it works:**
- Hooks into Claude Code's `PreToolUse` event
- Before each tool call, injects a brief skill-evaluation prompt
- Forces Claude to explicitly check if any loaded skill applies to the current action

```bash
#!/bin/bash
# hooks/forced_eval.sh
# Triggered on: PreToolUse
# Reads: AGENTKIT_LOADED_SKILLS env var (set by skill router)

LOADED_SKILLS="${AGENTKIT_LOADED_SKILLS:-}"
if [ -z "$LOADED_SKILLS" ]; then
  exit 0
fi

# Inject skill eval reminder into tool context
echo "SKILL_EVAL: Before proceeding, check if any active skill applies: ${LOADED_SKILLS}"
```

**Registration in `.claude/settings.json`:**
```json
{
  "hooks": {
    "PreToolUse": [
      { "command": "bash /path/to/agentkit/hooks/forced_eval.sh" }
    ]
  }
}
```

### 2.2 Skill Router Hook
**File:** `hooks/skill_router_hook.sh`

Triggered at session start and on each new user message. Runs classifier → selector → loads skills into context.

```bash
#!/bin/bash
# hooks/skill_router_hook.sh
# Triggered on: UserPromptSubmit

PROMPT="$1"
PROJECT_DIR="${AGENTKIT_PROJECT:-$(pwd)}"

# Run Python classifier
RESULT=$(python3 "${AGENTKIT_HOME}/router/classifier.py" --prompt "$PROMPT" --project "$PROJECT_DIR")

# Export loaded skills for forced-eval hook
export AGENTKIT_LOADED_SKILLS=$(echo "$RESULT" | jq -r '.skill_ids | join(",")')

# Output skill content to be injected into context
echo "$RESULT" | python3 "${AGENTKIT_HOME}/router/disclosure.py" --level 1
```

### 2.3 Cost Dashboard Hook
**File:** `hooks/cost_dashboard.sh`

Real-time cost tracking displayed in Claude Code status line.

**Tracked metrics:**
- Current session cost (input + output tokens × model rate)
- Model used on last turn (Haiku/Sonnet/Opus)
- Cost per completed task
- Projected daily spend (rolling 24h average)

**Status line format:**
```
💰 $0.034 | 🧠 sonnet | ⚡ 12,450 tok | 📈 $1.02/day
```

**Implementation:**
```bash
#!/bin/bash
# hooks/cost_dashboard.sh
# Triggered on: PostToolUse

SESSION_LOG="${AGENTKIT_HOME}/data/session_costs.jsonl"
MODEL="${CLAUDE_MODEL:-sonnet}"
INPUT_TOKENS="${CLAUDE_INPUT_TOKENS:-0}"
OUTPUT_TOKENS="${CLAUDE_OUTPUT_TOKENS:-0}"

# Calculate cost based on model
case "$MODEL" in
  *haiku*)   INPUT_RATE=0.00000025; OUTPUT_RATE=0.00000125 ;;
  *sonnet*)  INPUT_RATE=0.000003;   OUTPUT_RATE=0.000015   ;;
  *opus*)    INPUT_RATE=0.000015;   OUTPUT_RATE=0.000075   ;;
  *)         INPUT_RATE=0.000003;   OUTPUT_RATE=0.000015   ;;
esac

TURN_COST=$(echo "$INPUT_TOKENS * $INPUT_RATE + $OUTPUT_TOKENS * $OUTPUT_RATE" | bc -l)

# Append to session log
echo "{\"timestamp\": $(date +%s), \"model\": \"$MODEL\", \"cost\": $TURN_COST, \"input_tokens\": $INPUT_TOKENS, \"output_tokens\": $OUTPUT_TOKENS}" >> "$SESSION_LOG"

# Output status line
python3 "${AGENTKIT_HOME}/hooks/render_dashboard.py" --log "$SESSION_LOG"
```

---

## Week 3: Model Routing + Thinking Budget

### 3.1 Auto Model Router
**File:** `router/model_router.py`

Classifies task complexity → selects model → sets `CLAUDE_MODEL` env var.

**Complexity tiers:**
```
SIMPLE   → Haiku   ($0.25/M input, $1.25/M output)
  - File search, grep, reading docs
  - Simple variable renames
  - Formatting fixes
  - All subagent tasks (always Haiku)

STANDARD → Sonnet  ($3/M input, $15/M output)  [DEFAULT]
  - Standard feature implementation
  - Bug fixes
  - Test writing
  - Code review
  - API integration

COMPLEX  → Opus    ($15/M input, $75/M output)
  - System architecture design
  - Complex debugging across multiple files
  - Security audit
  - Performance optimization at scale
  - Anything involving extended reasoning
```

**Routing logic:**
```python
# router/model_router.py
from dataclasses import dataclass

COMPLEXITY_SIGNALS = {
    "simple": [
        "find", "search", "list", "show", "read", "what is", "where is",
        "rename", "format", "fix typo", "update comment"
    ],
    "complex": [
        "architect", "design system", "security audit", "performance optimize",
        "refactor entire", "migrate", "analyze all", "debug across"
    ]
}

def route_model(prompt: str, is_subagent: bool = False) -> str:
    if is_subagent:
        return "claude-haiku-4-5"

    prompt_lower = prompt.lower()

    # Check for complex signals first
    for signal in COMPLEXITY_SIGNALS["complex"]:
        if signal in prompt_lower:
            return "claude-opus-4-6"

    # Check for simple signals
    simple_matches = sum(1 for s in COMPLEXITY_SIGNALS["simple"] if s in prompt_lower)
    if simple_matches >= 2:
        return "claude-haiku-4-5"

    # Default: Sonnet handles 80% of tasks well
    return "claude-sonnet-4-6"
```

### 3.2 Thinking Budget Manager
**File:** `router/thinking_budget.py`

Extended thinking burns 31,999 output tokens by default. Auto-adjust based on task complexity.

**Budget tiers:**
```
TRIVIAL   → 0 tokens      (simple searches, file reads, formatting)
MODERATE  → 8,192 tokens  (standard coding, bug fixes, feature work)
COMPLEX   → 32,000 tokens (architecture, security, complex debugging)
```

**Cost impact at Sonnet rates:**
```
0 tokens:      $0.00 thinking cost
8K tokens:     $0.12 per request
32K tokens:    $0.48 per request

Saving (vs always 32K): ~$0.36 per simple/moderate request
At 50 requests/day:     ~$18/day saved = ~$540/month
```

**Implementation:**
```python
# router/thinking_budget.py

THINKING_BUDGETS = {
    "trivial":  0,
    "moderate": 8192,
    "complex":  32000
}

def get_thinking_budget(task_category: str, complexity: str) -> int:
    if task_category in ["debugging-simple", "formatting", "file-search"]:
        return THINKING_BUDGETS["trivial"]
    elif task_category in ["architecting", "security-audit", "complex-debugging"]:
        return THINKING_BUDGETS["complex"]
    else:
        return THINKING_BUDGETS["moderate"]
```

---

## Week 4: Skill Library + CLI Installer

### 4.1 Curated Skill Library (50 Skills)
**Directory:** `skills/`

50 battle-tested skills organized by role. Each skill has all 3 levels in a single SKILL.md file.

**SKILL.md format:**
```markdown
---
id: debugging-python
name: Python Debugger
category: debugging
level1: "For debugging Python errors, exceptions, and tracebacks"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1: 50 tokens — loaded always when skill is active -->
## Python Debugger
Activate for: Python errors, exceptions, assertion failures, stack traces.

<!-- LEVEL 2: 500 tokens — loaded when debugging task confirmed -->
## Core Instructions
1. Read the full traceback top-to-bottom before touching any code
2. Identify root cause (not symptoms) — check variable state, not just the line that errored
3. Use print/logging strategically: confirm assumptions before fixing
...

<!-- LEVEL 3: 2000 tokens — loaded for complex debugging sessions -->
## Reference
### Common Python Error Patterns
- AttributeError: object has no attribute → check object type, None guards
- KeyError: → use .get() with default, check dict keys
...
```

**Role bundles:**

| Bundle | Skills (10 each) |
|--------|-----------------|
| Backend Pro | debugging, testing-tdd, api-rest, api-graphql, db-sql, db-migrations, auth-jwt, docker, git-workflow, code-review |
| Frontend Wizard | ui-ux, react-patterns, css-responsive, accessibility, performance-web, testing-jest, api-integration, state-management, design-system, animations |
| DevOps Master | docker, kubernetes, ci-cd, monitoring, logging, terraform, security-hardening, performance-tuning, git-workflow, incident-response |
| Full-Stack Hero | Best 10 across all categories |
| AI Engineer | llm-prompting, agent-patterns, rag, evals, fine-tuning, mcp-tools, token-optimization, ai-testing, embeddings, deployment-ml |

### 4.2 npx agentkit init
**File:** `cli/index.js`

One command: detects platform → installs correct format → configures optimal defaults.

**Install flow:**
```
$ npx agentkit init

✓ Detecting platform...          Claude Code detected
✓ Checking existing config...    No existing config found
✓ Downloading AgentKit v0.1.0... Done
✓ Installing skill library...    50 skills installed
✓ Configuring hooks...           forced-eval, cost-dashboard, skill-router
✓ Setting up model routing...    Haiku/Sonnet/Opus auto-routing enabled
✓ Thinking budget tuning...      Auto-tuning enabled
✓ Creating .agentkit.yaml...     Config saved

AgentKit installed successfully!

  Skills loaded: 50 (loading 2-5 per task instead of all 50)
  Estimated token savings: ~40,000 tokens/session
  Estimated cost savings: ~70% vs default setup

Run `npx agentkit status` to see real-time savings.
```

**Platform detection logic:**
```javascript
// cli/detect-platform.js
const fs = require('fs');
const path = require('path');

function detectPlatform() {
  const home = process.env.HOME;

  if (fs.existsSync(path.join(home, '.claude'))) return 'claude-code';
  if (fs.existsSync(path.join(home, '.cursor'))) return 'cursor';
  if (process.env.CODEX_CLI) return 'codex';
  if (process.env.GEMINI_CLI) return 'gemini-cli';

  // Check project-level indicators
  if (fs.existsSync('.cursor/rules')) return 'cursor';
  if (fs.existsSync('.claude/settings.json')) return 'claude-code';

  return 'claude-code'; // safe default
}
```

---

## File Structure After Phase 1

```
agentkit/
├── cli/
│   ├── index.js              # npx agentkit entry point
│   ├── detect-platform.js    # platform detection
│   ├── install.js            # installation logic
│   └── status.js             # status dashboard CLI
├── router/
│   ├── classifier.py         # task classifier
│   ├── selector.py           # skill selector
│   ├── disclosure.py         # progressive disclosure engine
│   ├── model_router.py       # auto model routing
│   └── thinking_budget.py    # thinking budget manager
├── hooks/
│   ├── forced_eval.sh        # forced-eval hook (84% activation)
│   ├── skill_router_hook.sh  # skill loading on each prompt
│   ├── cost_dashboard.sh     # real-time cost tracking
│   └── render_dashboard.py   # status line renderer
├── skills/
│   ├── registry.yaml         # skill registry + metadata
│   ├── debugging/            # 8 debugging skills
│   ├── testing/              # 7 testing skills
│   ├── ui-ux/                # 5 UI/UX skills
│   ├── devops/               # 8 DevOps skills
│   ├── backend/              # 8 backend skills
│   ├── frontend/             # 7 frontend skills
│   ├── ai-engineering/       # 5 AI skills
│   └── workflow/             # 2 workflow skills
├── config/
│   ├── defaults.yaml         # default AgentKit config
│   └── platforms/
│       ├── claude-code.yaml  # Claude Code specific config
│       └── cursor.yaml       # Cursor specific config
├── data/
│   └── session_costs.jsonl   # session cost log (gitignored)
└── .agentkit.yaml            # user's project config
```

---

## Success Metrics for Phase 1

| Metric | Target |
|--------|--------|
| Tokens per session (skills) | < 5,000 (down from 45,000) |
| Skill activation rate | > 80% (target: 84%) |
| Install time | < 60 seconds |
| Cost reduction | > 60% vs default setup |
| Platforms supported | Claude Code + Cursor |
| Skills in library | 50 |
| CLI commands working | init, status |

---

## Phase 1 → Phase 2 Handoff Criteria

- `npx agentkit init` works on a fresh machine end-to-end
- Forced-eval hook measurably increases skill activation (logged)
- Cost dashboard shows real-time $/session in status line
- At least 30 skills tested and validated on real tasks
- Model routing correctly identifies Haiku/Sonnet/Opus for test prompts
