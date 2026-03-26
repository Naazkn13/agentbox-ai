# Architecture: Layer 5 — Universal Platform Layer
**Color:** Cyan (`#06b6d4`)
**Tagline:** One install, works everywhere — Claude Code, Cursor, Codex, Gemini CLI, Antigravity
**Platform Coverage:** 11+ platforms via SKILL.md universal format + platform adapters

---

## The Problem It Solves

Developers switch between AI coding tools constantly — Claude Code for complex tasks, Cursor for quick edits, Codex for scripting. Every switch means:
- Skills don't transfer (Claude Code `.md` files don't work in Cursor)
- Config doesn't transfer (model routing, hooks are platform-specific)
- Memory doesn't transfer (completely isolated)
- They rebuild their skill setup for EVERY platform

The SKILL.md universal format solves skills. AgentKit's platform adapter solves everything else. One install, one config — works everywhere.

---

## Component 1: SKILL.md Universal Format

**Purpose:** One skill file format that works natively across 11+ AI coding platforms.

**The format:**
```markdown
---
# Required fields
id: debugging-python
name: Python Debugger
category: debugging
level1: "For Python errors, exceptions, and tracebacks"
platforms: [claude-code, cursor, codex, gemini-cli, antigravity, opencode, aider, windsurf]

# Optional but recommended
priority: 1
keywords: [python, traceback, exception, AttributeError, TypeError, bug]
level1_tokens: 45
level2_tokens: 480
level3_tokens: 2100
author: agentkit-team
version: 1.0.0
---

<!-- LEVEL 1: Universal activation trigger (50 tokens) -->
## Python Debugger
Activate for: Python errors, exceptions, assertion failures, stack traces.

<!-- LEVEL 2: Core instructions (400-600 tokens) -->
## Core Instructions
1. Read the full traceback top-to-bottom before touching any code.
2. Identify root cause (not symptoms) — check variable state at the error.
...

<!-- LEVEL 3: Full reference (1500-2500 tokens) -->
## Reference
### Common Python Error Patterns
AttributeError: ...
KeyError: ...
```

**Why this format works across platforms:**
- Claude Code: reads SKILL.md natively — zero conversion needed
- Cursor: extracts Level 2 content → `.mdc` file (Cursor rules format)
- Codex: extracts Level 1 + Level 2 → appends to `AGENTS.md`
- Gemini CLI: extracts Level 2 → system prompt extension
- Antigravity: wraps in plugin YAML
- Aider: extracts as convention in `aider.conf.yml`

---

## Component 2: Platform Adapter

**Purpose:** Reads universal SKILL.md files → outputs the exact format each platform expects.

**Supported platforms and their formats:**

### Claude Code (Native)
```
Format: SKILL.md (no conversion)
Config: .claude/settings.json
Hooks: Full hook system (PreToolUse, PostToolUse, UserPromptSubmit, Stop)
Memory: .claude/memory/ (via AgentKit memory layer)
Install: Copy SKILL.md files + write hooks to settings.json
```

### Cursor
```
Format: .mdc files in .cursor/rules/
Config: .cursorrules or .cursor/rules/*.mdc
Hooks: Limited (no event hooks, but rules enforce via instructions)
Memory: Manual injection via system prompt rules
Install: Convert SKILL.md Level 2 → .mdc format
```

```python
# platform/adapters/cursor.py

class CursorAdapter(PlatformAdapter):
    def convert_skill(self, skill: Skill) -> str:
        return f"""---
description: {skill.level1}
globs: {self._get_globs(skill.category)}
alwaysApply: false
---

# {skill.name}

{self._extract_level2(skill.content)}
"""

    def _get_globs(self, category: str) -> str:
        # Map category to file globs Cursor should activate rule for
        CATEGORY_GLOBS = {
            "debugging":    "**/*.py,**/*.ts,**/*.js",
            "testing":      "**/*.test.*,**/*.spec.*",
            "designing-ui": "**/*.tsx,**/*.jsx,**/*.css",
            "db-work":      "**/migrations/**,**/*.sql,**/schema.*",
            "api-work":     "**/routes/**,**/api/**,**/endpoints/**",
        }
        return CATEGORY_GLOBS.get(category, "**/*")

    def install(self, skills: list[Skill], config: AgentKitConfig) -> None:
        os.makedirs(".cursor/rules", exist_ok=True)

        for skill in skills:
            mdc_content = self.convert_skill(skill)
            mdc_path = f".cursor/rules/agentkit-{skill.id}.mdc"
            with open(mdc_path, "w") as f:
                f.write(mdc_content)

        # Write AgentKit model routing as a global rule
        self._write_model_routing_rule(config)
```

