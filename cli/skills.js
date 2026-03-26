/**
 * AgentKit CLI — Skill Management
 * `npx agentkit skills list|info|add|remove`
 */

"use strict";

const fs   = require("fs");
const path = require("path");
const { spawnSync } = require("child_process");

function listSkills(options = {}) {
  const agentKitHome = options.agentKitHome
    || process.env.AGENTKIT_HOME
    || path.join(process.env.HOME || "~", ".agentkit");

  const skillsDir = path.join(agentKitHome, "skills");
  if (!fs.existsSync(skillsDir)) {
    console.log("Skills directory not found:", skillsDir);
    return;
  }

  console.log("\nInstalled Skills\n" + "─".repeat(50));

  // Use Python to parse frontmatter
  const result = spawnSync(
    "python3",
    ["-c", `
import sys, os, yaml, pathlib
sys.path.insert(0, '${agentKitHome}')
from platform.adapter import load_skills
skills = load_skills('${skillsDir}')
for s in sorted(skills, key=lambda x: x.category):
    print(f"  {s.category:20s} {s.id:30s} {s.name}")
`],
    { encoding: "utf8" },
  );

  if (result.status === 0 && result.stdout.trim()) {
    console.log(result.stdout);
  } else {
    // Fallback: just list files
    const files = _findSkillFiles(skillsDir);
    for (const f of files) {
      console.log("  " + path.relative(skillsDir, f));
    }
  }
  console.log("─".repeat(50) + "\n");
}

function skillInfo(skillId, options = {}) {
  const agentKitHome = options.agentKitHome
    || process.env.AGENTKIT_HOME
    || path.join(process.env.HOME || "~", ".agentkit");

  const result = spawnSync(
    "python3",
    ["-c", `
import sys
sys.path.insert(0, '${agentKitHome}')
from platform.adapter import load_skills
skills = load_skills('${agentKitHome}/skills')
skill = next((s for s in skills if s.id == '${skillId}'), None)
if skill:
    print(f"ID:       {skill.id}")
    print(f"Name:     {skill.name}")
    print(f"Category: {skill.category}")
    print(f"Activate: {skill.level1}")
    print(f"Tokens:   L1={skill.level1_tokens} L2={skill.level2_tokens} L3={skill.level3_tokens}")
    print(f"Version:  {skill.version}")
    print(f"Path:     {skill.path}")
else:
    print(f"Skill not found: ${skillId}")
`],
    { encoding: "utf8" },
  );
  console.log(result.stdout || result.stderr || "Error");
}

function _findSkillFiles(dir) {
  const results = [];
  function walk(d) {
    for (const entry of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, entry.name);
      if (entry.isDirectory()) walk(full);
      else if (entry.name === "SKILL.md" || entry.name.endsWith("SKILL.md")) results.push(full);
    }
  }
  walk(dir);
  return results;
}

module.exports = { listSkills, skillInfo };
