#!/usr/bin/env node
/**
 * AgentKit — Post-install script
 * Runs after `npm install -g agentkit-ai` to:
 *   1. Check Python 3 is available
 *   2. Install Python dependencies (PyYAML + anthropic)
 *   3. Set AGENTKIT_HOME to the install directory
 *   4. Print a friendly getting-started message
 */

"use strict";

const { execSync, spawnSync } = require("child_process");
const path = require("path");
const fs   = require("fs");

const AGENTKIT_HOME = path.resolve(__dirname, "..");

// Don't run in CI or when explicitly skipped
if (process.env.CI || process.env.AGENTKIT_SKIP_POSTINSTALL) {
  process.exit(0);
}

console.log("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
console.log("  AgentKit v0.4.0 — Post-install setup");
console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n");

// 1. Check Python 3
const python = findPython();
if (!python) {
  console.error("  ✗ Python 3 not found. Install Python 3.9+ and re-run.");
  console.error("    https://python.org/downloads\n");
  process.exit(0);   // non-fatal — user can fix and re-run
}
console.log(`  ✓ Python found: ${python}`);

// 2. Install Python dependencies
const reqFile = path.join(AGENTKIT_HOME, "requirements.txt");
if (fs.existsSync(reqFile)) {
  console.log("  Installing Python dependencies...");
  const pip = spawnSync(
    python, ["-m", "pip", "install", "-q", "-r", reqFile, "--break-system-packages"],
    { encoding: "utf8", stdio: "pipe" },
  );
  if (pip.status === 0) {
    console.log("  ✓ Python dependencies installed (PyYAML + anthropic)");
  } else {
    // Try without --break-system-packages (older pip)
    const pip2 = spawnSync(
      python, ["-m", "pip", "install", "-q", "-r", reqFile],
      { encoding: "utf8", stdio: "pipe" },
    );
    if (pip2.status === 0) {
      console.log("  ✓ Python dependencies installed");
    } else {
      console.warn("  ⚠  Could not install Python dependencies automatically.");
      console.warn(`    Run: ${python} -m pip install -r ${reqFile}`);
    }
  }
}

// 3. Suggest env var
console.log(`\n  AGENTKIT_HOME is: ${AGENTKIT_HOME}`);
console.log("  Add this to your shell profile:");

const shell = process.env.SHELL || "";
if (shell.includes("zsh")) {
  console.log(`    echo 'export AGENTKIT_HOME="${AGENTKIT_HOME}"' >> ~/.zshrc`);
} else if (shell.includes("fish")) {
  console.log(`    set -Ux AGENTKIT_HOME "${AGENTKIT_HOME}"`);
} else {
  console.log(`    echo 'export AGENTKIT_HOME="${AGENTKIT_HOME}"' >> ~/.bashrc`);
}

// 4. Getting started
console.log(`
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ AgentKit installed!

  Next steps:
    npx agentkit init        ← install into your project
    npx agentkit status      ← health check
    npx agentkit costs       ← cost analytics

  Docs: https://github.com/Ajaysable123/AgentKit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
`);

function findPython() {
  for (const cmd of ["python3", "python"]) {
    try {
      const result = spawnSync(cmd, ["--version"], { encoding: "utf8" });
      if (result.status === 0 && result.stdout.includes("Python 3")) {
        return cmd;
      }
    } catch { /* skip */ }
  }
  return null;
}
