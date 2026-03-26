# Architecture: Layer 3 — Token Budget Intelligence
**Color:** Green (`#4ade80`)
**Tagline:** Automatically optimizes cost without you thinking about it
**Token Impact:** $200/mo → ~$60/mo per developer (70% cost reduction)

---

## The Problem It Solves

Claude Code costs $100-200/developer/month at default settings because:
1. **Wrong model used:** Opus ($15/M) for a file search that Haiku ($0.25/M) could do — 60x overspend
2. **Extended thinking always on:** 31,999 output tokens burned on simple tasks — $0.48/request wasted
3. **Subagents use main model:** CLAUDE_CODE_SUBAGENT_MODEL unset → subagents cost as much as primary
4. **No real-time visibility:** Developers don't see costs until the monthly Anthropic bill
5. **Context bloat:** Auto-compact at 80% is reactive, not proactive — wastes 30% of context budget

---

## Component 1: Auto Model Router

**Purpose:** Every agent turn, classify task complexity → route to the right model automatically.

**Model price ladder (as of 2026):**
```
Model                  Input ($/M)   Output ($/M)   Use case
─────────────────────  ───────────   ────────────   ─────────────────────────────────
claude-haiku-4-5       $0.25         $1.25          Simple tasks, subagents, searches
claude-sonnet-4-6      $3.00         $15.00         Standard coding (80% of tasks)
claude-opus-4-6        $15.00        $75.00         Complex architecture, security
```

**Complexity classification (3 tiers):**

```python
# router/model_router.py

SIMPLE_SIGNALS = [
    # File operations
    "find", "search", "list files", "show me", "what is", "where is",
    "read", "look at", "open", "which file",
    # Trivial edits
    "rename", "format", "fix typo", "update comment", "add space",
    # Simple lookups
    "what does", "explain this line", "what's the type of",
]

COMPLEX_SIGNALS = [
    # Architecture
    "architect", "design system", "design the", "how should we structure",
    "what's the best approach for", "trade-offs",
    # Security
    "security audit", "vulnerability", "penetration", "threat model",
    # Performance
    "performance audit", "profile", "benchmark", "optimize across",
    # Scale
    "migrate entire", "refactor the whole", "analyze all files",
    # Deep reasoning
    "why is this happening", "root cause of", "investigate",
]

def route_model(prompt: str, context: RoutingContext) -> str:
    # Rule 1: Subagents ALWAYS use Haiku
    if context.is_subagent:
        return "claude-haiku-4-5"

    prompt_lower = prompt.lower()

    # Rule 2: Check complex signals (override everything)
    complex_score = sum(1 for s in COMPLEX_SIGNALS if s in prompt_lower)
    if complex_score >= 1:
        return "claude-opus-4-6"

    # Rule 3: Check simple signals
    simple_score = sum(1 for s in SIMPLE_SIGNALS if s in prompt_lower)
    if simple_score >= 2:
        return "claude-haiku-4-5"

    # Rule 4: Short prompts with no code context → Haiku
    if len(prompt) < 100 and not context.has_code_context:
        return "claude-haiku-4-5"

    # Rule 5: Personal model override (Phase 4)
    if personal_model.has_override(prompt):
        return personal_model.get_model(prompt)

    # Default: Sonnet handles 80% of tasks well
    return "claude-sonnet-4-6"
```

**Cost impact of routing correctly:**
```
Assume 50 turns per session:
  Without routing: All Sonnet
    50 turns × avg 2K tokens × $15/M output = $1.50/session

  With routing (typical distribution):
    30 turns Haiku:   30 × 2K × $1.25/M   = $0.075
    18 turns Sonnet:  18 × 2K × $15/M     = $0.54
    2 turns Opus:     2  × 2K × $75/M     = $0.30
    Total:                                  = $0.915/session
    Savings: 39% on output tokens alone

  With Haiku subagents (additional):
    Subagents now cost 1/15th of Sonnet → ~$0.20 savings/session
    Combined: ~60% cost reduction
```

**Routing hook** (`hooks/model_router_hook.sh`):
```bash
#!/bin/bash
# Triggered on: UserPromptSubmit

PROMPT="$1"
IS_SUBAGENT="${CLAUDE_CODE_SUBAGENT:-false}"

ROUTED_MODEL=$(python3 "${AGENTKIT_HOME}/router/model_router.py" \
  --prompt "$PROMPT" \
  --is-subagent "$IS_SUBAGENT")

export CLAUDE_MODEL="$ROUTED_MODEL"
export CLAUDE_CODE_SUBAGENT_MODEL="claude-haiku-4-5"  # Always Haiku for subagents

echo "[AgentKit] Model: ${ROUTED_MODEL}"
```

---

## Component 2: Thinking Budget Manager

