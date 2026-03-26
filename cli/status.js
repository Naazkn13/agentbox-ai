/**
 * AgentKit CLI — Status + Health Check
 * `npx agentkit status` — shows installed platforms, layer health, recent costs.
 */

"use strict";

const fs   = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");
const { detectPlatforms } = require("./detect-platform");

function status(options = {}) {
  const agentKitHome = options.agentKitHome
    || process.env.AGENTKIT_HOME
    || path.join(process.env.HOME || "~", ".agentkit");

  const cwd = process.cwd();

  console.log("\nAgentKit Status\n" + "═".repeat(50));

  // 1. Platforms
  console.log("\nPlatforms:");
  const detected = detectPlatforms();
  if (detected.length === 0) {
    console.log("  (none detected)");
  } else {
    for (const p of detected) {
      const tier = ["", "Full", "Partial", "Basic"][p.tier] || "?";
      console.log(`  ✓ ${p.name.padEnd(20)} Tier ${p.tier} (${tier})`);
    }
  }

  // 2. Layers
  console.log("\nAgentKit Layers:");
  const layers = [
    { name: "Layer 1: Skill Router",   check: () => fs.existsSync(path.join(agentKitHome, "router", "classifier.py")) },
    { name: "Layer 2: Memory Graph",   check: () => fs.existsSync(path.join(agentKitHome, "memory", "graph.py")) },
    { name: "Layer 3: Token Budget",   check: () => fs.existsSync(path.join(agentKitHome, "router", "model_router.py")) },
    { name: "Layer 4: Workflow Engine",check: () => fs.existsSync(path.join(agentKitHome, "workflow", "enforcer.py")) },
    { name: "Layer 5: Platform Layer", check: () => fs.existsSync(path.join(agentKitHome, "platform", "adapter.py")) },
  ];

  for (const layer of layers) {
    const ok = (() => { try { return layer.check(); } catch { return false; } })();
    console.log(`  ${ok ? "✓" : "✗"} ${layer.name}`);
  }

  // 3. Workflow state
  console.log("\nWorkflow State:");
  const workflowResult = spawnSync(
    "python3",
    [path.join(agentKitHome, "workflow", "enforcer.py"), "status"],
    { encoding: "utf8", cwd },
  );
  if (workflowResult.status === 0) {
    for (const line of workflowResult.stdout.trim().split("\n")) {
      console.log("  " + line);
    }
  } else {
    console.log("  (workflow state unavailable)");
  }

  // 4. Recent costs
  console.log("\nRecent Costs (today):");
  const dashResult = spawnSync(
    "python3",
    [path.join(agentKitHome, "hooks", "render_dashboard.py"), "status"],
    { encoding: "utf8", cwd },
  );
  if (dashResult.status === 0) {
    try {
      const data = JSON.parse(dashResult.stdout.trim());
      console.log("  " + (data.status_line || "no data"));
    } catch {
      console.log("  " + dashResult.stdout.trim());
    }
  } else {
    console.log("  (cost data unavailable)");
  }

  // 5. Active skills
  console.log("\nSkills Library:");
  const skillsDir = path.join(agentKitHome, "skills");
  if (fs.existsSync(skillsDir)) {
    const skillFiles = _findSkillFiles(skillsDir);
    console.log(`  ${skillFiles.length} skills installed`);
    for (const f of skillFiles.slice(0, 8)) {
      console.log(`  • ${path.relative(skillsDir, f)}`);
    }
    if (skillFiles.length > 8) {
      console.log(`  … and ${skillFiles.length - 8} more`);
    }
  } else {
    console.log("  (skills directory not found)");
  }

  console.log("\n" + "═".repeat(50) + "\n");
}

function _findSkillFiles(dir) {
  const results = [];
  function walk(d) {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, entry.name);
      if (entry.isDirectory()) {
        walk(full);
      } else if (entry.name.endsWith(".md") && !["README.md", "registry.md", "index.md"].includes(entry.name)) {
        results.push(full);
      }
    }
  }
  walk(dir);
  return results;
}

module.exports = { status };
