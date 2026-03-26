# AgentKit

> Intelligent orchestration layer for agentic coding.
> One install. Works everywhere. 70% cost reduction.

```
npx agentkit init
```

---

## What it is

AgentKit is the missing runtime between you and your AI coding agent. It sits between your prompts and the model and makes every session smarter, cheaper, and more disciplined — without changing how you work.

| Without AgentKit | With AgentKit |
|-----------------|---------------|
| 45,000 tokens/session | ~5,000 tokens/session (89% reduction) |
| All-Sonnet pricing (~$200/mo) | Auto-routed Haiku/Sonnet/Opus (~$60/mo) |
| Skills forgotten each session | Persistent memory graph + session handoffs |
| Jump straight to coding | Enforced Research→Plan→Execute→Review→Ship |
| Claude Code only | Claude Code + Cursor + Codex + 7 more platforms |

---

## Five Layers

### Layer 1 — Intelligent Skill Router
Classifies every prompt (< 10ms) → loads only the relevant skills → injects them at the right detail level. Token budget: 5,000/session vs the naive 45,000.

### Layer 2 — Project Memory Graph
SQLite knowledge graph that captures files, functions, API routes, and decisions across sessions. Haiku-compressed handoffs ensure context carries over.

### Layer 3 — Token Budget Intelligence
- **Auto model routing** — Haiku for simple/subagent tasks, Sonnet for standard, Opus for architecture/security
- **Thinking budget** — 0/8K/32K tokens mapped to trivial/moderate/complex tasks
- **Smart compaction** — proactive at 60% fill, not reactive at 80%
- **Cost dashboard** — real-time $/session in status bar

### Layer 4 — Workflow Engine
Enforces the Research→Plan→Execute→Review→Ship pipeline via hooks. Can't skip planning. Quality gates (syntax→lint→types→tests) run after every edit. Subagent orchestrator dispatches to Haiku/Sonnet/Opus specialists.

### Layer 5 — Universal Platform Layer
One `SKILL.md` file — 10 platforms. Auto-converts to `.mdc` (Cursor), `AGENTS.md` (Codex), `.gemini/` config, plugin YAML (Antigravity), and more.

---

## Quick Start

```bash
# Install globally
npm install -g agentkit-ai

# In any project directory
npx agentkit init

# Check status
npx agentkit status

# View cost savings
npx agentkit costs
```

### Manual install (Claude Code)

```bash
git clone https://github.com/Ajaysable123/AgentKit.git ~/.agentkit
pip3 install -r ~/.agentkit/requirements.txt
export AGENTKIT_HOME=~/.agentkit
npx agentkit init
```

---

## CLI Commands

```
npx agentkit init              Detect platforms → install hooks + skills
npx agentkit sync              Re-sync config across all detected platforms
npx agentkit status            Health check + layers + platforms + costs
npx agentkit costs [--days N]  Cost analytics (default: last 7 days)
npx agentkit skills list       List installed skills
npx agentkit skills info <id>  Show skill details
npx agentkit workflow status   Current workflow state
npx agentkit workflow approve  Approve the implementation plan
npx agentkit workflow reset    Reset workflow to IDLE
npx agentkit detect            Show detected AI coding platforms
npx agentkit bundles           List available skill bundles
```

---

## Skill Bundles

| Bundle | Skills |
|--------|--------|
| `backend-pro` | python-debugger, tdd-workflow, rest-api, sql-query, auth-jwt, clean-code, docker |
| `frontend-wizard` | js-debugger, jest-testing, react-patterns, graphql, clean-code |
| `devops-master` | docker, python-debugger, sql-query, clean-code |
| `full-stack-hero` | All 11 skills |
| `ai-engineer` | llm-prompting, python-debugger, rest-api, clean-code, tdd-workflow |

---

## Platform Support

| Platform | Tier | Skills | Hooks | Memory |
|----------|------|--------|-------|--------|
| Claude Code | Full | ✅ Native | ✅ Full | ✅ |
| Antigravity | Full | ✅ Plugin YAML | ✅ Full | ✅ Partial |
| Cursor | Partial | ✅ `.mdc` rules | ❌ | ❌ |
| Gemini CLI | Partial | ✅ System prompt | ⚠️ Limited | ❌ |
| OpenCode | Partial | ✅ Config JSON | ⚠️ Limited | ❌ |
| Windsurf | Partial | ✅ Cascade rules | ❌ | ❌ |
| Kilo Code | Partial | ✅ Plugin YAML | ⚠️ | ❌ |
| Codex CLI | Basic | ✅ `AGENTS.md` | ❌ | ❌ |
| Aider | Basic | ✅ `aider.conf.yml` | ❌ | ❌ |
| Augment | Basic | ✅ Context file | ❌ | ❌ |

---

## Architecture

```
AgentKit/
├── router/          # Skill classifier + model router + thinking budget + compaction
├── memory/          # SQLite knowledge graph + session recorder + injector + handoffs
├── workflow/        # State machine + subagent orchestrator + quality gates + worktree
├── platform/        # Base adapter + 10 platform adapters + SKILL.md spec
├── hooks/           # Claude Code hook scripts (UserPromptSubmit, PreToolUse, PostToolUse, Stop)
├── skills/          # 13 SKILL.md files across 9 categories
├── cli/             # npx agentkit CLI (Node.js + Python bridge)
└── config/          # settings.json template
```

---

## Requirements

- **Node.js** ≥ 18
- **Python** ≥ 3.9
- **Claude Code** (for full feature set) — [install here](https://claude.ai/code)

Python dependencies (auto-installed):
```
PyYAML>=6.0
anthropic>=0.40.0
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENTKIT_HOME` | `~/.agentkit` | AgentKit install directory |
| `AGENTKIT_PROJECT` | `cwd` | Project root for workflow state |
| `AGENTKIT_GATES_BLOCK` | `false` | Set `true` to make quality gates block on failure |
| `AGENTKIT_SKIP_POSTINSTALL` | — | Skip post-install setup (useful in CI) |

---

## License

MIT — see [LICENSE](LICENSE)
