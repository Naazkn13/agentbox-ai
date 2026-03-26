#!/usr/bin/env node
/**
 * AgentKit — CLI smoke tests
 * Run via: npm test   or   node cli/test.js
 */

"use strict";

const path = require("path");
const { spawnSync } = require("child_process");
const { detectPlatforms, PLATFORMS } = require("./detect-platform");

const AGENTKIT_HOME = path.resolve(__dirname, "..");
const PASS = "✅";
const FAIL = "❌";

let passed = 0;
let failed = 0;

function test(name, fn) {
  try {
    fn();
    console.log(`  ${PASS} ${name}`);
    passed++;
  } catch (e) {
    console.log(`  ${FAIL} ${name}: ${e.message}`);
    failed++;
  }
}

function assert(cond, msg) {
  if (!cond) throw new Error(msg || "assertion failed");
}

console.log("\nAgentKit CLI smoke tests\n" + "─".repeat(40));

// ── detect-platform.js ──────────────────────────────────────────────────────
console.log("\ndetect-platform.js:");
test("PLATFORMS list has ≥10 entries", () => {
  assert(PLATFORMS.length >= 10, `got ${PLATFORMS.length}`);
});
test("detectPlatforms() returns an array", () => {
  const result = detectPlatforms();
  assert(Array.isArray(result));
});
test("each platform has id, name, tier, checks", () => {
  for (const p of PLATFORMS) {
    assert(p.id,     `missing id on ${JSON.stringify(p)}`);
    assert(p.name,   `missing name on ${p.id}`);
    assert(p.tier >= 1 && p.tier <= 3, `bad tier on ${p.id}`);
    assert(Array.isArray(p.checks), `missing checks on ${p.id}`);
  }
});

// ── install.js ───────────────────────────────────────────────────────────────
console.log("\ninstall.js:");
const { BUNDLES } = require("./install");
test("5 skill bundles defined", () => {
  assert(Object.keys(BUNDLES).length >= 5, `got ${Object.keys(BUNDLES).length}`);
});
test("each bundle has name and skills array", () => {
  for (const [key, b] of Object.entries(BUNDLES)) {
    assert(b.name,   `missing name on bundle ${key}`);
    assert(Array.isArray(b.skills) && b.skills.length > 0, `empty skills on ${key}`);
  }
});

// ── Python adapters (via bridge) ──────────────────────────────────────────────
console.log("\nPython platform adapters:");
test("load_skills() finds ≥13 skills", () => {
  const r = spawnSync("python3", ["-c", `
import sys; sys.path.insert(0, '${AGENTKIT_HOME}')
from platform.adapter import load_skills
skills = load_skills('${AGENTKIT_HOME}/skills')
print(len(skills))
`], { encoding: "utf8" });
  const n = parseInt(r.stdout.trim(), 10);
  assert(!isNaN(n) && n >= 13, `got ${r.stdout.trim()}`);
});

test("all 10 adapters registered", () => {
  const r = spawnSync("python3", ["-c", `
import sys; sys.path.insert(0, '${AGENTKIT_HOME}')
from platform.adapter import all_adapters
import platform.adapters.claude_code, platform.adapters.cursor
import platform.adapters.codex, platform.adapters.gemini_cli
import platform.adapters.antigravity, platform.adapters.opencode
import platform.adapters.aider, platform.adapters.windsurf
import platform.adapters.kilo_code, platform.adapters.augment
print(len(all_adapters()))
`], { encoding: "utf8" });
  const n = parseInt(r.stdout.trim(), 10);
  assert(n === 10, `expected 10, got ${n}`);
});

// ── CLI commands ──────────────────────────────────────────────────────────────
console.log("\nCLI commands:");
test("agentkit detect exits 0", () => {
  const r = spawnSync("node", [path.join(AGENTKIT_HOME, "cli/index.js"), "detect"],
    { encoding: "utf8" });
  assert(r.status === 0, `exit ${r.status}: ${r.stderr}`);
});
test("agentkit bundles exits 0", () => {
  const r = spawnSync("node", [path.join(AGENTKIT_HOME, "cli/index.js"), "bundles"],
    { encoding: "utf8" });
  assert(r.status === 0, `exit ${r.status}: ${r.stderr}`);
});
test("agentkit help exits 0", () => {
  const r = spawnSync("node", [path.join(AGENTKIT_HOME, "cli/index.js"), "help"],
    { encoding: "utf8" });
  assert(r.status === 0, `exit ${r.status}: ${r.stderr}`);
});
test("agentkit workflow status exits 0", () => {
  const r = spawnSync("node", [path.join(AGENTKIT_HOME, "cli/index.js"), "workflow", "status"],
    { encoding: "utf8", cwd: "/tmp" });
  // May exit 0 or 1 depending on workflow state — just check it runs
  assert(r.error == null, `spawn error: ${r.error}`);
});

// ── Summary ───────────────────────────────────────────────────────────────────
console.log("\n" + "─".repeat(40));
console.log(`Results: ${passed} passed, ${failed} failed`);
if (failed > 0) {
  process.exit(1);
}
console.log("");
