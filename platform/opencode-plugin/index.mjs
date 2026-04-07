/**
 * AgentKit — OpenCode TUI Plugin
 *
 * Shows a startup toast + /agentkit slash command inside OpenCode's TUI.
 * NO top-level Node.js built-in imports (required for TUI context detection).
 *
 * Install: agentkit init  (automatically registered via opencode plugin CLI)
 */

// TUI-only plugin — no server export (required for TUI detection)
export const id = "agentkit";

export const tui = async (api) => {
  // Lazy imports inside the function (TUI context allows dynamic imports)
  const { readFileSync, existsSync } = await import("fs");
  const { execSync }                 = await import("child_process");
  const { resolve, dirname }         = await import("path");
  const { fileURLToPath }            = await import("url");

  const __dirname     = dirname(fileURLToPath(import.meta.url));
  const AGENTKIT_HOME = resolve(__dirname, "../..");

  let version = "?.?.?";
  let skills  = 0;
  let status  = "no session data";

  try {
    const pkg = JSON.parse(readFileSync(resolve(AGENTKIT_HOME, "package.json"), "utf8"));
    version = pkg.version || version;
  } catch {}

  try {
    const out = execSync(
      `find "${AGENTKIT_HOME}/skills" -name "*.md" 2>/dev/null | wc -l`,
      { encoding: "utf8", timeout: 3000 }
    ).trim();
    skills = parseInt(out) || 0;
  } catch {}

  try {
    const f = resolve(AGENTKIT_HOME, "data/status_line.txt");
    if (existsSync(f)) status = readFileSync(f, "utf8").trim();
  } catch {}

  // Startup toast — visible inside the TUI immediately on launch
  api.ui.toast({
    variant: "success",
    title: `⚡ AgentKit v${version} Active`,
    message: `${skills} skills loaded  ·  ${status}`,
    duration: 6000,
  });

  // Register /agentkit and /ak slash commands
  api.command.register(() => [
    {
      title: "AgentKit: Status",
      value: "agentkit-status",
      description: `⚡ v${version} · ${skills} skills · ${status}`,
      category: "AgentKit",
      slash: { name: "agentkit", aliases: ["ak"] },
      onSelect: () => {
        api.ui.toast({
          variant: "info",
          title: `⚡ AgentKit v${version}`,
          message: `Skills: ${skills}  ·  ${status}\nRun: agentkit analytics  in terminal for full dashboard`,
          duration: 8000,
        });
      },
    },
    {
      title: "AgentKit: Analytics Dashboard",
      value: "agentkit-analytics",
      description: "Show cost & usage stats",
      category: "AgentKit",
      slash: { name: "agentkit-analytics" },
      onSelect: () => {
        api.ui.toast({
          variant: "info",
          title: "AgentKit Analytics",
          message: `Run: agentkit analytics --days 7\nin your terminal for the full dashboard.`,
          duration: 8000,
        });
      },
    },
  ]);
};
