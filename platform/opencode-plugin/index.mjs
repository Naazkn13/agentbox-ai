/**
 * AgentKit — OpenCode Plugin
 *
 * Server side: injects AgentKit system prompt into every conversation via
 * experimental.chat.system.transform (reliable, model-agnostic).
 *
 * TUI side: shows a toast notification when OpenCode starts, and registers
 * an /agentkit slash command to display the live status dashboard.
 *
 * Install: agentkit init  (registers this plugin automatically)
 * Or manually: opencode plugin file:/path/to/agentkit/platform/opencode-plugin/index.mjs
 */

import { readFileSync, existsSync } from "fs";
import { execSync } from "child_process";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const AGENTKIT_HOME = resolve(__dirname, "../..");

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function getVersion() {
  try {
    const pkg = JSON.parse(readFileSync(resolve(AGENTKIT_HOME, "package.json"), "utf8"));
    return pkg.version || "?.?.?";
  } catch {
    return "?.?.?";
  }
}

function getSkillCount() {
  try {
    const out = execSync(
      `find "${AGENTKIT_HOME}/skills" -name "*.md" 2>/dev/null | wc -l`,
      { encoding: "utf8", timeout: 3000 }
    ).trim();
    return parseInt(out) || 0;
  } catch {
    return 0;
  }
}

function getAgentKitSystemPrompt() {
  try {
    const out = execSync(
      `python3 "${AGENTKIT_HOME}/hooks/render_dashboard.py" analytics-md --days 7`,
      { encoding: "utf8", timeout: 10000 }
    ).trim();
    return out || "";
  } catch {
    return "";
  }
}

function getStatusLine() {
  try {
    const statusFile = resolve(AGENTKIT_HOME, "data/status_line.txt");
    if (existsSync(statusFile)) return readFileSync(statusFile, "utf8").trim();
  } catch {}
  return "$0.000 | no data";
}

function getDashboard() {
  try {
    return execSync(
      `python3 "${AGENTKIT_HOME}/hooks/render_dashboard.py" analytics --days 7`,
      { encoding: "utf8", timeout: 10000 }
    ).trim();
  } catch {
    return "AgentKit analytics unavailable. Run: agentkit analytics";
  }
}

// ---------------------------------------------------------------------------
// Server plugin — injects AgentKit context into every conversation
// ---------------------------------------------------------------------------

export const id = "agentkit";

export const server = async (_ctx) => {
  const analyticsBlock = getAgentKitSystemPrompt();

  return {
    /**
     * Inject AgentKit skills + analytics into every conversation's system prompt.
     * This is the reliable way — no AI model can ignore it.
     */
    "experimental.chat.system.transform": async (_input, output) => {
      if (analyticsBlock) {
        output.system.push(analyticsBlock);
      }
    },
  };
};

// ---------------------------------------------------------------------------
// TUI plugin — toast notification + /agentkit slash command
// ---------------------------------------------------------------------------

export const tui = async (api) => {
  const version = getVersion();
  const skills  = getSkillCount();
  const status  = getStatusLine();

  // Show startup toast inside the TUI
  api.ui.toast({
    variant: "success",
    title: `⚡ AgentKit v${version} Active`,
    message: `${skills} skills loaded · ${status}`,
    duration: 6000,
  });

  // Register /agentkit slash command — shows live analytics dashboard
  api.command.register(() => [
    {
      title: "AgentKit: Show Analytics",
      value: "agentkit-analytics",
      description: `⚡ AgentKit v${version} · ${skills} skills · ${status}`,
      category: "AgentKit",
      slash: { name: "agentkit", aliases: ["ak"] },
      onSelect: () => {
        const dashboard = getDashboard();
        api.ui.toast({
          variant: "info",
          title: "AgentKit Analytics",
          message: `Run: agentkit analytics  in your terminal for the full dashboard.\n${status}`,
          duration: 8000,
        });
      },
    },
    {
      title: "AgentKit: Status",
      value: "agentkit-status",
      description: "Show AgentKit health check",
      category: "AgentKit",
      slash: { name: "agentkit-status" },
      onSelect: () => {
        api.ui.toast({
          variant: "info",
          title: `⚡ AgentKit v${version}`,
          message: `Skills: ${skills} · Session: ${status} · Run: agentkit status`,
          duration: 8000,
        });
      },
    },
  ]);
};