### Codex CLI
```
Format: AGENTS.md (single file, appended sections)
Config: AGENTS.md in project root
Hooks: Via AGENTS.md instructions (command-based)
Memory: Injected into AGENTS.md context section
Install: Append skill sections to AGENTS.md
```

```python
# platform/adapters/codex.py

class CodexAdapter(PlatformAdapter):
    def install(self, skills: list[Skill], config: AgentKitConfig) -> None:
        agents_md = self._load_or_create_agents_md()

        # Add AgentKit section
        agentkit_section = "## AgentKit Skills\n\n"
        for skill in skills:
            agentkit_section += f"### {skill.name}\n"
            agentkit_section += f"Activate when: {skill.level1}\n\n"
            agentkit_section += f"{self._extract_level2(skill.content)}\n\n"

        # Add memory context section (placeholder, updated by memory layer)
        agentkit_section += "## Project Memory\n"
        agentkit_section += "<!-- AGENTKIT_MEMORY_INJECT -->\n\n"

        self._write_agents_md(agents_md + agentkit_section)
```

### Gemini CLI
```
Format: Markdown system prompt extensions
Config: .gemini/config.yaml
Hooks: Via .gemini/extensions/ (limited)
Memory: System prompt injection
Install: Write to .gemini/ directory
```

```python
# platform/adapters/gemini_cli.py

class GeminiCLIAdapter(PlatformAdapter):
    def install(self, skills: list[Skill], config: AgentKitConfig) -> None:
        os.makedirs(".gemini", exist_ok=True)

        # Build system prompt extension
        system_prompt = "## AgentKit — Skill Instructions\n\n"
        for skill in skills:
            system_prompt += f"**{skill.name}** (activate when: {skill.level1})\n"
            system_prompt += f"{self._extract_level2(skill.content)}\n\n"

        # Write to Gemini config
        gemini_config = {
            "system_prompt_extension": system_prompt,
            "model": config.model_routing.default,
        }

        with open(".gemini/config.yaml", "w") as f:
            yaml.dump(gemini_config, f)
```

### Antigravity
```
Format: Plugin YAML with prompt + tools
Config: .antigravity/plugins/*.yaml
Hooks: Full plugin system
Memory: Via plugin context
Install: Convert to Antigravity plugin format
```

```python
# platform/adapters/antigravity.py

class AntigravityAdapter(PlatformAdapter):
    def convert_skill(self, skill: Skill) -> dict:
        return {
            "name": f"agentkit-{skill.id}",
            "description": skill.level1,
            "trigger": {"keywords": skill.keywords},
            "prompt": self._extract_level2(skill.content),
            "priority": skill.priority,
        }

    def install(self, skills: list[Skill], config: AgentKitConfig) -> None:
        os.makedirs(".antigravity/plugins", exist_ok=True)

        for skill in skills:
            plugin = self.convert_skill(skill)
            path = f".antigravity/plugins/agentkit-{skill.id}.yaml"
            with open(path, "w") as f:
                yaml.dump(plugin, f)
```

### OpenCode
```
Format: System prompt JSON config
Config: .opencode/config.json
Hooks: Limited
Install: Append to system prompt config
```

### Aider
```
Format: Convention rules in aider.conf.yml
Config: .aider.conf.yml
Hooks: Via aider conventions system
Install: Append skill rules to .aider.conf.yml
```