**Purpose:** Extended thinking burns 31,999 output tokens by default. Auto-adjust based on task complexity — 0 for trivial, 32K only for genuinely complex tasks.

**The problem in numbers:**
```
Extended thinking at 32K tokens (Sonnet):
  32,000 output tokens × $15/M = $0.48 per request
  At 50 requests/day:           $24/day = $720/month

Extended thinking at 8K (moderate tasks):
  8,000 × $15/M = $0.12 per request
  Savings: $0.36 per request

Extended thinking at 0 (simple tasks):
  0 × anything = $0.00
  Savings: $0.48 per request
```

**Budget tiers:**
```python
# router/thinking_budget.py

THINKING_BUDGETS = {
    "trivial":  0,      # No extended thinking
    "moderate": 8192,   # Moderate reasoning
    "complex":  32000,  # Full extended thinking
}

TRIVIAL_TASKS = [
    "debugging",     # Find bug, read traceback — no deep reasoning needed
    "formatting",    # Code formatting
    "file-search",   # Finding files
    "simple-edit",   # Variable rename, comment update
    "reading-docs",  # Summarizing documentation
]

COMPLEX_TASKS = [
    "architecting",        # System design requires deep reasoning
    "security-audit",      # Security reasoning across multiple files
    "complex-debugging",   # Multi-file, hard-to-reproduce bugs
    "performance-analysis",# Profiling + optimization strategy
    "migration-planning",  # Large-scale refactors
]

def get_thinking_budget(task_category: str, complexity: float) -> int:
    if task_category in TRIVIAL_TASKS or complexity < 0.3:
        return THINKING_BUDGETS["trivial"]
    elif task_category in COMPLEX_TASKS or complexity > 0.8:
        return THINKING_BUDGETS["complex"]
    else:
        return THINKING_BUDGETS["moderate"]
```

**Thinking budget hook:**
```bash
#!/bin/bash
# hooks/thinking_budget.sh
# Triggered on: UserPromptSubmit

TASK_CATEGORY="${AGENTKIT_TASK_CATEGORY:-standard}"
COMPLEXITY="${AGENTKIT_COMPLEXITY:-0.5}"

BUDGET=$(python3 "${AGENTKIT_HOME}/router/thinking_budget.py" \
  --category "$TASK_CATEGORY" \
  --complexity "$COMPLEXITY")

export MAX_THINKING_TOKENS="$BUDGET"
echo "[AgentKit] Thinking budget: ${BUDGET} tokens"
```

**Monthly savings from thinking budget tuning:**
```
Assume: 40 requests/day, mix of complexity
  10 trivial (0 tokens):   0 × $0.48  = $0.00
  25 moderate (8K tokens): 25 × $0.12 = $3.00
  5 complex (32K tokens):  5  × $0.48 = $2.40
  Daily total:                          $5.40
  Monthly:                              $162

Without tuning (always 32K):
  40 × $0.48 = $19.20/day = $576/month

Savings: $414/month (72% reduction in thinking costs)
```

---

## Component 3: Smart Compaction

**Purpose:** Instead of waiting for context to hit 80% (crude, reactive), proactively compact at logical breakpoints while preserving high-value context.

**Compaction triggers (proactive):**
```python
COMPACTION_TRIGGERS = [
    "task_completed",      # Quality gates all passed, task done
    "branch_merged",       # git merge detected
    "test_suite_passed",   # Full test run passed
    "context_at_60pct",    # 60% full (not 80%) — earlier is better
    "topic_shift",         # Classifier detects major task category change
    "user_command",        # User types /compact
]
```

**Smart compaction algorithm:**
```python
# router/compaction.py

def smart_compact(session: Session, trigger: str) -> CompactionResult:
    # Step 1: Categorize all context elements
    elements = session.get_all_context_elements()

    keep = []
    discard = []

    for element in elements:
        score = _score_element(element, session.current_task)

        if score > 0.6:
            keep.append(element)
        else:
            discard.append(element)

    # Step 2: Ensure decisions are in memory graph before discarding
    for element in discard:
        if element.type == "decision":
            memory_graph.upsert_decision(element)

    # Step 3: Generate concise summary of discarded elements
    discarded_summary = haiku.summarize(discard, max_tokens=200)

    return CompactionResult(
        kept=keep,
        discarded_summary=discarded_summary,
        tokens_freed=sum(e.token_count for e in discard)
    )

def _score_element(element: ContextElement, current_task: str) -> float:
    score = 0.0

    # High value: keep always
    if element.type in ["current_plan", "current_error", "current_task"]:
        return 1.0

    # Medium value: keep if relevant to current task
    if element.type == "file_content" and element.path in current_active_files:
        score += 0.7
    if element.type == "decision" and element.category == current_task_category:
        score += 0.6

    # Low value: discard
    if element.type == "successful_command" and element.captured_in_memory:
        score += 0.1  # Already in memory — safe to discard
    if element.type == "old_conversation" and element.age_turns > 20:
        score += 0.1

    return score
```

