# Architecture: Layer 4 — Workflow Engine
**Color:** Amber (`#f59e0b`)
**Tagline:** Superpowers methodology + subagent orchestration + quality gates
**Source:** Adapted from Superpowers (108K stars) — their methodology, our enforcement

---

## The Problem It Solves

Without workflow enforcement:
- Developers (and agents) jump straight to coding without understanding the problem
- Tests are an afterthought, not a gate
- Code gets merged without review
- Subagents spin up with full context (expensive) when they only need task-specific context
- Quality issues slip through to PR — and get caught at review, not at write time

Superpowers identified the right workflow (Research → Plan → Execute → Review → Ship). AgentKit enforces it via hooks — agents can't skip steps, not just suggestions.

---

## Component 1: Methodology Enforcer

**Purpose:** Enforced (not suggested) Research → Plan → Execute → Review → Ship pipeline via hooks.

**Workflow states:**
```
IDLE        → no active task
RESEARCH    → reading files, understanding the codebase
PLAN        → writing implementation plan (REQUIRED before coding)
EXECUTE     → writing code, running commands
REVIEW      → reviewing output, running tests, checking quality
SHIP        → committing, creating PR
```

**State machine:**
```python
# workflow/enforcer.py

VALID_TRANSITIONS = {
    "IDLE":    ["RESEARCH"],
    "RESEARCH":["PLAN"],
    "PLAN":    ["EXECUTE"],           # Only after plan is approved
    "EXECUTE": ["REVIEW"],            # Only after code is written
    "REVIEW":  ["SHIP", "EXECUTE"],   # Ship if all gates pass, back to Execute if not
    "SHIP":    ["IDLE"],
}

STATE_REQUIREMENTS = {
    "RESEARCH → PLAN": lambda ctx: ctx.files_read_count >= 2,
    "PLAN → EXECUTE":  lambda ctx: ctx.plan_exists and ctx.plan_approved,
    "EXECUTE → REVIEW":lambda ctx: ctx.edits_count >= 1,
    "REVIEW → SHIP":   lambda ctx: ctx.all_quality_gates_passed,
}
```

**Plan gate hook** (blocks coding without a plan):
```bash
#!/bin/bash
# hooks/plan_gate.sh
# Triggered on: PreToolUse (when tool=Edit or tool=Write)

WORKFLOW_STATE=$(cat "${AGENTKIT_PROJECT}/.agentkit/workflow_state" 2>/dev/null || echo "IDLE")
PLAN_FILE="${AGENTKIT_PROJECT}/.agentkit/current_plan.md"

# Allow if already in EXECUTE state
if [ "$WORKFLOW_STATE" = "EXECUTE" ]; then
  exit 0
fi

# Allow if in SHIP state (finalizing)
if [ "$WORKFLOW_STATE" = "SHIP" ]; then
  exit 0
fi

# Block if no plan exists
if [ ! -f "$PLAN_FILE" ] || [ ! -s "$PLAN_FILE" ]; then
  echo "┌─────────────────────────────────────────────┐"
  echo "│  AgentKit: PLAN REQUIRED before coding      │"
  echo "│                                             │"
  echo "│  Create a plan first:                       │"
  echo "│    1. What are you building?                │"
  echo "│    2. What files need to change?            │"
  echo "│    3. What are the steps?                   │"
  echo "│    4. What could go wrong?                  │"
  echo "└─────────────────────────────────────────────┘"
  exit 1
fi

# Transition to EXECUTE state
echo "EXECUTE" > "${AGENTKIT_PROJECT}/.agentkit/workflow_state"
exit 0
```

**Research enforcer** (ensures reading before coding):
```bash
#!/bin/bash
# hooks/research_gate.sh
# Triggered on: first Edit tool call after IDLE

FILES_READ=$(cat "${AGENTKIT_PROJECT}/.agentkit/session_reads_count" 2>/dev/null || echo "0")

if [ "$FILES_READ" -lt 2 ]; then
  echo "AgentKit: Read at least 2 relevant files before making changes."
  echo "Suggestion: Read the file you're about to edit + its tests."
  exit 1
fi
```

**Workflow commands (CLI):**
```bash
$ npx agentkit workflow status
Current state: PLAN
Plan: .agentkit/current_plan.md ✓
Files read: 4
Next step: Review plan → type 'approve' to start coding

$ npx agentkit workflow approve  # approve plan, transition to EXECUTE
$ npx agentkit workflow reset     # reset to IDLE (new task)
$ npx agentkit workflow skip-gates  # emergency override (logged)
```