### Windsurf
```
Format: Cascade rules (.windsurf/rules.md)
Config: .windsurf/rules.md
Hooks: Limited
Install: Write to .windsurf/rules.md
```

---

## Component 3: CLI + Plugin Installer

**Purpose:** `npx agentkit init` — detects platform → installs correct format → configures optimal defaults.

**Detection logic:**
```javascript
// cli/detect-platform.js

function detectPlatforms() {
  const platforms = [];
  const home = process.env.HOME;
  const cwd = process.cwd();

  const checks = [
    {
      id: "claude-code",
      name: "Claude Code",
      checks: [
        () => fs.existsSync(path.join(home, ".claude")),
        () => fs.existsSync(path.join(cwd, ".claude")),
        () => which.sync("claude", { nothrow: true }),
      ]
    },
    {
      id: "cursor",
      name: "Cursor",
      checks: [
        () => fs.existsSync(path.join(home, ".cursor")),
        () => fs.existsSync(path.join(cwd, ".cursor")),
        () => fs.existsSync(path.join(cwd, ".cursorrules")),
        () => which.sync("cursor", { nothrow: true }),
      ]
    },
    {
      id: "codex",
      name: "Codex CLI",
      checks: [
        () => process.env.OPENAI_API_KEY,
        () => which.sync("codex", { nothrow: true }),
        () => fs.existsSync(path.join(cwd, "AGENTS.md")),
      ]
    },
    {
      id: "gemini-cli",
      name: "Gemini CLI",
      checks: [
        () => process.env.GEMINI_API_KEY,
        () => which.sync("gemini", { nothrow: true }),
        () => fs.existsSync(path.join(cwd, ".gemini")),
      ]
    },
    {
      id: "antigravity",
      name: "Antigravity",
      checks: [
        () => which.sync("antigravity", { nothrow: true }),
        () => fs.existsSync(path.join(cwd, ".antigravity")),
      ]
    },
    {
      id: "aider",
      name: "Aider",
      checks: [
        () => which.sync("aider", { nothrow: true }),
        () => fs.existsSync(path.join(cwd, ".aider.conf.yml")),
      ]
    },
  ];

  for (const platform of checks) {
    if (platform.checks.some(check => { try { return check(); } catch { return false; } })) {
      platforms.push(platform);
    }
  }

  return platforms;
}
```

**Install flow (full):**
```
$ npx agentkit init

AgentKit Installer v0.1.0
─────────────────────────

Detecting platforms...
  ✓ Claude Code (primary)
  ✓ Cursor (secondary)
  ○ Codex CLI (not found)
  ○ Gemini CLI (not found)

Install for:
  [x] Claude Code — full hooks + SKILL.md native
  [x] Cursor     — .mdc rules + limited hooks
  [ ] All detected

Selecting skill library...
  Which role bundle? (or 'custom' to pick manually)
  > [1] Backend Pro  [2] Frontend Wizard  [3] DevOps Master
  > [4] Full-Stack Hero  [5] AI Engineer  [6] Custom
  Selection: 1

Installing Backend Pro bundle...
  ✓ 10 skills downloaded
  ✓ Skills converted for Claude Code (SKILL.md native)
  ✓ Skills converted for Cursor (.mdc format, .cursor/rules/)

Configuring hooks...
  ✓ Forced-eval hook    → .claude/settings.json (PreToolUse)
  ✓ Skill router hook   → .claude/settings.json (UserPromptSubmit)
  ✓ Cost dashboard hook → .claude/settings.json (statusCommand)
  ✓ Quality gates hook  → .claude/settings.json (PostToolUse)
  ✓ Memory hooks        → .claude/settings.json (PostToolUse, Stop)

Configuring model routing...
  ✓ Auto model routing enabled (Haiku/Sonnet/Opus)
  ✓ Subagent model: claude-haiku-4-5 (always)
  ✓ Thinking budget: auto-tuning enabled

Creating config...
  ✓ .agentkit.yaml created
  ✓ .agentkit/ directory initialized (gitignored)

──────────────────────────────────────────────────
✓ AgentKit installed successfully!

  Claude Code: full install (skills + hooks + memory)
  Cursor:      partial install (skills via .mdc rules)

  Estimated savings:
    Tokens:  ~40,000/session (89% reduction)
    Cost:    ~70% reduction ($200/mo → $60/mo)

  Run: npx agentkit status   → view real-time stats
  Run: npx agentkit skills   → manage skill library
  Run: npx agentkit costs    → view cost analytics
──────────────────────────────────────────────────
```

