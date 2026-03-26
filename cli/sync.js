/**
 * AgentKit CLI — Cross-Platform Sync
 * `npx agentkit sync` — re-runs install for all detected platforms
 * to pick up new/updated skills and config changes.
 */

"use strict";

const path = require("path");
const { detectPlatforms } = require("./detect-platform");
const { install } = require("./install");

function sync(options = {}) {
  const agentKitHome = options.agentKitHome
    || process.env.AGENTKIT_HOME
    || path.join(process.env.HOME || "~", ".agentkit");

  const silent = options.silent || false;
  function log(...args) { if (!silent) console.log(...args); }

  log("\nSyncing AgentKit config across platforms...");

  const detected = detectPlatforms();
  if (detected.length === 0) {
    log("  No platforms detected. Nothing to sync.");
    return;
  }

  const result = install({
    agentKitHome,
    platforms: detected.map(p => p.id),
    bundle: options.bundle || "backend-pro",
    silent,
  });

  const succeeded = result.platforms.filter(r => r.success);
  const failed    = result.platforms.filter(r => !r.success);

  log("Sync complete:");
  for (const r of succeeded) log(`  ✓ ${r.platform}`);
  for (const r of failed)    log(`  ✗ ${r.platform}: ${r.error || "failed"}`);
  log("");
}

module.exports = { sync };
