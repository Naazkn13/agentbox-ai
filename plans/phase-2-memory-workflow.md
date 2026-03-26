# Phase 2: Memory + Workflow
**Timeline:** Weeks 5–8
**Goal:** Add persistent project memory (SQLite knowledge graph), enforced workflow methodology, subagent orchestration, quality gates, and ship the public GitHub launch.

---

## Deliverables Checklist

- [ ] SQLite-backed session recorder
- [ ] Project knowledge graph (entities + relationships + annotations)
- [ ] AI-compressed session handoffs (Haiku compression)
- [ ] Smart context injection (relevant memory nodes per task)
- [ ] Workflow enforcer: Research → Plan → Execute → Review → Ship
- [ ] Subagent orchestrator with skill + model routing per subtask
- [ ] Git worktree integration for parallel development
- [ ] Quality gate pipeline (auto lint + typecheck + test)
- [ ] GitHub public launch with README + demo video

---

## Week 5: Project Memory — Session Recorder + Knowledge Graph

### 5.1 Database Schema
**File:** `memory/schema.sql`

```sql
-- Core entity store
CREATE TABLE entities (
  id          TEXT PRIMARY KEY,          -- e.g., "file:src/auth/jwt.py"
  type        TEXT NOT NULL,             -- file | function | api | package | concept | decision
  name        TEXT NOT NULL,
  path        TEXT,                      -- filesystem path if applicable
  description TEXT,
  confidence  REAL DEFAULT 1.0,         -- 0.0–1.0, decays over time
  source_session TEXT,                   -- which session created this
  created_at  INTEGER NOT NULL,
  updated_at  INTEGER NOT NULL
);

-- Relationships between entities
CREATE TABLE relationships (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  from_id     TEXT NOT NULL REFERENCES entities(id),
  to_id       TEXT NOT NULL REFERENCES entities(id),
  type        TEXT NOT NULL,             -- depends-on | calls | tested-by | implements | extends
  weight      REAL DEFAULT 1.0,
  source_session TEXT,
  created_at  INTEGER NOT NULL
);

-- High-value decisions and patterns
CREATE TABLE decisions (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  title       TEXT NOT NULL,
  content     TEXT NOT NULL,            -- the actual decision/pattern
  category    TEXT NOT NULL,            -- architecture | api | db | security | pattern | convention
  tags        TEXT,                     -- JSON array of tags
  session_id  TEXT NOT NULL,
  created_at  INTEGER NOT NULL
);

-- Session summaries (AI-compressed)
CREATE TABLE sessions (
  id          TEXT PRIMARY KEY,
  started_at  INTEGER NOT NULL,
  ended_at    INTEGER,
  summary     TEXT,                     -- AI-compressed ~500 token summary
  raw_decisions TEXT,                   -- JSON: decisions captured this session
  token_count INTEGER,
  cost        REAL
);

-- Full-text search index
CREATE VIRTUAL TABLE entities_fts USING fts5(
  name, description, content=entities
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_relationships_from ON relationships(from_id);
CREATE INDEX idx_decisions_category ON decisions(category);
CREATE INDEX idx_decisions_created ON decisions(created_at DESC);
```

### 5.2 Session Recorder
**File:** `memory/recorder.py`

Automatically captures architectural decisions, API discoveries, bug fixes, and patterns during each session.

**What gets captured:**

| Signal | Trigger | Example |
|--------|---------|---------|
| Architecture decision | Claude says "I'll use X for Y because..." | "Using JWT with Redis session store for auth because..." |
| API discovered | Claude reads an API file or endpoint | `POST /api/auth/login` returns `{token, user}` |
| Bug fixed | Tool call sequence: read → edit → test passes | Fixed: null check missing in `getUserById()` |
| Pattern established | Claude creates a reusable pattern | "All API routes follow: validate → authorize → execute → respond" |
| Command that worked | Shell command succeeds | `npm run test:integration` → runs integration tests |
| File purpose discovered | Claude reads + summarizes a file | `src/config/db.js` → PostgreSQL connection pool config |

**Capture hook** (`hooks/memory_recorder.sh`):
```bash
#!/bin/bash
# Triggered on: PostToolUse (when tool = Edit or Bash with success)
# Pipe tool result to recorder for entity extraction

TOOL_NAME="$1"
TOOL_INPUT="$2"
TOOL_OUTPUT="$3"

python3 "${AGENTKIT_HOME}/memory/recorder.py" \
  --tool "$TOOL_NAME" \
  --input "$TOOL_INPUT" \
  --output "$TOOL_OUTPUT" \
  --session "${AGENTKIT_SESSION_ID}" \
  --db "${AGENTKIT_MEMORY_DB}"
```

