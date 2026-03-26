# Architecture: Layer 2 — Project Memory Graph
**Color:** Purple (`#8b7cf7`)
**Tagline:** Claude-mem on steroids — project-level knowledge that persists forever
**Token Impact:** 10,000 → 2,000 tokens/session (80% reduction in memory context)

---

## The Problem It Solves

Claude forgets everything between sessions. Developers constantly:
- Re-explain the architecture ("so we use JWT with Redis for auth because...")
- Re-discover APIs they found two sessions ago
- Re-establish coding conventions Claude keeps ignoring
- Start new sessions with zero context on where they left off

claude-mem (39.9K stars) proves the demand is real. But it's memory-only — no skills, no workflow, no optimization. AgentKit's memory graph is smarter: structured knowledge (not flat text), relationship-aware, and injects only what's relevant.

---

## Components

### Component 1: Session Recorder

**Purpose:** Automatically captures high-value knowledge from each session without any manual effort.

**What gets captured and how:**

| Signal Type | Capture Trigger | Storage Location | Example |
|-------------|----------------|-----------------|---------|
| Architecture decision | Claude explains a choice | `decisions` table | "Using JWT (not sessions) because we need stateless auth for mobile" |
| File purpose | `Read` tool used on a file | `entities` table | `src/config/db.js` → "PostgreSQL connection pool, max 10 connections" |
| API endpoint | Code contains route definition | `entities` table | `POST /api/auth/login` → accepts `{email, password}`, returns `{token, user}` |
| Bug fixed | Edit + test success sequence | `decisions` table | "Fixed null check in getUserById — add `if (!user) return null`" |
| Pattern established | Claude creates reusable code | `decisions` table | "All API handlers follow: validate → auth check → execute → respond" |
| Working command | Bash tool succeeds | `decisions` table | `npm run test:integration` → runs integration tests against local DB |
| Package/dependency | package.json or requirements.txt read | `entities` table | `prisma@5.x` → ORM for PostgreSQL |
| Convention confirmed | Claude references a rule multiple times | `decisions` table | "We always use snake_case for DB columns, camelCase in JS" |

**Capture hook triggers:**
```
PostToolUse (tool=Read)    → entity extraction from file contents
PostToolUse (tool=Edit)    → change recorded, entity updated
PostToolUse (tool=Bash)    → if success: command captured; if fails: failure noted
Stop                       → session summary + handoff generation
```

**Entity extraction (from file reads):**
```python
# memory/recorder.py

class EntityExtractor:
    def extract_from_file_read(self, file_path: str, content: str) -> list[Entity]:
        entities = []
        ext = file_path.split(".")[-1]

        if ext in ["ts", "js", "py"]:
            # Extract function definitions
            entities.extend(self._extract_functions(content, file_path))
            # Extract API routes
            entities.extend(self._extract_routes(content, file_path))
            # Extract imports (dependencies)
            entities.extend(self._extract_imports(content, file_path))

        return entities

    def _extract_routes(self, content: str, file_path: str) -> list[Entity]:
        # Match: app.get('/path', ...), router.post('/path', ...)
        patterns = [
            r"(app|router)\.(get|post|put|delete|patch)\(['\"](.*?)['\"]",
            r"@(Get|Post|Put|Delete|Patch)\(['\"](.*?)['\"]",  # NestJS
        ]
        routes = []
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                routes.append(Entity(
                    id=f"api:{match.group(3)}",
                    type="api",
                    name=f"{match.group(2).upper()} {match.group(3)}",
                    path=file_path,
                    description=self._extract_route_context(content, match.start())
                ))
        return routes
```

**AI-assisted description generation (cheap — Haiku):**
```python
def generate_entity_description(entity_type: str, content_snippet: str) -> str:
    """Use Haiku to generate a 1-sentence description of an entity."""
    # Cost: ~50 tokens = ~$0.00006 per entity
    # Only called when regex extraction isn't descriptive enough
    prompt = f"Describe this {entity_type} in one sentence (max 20 words):\n\n{content_snippet[:300]}"
    return haiku_client.complete(prompt, max_tokens=50)
```

---

### Component 2: Project Knowledge Graph

**Purpose:** Store entities + relationships in a queryable graph structure. Not flat text — structured knowledge.

**Entity types:**
```
file        → source files (tracked with purpose + last-modified)
function    → named functions/methods (with signature + purpose)
api         → API endpoints (with method, path, params, returns)
package     → npm/pip packages (with version + why it's used)
concept     → abstract concepts (e.g., "JWT auth flow", "event sourcing")
decision    → architectural/implementation decisions
convention  → coding standards established in the project
command     → shell commands that work (with purpose)
```

