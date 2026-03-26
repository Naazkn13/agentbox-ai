"""
AgentKit — Layer 4: Quality Gate Pipeline
Runs language-appropriate checks on edited files: syntax → lint → types → tests.
Called by hooks/quality_gates.sh after every Edit tool use.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GATE_TIMEOUT = 60   # seconds per gate


@dataclass
class GateResult:
    name: str
    passed: bool
    output: str = ""
    duration_ms: int = 0


@dataclass
class QualityReport:
    file_path: str
    gates_run: list[GateResult] = field(default_factory=list)
    overall_passed: bool = True

    def add(self, result: GateResult) -> None:
        self.gates_run.append(result)
        if not result.passed:
            self.overall_passed = False

    def format(self) -> str:
        lines = [f"Quality Gates: {self.file_path}"]
        for g in self.gates_run:
            icon = "✓" if g.passed else "✗"
            suffix = f" ({g.duration_ms}ms)" if g.duration_ms else ""
            lines.append(f"  {icon} {g.name}{suffix}")
        if not self.overall_passed:
            lines.append("")
            lines.append("Failures to fix:")
            for g in self.gates_run:
                if not g.passed and g.output:
                    lines.append(f"  {g.name}: {g.output[:300]}")
        else:
            lines.append("All gates passed.")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Gate runner
# ---------------------------------------------------------------------------

def _run(cmd: list[str], cwd: str | None = None) -> tuple[bool, str]:
    """Run a command, return (passed, output_snippet)."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=GATE_TIMEOUT,
            cwd=cwd,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output[:600]
    except subprocess.TimeoutExpired:
        return False, f"Gate timed out after {GATE_TIMEOUT}s"
    except FileNotFoundError:
        return None, f"Command not found: {cmd[0]}"  # None = gate skipped


def _tool_available(name: str) -> bool:
    import shutil
    return shutil.which(name) is not None


# ---------------------------------------------------------------------------
# Per-language gate sets
# ---------------------------------------------------------------------------

def _gates_python(file_path: str, project_root: str) -> list[tuple[str, list[str]]]:
    gates = [("syntax", ["python3", "-m", "py_compile", file_path])]
    if _tool_available("ruff"):
        gates.append(("lint", ["ruff", "check", file_path, "--select=E,W,F", "--no-cache"]))
    elif _tool_available("flake8"):
        gates.append(("lint", ["flake8", file_path, "--max-line-length=120"]))
    if _tool_available("mypy"):
        gates.append(("types", ["mypy", file_path, "--ignore-missing-imports", "--no-error-summary"]))
    return gates


def _gates_typescript(file_path: str, project_root: str) -> list[tuple[str, list[str]]]:
    gates = []
    if _tool_available("tsc"):
        gates.append(("types", ["tsc", "--noEmit", "--allowJs"]))
    if _tool_available("eslint"):
        gates.append(("lint", ["eslint", file_path, "--max-warnings=0"]))
    return gates


def _gates_javascript(file_path: str, project_root: str) -> list[tuple[str, list[str]]]:
    gates = []
    if _tool_available("eslint"):
        gates.append(("lint", ["eslint", file_path, "--max-warnings=0"]))
    return gates


def _gates_go(file_path: str, project_root: str) -> list[tuple[str, list[str]]]:
    gates = [("syntax", ["go", "vet", file_path])]
    if _tool_available("staticcheck"):
        gates.append(("lint", ["staticcheck", file_path]))
    return gates


def _gates_rust(file_path: str, project_root: str) -> list[tuple[str, list[str]]]:
    gates = [("syntax+types", ["cargo", "check", "--quiet"])]
    if _tool_available("cargo"):
        gates.append(("lint", ["cargo", "clippy", "--quiet", "--", "-D", "warnings"]))
    return gates


LANGUAGE_GATES = {
    ".py":   _gates_python,
    ".ts":   _gates_typescript,
    ".tsx":  _gates_typescript,
    ".js":   _gates_javascript,
    ".jsx":  _gates_javascript,
    ".go":   _gates_go,
    ".rs":   _gates_rust,
}


# ---------------------------------------------------------------------------
# Test discovery
# ---------------------------------------------------------------------------

