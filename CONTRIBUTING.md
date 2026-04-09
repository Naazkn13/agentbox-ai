# Contributing to AgentKit

First off — thank you for taking the time to contribute. AgentKit is an open-source project and every contribution, from a typo fix to a new platform adapter, makes it better for the entire community.

---

## Philosophy

AgentKit's goal is simple: make AI coding agents cheaper, smarter, and more reliable — without locking anyone into a specific model or platform. Contributions that advance that goal are always welcome. Contributions that add complexity without clear benefit are not.

**We value:**
- Code that works over code that's clever
- Simplicity over abstraction
- Real-world tested over theoretically correct

---

## Contribution Priorities

When deciding what to work on, here's what has the most impact (ranked):

| Priority | Type | Why |
|----------|------|-----|
| 🔴 1 | **Bug fixes** | Broken things block everyone |
| 🟠 2 | **New platform adapters** | Broader reach, more users |
| 🟡 3 | **New skills** | Direct value for existing users |
| 🟢 4 | **Performance improvements** | Token reduction = cost savings |
| 🔵 5 | **New features** | Must solve a real problem |
| ⚪ 6 | **Documentation** | Always needed, always welcome |

If you're unsure what to work on, check [open issues](https://github.com/Ajaysable123/AgentKit/issues) tagged `good first issue`.

---

## What You Can Contribute

### Skills
A skill is a markdown file (`SKILL.md`) that teaches the AI agent domain-specific knowledge. Skills are the highest-leverage contribution — each one immediately helps every user on every platform.

