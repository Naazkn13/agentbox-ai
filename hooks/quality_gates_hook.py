"""
AgentKit — Quality Gates Hook (cross-platform Python equivalent of quality_gates.sh)
Event: PostToolUse (Edit|Write|MultiEdit)
Purpose: Run syntax/lint/types/tests on the edited file.
"""

import json
import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

SUPPORTED_EXTENSIONS = {"py", "ts", "tsx", "js", "jsx", "go", "rs"}


def main() -> None:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", tool_input.get("path", ""))

    if not file_path:
        return

    # Only check supported source files
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    if ext not in SUPPORTED_EXTENSIONS:
        return

    # Skip test files (just run syntax check on them)
    is_test = any(pat in file_path for pat in ("test_", "_test.", ".test.", ".spec."))
    if is_test:
        if ext == "py":
            import subprocess
            r = subprocess.run(
                [sys.executable, "-m", "py_compile", file_path],
                capture_output=True, text=True,
            )
            icon = "✓" if r.returncode == 0 else "✗"
            print(f"{icon} syntax ({file_path})")
        return

    # Run full quality gates
    try:
        from workflow.quality_gates import run_quality_gates
        report = run_quality_gates(file_path)
        print(report.format())

        # Update workflow state if all gates passed
        if report.overall_passed:
            try:
                from workflow.enforcer import WorkflowEnforcer
                project_root = os.environ.get("AGENTKIT_PROJECT", os.getcwd())
                enforcer = WorkflowEnforcer(project_root)
                enforcer.on_file_edit(file_path)
            except Exception:
                pass

        # Block if configured to
        block_on_failure = os.environ.get("AGENTKIT_GATES_BLOCK", "false").lower() == "true"
        if not report.overall_passed and block_on_failure:
            sys.exit(2)
    except Exception as e:
        print(f"[AgentKit] Quality gates error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
