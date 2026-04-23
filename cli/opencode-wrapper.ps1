# AgentKit — OpenCode launcher wrapper (Windows PowerShell)
# Prints the AgentKit banner in the terminal BEFORE OpenCode starts.
#
# Usage: add to your PowerShell profile ($PROFILE):
#   function opencode { & "C:\path\to\agentkit\cli\opencode-wrapper.ps1" @args }
# Or install globally:
#   agentkit init   (automatically adds alias to $PROFILE)

$ErrorActionPreference = "SilentlyContinue"

# Resolve AgentKit home
if ($env:AGENTKIT_HOME) {
    $AgentKitHome = $env:AGENTKIT_HOME
} else {
    $AgentKitHome = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

# Find python executable
$PythonCmd = $null
foreach ($cmd in @("python", "python3")) {
    $found = Get-Command $cmd -ErrorAction SilentlyContinue
    if ($found) {
        $PythonCmd = $found.Source
        break
    }
}

# Print banner
if ($PythonCmd) {
    try {
        & $PythonCmd "$AgentKitHome\hooks\render_dashboard.py" banner --platform opencode 2>$null
    } catch {}
}

Write-Host ""
Write-Host "  Starting OpenCode..."
Write-Host ""

Start-Sleep -Milliseconds 800

# Find opencode executable
$OpenCodeBin = (Get-Command opencode -ErrorAction SilentlyContinue).Source
if (-not $OpenCodeBin) {
    $OpenCodeBin = "opencode"
}

# Hand off to the real opencode binary
& $OpenCodeBin @args