---

## Component 2: Subagent Orchestrator

**Purpose:** Dispatch subtasks to specialized subagents with the right skill + model combo. Each subagent gets only what it needs.

**The key insight:**
- Main agent: full context, Sonnet/Opus, all skills
- Subagent: fresh context, Haiku always, only task-specific skills
- Cost: subagent at Haiku = 1/15th the cost of main agent at Opus

**Subagent roster:**

```python
# workflow/orchestrator.py

SUBAGENT_CONFIGS = {
    "writer": {
        "model":       "claude-haiku-4-5",
        "skills":      ["coding-patterns", "git-workflow"],
        "max_tokens":  4096,
        "description": "Standard implementation work"
    },
    "reviewer": {
        "model":       "claude-sonnet-4-6",   # Sonnet for review (needs judgment)
        "skills":      ["code-review", "security-audit"],
        "max_tokens":  8192,
        "description": "Fresh-context code review — doesn't inherit main agent's biases",
        "fresh_context": True   # No memory injection — review with fresh eyes
    },
    "researcher": {
        "model":       "claude-haiku-4-5",
        "skills":      ["documentation", "web-search"],
        "max_tokens":  2048,
        "description": "Finding info, reading docs, searching codebase"
    },
    "architect": {
        "model":       "claude-opus-4-6",
        "skills":      ["system-design", "patterns", "ddd"],
        "max_tokens":  16384,
        "extended_thinking": 16000,
        "description": "Complex design decisions — worth the Opus cost"
    },
    "tester": {
        "model":       "claude-haiku-4-5",
        "skills":      ["testing-tdd", "debugging"],
        "max_tokens":  4096,
        "description": "Writing + running tests"
    },
    "security": {
        "model":       "claude-sonnet-4-6",
        "skills":      ["security-audit", "owasp", "secrets-detection"],
        "max_tokens":  8192,
        "description": "Security audit of changes before ship"
    }
}
```

**Dispatch interface:**
```python
def dispatch(
    task: str,
    agent_type: str,
    files: list[str] = None,
    context: str = None
) -> SubagentResult:
    config = SUBAGENT_CONFIGS[agent_type]

    # Build minimal context for subagent
    subagent_context = []

    if not config.get("fresh_context"):
        # Inject only relevant memory (not full session context)
        subagent_context.extend(memory_graph.get_context_for_task(task, max_tokens=1000))

    if files:
        subagent_context.extend([read_file(f) for f in files])

    # Set env vars for subagent
    env = {
        "CLAUDE_CODE_SUBAGENT_MODEL": config["model"],
        "AGENTKIT_LOADED_SKILLS": ",".join(config["skills"]),
        "MAX_THINKING_TOKENS": str(config.get("extended_thinking", 0)),
    }

    return claude_code.spawn_subagent(
        prompt=task,
        context=subagent_context,
        env=env,
        max_tokens=config["max_tokens"]
    )
```

**Orchestration patterns:**

**Pattern A: Writer → Reviewer**
```
Main agent plans the feature
  ↓
Writer subagent (Haiku): implements the code
  ↓
Reviewer subagent (Sonnet, fresh context): reviews with no bias
  ↓
Main agent: applies review feedback
  ↓
Tester subagent (Haiku): writes + runs tests
  ↓
Security subagent (Sonnet): quick security scan
  ↓
Main agent: ships
```

**Pattern B: Parallel Research**
```
Main agent identifies 3 areas needing research
  ↓ (parallel)
Researcher A (Haiku): API documentation for dependency X
Researcher B (Haiku): How competitors solved problem Y
Researcher C (Haiku): Existing code patterns in this codebase
  ↓
Main agent: synthesizes research, creates plan
```

**Pattern C: Architect First**
```
Complex feature request
  ↓
Architect subagent (Opus + extended thinking): designs the system
  ↓
Main agent reviews architecture
  ↓
Writer subagents (Haiku × 2, parallel): implement separate components
  ↓
Reviewer subagent (Sonnet): reviews both implementations
```

---

## Component 3: Quality Gate Pipeline

**Purpose:** After each Edit, automatically run the quality gauntlet. No "it works on my machine."

