# Phase 3: Ecosystem + Cross-Platform
**Timeline:** Weeks 9–14
**Goal:** Expand to 11+ platforms via SKILL.md adapters, launch skill marketplace, ship role bundles, enable team sharing, and add analytics dashboard.

---

## Deliverables Checklist

- [ ] Platform adapters: Codex CLI, Gemini CLI, Antigravity, OpenCode
- [ ] Skill marketplace: community skill submissions + quality rating
- [ ] Role bundles: Backend Pro, Frontend Wizard, DevOps Master, Full-Stack Hero, AI Engineer
- [ ] Team config sharing: export/import AgentKit setups
- [ ] Analytics dashboard: which skills save the most, which tasks cost most
- [ ] Linear + GitHub Issues integration for task injection
- [ ] Smart compaction at logical breakpoints

---

## Week 9–10: Universal Platform Layer

### 9.1 SKILL.md Universal Format
**File:** `platform/spec.md`

SKILL.md is the open standard that works across all 11+ platforms. AgentKit is the first tool to auto-convert between platform-specific formats.

**Supported platforms:**

| Platform | Format | Config File | Hook System |
|----------|--------|-------------|-------------|
| Claude Code | SKILL.md native | `.claude/settings.json` | Yes (full) |
| Cursor | `.mdc` rules | `.cursor/rules/*.mdc` | Limited |
| Codex CLI | `AGENTS.md` | `AGENTS.md` | Via commands |
| Gemini CLI | Markdown prompts | `.gemini/config.yaml` | Via extensions |
| Antigravity | Plugin YAML | `.antigravity/plugins/` | Yes |
| OpenCode | System prompts | `.opencode/config.json` | Limited |
| Aider | `aider.conf.yml` | `.aider.conf.yml` | Via scripts |
| Windsurf | Cascade rules | `.windsurf/rules.md` | Limited |
| Kilo Code | Plugin format | `.kilo/plugins/` | Yes |
| Augment | Context files | `.augment/context/` | Limited |
| OpenClaw | Agent config | `.openclaw/config.yaml` | Yes |

### 9.2 Platform Adapter
**File:** `platform/adapter.py`

Reads a universal SKILL.md → outputs platform-specific format.

**Adapter architecture:**

```python
# platform/adapter.py

from abc import ABC, abstractmethod

class PlatformAdapter(ABC):
    @abstractmethod
    def convert_skill(self, skill_md: str, metadata: dict) -> str:
        """Convert SKILL.md content to platform-specific format."""
        pass

    @abstractmethod
    def install_hooks(self, agentkit_config: dict) -> None:
        """Install AgentKit hooks in platform-specific way."""
        pass

    @abstractmethod
    def detect(self) -> bool:
        """Detect if this platform is installed."""
        pass


class ClaudeCodeAdapter(PlatformAdapter):
    def convert_skill(self, skill_md: str, metadata: dict) -> str:
        # Claude Code uses SKILL.md natively — minimal conversion
        return skill_md

    def install_hooks(self, config: dict) -> None:
        # Write to .claude/settings.json
        settings = self._load_settings()
        settings["hooks"] = self._merge_hooks(settings.get("hooks", {}), config["hooks"])
        self._save_settings(settings)


class CursorAdapter(PlatformAdapter):
    def convert_skill(self, skill_md: str, metadata: dict) -> str:
        # Convert SKILL.md to .mdc format for Cursor rules
        skill_id = metadata["id"]
        return f"""---
description: {metadata['level1']}
globs: {metadata.get('globs', '')}
alwaysApply: false
---

{self._extract_level2(skill_md)}
"""

    def install_hooks(self, config: dict) -> None:
        # Cursor has limited hook support — use .cursor/rules for enforcement
        os.makedirs(".cursor/rules", exist_ok=True)
        with open(".cursor/rules/agentkit.mdc", "w") as f:
            f.write(self._generate_cursor_rules(config))


class CodexAdapter(PlatformAdapter):
    def convert_skill(self, skill_md: str, metadata: dict) -> str:
        # Codex uses AGENTS.md format
        return f"""# {metadata['name']}
{metadata['level1']}

## Instructions
{self._extract_level2(skill_md)}
"""

    def install_hooks(self, config: dict) -> None:
        # Append to AGENTS.md
        with open("AGENTS.md", "a") as f:
            f.write(self._generate_agents_section(config))


class GeminiCLIAdapter(PlatformAdapter):
    def convert_skill(self, skill_md: str, metadata: dict) -> str:
        # Gemini CLI uses markdown system prompts
        return f"""## Skill: {metadata['name']}
**Activate when:** {metadata['level1']}

{self._extract_level2(skill_md)}
"""
```

### 9.3 Multi-Platform Installer Update
**File:** `cli/install.js` (updated)

```
$ npx agentkit init

✓ Detecting platforms...
  Claude Code detected ✓
  Cursor detected ✓
  Codex CLI not found

Install for: [Claude Code] [Cursor] [Both]
> Both

✓ Installing for Claude Code...    SKILL.md format, full hooks
✓ Installing for Cursor...         .mdc rules, limited hooks
✓ Syncing skill library...         50 skills converted for each platform

Your AgentKit config works across Claude Code and Cursor.
Skills stay in sync. Memory is shared.
```