**Entity extraction logic:**
```python
# memory/recorder.py
import re, json, sqlite3
from datetime import datetime

class SessionRecorder:
    def __init__(self, db_path: str, session_id: str):
        self.db = sqlite3.connect(db_path)
        self.session_id = session_id

    def record_tool_use(self, tool: str, input_data: dict, output: str):
        if tool == "Edit":
            self._record_file_change(input_data, output)
        elif tool == "Bash":
            self._record_command(input_data, output)
        elif tool == "Read":
            self._record_file_read(input_data, output)

    def _record_file_change(self, input_data: dict, output: str):
        file_path = input_data.get("file_path", "")
        # Create/update file entity
        self._upsert_entity(
            id=f"file:{file_path}",
            type="file",
            name=file_path.split("/")[-1],
            path=file_path,
            description=self._summarize_change(input_data)
        )

    def _summarize_change(self, edit_data: dict) -> str:
        # Use Haiku to generate a 1-sentence summary of the change
        # This is cheap: ~100 tokens per edit
        old = edit_data.get("old_string", "")[:200]
        new = edit_data.get("new_string", "")[:200]
        return f"Changed: {old[:50]}... → {new[:50]}..."
```

### 5.3 Project Knowledge Graph
**File:** `memory/graph.py`

Manages the entity-relationship graph. Supports queries like "what does auth depend on?" or "what calls getUserById?".

```python
# memory/graph.py

class KnowledgeGraph:
    def __init__(self, db_path: str):
        self.db = sqlite3.connect(db_path)

    def get_related(self, entity_id: str, depth: int = 2) -> list:
        """Get all entities related to the given entity up to `depth` hops."""
        ...

    def get_by_task(self, task_category: str, current_files: list) -> list:
        """
        Smart context injection: given the current task + files being worked on,
        return the most relevant memory nodes.

        Priority order:
        1. Entities directly matching current files
        2. Decisions in the same category as current task
        3. Entities 1-hop away from current files
        4. Recent high-confidence decisions
        """
        ...

    def search(self, query: str) -> list:
        """Full-text search across entities and decisions."""
        return self.db.execute(
            "SELECT * FROM entities_fts WHERE entities_fts MATCH ? LIMIT 20",
            (query,)
        ).fetchall()
```

---

## Week 6: Smart Context Injection + Session Handoffs

### 6.1 Smart Context Injection
**File:** `memory/injector.py`

Before every agent turn, injects ONLY the memory nodes relevant to the current task.

**Injection budget:** Max 2,000 tokens of memory context (vs 10,000+ with full CLAUDE.md)

**What gets injected:**
```
Working on: src/auth/jwt.py (Edit tool)
Current task category: api-work

Injected memory:
  DECISION [auth]: JWT tokens expire in 15min. Refresh tokens in Redis, 7-day TTL.
  ENTITY [function]: validateToken() in src/auth/jwt.py — verifies + refreshes
  ENTITY [api]: POST /api/auth/refresh — refresh token endpoint
  DECISION [security]: All auth routes require rate limiting (express-rate-limit)
  ENTITY [file]: src/middleware/auth.js — JWT middleware, used by all protected routes
```

**Injection hook** (`hooks/memory_inject.sh`):
```bash
#!/bin/bash
# Triggered on: UserPromptSubmit

PROMPT="$1"
CURRENT_FILES=$(git diff --name-only HEAD 2>/dev/null | head -10)

python3 "${AGENTKIT_HOME}/memory/injector.py" \
  --prompt "$PROMPT" \
  --files "$CURRENT_FILES" \
  --task-category "${AGENTKIT_TASK_CATEGORY}" \
  --db "${AGENTKIT_MEMORY_DB}" \
  --max-tokens 2000
```

### 6.2 AI-Compressed Session Handoffs
**File:** `memory/handoff.py`

End of session: compress everything learned → ~500 token handoff document.
Start of new session: load handoff + inject relevant memory nodes.

**Compression prompt (sent to Haiku — cheap):**
```
You are compressing a coding session into a handoff document.
Session decisions and changes: [raw session data]

Create a handoff in this format (max 500 tokens):
## What We Built
[1-2 sentences]

## Key Decisions Made
- [decision 1]
- [decision 2]
...

## Current State
[what's complete, what's in progress, what's blocked]

## Critical Context for Next Session
[the 3-5 most important things to remember]

## Files Changed
[list of files + what changed]
```