def _find_test_file(file_path: str, project_root: str) -> Optional[str]:
    stem = Path(file_path).stem
    ext  = Path(file_path).suffix

    patterns = [
        f"test_{stem}{ext}",
        f"{stem}_test{ext}",
        f"{stem}.test{ext}",
        f"{stem}.spec{ext}",
    ]

    for root, dirs, files in os.walk(project_root):
        # Skip heavy dirs
        dirs[:] = [d for d in dirs if d not in ("node_modules", ".git", "__pycache__", ".venv", "dist")]
        for fname in files:
            if fname in patterns:
                return os.path.join(root, fname)
    return None


def _run_tests(test_file: str, ext: str, project_root: str) -> tuple[bool, str]:
    if ext == ".py":
        if _tool_available("pytest"):
            return _run(["pytest", test_file, "-q", "--tb=short"], cwd=project_root)
        return _run(["python3", "-m", "unittest", test_file], cwd=project_root)
    elif ext in (".ts", ".tsx", ".js", ".jsx"):
        if _tool_available("jest"):
            return _run(["jest", test_file, "--no-coverage", "--silent"], cwd=project_root)
        if _tool_available("npx"):
            return _run(["npx", "jest", test_file, "--no-coverage", "--silent"], cwd=project_root)
    elif ext == ".go":
        pkg_dir = str(Path(test_file).parent)
        return _run(["go", "test", pkg_dir, "-v", "-run", "."], cwd=project_root)
    elif ext == ".rs":
        return _run(["cargo", "test", "--quiet"], cwd=project_root)
    return None, "no test runner available"


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_quality_gates(
    file_path: str,
    project_root: str | None = None,
    run_tests: bool = True,
    fail_fast: bool = False,
) -> QualityReport:
    """
    Run all relevant quality gates for the given file.
    Returns a QualityReport with pass/fail per gate.
    """
    import time

    file_path   = os.path.abspath(file_path)
    project_root = project_root or _find_project_root(file_path)
    ext = Path(file_path).suffix.lower()
    report = QualityReport(file_path=file_path)

    gate_factory = LANGUAGE_GATES.get(ext)
    if gate_factory is None:
        return report  # no gates for this file type

    gates = gate_factory(file_path, project_root)
    for gate_name, cmd in gates:
        t0 = time.time()
        ok, out = _run(cmd, cwd=project_root)
        ms = int((time.time() - t0) * 1000)

        if ok is None:
            # Tool not found — skip
            continue

        report.add(GateResult(name=gate_name, passed=ok, output=out, duration_ms=ms))
        if fail_fast and not ok:
            break

    # Test gate
    if run_tests and (not fail_fast or report.overall_passed):
        test_file = _find_test_file(file_path, project_root)
        if test_file:
            t0 = time.time()
            ok, out = _run_tests(test_file, ext, project_root)
            ms = int((time.time() - t0) * 1000)
            if ok is not None:
                report.add(GateResult(name="tests", passed=ok, output=out, duration_ms=ms))

    return report


def _find_project_root(file_path: str) -> str:
    """Walk up from file_path to find the git root (or use cwd)."""
    current = Path(file_path).parent
    for _ in range(10):
        if (current / ".git").exists():
            return str(current)
        parent = current.parent
        if parent == current:
            break
        current = parent
    return os.getcwd()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AgentKit quality gates")
    parser.add_argument("file", help="File to check")
    parser.add_argument("--no-tests",  action="store_true", help="Skip test gate")
    parser.add_argument("--fail-fast", action="store_true", help="Stop on first failure")
    parser.add_argument("--json",      action="store_true", help="Output JSON")
    args = parser.parse_args()

    report = run_quality_gates(
        file_path=args.file,
        run_tests=not args.no_tests,
        fail_fast=args.fail_fast,
    )

    if args.json:
        import json
        print(json.dumps({
            "file":           report.file_path,
            "overall_passed": report.overall_passed,
            "gates": [
                {"name": g.name, "passed": g.passed, "output": g.output}
                for g in report.gates_run
            ],
        }, indent=2))
    else:
        print(report.format())

    sys.exit(0 if report.overall_passed else 1)
