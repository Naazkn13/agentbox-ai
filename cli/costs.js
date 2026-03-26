/**
 * AgentKit CLI — Cost Analytics
 * `npx agentkit costs` — shows cost report and savings.
 */

"use strict";

const path = require("path");
const { spawnSync } = require("child_process");

function costs(options = {}) {
  const agentKitHome = options.agentKitHome
    || process.env.AGENTKIT_HOME
    || path.join(process.env.HOME || "~", ".agentkit");

  const days = options.days || 7;

  const result = spawnSync(
    "python3",
    [
      path.join(agentKitHome, "hooks", "render_dashboard.py"),
      "report",
      "--days", String(days),
    ],
    { encoding: "utf8" },
  );

  if (result.status === 0) {
    console.log("\n" + result.stdout);
  } else {
    console.log("No cost data available. Run some sessions first.");
    if (result.stderr) console.error(result.stderr);
  }
}

module.exports = { costs };
