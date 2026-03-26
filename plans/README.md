# AgentKit — Build Plans Index

The intelligent orchestration layer for agentic coding.
**Stack:** Shell scripts + Python + YAML + SQLite. No exotic dependencies.

---

## Phase Plans

| File | Phase | Timeline | Focus |
|------|-------|----------|-------|
| [phase-1-core-plugin.md](phase-1-core-plugin.md) | Core Plugin | Weeks 1-4 | Skill router, model routing, cost dashboard, npx install |
| [phase-2-memory-workflow.md](phase-2-memory-workflow.md) | Memory + Workflow | Weeks 5-8 | SQLite memory graph, workflow enforcer, subagent orchestrator, GitHub launch |
| [phase-3-ecosystem-crossplatform.md](phase-3-ecosystem-crossplatform.md) | Ecosystem + Cross-Platform | Weeks 9-14 | Multi-platform adapters, skill marketplace, role bundles, analytics |
| [phase-4-intelligence-monetize.md](phase-4-intelligence-monetize.md) | Intelligence + Monetize | Weeks 15-24 | Learning system, AgentKit Pro cloud, enterprise features |

---

## Architecture Layer Plans

| File | Layer | Color | Key Benefit |
|------|-------|-------|-------------|
| [arch-layer-1-skill-router.md](arch-layer-1-skill-router.md) | Intelligent Skill Router | Red | Saves 40K tokens/session — loads only 2-5 relevant skills |
| [arch-layer-2-memory-graph.md](arch-layer-2-memory-graph.md) | Project Memory Graph | Purple | Persistent cross-session project knowledge via SQLite |
| [arch-layer-3-token-budget.md](arch-layer-3-token-budget.md) | Token Budget Intelligence | Green | Auto model routing + thinking budget = 70% cost cut |
| [arch-layer-4-workflow-engine.md](arch-layer-4-workflow-engine.md) | Workflow Engine | Amber | Enforced methodology + subagent orchestration + quality gates |
| [arch-layer-5-universal-platform.md](arch-layer-5-universal-platform.md) | Universal Platform Layer | Cyan | One SKILL.md format → 11+ platforms via auto-adapters |

---

## Key Numbers to Hit

- Token reduction: **89%** via skill router (45K → 5K tokens/session)
- Cost reduction: **70%** combined ($200/mo → $60/mo)
- Skill activation rate: **84%** with forced-eval hook (vs 20% without)
- Platforms supported: **11+** via SKILL.md universal format
- Install: **one command** — `npx agentkit init`

---

## Tech Stack

```
agentkit/
├── router/          # Skill router (Python)
├── memory/          # SQLite memory graph (Python)
├── hooks/           # Claude Code hooks (Shell + Python)
├── skills/          # Curated skill library (SKILL.md files)
├── workflow/        # Workflow enforcer (Shell + YAML)
├── platform/        # Platform adapters (Python)
└── cli/             # npx agentkit CLI (Node.js)
```

---

## Positioning

- NOT competing with Superpowers (108K stars) — complementing it
- NOT competing with claude-mem (39.9K stars) — subsuming + improving it
- Viral headline: **"Cuts Claude Code costs by 70%"**
