# SKILL.md Universal Format Specification
**Version:** 1.0.0
**AgentKit Layer:** 5 — Universal Platform Layer

---

## Overview

SKILL.md is a universal skill format that works natively across 11+ AI coding platforms.
One file — multiple platforms, zero manual conversion.

---

## File Structure

```markdown
---
# Required
id: debugging-python
name: Python Debugger
category: debugging
level1: "For Python errors, exceptions, and tracebacks"
platforms: [claude-code, cursor, codex, gemini-cli, antigravity, opencode, aider, windsurf]

# Optional
priority: 1
keywords: [python, traceback, exception, AttributeError, TypeError, bug]
level1_tokens: 45
level2_tokens: 480
level3_tokens: 2100
author: agentkit-team
version: 1.0.0
---

<!-- LEVEL 1 START -->
## Python Debugger
Activate for: Python errors, exceptions, assertion failures, stack traces.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Core Instructions

1. Read the full traceback top-to-bottom before touching any code.
2. Identify root cause (not symptoms) — check variable state at the error line.
3. Reproduce the error with the minimal possible input.
4. Fix the root cause, not the symptom.
5. Run the tests after fixing.

### Quick Debug Checklist
- [ ] Read the full traceback
- [ ] Check the exact line that threw the error
- [ ] Inspect variable values at that point
- [ ] Search for similar error patterns in the codebase
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Full Reference

### Common Python Error Patterns

**AttributeError: 'NoneType' object has no attribute 'X'**
→ A variable you expected to be set is None.
→ Check where it's assigned. Is it conditional? Did the assignment fail silently?

**KeyError: 'key'**
→ Dictionary doesn't have this key. Use `.get('key', default)` or check `'key' in d`.

**TypeError: unsupported operand type(s)**
→ Type mismatch. Add `type()` prints to see actual types at runtime.

**ImportError / ModuleNotFoundError**
→ Module not installed (`pip3 install X`) or wrong Python environment.

**RecursionError**
→ Infinite recursion. Check base case. Add `print(locals())` to trace depth.

### Debugging Tools
```python
import pdb; pdb.set_trace()          # Interactive debugger
import traceback; traceback.print_exc() # Full traceback in except block
print(type(x), repr(x))              # Inspect a variable
```
<!-- LEVEL 3 END -->
```

---

## Frontmatter Fields

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `id` | ✅ | string | Unique identifier (kebab-case) |
| `name` | ✅ | string | Human-readable name |
| `category` | ✅ | string | Category (debugging, testing, api, db, ui, devops, security, refactoring, ai-engineering) |
| `level1` | ✅ | string | Activation trigger — shown to determine if skill applies (~50 tokens) |
| `platforms` | ❌ | list | Supported platforms (omit = all) |
| `priority` | ❌ | int 1-10 | Load priority (1=highest) |
| `keywords` | ❌ | list | Keywords for classifier matching |
| `level1_tokens` | ❌ | int | Token count of Level 1 content |
| `level2_tokens` | ❌ | int | Token count of Level 2 content |
| `level3_tokens` | ❌ | int | Token count of Level 3 content |
| `author` | ❌ | string | Skill author |
| `version` | ❌ | string | Semantic version |

---

## Level Definitions

| Level | Token Budget | Purpose | When Used |
|-------|-------------|---------|-----------|
| L1 | ~50 tokens | Activation trigger + one-line summary | Every turn (classifier check) |
| L2 | 400–600 tokens | Core instructions + quick reference | When skill is activated |
| L3 | 1500–2500 tokens | Full reference, examples, edge cases | When user escalates or requests deep help |

---

## Platform Conversion Matrix

| Platform | Format | Level Used | Hook Support |
|----------|--------|-----------|--------------|
| Claude Code | SKILL.md (native) | L1+L2+L3 | Full |
| Cursor | `.mdc` in `.cursor/rules/` | L2 | None (rules-based) |
| Codex CLI | Section in `AGENTS.md` | L1+L2 | Limited |
| Gemini CLI | `.gemini/GEMINI.md` | L2 | Limited |
| Antigravity | `.antigravity/plugins/*.yaml` | L2 | Full |
| OpenCode | `.opencode/config.json` | L2 | Limited |
| Aider | `.aider.conf.yml` conventions | L1 | None |
| Windsurf | `.windsurf/rules.md` | L2 | None |
| Kilo Code | `.kilo/plugins/*.yaml` | L2 | Partial |
| Augment | `.augment/context.md` | L2 | None |

---

## Categories

| Category | Skills | File Patterns |
|----------|--------|---------------|
| `debugging` | Language-specific debuggers | `**/*.py`, `**/*.ts`, `**/*.js` |
| `testing` | TDD workflow, jest, pytest | `**/*.test.*`, `test_*.py` |
| `api` | REST, GraphQL | `**/routes/**`, `**/api/**` |
| `db` | SQL, ORM (Prisma, SQLAlchemy) | `**/migrations/**`, `**/*.sql` |
| `ui` | React, CSS patterns | `**/*.tsx`, `**/*.jsx` |
| `devops` | Docker, K8s, CI | `**/Dockerfile`, `**/*.yml` |
| `security` | Auth, JWT, OWASP | `**/auth/**`, `**/middleware/**` |
| `refactoring` | Clean code principles | Any source file |
| `ai-engineering` | LLM prompting, agents | `**/*.py` |
