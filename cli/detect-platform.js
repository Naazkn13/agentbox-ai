/**
 * AgentKit CLI — Platform Detector
 * Checks the current environment for known AI coding tools.
 */

"use strict";

const fs   = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const PLATFORMS = [
  {
    id:    "claude-code",
    name:  "Claude Code",
    tier:  1,
    checks: [
      () => fs.existsSync(path.join(process.env.HOME || "", ".claude")),
      () => fs.existsSync(path.join(process.cwd(), ".claude")),
      () => which("claude"),
    ],
  },
  {
    id:    "cursor",
    name:  "Cursor",
    tier:  2,
    checks: [
      () => fs.existsSync(path.join(process.env.HOME || "", ".cursor")),
      () => fs.existsSync(path.join(process.cwd(), ".cursor")),
      () => fs.existsSync(path.join(process.cwd(), ".cursorrules")),
      () => which("cursor"),
    ],
  },
  {
    id:    "codex",
    name:  "Codex CLI",
    tier:  3,
    checks: [
      () => !!process.env.OPENAI_API_KEY,
      () => which("codex"),
      () => fs.existsSync(path.join(process.cwd(), "AGENTS.md")),
    ],
  },
  {
    id:    "gemini-cli",
    name:  "Gemini CLI",
    tier:  2,
    checks: [
      () => !!process.env.GEMINI_API_KEY,
      () => which("gemini"),
      () => fs.existsSync(path.join(process.cwd(), ".gemini")),
    ],
  },
  {
    id:    "antigravity",
    name:  "Antigravity",
    tier:  1,
    checks: [
      () => which("antigravity"),
      () => fs.existsSync(path.join(process.cwd(), ".antigravity")),
    ],
  },
  {
    id:    "opencode",
    name:  "OpenCode",
    tier:  2,
    checks: [
      () => which("opencode"),
      () => fs.existsSync(path.join(process.cwd(), ".opencode")),
    ],
  },
  {
    id:    "aider",
    name:  "Aider",
    tier:  3,
    checks: [
      () => which("aider"),
      () => fs.existsSync(path.join(process.cwd(), ".aider.conf.yml")),
      () => fs.existsSync(path.join(process.env.HOME || "", ".aider.conf.yml")),
    ],
  },
  {
    id:    "windsurf",
    name:  "Windsurf",
    tier:  2,
    checks: [
      () => which("windsurf"),
      () => fs.existsSync(path.join(process.cwd(), ".windsurf")),
    ],
  },
  {
    id:    "kilo-code",
    name:  "Kilo Code",
    tier:  2,
    checks: [
      () => which("kilo"),
      () => fs.existsSync(path.join(process.cwd(), ".kilo")),
    ],
  },
  {
    id:    "augment",
    name:  "Augment Code",
    tier:  3,
    checks: [
      () => which("augment"),
      () => fs.existsSync(path.join(process.cwd(), ".augment")),
    ],
  },
];

/** Return true if an executable is in PATH. */
function which(cmd) {
  try {
    execSync(`which ${cmd}`, { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

/** Detect all platforms present in the environment. */
function detectPlatforms() {
  const found = [];
  for (const platform of PLATFORMS) {
    const hit = platform.checks.some(fn => {
      try { return !!fn(); } catch { return false; }
    });
    if (hit) {
      found.push({ ...platform, detected: true });
    }
  }
  return found;
}

/** Return the primary platform (highest tier that's detected). */
function primaryPlatform(detected) {
  return detected.sort((a, b) => a.tier - b.tier)[0] || null;
}

module.exports = { detectPlatforms, primaryPlatform, PLATFORMS };
