/**
 * AgentKit CLI — Usage Analytics Dashboard
 * `npx agentkit analytics [--days N]`
 *
 * Works in any terminal: Claude Code, OpenCode, Gemini CLI, Codex, or plain shell.
 * Renders a full ASCII dashboard showing cost, model usage, skills, and platform breakdown.
 */

"use strict";

const path = require("path");
const { spawnSync } = require("child_process");

function analytics(options = {}) {
  const agentKitHome = options.agentKitHome
    || process.env.AGENTKIT_HOME
    || path.join(__dirname, "..");

  const days = options.days || 7;

  const result = spawnSync(
    "python3",
    [
      path.join(agentKitHome, "hooks", "render_dashboard.py"),
      "analytics",
      "--days", String(days),
    ],
    { encoding: "utf8" },
  );

  if (result.status === 0 && result.stdout.trim()) {
    console.log("\n" + result.stdout);
  } else {
    console.log("\nNo analytics data yet. Run some sessions first.");
    console.log("Tip: AgentKit logs cost data automatically once hooks are active.\n");
    if (result.stderr) console.error(result.stderr);
  }
}

/**
 * Fetch a compact markdown analytics summary (for platform injection).
 * Returns the string directly — callers decide what to do with it.
 */
function analyticsMarkdown(options = {}) {
  const agentKitHome = options.agentKitHome
    || process.env.AGENTKIT_HOME
    || path.join(__dirname, "..");

  const days = options.days || 7;

  const result = spawnSync(
    "python3",
    [
      path.join(agentKitHome, "hooks", "render_dashboard.py"),
      "analytics-md",
      "--days", String(days),
    ],
    { encoding: "utf8" },
  );

  return result.status === 0 ? result.stdout.trim() : "";
}

module.exports = { analytics, analyticsMarkdown };