**Handoff trigger** (`hooks/session_end.sh`):
```bash
#!/bin/bash
# Triggered on: Stop (session ending)

python3 "${AGENTKIT_HOME}/memory/handoff.py" \
  --session "${AGENTKIT_SESSION_ID}" \
  --db "${AGENTKIT_MEMORY_DB}" \
  --output "${AGENTKIT_PROJECT}/.agentkit/handoff.md"

echo "Session compressed. Handoff saved to .agentkit/handoff.md"
```

---

## Week 7: Workflow Engine

### 7.1 Methodology Enforcer
**File:** `workflow/enforcer.py`

Enforces: Research → Plan → Execute → Review → Ship via hooks. Agent can't skip steps.

**Workflow states:**

```
IDLE         → waiting for task
RESEARCHING  → reading files, understanding codebase
PLANNING     → creating plan (required before coding)
EXECUTING    → writing code, running commands
REVIEWING    → checking output, running tests
SHIPPING     → committing, PR creation
```

**State transitions (enforced via hooks):**

| From | To | Trigger | Gate |
|------|----|---------|------|
| IDLE | RESEARCHING | User gives task | None |
| RESEARCHING | PLANNING | Agent has read relevant files | Must create a plan first |
| PLANNING | EXECUTING | Plan approved by user | Plan must have steps |
| EXECUTING | REVIEWING | Edit tool used | Must run tests |
| REVIEWING | SHIPPING | Tests pass | All quality gates pass |

**Plan enforcement hook** (`hooks/plan_gate.sh`):
```bash
#!/bin/bash
# Triggered on: PreToolUse (tool=Edit)
# Blocks editing without a plan

PLAN_FILE="${AGENTKIT_PROJECT}/.agentkit/current_plan.md"
WORKFLOW_STATE="${AGENTKIT_WORKFLOW_STATE:-IDLE}"

if [ "$WORKFLOW_STATE" = "EXECUTING" ]; then
  exit 0  # Already in execute mode, allow
fi

if [ ! -f "$PLAN_FILE" ] || [ "$WORKFLOW_STATE" = "RESEARCHING" ]; then
  echo "BLOCKED: Create a plan before writing code."
  echo "Use: /plan to create your implementation plan."
  exit 1
fi
```

### 7.2 Subagent Orchestrator
**File:** `workflow/orchestrator.py`

Dispatches subtasks to subagents with the right skill + model combo.

**Subagent types:**

| Agent | Model | Skills | Purpose |
|-------|-------|--------|---------|
| Writer | Haiku | coding, testing | Standard implementation work |
| Reviewer | Sonnet | code-review, security | Fresh-context code review |
| Researcher | Haiku | documentation, search | Finding info, reading docs |
| Architect | Opus | system-design, patterns | Complex design decisions |
| Tester | Haiku | testing, debugging | Writing + running tests |

**Dispatch logic:**
```python
# workflow/orchestrator.py

class SubagentOrchestrator:
    AGENT_CONFIGS = {
        "writer":     {"model": "claude-haiku-4-5",  "skills": ["coding", "git-workflow"]},
        "reviewer":   {"model": "claude-sonnet-4-6", "skills": ["code-review", "security"]},
        "researcher": {"model": "claude-haiku-4-5",  "skills": ["documentation"]},
        "architect":  {"model": "claude-opus-4-6",   "skills": ["system-design", "patterns"]},
        "tester":     {"model": "claude-haiku-4-5",  "skills": ["testing", "debugging"]},
    }

    def dispatch(self, task: str, agent_type: str, context: dict) -> str:
        config = self.AGENT_CONFIGS[agent_type]
        # Sets CLAUDE_CODE_SUBAGENT_MODEL env var
        # Injects only the skills the subagent needs (not main agent's full context)
        ...
```

### 7.3 Quality Gate Pipeline
**File:** `workflow/quality_gates.py`

After each Edit: auto-run linter, type checker, tests. Route failures back to agent.

**Gate sequence:**
```
1. Syntax check     (instant — catches basic errors)
2. Lint             (eslint/pylint/ruff — catches style/logic issues)
3. Type check       (tsc/mypy — catches type errors)
4. Unit tests       (jest/pytest — catches regressions)
5. Integration test (optional — runs if relevant test file exists)
```