---

## Week 10–11: Skill Marketplace

### 10.1 Marketplace Architecture

Community can submit skills. Skills are rated by effectiveness (token savings + task completion rate).

**Submission format:**
```yaml
# skill-submission.yaml
skill_id: "nextjs-app-router"
author: "github:username"
name: "Next.js App Router Expert"
category: "frontend"
description: "Expert patterns for Next.js 14+ App Router, RSC, and streaming"
level1: "For Next.js App Router, React Server Components, and streaming patterns"
platforms: [claude-code, cursor, codex, gemini-cli]
tested_on:
  - platform: claude-code
    version: "1.x"
    activation_rate: 0.87
    task_completion_improvement: 0.23
```

**Marketplace index** (`skills/marketplace/index.yaml`):
```yaml
skills:
  - id: nextjs-app-router
    author: github:username
    downloads: 1240
    rating: 4.8
    effectiveness_score: 0.87   # activation rate
    token_delta: -2300           # avg token savings vs baseline
    category: frontend
    verified: true               # manually reviewed
    last_updated: 2026-03-01
```

### 10.2 Quality Rating System

Skills are automatically scored on:

| Metric | Weight | How Measured |
|--------|--------|--------------|
| Activation rate | 40% | % of times skill fires when task matches |
| Task completion rate | 30% | % of tasks completed without re-prompting |
| Token efficiency | 20% | Tokens saved vs not having the skill |
| User ratings | 10% | Manual 1-5 star ratings |

**Effectiveness score formula:**
```
score = (activation_rate × 0.4) + (completion_rate × 0.3) + (token_efficiency × 0.2) + (user_rating/5 × 0.1)
```

### 10.3 CLI Marketplace Commands
```
$ npx agentkit marketplace search "nextjs"
Found 3 skills:
  nextjs-app-router    ⭐ 4.8  📥 1240  💰 -2300 tok/session  [install]
  nextjs-testing       ⭐ 4.2  📥 890   💰 -1800 tok/session  [install]
  nextjs-deployment    ⭐ 3.9  📥 340   💰 -900 tok/session   [install]

$ npx agentkit marketplace install nextjs-app-router
$ npx agentkit marketplace submit my-skill.md
$ npx agentkit marketplace rate nextjs-app-router 5
```

---

## Week 11–12: Role Bundles

### 11.1 Bundle Definitions
**File:** `skills/bundles/bundles.yaml`

```yaml
bundles:
  - id: backend-pro
    name: "Backend Pro"
    description: "Everything a senior backend engineer needs"
    skills:
      - debugging-python
      - debugging-node
      - testing-tdd
      - api-rest
      - api-graphql
      - db-sql
      - db-migrations
      - auth-jwt
      - docker-compose
      - code-review
    install_command: "npx agentkit bundle install backend-pro"
    token_profile:
      avg_loaded_per_session: 3
      avg_tokens: 4200

  - id: frontend-wizard
    name: "Frontend Wizard"
    skills:
      - ui-ux-pro-max
      - react-patterns
      - nextjs-app-router
      - css-responsive
      - accessibility
      - performance-web
      - testing-jest
      - state-management
      - design-system
      - animations

  - id: devops-master
    name: "DevOps Master"
    skills:
      - docker-compose
      - kubernetes
      - ci-cd-github-actions
      - monitoring-grafana
      - logging-structured
      - terraform
      - security-hardening
      - performance-tuning
      - git-workflow
      - incident-response

  - id: ai-engineer
    name: "AI Engineer"
    skills:
      - llm-prompting
      - agent-patterns
      - rag-implementation
      - evals-framework
      - token-optimization
      - mcp-tools
      - embeddings
      - fine-tuning
      - ai-testing
      - deployment-ml
```

### 11.2 Bundle Installer
```
$ npx agentkit bundle install backend-pro

Installing Backend Pro bundle (10 skills)...
✓ debugging-python      (50 tok L1, 480 tok L2)
✓ testing-tdd          (52 tok L1, 510 tok L2)
✓ api-rest             (48 tok L1, 490 tok L2)
[...]

Bundle installed. Your skill router will load 2-3 of these per task.
Estimated token usage: ~3,500/session (vs loading all 10: ~5,000/session)
```

---

## Week 12–13: Team Sharing + Analytics

### 12.1 Team Config Sharing
**File:** `cli/share.js`

Export your entire AgentKit setup as a shareable config.

**Export format** (`.agentkit-team.yaml`):
```yaml
agentkit_version: "0.2.0"
team_config:
  name: "Acme Engineering"
  bundles:
    - backend-pro
    - ai-engineer
  custom_skills:
    - id: acme-api-patterns
      path: skills/custom/acme-api-patterns.md
  model_routing:
    default: sonnet
    subagents: haiku
    complex_threshold: 0.8
  workflow:
    enforce_planning: true
    quality_gates: [lint, typecheck, tests]
    methodology: research-plan-execute-review-ship
  memory:
    auto_compress: true
    handoff_tokens: 500
    injection_budget: 2000
```

