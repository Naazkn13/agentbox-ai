import { useState } from "react";

const sections = [
  { id: "what", label: "The Vision" },
  { id: "gap", label: "The Gap" },
  { id: "arch", label: "Architecture" },
  { id: "roadmap", label: "Build Plan" },
  { id: "token", label: "Token Savings" },
  { id: "compete", label: "Competition" },
  { id: "viral", label: "Go Viral" },
  { id: "money", label: "Revenue" }
];

const sourceRepos = [
  { name: "Superpowers", stars: "108K", what: "Agentic skills framework + TDD workflow methodology", takes: "Workflow methodology (brainstorm → spec → plan → TDD → subagent → review → ship), skill auto-activation pattern, subagent-driven development" },
  { name: "claude-mem", stars: "39.9K", what: "Automatic session memory — captures, compresses, and injects context across sessions", takes: "Persistent project memory, AI-compressed context injection, session-to-session knowledge transfer" },
  { name: "awesome-claude-code", stars: "30.9K", what: "Curated directory of 1,234+ skills, hooks, commands, plugins", takes: "Skill categorization taxonomy, role-based bundles concept, cross-platform compatibility list" },
  { name: "ui-ux-pro-max-skill", stars: "~500", what: "Design intelligence SKILL.md for professional UI/UX", takes: "Domain-specific skill pattern, anti-AI-slop design guidelines, platform-aware rendering rules" }
];

const archLayers = [
  {
    name: "🧠 Intelligent Skill Router",
    color: "#f43f5e",
    tagline: "The biggest token saver — loads ONLY what you need, when you need it",
    components: [
      { name: "Task Classifier", desc: "Analyzes what you're doing right NOW: debugging? writing tests? designing UI? deploying? reviewing PR? — classifies in real-time from your prompt + file context." },
      { name: "Skill Selector", desc: "From your curated skill library (500+ skills), loads ONLY the 2-5 skills relevant to the current task. Not 1,234 skills dumped into context. Not even 20. Just the exact ones needed. This alone saves 15,000-50,000 tokens per session." },
      { name: "Progressive Disclosure Engine", desc: "Skills load in layers: Level 1 (trigger description, 50 tokens) → Level 2 (core instructions, 500 tokens) → Level 3 (full references/examples, 2000+ tokens). Agent only goes deeper if the task requires it." },
      { name: "Forced-Eval Hook", desc: "Borrowed from the community's discovery: skills activate 84% of the time with forced-eval vs 20% without. This hook ensures skills actually fire when they should." }
    ]
  },
  {
    name: "💾 Project Memory Graph",
    color: "#8b7cf7",
    tagline: "Claude-mem on steroids — project-level knowledge that persists forever",
    components: [
      { name: "Session Recorder", desc: "Automatically captures: architectural decisions made, APIs discovered, bugs found and fixed, patterns established, commands that worked. Uses AI compression (via Haiku — cheap) to distill sessions to ~500 tokens of high-value context." },
      { name: "Project Knowledge Graph", desc: "Not flat text files. A structured graph: entities (files, functions, APIs, packages), relationships (depends-on, calls, tested-by), and annotations (last-modified, confidence, source-session). Stored as SQLite (like the community is already doing)." },
      { name: "Smart Context Injection", desc: "Before every agent turn, injects ONLY the memory nodes relevant to the current task. Working on auth? Get auth decisions + API patterns. Working on DB? Get schema decisions + query patterns. Not everything." },
      { name: "Cross-Session Handoff", desc: "End of session: auto-generate handoff document. Start of new session: load handoff + relevant memory nodes. Zero 'where were we?' moments. This is what claude-mem does, but smarter." }
    ]
  },
  {
    name: "💰 Token Budget Intelligence",
    color: "#4ade80",
    tagline: "Automatically optimizes cost without you thinking about it",
    components: [
      { name: "Auto Model Router", desc: "Classifies task complexity on every turn. Simple file search → Haiku ($0.25/M). Standard coding → Sonnet ($3/M). Complex architecture → Opus ($15/M). Subagent tasks → always Haiku. This alone cuts 60% of costs for most developers." },
      { name: "Thinking Budget Manager", desc: "Extended thinking burns 31,999 output tokens per request by default. For simple tasks, this is wasted money. Auto-adjusts MAX_THINKING_TOKENS: 0 for trivial, 8K for moderate, 32K for complex. Saves ~70% on thinking costs." },
      { name: "Smart Compaction", desc: "Instead of waiting for context to hit 80% and doing a crude summary, proactively compacts at logical breakpoints (task completed, branch merged, test passed). Preserves high-value context, discards noise." },
      { name: "Cost Dashboard Hook", desc: "Real-time cost tracking as a status line: current session cost, cost-per-task breakdown, model used per turn, projected daily spend. No more bill shock." }
    ]
  },
  {
    name: "⚡ Workflow Engine",
    color: "#f59e0b",
    tagline: "Superpowers methodology + subagent orchestration + quality gates",
    components: [
      { name: "Methodology Enforcer", desc: "Adapted from Superpowers: Research → Plan → Execute → Review → Ship. Not suggestions — enforced via hooks. Agent can't start coding without a plan. Can't merge without tests. Can't ship without review." },
      { name: "Subagent Orchestrator", desc: "Dispatch tasks to subagents with the right skill + model combo. Writer subagent (Sonnet + coding skills) → Reviewer subagent (fresh context, Opus + security skills). Each subagent gets only the skills it needs, not your whole context." },
      { name: "Quality Gate Pipeline", desc: "After each task: auto-run linter, type checker, tests. If any fail, route back to agent with failure context. No 'it works on my machine' moments." },
      { name: "Git Worktree Manager", desc: "Auto-create worktree for each feature. Parallel development branches. Clean merges. Borrowed from Superpowers' using-git-worktrees skill." }
    ]
  },
  {
    name: "🌍 Universal Platform Layer",
    color: "#06b6d4",
    tagline: "One install, works everywhere — Claude Code, Cursor, Codex, Gemini CLI, Antigravity",
    components: [
      { name: "SKILL.md Universal Format", desc: "All skills use the open SKILL.md standard. Works natively with 11+ tools: Claude Code, Codex, Cursor, Gemini CLI, Antigravity, OpenCode, Aider, Windsurf, Kilo Code, Augment, OpenClaw." },
      { name: "Platform Adapter", desc: "Detects which platform you're using and adapts: Claude Code plugin format, Cursor plugin format, Codex agent format, Gemini extension format. One codebase, auto-converts for each platform." },
      { name: "CLI + Plugin Installer", desc: "npx agentkit init → detects platform → installs correct format → configures optimal defaults. One command setup." }
    ]
  }
];