**Smart vs naive compaction:**
```
Naive (auto-compact at 80%):
  Context: 160K tokens (80% of 200K)
  Summary: crude "summarize the conversation" prompt
  Result: loses 40% of important context, keeps irrelevant chat
  Tokens freed: 80K (40% of total)

Smart (proactive at logical breakpoints):
  Trigger: Task completed at 55K tokens (27% full)
  Identifies: 20K tokens of completed task's raw file reads
  Result: frees 20K, saves all decisions to memory graph
  Tokens freed: 20K, zero context lost
  Benefit: next 2-3 tasks have full context budget
```

---

## Component 4: Cost Dashboard Hook

**Purpose:** Real-time cost tracking in the Claude Code status line. No more bill shock.

**Status line format:**
```
💰 $0.034 | 🧠 sonnet | ⚡ 12,450 tok | 📊 $1.02/day est
```

**What's tracked:**
- `$0.034` — cost of this session so far
- `sonnet` — model used on last turn
- `12,450 tok` — tokens used this session (input + output)
- `$1.02/day est` — estimated daily spend based on rolling 30-day average

**Cost tracking implementation:**
```python
# hooks/render_dashboard.py

MODEL_RATES = {
    "claude-haiku-4-5":  {"input": 0.00000025, "output": 0.00000125},
    "claude-sonnet-4-6": {"input": 0.000003,   "output": 0.000015},
    "claude-opus-4-6":   {"input": 0.000015,   "output": 0.000075},
}

def render_status_line(session_log_path: str) -> str:
    logs = load_jsonl(session_log_path)

    session_cost = sum(l["cost"] for l in logs)
    last_model = logs[-1]["model"] if logs else "unknown"
    total_tokens = sum(l["input_tokens"] + l["output_tokens"] for l in logs)
    daily_estimate = calculate_daily_estimate()

    model_short = last_model.replace("claude-", "").replace("-4-5", "").replace("-4-6", "")

    return f"💰 ${session_cost:.3f} | 🧠 {model_short} | ⚡ {total_tokens:,} tok | 📊 ${daily_estimate:.2f}/day"
```

**Hook registration:**
```json
// .claude/settings.json
{
  "statusCommand": "python3 ${AGENTKIT_HOME}/hooks/render_dashboard.py --log ${AGENTKIT_DATA}/session_costs.jsonl"
}
```

**Weekly cost report (automated):**
```
$ npx agentkit costs --week

📊 Cost Report: March 20-26, 2026

Total spent:        $34.20
Without AgentKit:   ~$98.50 (estimated baseline)
Savings:            $64.30 (65%)

By model:
  Haiku:   42 turns  $0.80   (2%)
  Sonnet: 156 turns $28.40  (83%)
  Opus:    12 turns  $5.00  (15%)

Most expensive sessions:
  Mon Mar 25: $8.40  "Refactor auth system + JWT refresh"
  Tue Mar 24: $6.20  "Debug WebSocket connection leaks"
  Wed Mar 23: $4.80  "Design new payment flow architecture"

Optimization opportunities:
  → 18 turns used Sonnet for simple file searches (should be Haiku)
  → Potential extra savings: $2.10/week
  → Run: npx agentkit optimize to auto-fix routing
```

---

## Combined Cost Reduction Math

Starting point: $200/month developer spending on Claude Code

| Optimization | Monthly Savings | % Reduction |
|-------------|----------------|-------------|
| Skill Router (89% fewer skill tokens) | $20-30 | 10-15% |
| Auto Model Routing (Haiku for simple + subagents) | $40-60 | 20-30% |
| Thinking Budget Tuning | $30-50 | 15-25% |
| Smart Context Injection (memory, not full CLAUDE.md) | $10-15 | 5-7% |
| Smart Compaction | $10-20 | 5-10% |
| **Combined** | **$110-175** | **55-87%** |
| **Conservative estimate** | **$140** | **70%** |

**Result: $200/mo → $60/mo (70% reduction)**

---

## Files Owned by This Layer

```
router/
├── model_router.py       # Auto model routing (complexity → model)
├── thinking_budget.py    # Thinking budget manager (task → budget)
└── compaction.py         # Smart compaction (proactive at breakpoints)

hooks/
├── model_router_hook.sh  # UserPromptSubmit → sets CLAUDE_MODEL
├── thinking_budget.sh    # UserPromptSubmit → sets MAX_THINKING_TOKENS
├── cost_dashboard.sh     # PostToolUse → logs cost, updates status
└── render_dashboard.py   # Renders status line + cost reports

data/
└── session_costs.jsonl   # Per-turn cost log (gitignored)
```