**Gate hook** (`hooks/quality_gates.sh`):
```bash
#!/bin/bash
# Triggered on: PostToolUse (tool=Edit)

FILE_PATH="$1"
EXT="${FILE_PATH##*.}"
FAILURES=""

case "$EXT" in
  py)
    ruff check "$FILE_PATH" 2>&1 | grep -q "error" && FAILURES+="lint "
    mypy "$FILE_PATH" 2>&1 | grep -q "error" && FAILURES+="types "
    ;;
  ts|tsx|js|jsx)
    eslint "$FILE_PATH" 2>&1 | grep -q "error" && FAILURES+="lint "
    tsc --noEmit 2>&1 | grep -q "error" && FAILURES+="types "
    ;;
esac

# Run tests if test file exists
TEST_FILE=$(find . -name "*${FILE_PATH%.*}*test*" -o -name "*test*${FILE_PATH%.*}*" 2>/dev/null | head -1)
if [ -n "$TEST_FILE" ]; then
  npx jest "$TEST_FILE" --silent 2>&1 | grep -q "FAIL" && FAILURES+="tests "
fi

if [ -n "$FAILURES" ]; then
  echo "QUALITY_GATE_FAILED: ${FAILURES}"
  echo "Fix these issues before continuing."
  exit 1
fi
```

### 7.4 Git Worktree Manager
**File:** `workflow/worktree.py`

Auto-create git worktree for each feature. Clean parallel development.

```bash
# workflow/worktree.sh
# Usage: agentkit worktree create feature/auth-refresh

FEATURE_NAME="$1"
WORKTREE_DIR="${AGENTKIT_PROJECT}/../agentkit-worktrees/${FEATURE_NAME}"

git worktree add "$WORKTREE_DIR" -b "$FEATURE_NAME"
echo "Worktree created: $WORKTREE_DIR"
echo "AgentKit config copied. Subagent can work here independently."

# Copy .agentkit config to worktree
cp -r "${AGENTKIT_PROJECT}/.agentkit" "${WORKTREE_DIR}/.agentkit"
```

---

## Week 8: GitHub Launch

### 8.1 README Structure

```markdown
# AgentKit — The Intelligent Orchestration Layer for Agentic Coding

> One install. 70% less cost. Your agent actually remembers things.

[GIF: install → auto-skill-loading → memory injection → cost dashboard]

## The Problem
[3 bullet points with real numbers]

## The Solution
[5-layer architecture diagram]

## Quick Start
npx agentkit init

## What You Get
- 89% token reduction via smart skill loading
- Persistent project memory (never re-explain your architecture)
- 70% cost reduction via model routing
- Enforced coding workflow with quality gates
- Works on Claude Code, Cursor, Codex, Gemini CLI + 7 more
```

### 8.2 Launch Checklist

- [ ] Demo video: 3-minute screen recording showing all 4 core features
- [ ] Benchmark post: before/after token counts from real sessions
- [ ] HN post draft ready
- [ ] Discord announcement ready (Claude Code Discord)
- [ ] Reddit posts ready (r/ClaudeAI, r/ChatGPTCoding)
- [ ] Twitter thread with GIF ready

---

## File Structure After Phase 2

```
agentkit/
├── [Phase 1 files...]
├── memory/
│   ├── schema.sql            # SQLite schema
│   ├── recorder.py           # session recorder
│   ├── graph.py              # knowledge graph queries
│   ├── injector.py           # smart context injection
│   └── handoff.py            # AI-compressed session handoffs
├── workflow/
│   ├── enforcer.py           # methodology enforcer
│   ├── orchestrator.py       # subagent orchestrator
│   ├── quality_gates.py      # lint + typecheck + test pipeline
│   └── worktree.py           # git worktree manager
├── hooks/
│   ├── [Phase 1 hooks...]
│   ├── memory_recorder.sh    # captures entities from tool use
│   ├── memory_inject.sh      # injects relevant memory per turn
│   ├── session_end.sh        # compresses session on stop
│   ├── plan_gate.sh          # blocks coding without a plan
│   └── quality_gates.sh      # auto lint/test after edits
└── .agentkit/               # per-project state (gitignored)
    ├── memory.db             # SQLite knowledge graph
    ├── handoff.md            # latest session handoff
    └── current_plan.md       # current active plan
```

---

## Success Metrics for Phase 2

| Metric | Target |
|--------|--------|
| Memory injection token budget | < 2,000 tokens (relevant nodes only) |
| Session handoff compression ratio | Raw session → 500 token summary |
| Workflow enforcement | 0 code edits without a plan |
| Quality gate catch rate | > 90% of lint/type errors caught pre-commit |
| GitHub stars at launch | 500+ in first week |
| Subagent cost vs main agent | < 10% (Haiku vs Opus) |
