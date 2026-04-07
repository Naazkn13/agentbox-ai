/**
 * AgentKit — OpenCode TUI Plugin
 *
 * - Startup toast
 * - /agentkit slash command (status)
 * - /agentkit-task  → dialog prompt → new session with task pre-filled
 * - /agentkit-analytics → usage info
 *
 * Install: agentkit init  (automatically registered via opencode plugin CLI)
 */

export default {
  id: "agentkit",

  tui: async (api) => {
    // Lazy imports (dynamic — TUI plugins run in browser context, no top-level Node.js imports)
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

    // ── Startup toast ────────────────────────────────────────────────────────
    api.ui.toast({
      variant: "success",
      title: `⚡ AgentKit v${version} Active`,
      message: `${skills} skills loaded  ·  ${status}`,
      duration: 6000,
    });

    // ── Helpers ──────────────────────────────────────────────────────────────

    /**
     * On /agentkit-task selection: navigate home, clear the prompt,
     * and pre-fill with "@agentkit-task: " so the user types their
     * task directly in the native input box and presses Enter themselves.
     */
    async function prefillTaskPrompt() {
      // Go home first so we're on a fresh session context
      if (api.route.current.name !== "home") {
        api.route.navigate("home");
        await new Promise((r) => setTimeout(r, 150));
      }

      try {
        await api.client.tui.clearPrompt({});
        await api.client.tui.appendPrompt({ text: "@agentkit-task: " });
      } catch {
        // Silent — user can still type manually
      }
    }

    // ── Slash commands ────────────────────────────────────────────────────────
    api.command.register(() => [
      // /agentkit  or  /ak  — status overview
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

      // /agentkit-task — pre-fill prompt with @agentkit-task: prefix
      {
        title: "AgentKit: Assign Task",
        value: "agentkit-task",
        description: "Pre-fill the prompt with @agentkit-task — type your task & press Enter",
        category: "AgentKit",
        slash: { name: "agentkit-task", aliases: ["ak-task"] },
        onSelect: () => prefillTaskPrompt(),
      },

      // /agentkit-analytics — usage info
      {
        title: "AgentKit: Analytics",
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
  },
};