**Share commands:**
```
$ npx agentkit config export > .agentkit-team.yaml
$ npx agentkit config import .agentkit-team.yaml

# Share via GitHub (just commit .agentkit-team.yaml to your repo)
# Teammates run: npx agentkit config import
# AgentKit auto-detects .agentkit-team.yaml in repo root
```

### 12.2 Analytics Dashboard
**File:** `dashboard/analytics.py`

Which skills save the most tokens? Which tasks cost the most? Which model choices were wrong?

**Tracked per session:**
```json
{
  "session_id": "sess_20260326_001",
  "duration_minutes": 47,
  "total_cost": 0.83,
  "model_breakdown": {
    "haiku": {"turns": 12, "cost": 0.08},
    "sonnet": {"turns": 31, "cost": 0.71},
    "opus": {"turns": 2, "cost": 0.04}
  },
  "skills_used": [
    {"id": "debugging-python", "activations": 8, "tokens_saved": 3200},
    {"id": "testing-tdd", "activations": 5, "tokens_saved": 2100}
  ],
  "tasks_completed": 4,
  "quality_gate_catches": 3
}
```

**Dashboard output:**
```
$ npx agentkit analytics

📊 AgentKit Analytics (Last 30 days)

💰 Cost Summary
  Total spent:     $24.30
  Without AgentKit: ~$81.00 (estimated)
  Savings:         $56.70 (70%)

🧠 Top Skills by Token Savings
  1. debugging-python    → saved 28,400 tok ($8.52)
  2. testing-tdd         → saved 19,200 tok ($5.76)
  3. api-rest            → saved 14,800 tok ($4.44)

💸 Most Expensive Tasks
  1. "Refactor auth system"  → $4.20 (Opus, 12 turns)
  2. "Debug memory leak"     → $2.80 (Sonnet, 18 turns)

📈 Model Routing Accuracy
  Haiku used correctly:  94% of simple tasks
  Sonnet used correctly: 87% of standard tasks
  Opus escalations:      8 (all justified)
```

---

## Week 13–14: Linear + GitHub Issues Integration

### 13.1 Task Injection
**File:** `integrations/github.py`, `integrations/linear.py`

Pull task context from issue trackers directly into the agent session.

**GitHub Issues:**
```bash
$ npx agentkit task load github:Ajaysable123/AgentKit#42

Loading issue #42: "Add OAuth2 support"
  Labels: enhancement, auth
  Assignee: you
  Description: [full issue body]

Injecting into session context...
  Task: Implement OAuth2 with Google provider
  Acceptance criteria: [from issue]
  Related files: [auto-detected from issue mentions]

AgentKit will track this task in memory and link commits to it.
```

**Linear:**
```bash
$ npx agentkit task load linear:PROJ-123

Loading LINEAR-123: "Performance: optimize DB queries"
  Priority: P1
  Estimate: 3 points
  Context: [description + comments]

Injecting into session...
```

---

## Smart Compaction (Upgrade from Phase 1)

### Phase 1 compaction: crude (wait for 80% context, then summary)
### Phase 3 compaction: proactive at logical breakpoints

**Compaction triggers:**
- Task completed (quality gates all pass)
- Branch merged
- Test suite passes
- User types `/compact` manually
- Detected context at 60% (proactive, not reactive)

**What to keep vs discard:**
```
KEEP:
  - All decisions captured in memory graph
  - Current plan + remaining steps
  - Files being actively modified
  - Recent error messages + their fixes
  - Current task context

DISCARD:
  - File contents already saved to memory
  - Successful command outputs (captured in memory)
  - Old conversation turns about completed subtasks
  - Duplicated context (same file read multiple times)
```

---

## File Structure After Phase 3

```
agentkit/
├── [Phase 1 + 2 files...]
├── platform/
│   ├── adapter.py            # base adapter class
│   ├── adapters/
│   │   ├── claude_code.py
│   │   ├── cursor.py
│   │   ├── codex.py
│   │   ├── gemini_cli.py
│   │   ├── antigravity.py
│   │   └── opencode.py
│   └── spec.md               # SKILL.md universal format spec
├── skills/
│   ├── [Phase 1 skills...]
│   ├── bundles/
│   │   └── bundles.yaml
│   └── marketplace/
│       ├── index.yaml
│       └── submissions/
├── dashboard/
│   └── analytics.py
├── integrations/
│   ├── github.py
│   └── linear.py
└── cli/
    ├── [Phase 1 CLI...]
    ├── share.js              # team config export/import
    ├── marketplace.js        # marketplace commands
    └── analytics.js          # analytics commands
```

---

## Success Metrics for Phase 3

| Metric | Target |
|--------|--------|
| Platforms supported | 8+ (Claude Code, Cursor, Codex, Gemini, Antigravity, OpenCode, Aider, Windsurf) |
| Skills in marketplace | 200+ community skills |
| Role bundles shipped | 5 (Backend, Frontend, DevOps, Full-Stack, AI Engineer) |
| GitHub stars | 5,000+ |
| Analytics adoption | 60%+ of users check dashboard weekly |
| Team configs shared | 100+ public team configs |