**Relationship types:**
```
depends-on  → file A imports from file B
calls       → function A calls function B
tested-by   → function A is tested by test file B
implements  → file A implements interface/type B
extends     → class A extends class B
uses        → code uses package/library
related-to  → loosely related concepts
```

**Graph query examples:**
```python
# "What does src/auth/jwt.py depend on?"
graph.get_related("file:src/auth/jwt.py", relationship="depends-on")
# → ["package:jsonwebtoken", "file:src/config/env.js", "file:src/models/user.js"]

# "What calls getUserById?"
graph.get_related("function:getUserById", relationship="calls", direction="incoming")
# → ["function:getUser", "function:updateUserProfile", "function:deleteUser"]

# "What decisions were made about authentication?"
graph.query_decisions(category="auth")
# → [Decision("Use JWT", "..."), Decision("Refresh token in Redis", "...")]

# "What's relevant when working on src/auth/jwt.py?"
graph.get_context_for_file("src/auth/jwt.py", task="debugging")
# → 2000 tokens of relevant entities + decisions
```

**Graph storage (SQLite):**

The full schema is in `memory/schema.sql` (see Phase 2 plan). Key design decisions:
- **SQLite** (not Postgres, not a graph DB) — zero infrastructure, file-based, works offline
- **FTS5 virtual table** for full-text search across entities
- **Confidence scores** on entities — decay over time if not referenced
- **Source session** tracked — know when each piece of knowledge was learned

---

### Component 3: Smart Context Injection

**Purpose:** Before every agent turn, inject ONLY the memory nodes relevant to the current task. Budget: max 2,000 tokens.

**Relevance scoring algorithm:**
```python
def score_entity_relevance(entity: Entity, context: InjectionContext) -> float:
    score = 0.0

    # 1. Direct file match (highest priority)
    if entity.path in context.current_files:
        score += 1.0

    # 2. Related to current files (1 hop in graph)
    if entity.id in context.related_entity_ids:
        score += 0.7

    # 3. Category matches task
    if entity.category == context.task_category:
        score += 0.5

    # 4. Recent + high confidence
    recency_bonus = 1.0 / (1 + (time.time() - entity.updated_at) / 86400)  # days old
    score += recency_bonus * entity.confidence * 0.3

    # 5. Keyword overlap with prompt
    overlap = len(set(context.prompt_keywords) & set(entity.keywords))
    score += overlap * 0.2

    return score
```