→ See [How to Add a Skill](#how-to-add-a-skill)

### Platform Adapters
AgentKit currently supports 10 platforms. Adding a new one means every existing skill instantly works on it.

→ See [How to Add a Platform Adapter](#how-to-add-a-platform-adapter)

### Bug Fixes
Found something broken? Fix it and open a PR. Small focused PRs merge faster than large ones.

### Documentation
Improved explanations, better examples, clearer guides — all welcome.

---

## Architecture Overview

AgentKit is a 5-layer runtime:

```
Layer 1 — Skill Router       router/classifier.py → router/selector.py → router/disclosure.py
Layer 2 — Memory Graph       memory/graph.py → memory/injector.py → memory/recorder.py
Layer 3 — Token Budget       router/model_router.py → router/thinking_budget.py
Layer 4 — Workflow Engine    workflow/enforcer.py → workflow/quality_gates.py
Layer 5 — Platform Layer     platform/adapter.py → platform/adapters/*.py
```

Every user prompt flows through: **classify → select skills → inject context → enforce workflow → run quality gates**.

The key design principle: **skills are platform-agnostic**. You write one `SKILL.md` and all 10 platform adapters convert it automatically.

---

## Project Structure

```
AgentKit/
├── router/
│   ├── classifier.py        # 3-tier prompt classifier (keyword → heuristic → LLM)
│   ├── selector.py          # Token-budget-aware skill selector
│   ├── disclosure.py        # Progressive L1/L2/L3 content extraction
│   ├── marketplace.py       # External skill search + install
│   └── models.py            # Shared dataclasses
│
├── skills/
│   ├── registry.yaml        # Master skill registry (id, category, keywords, paths)
│   ├── debugging/           # Skill .md files by category
│   ├── testing/
│   ├── api/
│   └── ...                  # One folder per category
│
├── platform/
│   ├── adapter.py           # PlatformAdapter base class + registry
│   ├── spec.md              # SKILL.md format specification
│   └── adapters/
│       ├── claude_code.py   # Tier 1 — hooks + native SKILL.md
│       ├── cursor.py        # Tier 2 — .mdc rules
│       ├── gemini_cli.py    # Tier 2 — GEMINI.md
│       └── ...
│
├── hooks/
│   ├── skill_router_hook.py # UserPromptSubmit → classify + inject skills
│   ├── plan_gate.sh         # PreToolUse → block edits without approved plan
│   ├── quality_gates.sh     # PostToolUse → lint/types/tests after every edit
│   └── ...
│
├── workflow/
│   ├── enforcer.py          # State machine: IDLE→RESEARCH→PLAN→EXECUTE→REVIEW→SHIP
│   └── quality_gates.py     # Per-language gate pipeline
│
├── memory/
│   ├── graph.py             # SQLite knowledge graph
│   ├── injector.py          # Relevance-scored context injection
│   └── recorder.py          # Session entity extraction
│
└── cli/
    ├── index.js             # `npx agentkit` entry point
    └── install.js           # Platform-aware installer
```

---

## Development Setup

```bash
# 1. Clone the repo
git clone https://github.com/Ajaysable123/AgentKit.git
cd AgentKit

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Node dependencies (CLI only)
npm install

# 4. Verify everything works
python3 -c "from router.classifier import classify; print(classify('fix this bug'))"
node cli/index.js --help
```

**Requirements:** Python ≥ 3.9 · Node.js ≥ 18

Optional: Set `ANTHROPIC_API_KEY` to enable the Haiku LLM fallback in the classifier (Tier 3). Without it, the classifier uses keyword + heuristic matching only (Tier 1 + 2).

---

## How to Add a Skill

Skills live in `skills/<category>/<skill-id>.md`. Each file follows the SKILL.md format with three progressive disclosure levels.

### Step 1 — Create the skill file

```bash
# Pick a category that matches your skill
# Categories: debugging, testing, api, db, ui, devops, security, refactoring, ai-engineering, data, mobile, quality, utilities
mkdir -p skills/your-category
touch skills/your-category/your-skill.md
```

### Step 2 — Write the SKILL.md

```markdown
---
id: your-skill
name: Your Skill Name
category: your-category
priority: 2
platforms: [claude-code, cursor, codex, gemini-cli, opencode, aider, windsurf]
keywords: [keyword1, keyword2, keyword3]
effectiveness: 0.85
bundles: []
---

## Level 1 — Core Rules (always injected, ~50 tokens)

1. Rule one — the most important thing
2. Rule two
3. Rule three (max 7 rules)

## Level 2 — Patterns & Examples (~400–600 tokens)

[More detailed guidance, common patterns, examples]

## Level 3 — Reference (~1500–2500 tokens)

[Full reference, edge cases, anti-patterns, troubleshooting]
```

**Frontmatter fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `id` | ✅ | Unique slug, lowercase, hyphens |
| `name` | ✅ | Human-readable name |
| `category` | ✅ | Must match a folder in `skills/` |
| `priority` | ✅ | 1=core (always load), 2=supplemental, 3=reference |
| `platforms` | ✅ | List of supported platform IDs |
| `keywords` | ✅ | Trigger words for the classifier to select this skill |
| `effectiveness` | ✅ | 0.0–1.0, your honest estimate |
| `bundles` | ✅ | Role bundles: `backend-pro`, `frontend-wizard`, `full-stack-hero`, etc. |

### Step 3 — Register in registry.yaml

Add an entry to `skills/registry.yaml`:

```yaml
  - id: your-skill
    name: Your Skill Name
    category: your-category
    priority: 2
    path: skills/your-category/your-skill.md
    level1_tokens: 50
    level2_tokens: 500
    level3_tokens: 2000
    platforms: [claude-code, cursor, codex, gemini-cli, opencode, aider, windsurf]
    keywords: [keyword1, keyword2, keyword3]
    effectiveness: 0.85
    bundles: []
```

### Step 4 — Test

```bash
# Test the classifier picks up your skill
python3 -c "
from router.classifier import classify
from router.registry import SkillRegistry
from router.selector import select_skills

result = classify('your trigger phrase here')
reg = SkillRegistry()
skills = select_skills(result, reg=reg)
print([s.meta.id for s in skills])
"
```

---

## How to Add a Platform Adapter

Platform adapters live in `platform/adapters/`. Each one converts a `SKILL.md` into the format the target platform understands.

### Step 1 — Create the adapter file

```python
# platform/adapters/your_platform.py
from platform.adapter import PlatformAdapter, AdapterResult, Skill, AgentKitConfig, register

@register("your-platform")
class YourPlatformAdapter(PlatformAdapter):
    tier = 2  # 1=Full, 2=Partial, 3=Basic

    def detect(self) -> bool:
        """Return True if this platform is installed/configured."""
        return Path(".yourplatform").exists()

    def convert_skill(self, skill: Skill) -> str:
        """Convert a Skill object to your platform's format."""
        return f"# {skill.name}\n\n{skill.content_l2}"

    def install(self, skills: list[Skill], config: AgentKitConfig) -> AdapterResult:
        """Write converted skills to the platform's expected location."""
        result = AdapterResult()
        for skill in skills:
            content = self.convert_skill(skill)
            dest = Path(f".yourplatform/skills/{skill.id}.md")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content)
            result.files_written.append(str(dest))
        return result

    def uninstall(self) -> AdapterResult:
        """Remove all AgentKit files from this platform."""
        result = AdapterResult()
        # ... remove files
        return result
```

### Step 2 — Register in the detector

Add your platform's detection logic to `cli/detect-platform.js`:

```javascript
{ id: "your-platform", name: "Your Platform", markers: [".yourplatform/"] }
```

### Step 3 — Test

```bash
python3 -c "
from platform.adapter import load_adapters, get_adapter
load_adapters()
adapter = get_adapter('your-platform')
print(adapter.detect())
"
```

---

## Code Style

**Python:** Follow PEP 8. We use `ruff` for linting.
```bash
ruff check router/ platform/ memory/ workflow/
```

**JavaScript:** Standard Node.js style, no framework required.

**YAML:** 2-space indent, consistent quoting. Run `python3 -c "import yaml; yaml.safe_load(open('skills/registry.yaml'))"` to validate.

**Markdown:** Skill files use ATX headings (`##`), no trailing spaces.

---

## PR Process

### Branch naming
```
fix/short-description          # bug fixes
feat/short-description         # new features or skills
skill/skill-name               # new skills
adapter/platform-name          # new platform adapters
docs/what-you-changed          # documentation only
```

### Commit format (Conventional Commits)
```
fix: describe what was broken and how you fixed it
feat: describe what you added
skill: add <skill-name> skill for <category>
adapter: add <platform-name> platform adapter
docs: what you documented
chore: version bump, dependency update
```

### What reviewers check
- [ ] Does the classifier correctly trigger the new skill?
- [ ] Is the skill content accurate and concise?
- [ ] Are L1 rules genuinely the most important (≤7)?
- [ ] Does registry.yaml have the correct token counts?
- [ ] Do existing tests still pass?
- [ ] Is the PR focused on one thing?

### Testing before opening a PR
```bash
# Run classifier tests
python3 -m pytest tests/ -v

# Verify skill loads correctly
python3 -c "from router.registry import SkillRegistry; reg = SkillRegistry(); print(reg.get_skill('your-skill-id'))"

# Check the full pipeline
python3 -c "
from router.classifier import classify
from router.registry import SkillRegistry
from router.selector import select_skills
from router.disclosure import run_router
r = SkillRegistry()
c = classify('your trigger phrase')
s = select_skills(c, reg=r)
out = run_router(c, s, reg=r)
print(out.injected_content[:500])
"
```

---

## Issue Reporting

### Bug report
Please include:
1. **What you did** — exact command or prompt
2. **What you expected** — what should have happened
3. **What happened** — exact error or wrong output
4. **Environment** — OS, Python version, Node version, Claude Code version

### Feature request
Please include:
1. **The problem** — what can't you do today?
2. **Your proposed solution** — how would it work?
3. **Alternatives considered** — what else did you think about?

---

## Questions?

Open a [GitHub Discussion](https://github.com/Ajaysable123/AgentKit/discussions) or tag `@Ajaysable123` in an issue.

---

<div align="center">

Built with care for the open-source AI coding community.

[GitHub](https://github.com/Ajaysable123/AgentKit) · [npm](https://www.npmjs.com/package/agentkit-ai) · [MIT License](LICENSE)

</div>
