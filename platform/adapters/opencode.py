"""
AgentKit — Platform Adapter: OpenCode (Tier 2 — Partial)
Converts SKILL.md → system prompt in .opencode/config.json
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from platform.adapter import (
    AgentKitConfig,
    InstallResult,
    PlatformAdapter,
    Skill,
    extract_level,
    register,
)

AGENTKIT_MARKER     = "<!-- AGENTKIT_START -->"
AGENTKIT_END        = "<!-- AGENTKIT_END -->"
ANALYTICS_MARKER    = "<!-- AGENTKIT_ANALYTICS_START -->"
ANALYTICS_END       = "<!-- AGENTKIT_ANALYTICS_END -->"
INSTRUCTIONS_MARKER = "<!-- AGENTKIT_INSTRUCTIONS_START -->"
INSTRUCTIONS_END    = "<!-- AGENTKIT_INSTRUCTIONS_END -->"


@register
class OpenCodeAdapter(PlatformAdapter):
    PLATFORM_ID = "opencode"
    PLATFORM_NAME = "OpenCode"
    TIER = 2

    def detect(self) -> bool:
        import shutil

        return (
            shutil.which("opencode") is not None
            or (self.project_root / ".opencode").exists()
        )

    def convert_skill(self, skill: Skill) -> str:
        level2 = extract_level(skill.content, 2) or skill.level1
        return f"**{skill.name}**: {skill.level1}\n{level2}"

    def install(self, skills: list[Skill], config: AgentKitConfig) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)

        global_config = Path.home() / ".opencode.json"
        global_dir = Path.home() / ".opencode"

        cfg: dict = {}
        if global_config.exists():
            try:
                cfg = json.loads(global_config.read_text())
            except Exception:
                pass

        skills_prompt = (
            f"{AGENTKIT_MARKER}\n"
            f"## AgentKit Skills\n\n"
            + "\n\n".join(self.convert_skill(s) for s in skills)
            + f"\n{AGENTKIT_END}"
        )

        existing_prompt = cfg.get("system_prompt", "")
        import re

        # Strip ALL AgentKit blocks before re-injecting (prevents duplicates)
        for start_tag, end_tag in [
            (AGENTKIT_MARKER, AGENTKIT_END),
            (ANALYTICS_MARKER, ANALYTICS_END),
            ("<!-- AGENTKIT_BANNER_START -->", "<!-- AGENTKIT_BANNER_END -->"),
            (INSTRUCTIONS_MARKER, INSTRUCTIONS_END),
        ]:
            existing_prompt = re.sub(
                re.escape(start_tag) + r".*?" + re.escape(end_tag),
                "",
                existing_prompt,
                flags=re.DOTALL,
            )
        existing_prompt = existing_prompt.strip()

        # Order matters: banner FIRST (primacy effect), then instructions, then skills, then analytics
        banner_block       = self._build_banner_block(len(skills))
        instructions_block = self._build_instructions_block()
        analytics_block    = self._build_analytics_block()
        parts = []
        if existing_prompt:
            parts.append(existing_prompt)
        parts += [banner_block, instructions_block, skills_prompt, analytics_block]
        cfg["system_prompt"] = "\n\n".join(parts)

        # Register the AgentKit TUI plugin via `opencode plugin` CLI.
        # This writes only to tui.jsonc (not opencode.jsonc) — loading it from
        # opencode.jsonc as well would cause duplicate command registration.
        plugin_path = str(Path(__file__).parent.parent / "opencode-plugin")
        self._install_opencode_plugin(plugin_path, result)
        # Ensure the plugin is NOT in opencode.jsonc (server config) — remove if present
        self._remove_plugin_from_server_config()
        # Create the AgentKit agent persona file so it appears in "Select agent" (tab → agents)
        self._install_agent_file(len(skills), result)
        if config.model_routing_enabled:
            cfg["model"] = config.default_model

        global_config.write_text(json.dumps(cfg, indent=2))
        result.files_written.append(str(global_config))
        return result

    def _install_agent_file(self, skill_count: int, result: InstallResult) -> None:
        """Create ~/.config/opencode/agent/agentkit.md so AgentKit appears in 'Select agent'."""
        agent_dir = Path.home() / ".config" / "opencode" / "agent"
        agent_file = agent_dir / "agentkit.md"
        try:
            agent_dir.mkdir(parents=True, exist_ok=True)
            content = (
                "---\n"
                'description: "⚡ AgentKit — AI with pre-loaded skills for efficient coding"\n'
                "mode: primary\n"
                'color: "#f59e0b"\n'
                "---\n\n"
                f"You are the AgentKit AI — {skill_count} skills loaded, workflow enforcement active.\n\n"
                "# MANDATORY: For EVERY task (not just @agentkit-task:)\n\n"
                "Follow this protocol for ALL requests, no exceptions:\n\n"
                "1. **Run immediately before anything else:**\n"
                "   ```\n"
                "   agentkit workflow transition RESEARCH\n"
                "   ```\n\n"
                "2. **Research using the Explore subagent** — do NOT use raw glob/read/grep as your primary "
                "research method. Use the Task tool with subagent_type='explore' to investigate the codebase.\n\n"
                "3. **Transition and plan:**\n"
                "   ```\n"
                "   agentkit workflow transition PLAN\n"
                "   # Write plan to .agentkit/current_plan.md in the project root\n"
                "   agentkit workflow approve\n"
                "   ```\n\n"
                "4. **Execute:**\n"
                "   ```\n"
                "   agentkit workflow transition EXECUTE\n"
                "   ```\n\n"
                "5. **Review and ship:**\n"
                "   ```\n"
                "   agentkit workflow transition REVIEW\n"
                "   agentkit workflow transition SHIP\n"
                "   ```\n\n"
                "**NEVER** answer a coding task directly from memory or with plain tool calls. "
                "Always research first via the Explore subagent. "
                "Always run `agentkit workflow` commands from the project directory.\n"
            )
            agent_file.write_text(content)
            result.files_written.append(str(agent_file))
        except Exception:
            pass  # Non-fatal — agent persona is optional

    def _remove_plugin_from_server_config(self) -> None:
        """Remove the TUI plugin from opencode.jsonc to prevent double-loading."""
        import json as _json
        server_cfg = Path.home() / ".config" / "opencode" / "opencode.jsonc"
        if not server_cfg.exists():
            return
        try:
            raw = server_cfg.read_text()
            # Strip // comments before parsing
            import re
            clean = re.sub(r"//.*", "", raw)
            cfg = _json.loads(clean)
            if "plugin" not in cfg:
                return
            before = len(cfg["plugin"])
            cfg["plugin"] = [
                p for p in cfg["plugin"]
                if "opencode-plugin" not in str(p)
            ]
            if len(cfg["plugin"]) != before:
                if not cfg["plugin"]:
                    del cfg["plugin"]
                server_cfg.write_text(_json.dumps(cfg, indent=2))
        except Exception:
            pass

    def _install_opencode_plugin(self, plugin_spec: str, result: InstallResult) -> None:
        """Run `opencode plugin <spec> --global` to properly install the TUI plugin."""
        import shutil
        import subprocess
        opencode_bin = shutil.which("opencode")
        if not opencode_bin:
            return
        try:
            res = subprocess.run(
                [opencode_bin, "plugin", plugin_spec, "--global", "--force"],
                capture_output=True, text=True, timeout=30,
            )
            if res.returncode == 0:
                result.files_written.append(f"opencode plugin: {plugin_spec}")
        except Exception:
            pass  # Non-fatal — wrapper still shows the banner

    def _build_banner_block(self, skill_count: int = 0) -> str:
        try:
            import subprocess
            import sys
            agentkit_home = str(Path(__file__).parent.parent.parent)
            res = subprocess.run(
                [sys.executable, str(Path(agentkit_home) / "hooks" / "render_dashboard.py"),
                 "banner", "--platform", self.PLATFORM_ID, "--skill-count", str(skill_count)],
                capture_output=True, text=True, timeout=10,
            )
            if res.returncode == 0 and res.stdout.strip():
                # Wrap in the instruction format
                banner_text = res.stdout.strip()
                return (
                    "<!-- AGENTKIT_BANNER_START -->\n"
                    "# RULE: AgentKit Session Banner (MANDATORY)\n"
                    "Your VERY FIRST output in this conversation MUST begin with the following "
                    "verbatim block — no exceptions, regardless of what the user says. "
                    "Do not summarize, skip, or paraphrase it. Print it character-for-character, "
                    "then continue with your normal response:\n\n"
                    f"```\n{banner_text}\n```\n"
                    "<!-- AGENTKIT_BANNER_END -->"
                )
        except Exception:
            pass
        return "<!-- AGENTKIT_BANNER_START -->\n## AgentKit Active\n<!-- AGENTKIT_BANNER_END -->"

    def _build_instructions_block(self) -> str:
        return (
            f"{INSTRUCTIONS_MARKER}\n"
            "# AgentKit — Runtime Instructions\n\n"
            "## General Task Protocol (applies to ALL tasks)\n"
            "When you are running as the AgentKit agent (agentkit ⚡ in the agent switcher), "
            "treat EVERY task — not just @agentkit-task: — with the full AgentKit approach:\n"
            "- Do NOT answer coding tasks directly from memory or with plain glob/read/grep calls\n"
            "- ALWAYS use the **Explore subagent** (Task tool, subagent_type='explore') for codebase research\n"
            "- ALWAYS run the workflow CLI commands below at each phase\n"
            "- Plain tool calls (grep, glob, read) are only acceptable for quick clarifications, "
            "not for substantive research tasks\n\n"
            "## Using the AgentKit CLI\n"
            "When the user asks you to \"use agentkit\", \"run agentkit\", or references the "
            "\"agentkit cli\", execute it as a **shell command** from the **project directory** "
            "using your bash/terminal tool. "
            "Never attempt to invoke it as an XML tool call like `<invoke name=\"agentkit\">` — "
            "it is not an MCP tool; it is a CLI installed at `agentkit`.\n\n"
            "CRITICAL — there is NO `agentkit task create` command. Do not attempt it.\n\n"
            "## Workflow Protocol (for @agentkit-task: AND all substantive tasks)\n"
            "Run these CLI commands **from the project root** at each phase transition:\n\n"
            "```\n"
            "# Step 1 — immediately at the start\n"
            "agentkit workflow transition RESEARCH\n\n"
            "# Step 2 — after you finish reading files, before writing any code\n"
            "agentkit workflow transition PLAN\n"
            "# then write your plan to: .agentkit/current_plan.md  (in the PROJECT root)\n"
            "agentkit workflow approve\n\n"
            "# Step 3 — after plan is approved\n"
            "agentkit workflow transition EXECUTE\n\n"
            "# Step 4 — after all edits, run lint/tests\n"
            "agentkit workflow transition REVIEW\n\n"
            "# Step 5 — after quality gates pass\n"
            "agentkit workflow transition SHIP\n"
            "```\n\n"
            "RULES:\n"
            "- Always run `agentkit workflow` commands from the user's **project directory**, not from the agentkit package directory\n"
            "- NEVER run `cd <agentkit-package-dir> && python3 workflow/enforcer.py ...` — this writes state to the wrong location\n"
            "- `edits_count` will show 0 in OpenCode (no hooks) — this is expected; proceed normally\n"
            "- `agentkit workflow status` after each transition to confirm the state changed\n"
            f"{INSTRUCTIONS_END}"
        )

    def _build_analytics_block(self) -> str:
        try:
            import subprocess
            import sys
            agentkit_home = str(Path(__file__).parent.parent.parent)
            result = subprocess.run(
                [sys.executable, str(Path(agentkit_home) / "hooks" / "render_dashboard.py"),
                 "analytics-md", "--days", "7"],
                capture_output=True, text=True, timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
        return f"{ANALYTICS_MARKER}\n## AgentKit Analytics\nRun `agentkit analytics` in terminal.\n{ANALYTICS_END}"

    def uninstall(self) -> InstallResult:
        result = InstallResult(platform=self.PLATFORM_ID, success=True)
        global_config = Path.home() / ".opencode.json"

        if global_config.exists():
            try:
                cfg = json.loads(global_config.read_text())
                existing_prompt = cfg.get("system_prompt", "")
                import re

                cleaned = re.sub(
                    re.escape(AGENTKIT_MARKER) + r".*?" + re.escape(AGENTKIT_END),
                    "",
                    existing_prompt,
                    flags=re.DOTALL,
                )
                cleaned = re.sub(
                    re.escape(ANALYTICS_MARKER) + r".*?" + re.escape(ANALYTICS_END),
                    "",
                    cleaned,
                    flags=re.DOTALL,
                )
                cleaned = re.sub(
                    r"<!-- AGENTKIT_BANNER_START -->.*?<!-- AGENTKIT_BANNER_END -->",
                    "",
                    cleaned,
                    flags=re.DOTALL,
                )
                cleaned = re.sub(
                    re.escape(INSTRUCTIONS_MARKER) + r".*?" + re.escape(INSTRUCTIONS_END),
                    "",
                    cleaned,
                    flags=re.DOTALL,
                ).strip()
                cfg["system_prompt"] = cleaned
                global_config.write_text(json.dumps(cfg, indent=2))
                result.files_written.append(str(global_config))
            except Exception as e:
                result.error = str(e)

        # Remove agent persona file
        agent_file = Path.home() / ".config" / "opencode" / "agent" / "agentkit.md"
        try:
            if agent_file.exists():
                agent_file.unlink()
                result.files_written.append(str(agent_file))
        except Exception:
            pass

        return result