const roadmap = [
  {
    phase: "Phase 1: Core Plugin",
    weeks: "Weeks 1-4",
    color: "#f43f5e",
    items: [
      "Skill Router: task classifier + progressive disclosure loader (the biggest token saver)",
      "Curated skill library: 50 battle-tested skills organized by role (backend, frontend, devops, full-stack)",
      "Forced-eval hook for reliable skill activation (84% vs 20%)",
      "Token cost dashboard hook (real-time $/session tracking)",
      "Auto model routing: Haiku for subagents, Sonnet default, Opus for complex reasoning",
      "MAX_THINKING_TOKENS auto-tuning based on task complexity",
      "Claude Code plugin format + Cursor plugin format",
      "npx agentkit init → one-command install"
    ]
  },
  {
    phase: "Phase 2: Memory + Workflow",
    weeks: "Weeks 5-8",
    color: "#8b7cf7",
    items: [
      "Project Memory: SQLite-backed session recorder + knowledge graph",
      "AI-compressed session handoffs (using Haiku for cheap compression)",
      "Smart context injection: only relevant memory per task",
      "Workflow enforcer: Research → Plan → Execute → Review → Ship pipeline",
      "Subagent orchestrator with skill+model routing per subtask",
      "Git worktree integration for parallel development",
      "Quality gate hooks: auto-lint, type-check, test after each task",
      "GitHub launch with demo video + comprehensive README"
    ]
  },
  {
    phase: "Phase 3: Ecosystem + Cross-Platform",
    weeks: "Weeks 9-14",
    color: "#4ade80",
    items: [
      "Codex CLI, Gemini CLI, Antigravity, OpenCode support via platform adapter",
      "Skill marketplace: community contributes skills, rated by effectiveness",
      "Role bundles: 'Backend Pro', 'Frontend Wizard', 'DevOps Master', 'Full-Stack Hero'",
      "Team sharing: export your AgentKit config, share with teammates",
      "Analytics dashboard: which skills save the most tokens, which tasks cost most",
      "Integration with Linear, GitHub Issues for task injection",
      "Smart compaction: proactive at logical breakpoints vs crude auto-compact"
    ]
  },
  {
    phase: "Phase 4: Intelligence + Monetize",
    weeks: "Weeks 15-24",
    color: "#f59e0b",
    items: [
      "Learning system: AgentKit improves skill routing based on YOUR usage patterns",
      "Team analytics: which developers are most cost-efficient, which skills help most",
      "Custom skill creator wizard: 'describe what you need' → auto-generates SKILL.md",
      "Cloud sync: memory + config synced across machines",
      "Enterprise features: RBAC, SSO, audit trails, spend limits per developer",
      "AgentKit Pro (managed cloud version) launch",
      "Partner program: skill creators get revenue share from Pro bundles"
    ]
  }
];