**Gate sequence (order matters):**
```
1. Syntax check    (< 100ms)  → catches Python syntax errors, JS parse errors
2. Lint            (< 5s)     → style, logic issues, common anti-patterns
3. Type check      (< 30s)    → TypeScript/mypy type errors
4. Unit tests      (< 60s)    → runs test file matching changed file
5. Integration     (optional) → runs if AGENTKIT_RUN_INTEGRATION=true
```

**Gate hook:**
```bash
#!/bin/bash
# hooks/quality_gates.sh
# Triggered on: PostToolUse (tool=Edit)

FILE="$1"
EXT="${FILE##*.}"
FAILURES=()
GATE_RESULTS=()

run_gate() {
  local name="$1"
  local cmd="$2"

  if output=$(eval "$cmd" 2>&1); then
    GATE_RESULTS+=("  ✓ ${name}")
  else
    GATE_RESULTS+=("  ✗ ${name}")
    FAILURES+=("$name: $output")
  fi
}

case "$EXT" in
  py)
    run_gate "syntax"    "python3 -m py_compile '$FILE'"
    run_gate "lint"      "ruff check '$FILE' --select=E,W,F"
    run_gate "types"     "mypy '$FILE' --ignore-missing-imports"
    ;;
  ts|tsx)
    run_gate "syntax"    "npx tsc --noEmit --allowJs '$FILE' 2>&1 | head -5"
    run_gate "lint"      "npx eslint '$FILE' --max-warnings=0"
    run_gate "types"     "npx tsc --noEmit"
    ;;
  js|jsx)
    run_gate "lint"      "npx eslint '$FILE' --max-warnings=0"
    ;;
esac

# Find and run matching test file
TEST_FILE=$(find . -path "*/test*${FILE%.*}*" -o -path "*${FILE%.*}*test*" 2>/dev/null | grep -v node_modules | head -1)
if [ -n "$TEST_FILE" ]; then
  run_gate "tests" "npx jest '$TEST_FILE' --silent 2>&1 | tail -3"
fi

# Print results
echo "Quality Gates: $FILE"
printf '%s\n' "${GATE_RESULTS[@]}"

# Fail if any gate failed
if [ ${#FAILURES[@]} -gt 0 ]; then
  echo ""
  echo "Failures to fix:"
  printf '%s\n' "${FAILURES[@]}"
  exit 1
fi

exit 0
```

**Gate output examples:**

Success:
```
Quality Gates: src/auth/jwt.py
  ✓ syntax
  ✓ lint
  ✓ types
  ✓ tests (23 passed)
All gates passed. Ready to continue.
```

Failure:
```
Quality Gates: src/auth/jwt.py
  ✓ syntax
  ✗ lint (2 errors)
  ✓ types
  ✗ tests (1 failed)

Failures to fix:
  lint: jwt.py:45:5 E501 line too long (102 > 88 characters)
  lint: jwt.py:67:12 F841 local variable 'result' is assigned but never used
  tests: FAIL tests/auth/test_jwt.py::test_token_refresh - AssertionError: expected 401, got 200
```

**Gate configuration** (`.agentkit.yaml`):
```yaml
quality_gates:
  enabled: true
  on_edit: true
  on_commit: true
  gates:
    syntax: true
    lint: true
    typecheck: true
    unit_tests: true
    integration_tests: false  # Enable when CI is fast enough
  fail_behavior: "block"      # block | warn | log
  bypass_command: "npx agentkit gates skip --reason 'WIP'"
```

---

## Component 4: Git Worktree Manager

**Purpose:** Auto-create isolated git worktrees for parallel feature development. Subagents work in isolation — no branch conflicts.

**Why worktrees (not branches):**
- Branch: you switch between them (one at a time, disrupts main work)
- Worktree: separate directory checked out to a branch (truly parallel)
- Subagent works in worktree → main agent continues in main directory