---

## Sync Across Platforms

When a developer uses both Claude Code and Cursor in the same project:
- Skills are kept in sync (source of truth: `skills/` directory)
- If a new skill is added via `npx agentkit skill install X`, it's immediately converted for all installed platforms
- Memory is Claude Code-only (other platforms don't have memory support)
- Config changes in `.agentkit.yaml` propagate to all platforms on next `npx agentkit sync`

**Sync command:**
```bash
$ npx agentkit sync

Syncing AgentKit config across platforms...
  Claude Code: up to date
  Cursor: 2 skills updated (.cursor/rules/ refreshed)
  Codex: not installed

All platforms synced.
```

---

## Platform Compatibility Matrix

| Feature | Claude Code | Cursor | Codex | Gemini CLI | Antigravity | Aider |
|---------|-------------|--------|-------|------------|-------------|-------|
| Skill loading | ✅ Full | ✅ Via .mdc | ✅ Via AGENTS.md | ✅ Via system prompt | ✅ Full | ✅ Via conf |
| Progressive disclosure | ✅ Full | ❌ Static | ❌ Static | ❌ Static | ✅ Partial | ❌ Static |
| Memory injection | ✅ Full | ⚠️ Manual | ⚠️ Manual | ⚠️ Manual | ✅ Partial | ❌ |
| Hooks (events) | ✅ Full | ❌ | ❌ | ⚠️ Limited | ✅ Full | ❌ |
| Model routing | ✅ Full | ⚠️ Partial | ❌ | ⚠️ Partial | ✅ Full | ❌ |
| Cost dashboard | ✅ Status bar | ❌ | ❌ | ❌ | ⚠️ | ❌ |
| Workflow engine | ✅ Full | ⚠️ Partial | ❌ | ❌ | ✅ Partial | ❌ |
| Quality gates | ✅ Full | ⚠️ Via rules | ❌ | ❌ | ✅ Full | ❌ |

**Tier classification:**
```
Tier 1 (Full):    Claude Code, Antigravity, OpenCode
Tier 2 (Partial): Cursor, Gemini CLI, Kilo Code, Windsurf
Tier 3 (Basic):   Codex, Aider, Augment (skills only)
```

---

## Files Owned by This Layer

```
platform/
├── adapter.py              # Base adapter class + adapter registry
├── adapters/
│   ├── claude_code.py      # Full implementation (native SKILL.md)
│   ├── cursor.py           # .mdc format conversion
│   ├── codex.py            # AGENTS.md format
│   ├── gemini_cli.py       # .gemini/ config
│   ├── antigravity.py      # Plugin YAML format
│   ├── opencode.py         # .opencode/ config
│   ├── aider.py            # aider.conf.yml format
│   ├── windsurf.py         # .windsurf/rules.md
│   ├── kilo_code.py        # .kilo/ plugins
│   ├── augment.py          # .augment/ context
│   └── openclaw.py         # .openclaw/ config
└── spec.md                 # SKILL.md universal format specification

cli/
├── index.js                # npx agentkit entry point
├── detect-platform.js      # Multi-platform detection
├── install.js              # Platform-aware installer
├── sync.js                 # Sync config across platforms
├── status.js               # Status + health check
├── skills.js               # Skill management commands
├── costs.js                # Cost analytics commands
├── marketplace.js          # Marketplace commands (Phase 3)
└── share.js                # Team config sharing (Phase 3)
```