const tokenSavings = [
  { technique: "Skill Router (on-demand loading)", baseline: "~45,000 tokens/session (all skills loaded)", optimized: "~5,000 tokens/session (2-5 relevant skills)", saving: "~40,000 tokens = 89% reduction", source: "ClaudeFast reports 82% improvement with progressive disclosure" },
  { technique: "Auto Model Routing", baseline: "$15/M output tokens (Opus for everything)", optimized: "$0.25-3/M (Haiku/Sonnet for 80% of tasks)", saving: "~60-75% cost reduction", source: "Sonnet handles 80% of coding tasks well" },
  { technique: "Thinking Budget Tuning", baseline: "31,999 thinking tokens per request", optimized: "0-8K for simple tasks, 32K only for complex", saving: "~70% on thinking costs", source: "Anthropic docs: lower budget for simpler tasks" },
  { technique: "Smart Memory Injection", baseline: "~10,000 tokens (full CLAUDE.md + all context)", optimized: "~2,000 tokens (relevant memory nodes only)", saving: "~8,000 tokens per session", source: "Keep CLAUDE.md under 500 lines → move rest to skills" },
  { technique: "Proactive Compaction", baseline: "Context bloat until auto-compact at 80%", optimized: "Compact at logical breakpoints, preserve high-value", saving: "~30% fewer wasted context tokens", source: "Community best practice: /clear between unrelated tasks" },
  { technique: "Subagent Model Routing", baseline: "Subagents use main model (Opus/Sonnet)", optimized: "CLAUDE_CODE_SUBAGENT_MODEL=haiku", saving: "~90% per subagent task", source: "everything-claude-code token optimization docs" }
];

const competitors = [
  { name: "Superpowers", stars: "108K", threat: "HIGH", position: "Workflow methodology + skills framework", yourEdge: "Superpowers is methodology-only. No memory, no token optimization, no model routing, no cross-platform. You ADD intelligence on top." },
  { name: "claude-mem", stars: "39.9K", threat: "MEDIUM", position: "Session memory persistence", yourEdge: "claude-mem is memory-only. No skills, no workflow, no token optimization. You subsume its functionality into a larger system." },
  { name: "ClaudeFast Code Kit", stars: "~5K", threat: "MEDIUM", position: "20+ skills with progressive disclosure", yourEdge: "Commercial product ($), limited skill count. You're open-source with 500+ skills + memory + token optimization." },
  { name: "everything-claude-code", stars: "~3K", threat: "LOW", position: "Skills + instincts + memory + security", yourEdge: "Good comprehensive attempt but documentation-heavy, not a one-command install. You focus on UX + intelligence." },
  { name: "token-optimizer-mcp", stars: "~1K", threat: "LOW", position: "Token optimization MCP server", yourEdge: "Token optimization only. You include it as one layer of a full system." },
  { name: "Anthropic Official Plugins", stars: "N/A", threat: "HIGH", position: "101 official plugins, expanding fast", yourEdge: "Official plugins are individual tools. You're the orchestration layer that makes them work together intelligently." }
];

const viralPlaybook = [
  { channel: "Hacker News", timing: "Day 1", strategy: "Show HN: 'AgentKit — One install that cuts Claude Code costs by 70% and makes your agent actually remember things'. HN loves: open-source, token savings (money!), developer productivity. Be in comments immediately with benchmarks.", impact: "500-2K stars in 24hrs" },
  { channel: "Claude Code Discord", timing: "Day 1", strategy: "Post in #skills and #plugins channels. This is THE most targeted audience — 50K+ developers actively using Claude Code. Show a before/after cost comparison.", impact: "200-500 stars, core early adopters" },
  { channel: "r/ClaudeAI + r/ChatGPTCoding", timing: "Day 1-2", strategy: "Post: 'I was spending $200/mo on Claude Code. Built an open-source toolkit that cut it to $60/mo. Here's how.' Real numbers get attention.", impact: "300-800 stars" },
  { channel: "Twitter/X Thread", timing: "Day 2", strategy: "'🧵 I analyzed 4 repos with 180K+ combined stars and built the tool they should've been: [GIF demo showing: install → auto-skill-loading → memory injection → cost dashboard]. One install. Works on Claude Code, Cursor, Codex, Antigravity.'", impact: "Viral potential — 100-5K+ RTs" },
  { channel: "DEV.to Technical Deep-Dive", timing: "Day 2-3", strategy: "'How I built a skill router that saves 40K tokens per Claude Code session'. Include architecture diagrams, token math, real benchmarks. Dev community loves deep technical content with real numbers.", impact: "300-1K stars + contributor interest" },
  { channel: "YouTube (Indian Tech)", timing: "Week 2", strategy: "Reach out to Hitesh Choudhary, Piyush Garg, Harkirat Singh. Pitch: 'Indian developer builds tool that saves Claude Code users $140/month'. Every Claude Code user is a potential viewer.", impact: "1K-5K stars from one video" },
  { channel: "Product Hunt", timing: "Week 2", strategy: "Launch as 'The Swiss Army Knife for AI-Assisted Coding'. Target badges: #1 Developer Tool, Featured. Get 10+ early reviews from Discord community.", impact: "500-2K stars + mainstream visibility" },
  { channel: "Superpowers Community", timing: "Week 1", strategy: "Don't compete — complement. Post: 'AgentKit works WITH Superpowers. It adds memory + token optimization + model routing on top of Superpowers' methodology.' Jesse Vincent's community (Discord 5K+) becomes your ally, not competitor.", impact: "Trust + 200-500 stars from power users" }
];