**Worktree lifecycle:**
```python
# workflow/worktree.py

class WorktreeManager:
    def create(self, feature_name: str) -> Worktree:
        branch = f"feature/{feature_name}"
        worktree_path = f"../agentkit-worktrees/{feature_name}"

        subprocess.run([
            "git", "worktree", "add",
            worktree_path, "-b", branch
        ], check=True)

        # Copy AgentKit config to worktree
        shutil.copytree(
            ".agentkit/",
            f"{worktree_path}/.agentkit/",
            dirs_exist_ok=True
        )

        return Worktree(path=worktree_path, branch=branch)

    def list_active(self) -> list[Worktree]:
        output = subprocess.check_output(["git", "worktree", "list"]).decode()
        return [Worktree.parse(line) for line in output.strip().split("\n")]

    def merge(self, worktree: Worktree, strategy: str = "squash") -> None:
        subprocess.run([
            "git", "merge",
            "--squash" if strategy == "squash" else "--no-ff",
            worktree.branch
        ], check=True)
        self.remove(worktree)

    def remove(self, worktree: Worktree) -> None:
        subprocess.run(["git", "worktree", "remove", worktree.path], check=True)
        subprocess.run(["git", "branch", "-d", worktree.branch])
```

**Parallel development workflow:**
```
Main agent: working on Feature A (main worktree)
  ↓ (dispatch to subagent)
Subagent: working on Feature B in separate worktree
  → zero conflict with main agent
  → uses same .agentkit config (copied)
  → memory graph is read-only in subagent (writes go to main)

When Feature B done:
  → Subagent writes to worktree_results.md
  → Main agent reviews + merges worktree
  → Worktree cleaned up
```

**CLI commands:**
```bash
$ npx agentkit worktree create feature/oauth2
Created worktree: ../agentkit-worktrees/oauth2 (branch: feature/oauth2)

$ npx agentkit worktree list
feature/oauth2    ../agentkit-worktrees/oauth2    [in progress]
feature/logging   ../agentkit-worktrees/logging   [idle]

$ npx agentkit worktree merge feature/oauth2 --strategy squash
Merging feature/oauth2 into main...
3 commits squashed.
Worktree cleaned up.
```

---

## Workflow: Full End-to-End Example

```
User: "Add OAuth2 login with Google"

Step 1: RESEARCH (enforced)
  → Classifier: "api-work" + "auth"
  → Skill Router: loads [auth-jwt, api-rest, oauth-patterns]
  → Memory: injects existing auth decisions
  → Agent reads: src/auth/, src/routes/auth.js, package.json
  → Research gate: 4 files read ✓

Step 2: PLAN (enforced, blocks coding)
  → Agent writes plan to .agentkit/current_plan.md:
    "1. Add @google-cloud/oauth2 package
     2. Create GET /api/auth/google (redirect to Google)
     3. Create GET /api/auth/google/callback (handle code exchange)
     4. Update User model to support oauth_provider
     5. Write tests for callback handler"
  → Plan gate: plan exists, approved ✓
  → State → EXECUTE

Step 3: EXECUTE
  → Writer subagent (Haiku) implements steps 1-4
  → Quality gates fire on each edit: syntax ✓ lint ✓ types ✓
  → Memory recorder captures: new entities (OAuth routes, Google client)
  → State → REVIEW

Step 4: REVIEW
  → Tester subagent (Haiku) writes + runs tests for step 5
  → Reviewer subagent (Sonnet, fresh context) reviews OAuth flow
  → Security subagent (Sonnet) checks: OAuth state param ✓, redirect URI validation ✓
  → All quality gates pass ✓
  → State → SHIP

Step 5: SHIP
  → Git worktree merged to main
  → Commit created with conventional message
  → Memory: session decisions saved
  → Handoff generated: "Added Google OAuth2. State param used for CSRF. Callback at /api/auth/google/callback."
  → State → IDLE

Total cost: ~$0.42 (Haiku for writer/tester, Sonnet for reviewer/security)
Without AgentKit: ~$2.80 (Opus throughout, no subagent routing)
```

---

## Files Owned by This Layer

```
workflow/
├── enforcer.py         # State machine + gate logic
├── orchestrator.py     # Subagent dispatch + config
├── quality_gates.py    # Gate sequence management
└── worktree.py         # Git worktree manager

hooks/
├── plan_gate.sh        # PreToolUse → block Edit without plan
├── research_gate.sh    # PreToolUse → ensure research before coding
├── quality_gates.sh    # PostToolUse (Edit) → lint + typecheck + test
└── workflow_state.sh   # State transitions + logging

.agentkit/
├── workflow_state      # Current state (IDLE/RESEARCH/PLAN/EXECUTE/REVIEW/SHIP)
├── current_plan.md     # Active implementation plan
└── session_reads_count # How many files read this session
```