**Injection output format (injected before agent turn):**
```markdown
## Project Memory (relevant to current task)

### Active Decisions
- **Auth**: JWT tokens expire in 15min. Refresh tokens stored in Redis, 7-day TTL.
- **Auth**: All auth routes use `express-rate-limit` — 100 req/15min per IP.
- **Convention**: API errors always return `{error: string, code: string}`.

### Current Files Context
- `src/auth/jwt.py` → JWT token generation + validation. Uses `python-jose`.
- `src/middleware/auth.py` → JWT middleware. Applied to all `/api/protected/*` routes.

### Related APIs
- `POST /api/auth/login` → accepts `{email, password}`, returns `{token, refreshToken, user}`
- `POST /api/auth/refresh` → accepts `{refreshToken}`, returns `{token}`

### Working Commands
- `python manage.py test auth` → runs auth unit tests
```

**Token budget enforcement:**
```python
MAX_INJECTION_TOKENS = 2000

def build_injection(context: InjectionContext) -> str:
    candidates = self.graph.get_context_for_task(context)
    candidates.sort(key=lambda c: c.relevance_score, reverse=True)

    injected = []
    total_tokens = 0

    for candidate in candidates:
        candidate_tokens = estimate_tokens(candidate.formatted_text)
        if total_tokens + candidate_tokens <= MAX_INJECTION_TOKENS:
            injected.append(candidate)
            total_tokens += candidate_tokens
        else:
            break  # Budget hit

    return format_injection(injected)
```

---

### Component 4: Cross-Session Handoff

**Purpose:** End of session: auto-generate a compressed handoff. Start of new session: load it instantly. Zero "where were we?" moments.

**Handoff generation (on `Stop` event):**
```python
# memory/handoff.py

HANDOFF_PROMPT = """
You are creating a session handoff for a software project.
Session data (decisions, changes, commands):
{session_data}

Create a handoff document using this exact format (max 500 tokens total):

## What We Built
[1-2 sentences: what was accomplished]

## Key Decisions Made
- [decision]: [rationale in 1 line]
- [decision]: [rationale in 1 line]
[max 5 decisions]

## Current State
- Complete: [list]
- In Progress: [list]
- Blocked: [list if any]

## Critical Context for Next Session
[The 3-5 most important things to remember. Be specific.]

## Files Changed
- [file]: [what changed in 1 line]
[max 10 files]
"""

def generate_handoff(session_id: str) -> str:
    session_data = self.db.get_session_summary(session_id)
    # Haiku call: ~800 tokens input, ~500 tokens output = ~$0.0015 per session
    return haiku_client.complete(
        HANDOFF_PROMPT.format(session_data=session_data),
        max_tokens=600
    )
```

**Handoff injection at session start:**
```bash
#!/bin/bash
# hooks/session_start.sh
# Triggered on: first UserPromptSubmit of session

HANDOFF_FILE="${AGENTKIT_PROJECT}/.agentkit/handoff.md"

if [ -f "$HANDOFF_FILE" ]; then
  HANDOFF_AGE=$(( ($(date +%s) - $(stat -f %m "$HANDOFF_FILE")) / 3600 ))

  if [ "$HANDOFF_AGE" -lt 168 ]; then  # < 7 days old
    echo "=== Session Handoff (from previous session) ==="
    cat "$HANDOFF_FILE"
    echo "================================================"
  fi
fi
```

**Handoff example output:**
```markdown
## What We Built
Implemented JWT refresh token flow with Redis session store. Fixed the token expiry bug
causing users to be logged out every 15 minutes.

## Key Decisions Made
- JWT access tokens: 15min expiry (mobile requirement)
- Refresh tokens: Redis, 7-day TTL, single-use (rotate on use)
- Token storage on client: httpOnly cookie (not localStorage — XSS protection)

## Current State
- Complete: Login, logout, refresh token endpoint
- In Progress: "Remember me" feature (30-day refresh token)
- Blocked: Nothing

## Critical Context for Next Session
1. Refresh tokens are stored in Redis key: `refresh:{userId}:{tokenId}`
2. The `rotateRefreshToken()` function in auth.py handles single-use rotation
3. Don't touch `src/middleware/auth.js` — the token validation logic is fragile
4. Run `pytest tests/auth/` before any auth changes — 23 tests covering edge cases

## Files Changed
- src/auth/jwt.py: Added refresh token generation + rotation logic
- src/routes/auth.py: Added POST /api/auth/refresh endpoint
- src/middleware/auth.py: Updated to handle expired access tokens gracefully
```

---

## Memory Lifecycle

```
Session Start
  ↓ Load handoff document (~500 tokens, always)
  ↓ Session Recorder initialized (new session ID)
  ↓ Memory injector primed with project DB

During Session (per agent turn)
  ↓ UserPromptSubmit → Smart Context Injection runs
    → Score entities by relevance to current task + files
    → Inject top entities (budget: 2,000 tokens)
  ↓ Tool use → Session Recorder captures
    → Read tool: extract entities from file
    → Edit tool: update entity, record change
    → Bash success: capture working command
    → Agent explanation: extract decisions (via hook)

Session End (Stop event)
  ↓ Session summarized (raw session data)
  ↓ Haiku generates handoff document (~$0.0015)
  ↓ Handoff saved to .agentkit/handoff.md
  ↓ New entities committed to memory.db
  ↓ Confidence scores updated (referenced = +, old = -)
```

---

## Confidence Decay System

Entities in memory aren't equally reliable forever. The confidence system handles this.

```python
def update_confidence(entity_id: str, event: str):
    entity = db.get_entity(entity_id)

    if event == "referenced":       # Agent used this memory node
        entity.confidence = min(1.0, entity.confidence + 0.1)
    elif event == "file_modified":  # The file this entity is about was changed
        entity.confidence *= 0.7    # Decay — the info may be outdated
    elif event == "age_30_days":    # 30 days without reference
        entity.confidence *= 0.8    # Slow decay
    elif event == "contradicted":   # New decision contradicts this one
        entity.confidence = 0.1     # Near-zero — mark as stale

    # Entities below 0.2 confidence are hidden from injection (but not deleted)
    db.update_entity(entity)
```

---

## Files Owned by This Layer

```
memory/
├── schema.sql          # SQLite database schema
├── recorder.py         # Session recorder + entity extractor
├── graph.py            # Knowledge graph queries + relationship traversal
├── injector.py         # Smart context injection (relevance scoring)
├── handoff.py          # AI-compressed session handoff generation
└── confidence.py       # Confidence decay system

hooks/
├── memory_recorder.sh  # PostToolUse → captures entities
├── memory_inject.sh    # UserPromptSubmit → injects relevant context
└── session_end.sh      # Stop → generates handoff

.agentkit/              # per-project, gitignored
├── memory.db           # SQLite knowledge graph
└── handoff.md          # latest session handoff
```