const revenue = [
  { period: "Month 1-3", stars: "500-3K", users: "200-1K", mrr: "$0", focus: "Open-source launch, community building, iterate on feedback" },
  { period: "Month 4-6", stars: "3K-10K", users: "1K-5K", mrr: "$1K-5K", focus: "AgentKit Pro waitlist: cloud sync, team analytics, premium skill bundles" },
  { period: "Month 7-12", stars: "10K-30K", users: "5K-20K", mrr: "$5K-25K", focus: "Pro launch ($9/mo individual, $29/mo team), enterprise pilots" },
  { period: "Year 2", stars: "30K-60K+", users: "20K-100K", mrr: "$25K-100K", focus: "Enterprise ($99/seat/mo), skill marketplace revenue share, potential acquisition interest" }
];

export default function AgentKitDeepDive() {
  const [active, setActive] = useState("what");
  const [expandedArch, setExpandedArch] = useState(0);
  const [activePhase, setActivePhase] = useState(0);
  const [expandedComp, setExpandedComp] = useState(null);

  return (
    <div style={{ fontFamily: "'Literata', 'Source Serif Pro', Georgia, serif", background: "#05070e", color: "#c8c3b8", minHeight: "100vh" }}>
      {/* Header */}
      <div style={{ background: "linear-gradient(155deg, #05070e 0%, #0f0825 35%, #081818 100%)", borderBottom: "1px solid rgba(255,255,255,0.04)", padding: "36px 20px 28px" }}>
        <div style={{ maxWidth: 780, margin: "0 auto" }}>
          <div style={{ fontFamily: "'Space Mono', 'Fira Code', monospace", fontSize: 10, letterSpacing: 4, color: "#06b6d4", textTransform: "uppercase", marginBottom: 14 }}>Deep Dive — The Developer Power Tool</div>
          <h1 style={{ fontSize: 28, fontWeight: 400, lineHeight: 1.25, margin: "0 0 10px", color: "#f0ede6" }}>AgentKit</h1>
          <p style={{ fontSize: 16, color: "#6b6578", lineHeight: 1.5, margin: "0 0 20px", fontStyle: "italic" }}>
            The intelligent orchestration layer for agentic coding.
            <br/>One install. Smart skills. Persistent memory. Token optimization. Works everywhere.
          </p>
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", fontSize: 11, fontFamily: "'Space Mono', monospace" }}>
            <span style={{ color: "#f43f5e" }}>🧠 Smart skill loading</span>
            <span style={{ color: "#8b7cf7" }}>💾 Project memory</span>
            <span style={{ color: "#4ade80" }}>💰 70% cost reduction</span>
            <span style={{ color: "#f59e0b" }}>⚡ Enforced workflows</span>
            <span style={{ color: "#06b6d4" }}>🌍 11+ platforms</span>
          </div>
        </div>
      </div>

      <div style={{ maxWidth: 780, margin: "0 auto", padding: "24px 20px" }}>
        {/* Nav */}
        <div style={{ display: "flex", gap: 4, marginBottom: 28, flexWrap: "wrap", borderBottom: "1px solid rgba(255,255,255,0.05)", paddingBottom: 14 }}>
          {sections.map(s => (
            <button key={s.id} onClick={() => setActive(s.id)} style={{
              padding: "7px 12px", borderRadius: 6, border: "none",
              background: active === s.id ? "rgba(6,182,212,0.1)" : "transparent",
              color: active === s.id ? "#06b6d4" : "#4a4557", fontSize: 11,
              fontFamily: "'Space Mono', monospace", cursor: "pointer", transition: "all 0.15s"
            }}>{s.label}</button>
          ))}
        </div>

        {/* THE VISION */}
        {active === "what" && (
          <div>
            <h2 style={{ fontSize: 20, color: "#f0ede6", fontWeight: 400, marginBottom: 20 }}>The Vision: What You're Actually Building</h2>
            <div style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(6,182,212,0.1)", borderRadius: 10, padding: "24px", marginBottom: 24, lineHeight: 1.85, fontSize: 14.5 }}>
              <p style={{ margin: "0 0 16px" }}>
                <strong style={{ color: "#06b6d4" }}>AgentKit is the "runtime" that sits between developers and their coding agents.</strong> It's not another skill pack. It's not another awesome-list. It's the intelligent layer that makes all those skills, memories, and workflows actually work together — while cutting your token costs by 70%.
              </p>
              <p style={{ margin: "0 0 16px" }}>
                Think of it as: <strong style={{ color: "#fff" }}>Superpowers (workflow) + claude-mem (memory) + awesome-claude-code (skills) + token-optimizer (cost) + ui-ux-pro-max (domain skills)</strong> — consolidated into one plugin that installs with a single command, auto-configures for your platform, and gets smarter as you use it.
              </p>
              <p style={{ margin: 0 }}>
                It works on <strong style={{ color: "#4ade80" }}>Claude Code, Cursor, Codex, Gemini CLI, Antigravity, OpenCode, Aider, Windsurf</strong> — because it uses the universal SKILL.md format with platform-specific adapters. Install once, works everywhere.
              </p>
            </div>

            <h3 style={{ fontSize: 14, color: "#f59e0b", fontFamily: "'Space Mono', monospace", fontWeight: 500, marginBottom: 14 }}>What you're consolidating from each repo</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {sourceRepos.map((r, i) => (
                <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)", borderRadius: 8, padding: "14px 18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6, flexWrap: "wrap", gap: 4 }}>
                    <span style={{ fontSize: 14, color: "#f0ede6", fontWeight: 600 }}>{r.name}</span>
                    <span style={{ fontSize: 11, fontFamily: "'Space Mono', monospace", color: "#f59e0b" }}>⭐ {r.stars}</span>
                  </div>
                  <div style={{ fontSize: 12, color: "#7a7585", marginBottom: 6 }}>{r.what}</div>
                  <div style={{ fontSize: 12, color: "#06b6d4", fontFamily: "'Space Mono', monospace" }}>→ You take: {r.takes}</div>
                </div>
              ))}
            </div>

            <div style={{ background: "rgba(244,63,94,0.06)", border: "1px solid rgba(244,63,94,0.1)", borderRadius: 10, padding: "18px 20px", marginTop: 20, fontSize: 13, color: "#d4a0a8", lineHeight: 1.7 }}>
              <strong style={{ color: "#f43f5e" }}>Critical positioning:</strong> You're NOT competing with Superpowers. You're COMPLEMENTING it. AgentKit works WITH Superpowers and adds the layers it doesn't have (memory, token optimization, model routing, cross-platform). This makes Jesse Vincent's 108K-star community your ally, not your enemy.
            </div>
          </div>
        )}

        {/* THE GAP */}
        {active === "gap" && (
          <div>
            <h2 style={{ fontSize: 20, color: "#f0ede6", fontWeight: 400, marginBottom: 20 }}>The Gap Nobody Has Filled</h2>
            {[
              { pain: "Fragmented tooling", detail: "To use Claude Code effectively, developers install 5-10 separate plugins, configure env vars manually, browse awesome-lists to find skills, and still don't know if things are working. One senior ML engineer wrote: 'I spent weeks digging through official docs until it clicked. Skills. Subagents. Plugins. MCP. Hooks. Suddenly Claude Code wasn't just an LLM I talked to.'", data: "The official marketplace has 101 plugins. Community marketplaces have 1,367+ skills. SkillsMP indexes 500,000+ skills. Nobody curates or orchestrates them." },
              { pain: "Token waste is the #1 complaint", detail: "Average Claude Code cost: $100-200/developer/month. Agent teams use 7x tokens. Extended thinking burns 32K output tokens by default. Skills loaded into CLAUDE.md add tokens to EVERY prompt even when irrelevant. Most developers don't know about /effort, model routing, or thinking budgets.", data: "Progressive disclosure saves 82% vs loading everything. Haiku subagents cost 1/15th of Opus. Smart thinking budgets save 70%. Combined potential: 60-70% cost reduction." },
              { pain: "No persistent project memory", detail: "Claude forgets everything between sessions. Developers re-explain architecture, re-discover APIs, re-establish conventions. One developer tracks 2,555 sessions with 70K messages and 19M tokens in SQLite — all context that Claude can't access next session.", data: "claude-mem (39.9K stars) proves the demand is massive. But it's memory-only — no skills, no workflow, no optimization." },
              { pain: "Skills don't activate reliably", detail: "Community discovered skills only fire 20% of the time without forced-eval hooks. Most developers don't know this. They install skills, they don't work, they give up and dump everything into CLAUDE.md.", data: "Forced-eval hook increases activation to 84%. This is a known fix that most skill packs don't include." },
              { pain: "Platform lock-in", detail: "Developers switch between Claude Code, Cursor, Codex, Antigravity depending on the task. Their skills and configs don't transfer. They rebuild their setup for each platform.", data: "Skills now use the universal SKILL.md format across 11+ platforms. But no tool auto-converts or manages this." }
            ].map((item, i) => (
              <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)", borderRadius: 8, padding: "16px 18px", marginBottom: 10 }}>
                <div style={{ fontSize: 15, color: "#f43f5e", fontWeight: 600, marginBottom: 6 }}>{item.pain}</div>
                <div style={{ fontSize: 13, color: "#8a8598", lineHeight: 1.7, marginBottom: 8 }}>{item.detail}</div>
                <div style={{ fontSize: 11, fontFamily: "'Space Mono', monospace", color: "#4ade80", background: "rgba(74,222,128,0.05)", padding: "8px 12px", borderRadius: 6 }}>{item.data}</div>
              </div>
            ))}
          </div>
        )}

        {/* ARCHITECTURE */}
        {active === "arch" && (
          <div>
            <h2 style={{ fontSize: 20, color: "#f0ede6", fontWeight: 400, marginBottom: 20 }}>System Architecture — 5 Layers</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {archLayers.map((layer, li) => (
                <div key={li} style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${layer.color}12`, borderRadius: 10, overflow: "hidden" }}>
                  <button onClick={() => setExpandedArch(expandedArch === li ? -1 : li)} style={{
                    width: "100%", display: "flex", justifyContent: "space-between", alignItems: "flex-start",
                    padding: "16px 20px", background: "none", border: "none", color: "#f0ede6",
                    fontSize: 15, cursor: "pointer", fontFamily: "inherit", textAlign: "left"
                  }}>
                    <div>
                      <div>{layer.name}</div>
                      <div style={{ fontSize: 11, color: layer.color, fontFamily: "'Space Mono', monospace", marginTop: 4 }}>{layer.tagline}</div>
                    </div>
                    <span style={{ color: layer.color, transform: expandedArch === li ? "rotate(45deg)" : "none", transition: "transform 0.2s", fontSize: 18, flexShrink: 0, marginLeft: 12 }}>+</span>
                  </button>
                  {expandedArch === li && (
                    <div style={{ padding: "0 20px 16px" }}>
                      {layer.components.map((c, ci) => (
                        <div key={ci} style={{ borderLeft: `2px solid ${layer.color}30`, paddingLeft: 14, marginBottom: 12 }}>
                          <div style={{ fontSize: 13, color: layer.color, fontFamily: "'Space Mono', monospace", fontWeight: 600, marginBottom: 4 }}>{c.name}</div>
                          <div style={{ fontSize: 12.5, color: "#7a7585", lineHeight: 1.7 }}>{c.desc}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div style={{ background: "rgba(6,182,212,0.06)", border: "1px solid rgba(6,182,212,0.12)", borderRadius: 10, padding: "18px 20px", marginTop: 16, fontSize: 13, color: "#8abfc8", lineHeight: 1.7 }}>
              <strong style={{ color: "#06b6d4" }}>Your skills coverage:</strong> Claude Code plugin development ✅ SKILL.md format ✅ Hooks system ✅ Shell scripting ✅ Python for tooling ✅ React (for future dashboard) ✅ SQLite ✅ LLM orchestration (LiteLLM) ✅. The entire thing is buildable with shell scripts + Python + YAML configs. No exotic dependencies.
            </div>
          </div>
        )}

        {/* BUILD PLAN */}
        {active === "roadmap" && (
          <div>
            <h2 style={{ fontSize: 20, color: "#f0ede6", fontWeight: 400, marginBottom: 20 }}>24-Week Build Plan</h2>
            <div style={{ display: "flex", gap: 6, marginBottom: 16, flexWrap: "wrap" }}>
              {roadmap.map((p, i) => (
                <button key={i} onClick={() => setActivePhase(i)} style={{
                  padding: "6px 12px", borderRadius: 6, fontSize: 11,
                  fontFamily: "'Space Mono', monospace", cursor: "pointer",
                  border: activePhase === i ? `1px solid ${p.color}` : "1px solid rgba(255,255,255,0.06)",
                  background: activePhase === i ? `${p.color}15` : "transparent",
                  color: activePhase === i ? p.color : "#4a4557"
                }}>{p.phase}</button>
              ))}
            </div>
            <div style={{ background: "rgba(255,255,255,0.02)", border: `1px solid ${roadmap[activePhase].color}15`, borderRadius: 10, padding: "20px 22px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16, flexWrap: "wrap", gap: 8 }}>
                <h3 style={{ fontSize: 17, color: "#f0ede6", margin: 0, fontWeight: 400 }}>{roadmap[activePhase].phase}</h3>
                <span style={{ fontSize: 11, fontFamily: "'Space Mono', monospace", color: roadmap[activePhase].color }}>{roadmap[activePhase].weeks}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {roadmap[activePhase].items.map((item, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, alignItems: "flex-start", fontSize: 13, color: "#9994a8", lineHeight: 1.6 }}>
                    <span style={{ color: roadmap[activePhase].color, fontFamily: "'Space Mono', monospace", fontSize: 11, flexShrink: 0, marginTop: 2 }}>{String(i + 1).padStart(2, '0')}</span>
                    <span>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TOKEN SAVINGS */}
        {active === "token" && (
          <div>
            <h2 style={{ fontSize: 20, color: "#f0ede6", fontWeight: 400, marginBottom: 20 }}>Token Savings Breakdown — The Math</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {tokenSavings.map((t, i) => (
                <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(74,222,128,0.08)", borderRadius: 8, padding: "16px 18px" }}>
                  <div style={{ fontSize: 14, color: "#f0ede6", fontWeight: 600, marginBottom: 8 }}>{t.technique}</div>
                  <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 8, fontSize: 12 }}>
                    <div><span style={{ color: "#f43f5e", fontFamily: "'Space Mono', monospace", fontSize: 10 }}>BEFORE</span><br/><span style={{ color: "#8a8598" }}>{t.baseline}</span></div>
                    <div><span style={{ color: "#4ade80", fontFamily: "'Space Mono', monospace", fontSize: 10 }}>AFTER</span><br/><span style={{ color: "#8fba9a" }}>{t.optimized}</span></div>
                    <div><span style={{ color: "#f59e0b", fontFamily: "'Space Mono', monospace", fontSize: 10 }}>SAVING</span><br/><span style={{ color: "#f59e0b", fontWeight: 600 }}>{t.saving}</span></div>
                  </div>
                  <div style={{ fontSize: 10, fontFamily: "'Space Mono', monospace", color: "#4a4557" }}>Source: {t.source}</div>
                </div>
              ))}
            </div>
            <div style={{ background: "rgba(74,222,128,0.06)", border: "1px solid rgba(74,222,128,0.15)", borderRadius: 10, padding: "18px 20px", marginTop: 16, fontSize: 14, color: "#8fba9a", lineHeight: 1.7, textAlign: "center" }}>
              <strong style={{ color: "#4ade80", fontSize: 20 }}>Combined: $200/mo → ~$60/mo per developer</strong>
              <br/>
              <span style={{ fontSize: 12, color: "#5a7565" }}>At 20K users, that's $2.8M/year in collective savings your community can point to.</span>
            </div>
          </div>
        )}

        {/* COMPETITION */}
        {active === "compete" && (
          <div>
            <h2 style={{ fontSize: 20, color: "#f0ede6", fontWeight: 400, marginBottom: 20 }}>Competitive Positioning</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {competitors.map((c, i) => (
                <div key={i} onClick={() => setExpandedComp(expandedComp === i ? null : i)} style={{
                  background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)", borderRadius: 8, padding: "14px 18px", cursor: "pointer"
                }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: 6 }}>
                    <div>
                      <span style={{ fontSize: 14, color: "#f0ede6", fontWeight: 600 }}>{c.name}</span>
                      <span style={{ fontSize: 10, fontFamily: "'Space Mono', monospace", color: "#f59e0b", marginLeft: 8 }}>⭐ {c.stars}</span>
                    </div>
                    <span style={{ fontSize: 10, fontFamily: "'Space Mono', monospace", color: c.threat === "HIGH" ? "#f43f5e" : c.threat === "MEDIUM" ? "#f59e0b" : "#4ade80", padding: "2px 8px", background: c.threat === "HIGH" ? "rgba(244,63,94,0.1)" : c.threat === "MEDIUM" ? "rgba(245,158,11,0.1)" : "rgba(74,222,128,0.1)", borderRadius: 4 }}>{c.threat} threat</span>
                  </div>
                  <div style={{ fontSize: 12, color: "#5a5565", marginTop: 4 }}>{c.position}</div>
                  {expandedComp === i && (
                    <div style={{ marginTop: 10, fontSize: 12.5, color: "#06b6d4", lineHeight: 1.7, background: "rgba(6,182,212,0.05)", padding: "10px 14px", borderRadius: 6 }}>
                      <strong>Your edge:</strong> {c.yourEdge}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* VIRAL */}
        {active === "viral" && (
          <div>
            <h2 style={{ fontSize: 20, color: "#f0ede6", fontWeight: 400, marginBottom: 20 }}>Go-To-Market — The Viral Playbook</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {viralPlaybook.map((v, i) => (
                <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)", borderRadius: 8, padding: "16px 18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6, flexWrap: "wrap", gap: 6 }}>
                    <span style={{ fontSize: 14, fontWeight: 600, color: "#f0ede6" }}>{v.channel}</span>
                    <div style={{ display: "flex", gap: 8 }}>
                      <span style={{ fontSize: 10, fontFamily: "'Space Mono', monospace", color: "#f59e0b" }}>{v.timing}</span>
                      <span style={{ fontSize: 10, fontFamily: "'Space Mono', monospace", color: "#4ade80" }}>{v.impact}</span>
                    </div>
                  </div>
                  <div style={{ fontSize: 12.5, color: "#7a7585", lineHeight: 1.7 }}>{v.strategy}</div>
                </div>
              ))}
            </div>
            <div style={{ background: "rgba(6,182,212,0.06)", border: "1px solid rgba(6,182,212,0.1)", borderRadius: 10, padding: "18px 20px", marginTop: 16, fontSize: 13, color: "#8abfc8", lineHeight: 1.7 }}>
              <strong style={{ color: "#06b6d4" }}>The money headline:</strong> "This open-source tool cuts Claude Code costs by 70%." That's the line that goes viral. Every Claude Code user is paying $100-200/month. You're offering to save them $140/month. The ROI story writes itself.
            </div>
          </div>
        )}

        {/* REVENUE */}
        {active === "money" && (
          <div>
            <h2 style={{ fontSize: 20, color: "#f0ede6", fontWeight: 400, marginBottom: 20 }}>Revenue Model</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 24 }}>
              {[
                { tier: "Community (Free Forever)", desc: "Full plugin: skill router, memory, token optimization, 50 curated skills, all platforms. Self-hosted. MIT license.", target: "Individual developers, hobbyists, evaluation" },
                { tier: "Pro ($9/mo)", desc: "Cloud sync (memory + config across machines), 500+ skill library, advanced analytics, priority skill bundles by role, custom skill creator wizard.", target: "Professional developers, freelancers" },
                { tier: "Team ($29/seat/mo)", desc: "Everything in Pro + team config sharing, developer cost analytics, shared memory across team, Slack notifications, admin dashboard.", target: "Engineering teams of 5-50" },
                { tier: "Enterprise ($99/seat/mo)", desc: "Everything in Team + SSO/RBAC, audit trails, spend limits per developer, on-prem memory storage, custom skill development, dedicated support.", target: "Companies with 50+ developers using Claude Code" }
              ].map((t, i) => (
                <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)", borderRadius: 8, padding: "16px 18px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, flexWrap: "wrap", gap: 4 }}>
                    <span style={{ fontSize: 14, color: "#f0ede6", fontWeight: 600 }}>{t.tier}</span>
                    <span style={{ fontSize: 10, fontFamily: "'Space Mono', monospace", color: "#4ade80" }}>{t.target}</span>
                  </div>
                  <div style={{ fontSize: 12.5, color: "#7a7585", lineHeight: 1.7 }}>{t.desc}</div>
                </div>
              ))}
            </div>
            <h3 style={{ fontSize: 14, color: "#4ade80", fontFamily: "'Space Mono', monospace", fontWeight: 500, marginBottom: 12 }}>Revenue Projection</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {revenue.map((r, i) => (
                <div key={i} style={{ background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.04)", borderRadius: 8, padding: "12px 16px", display: "grid", gridTemplateColumns: "90px 80px 80px 90px 1fr", gap: 8, alignItems: "center", fontSize: 12 }}>
                  <span style={{ color: "#f0ede6", fontWeight: 600 }}>{r.period}</span>
                  <span style={{ fontFamily: "'Space Mono', monospace", color: "#f59e0b" }}>{r.stars}⭐</span>
                  <span style={{ fontFamily: "'Space Mono', monospace", color: "#8b7cf7" }}>{r.users}</span>
                  <span style={{ fontFamily: "'Space Mono', monospace", color: "#4ade80", fontWeight: 700 }}>{r.mrr}</span>
                  <span style={{ color: "#5a5565" }}>{r.focus}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Verdict */}
        <div style={{ marginTop: 40, background: "linear-gradient(135deg, rgba(6,182,212,0.08), rgba(139,124,247,0.06))", border: "1px solid rgba(6,182,212,0.12)", borderRadius: 12, padding: "28px 24px" }}>
          <div style={{ fontSize: 18, color: "#f0ede6", marginBottom: 10, textAlign: "center" }}>The Honest Verdict</div>
          <div style={{ fontSize: 13, color: "#8a8598", lineHeight: 1.85, maxWidth: 600, margin: "0 auto" }}>
            <p style={{ margin: "0 0 14px" }}>
              <strong style={{ color: "#f43f5e" }}>Risk:</strong> Anthropic is rapidly improving Claude Code's built-in features. They just launched deferred tool search (85% token reduction), official plugins marketplace (101 plugins), and skills auto-activation. Some of what you build could get absorbed into the platform.
            </p>
            <p style={{ margin: "0 0 14px" }}>
              <strong style={{ color: "#4ade80" }}>Mitigation:</strong> Be the orchestration layer, not the feature. Anthropic builds primitives (skills, hooks, plugins). You build the intelligence that makes them work together. Just like n8n didn't get killed by individual API integrations — it became the glue layer. That's your position.
            </p>
            <p style={{ margin: 0 }}>
              <strong style={{ color: "#06b6d4" }}>My recommendation:</strong> This is your best product idea of the three. It sits at the exact intersection of your skills (agentic AI, LangChain orchestration, production systems) and the hottest market in dev tools right now. The "save 70% on Claude Code costs" headline alone will drive viral adoption. Ship Phase 1 in 4 weeks, launch on HN + Claude Code Discord, and iterate fast.
            </p>
          </div>
        </div>

        <div style={{ textAlign: "center", padding: "32px 0", fontSize: 10, color: "#1a1825", fontFamily: "'Space Mono', monospace" }}>
          AgentKit Blueprint v1.0 — March 26, 2026
        </div>
      </div>
    </div>
  );
}
