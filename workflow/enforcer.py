"""
AgentKit — Layer 4: Workflow Enforcer
State machine for Research → Plan → Execute → Review → Ship pipeline.
Persists state to .agentkit/ inside the project directory.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# State machine definition
# ---------------------------------------------------------------------------

STATES = ("IDLE", "RESEARCH", "PLAN", "EXECUTE", "REVIEW", "SHIP")

VALID_TRANSITIONS: dict[str, list[str]] = {
    "IDLE":    ["RESEARCH"],
    "RESEARCH":["PLAN"],
    "PLAN":    ["EXECUTE"],
    "EXECUTE": ["REVIEW"],
    "REVIEW":  ["SHIP", "EXECUTE"],   # back to EXECUTE if gates fail
    "SHIP":    ["IDLE"],
}


@dataclass
class WorkflowContext:
    state: str = "IDLE"
    files_read_count: int = 0
    plan_exists: bool = False
    plan_approved: bool = False
    edits_count: int = 0
    all_quality_gates_passed: bool = False
    current_task: str = ""
    state_entered_at: int = field(default_factory=lambda: int(time.time()))
    history: list[dict] = field(default_factory=list)


# Gate requirements: (from_state → to_state) → check function
def _gate_research_to_plan(ctx: WorkflowContext) -> tuple[bool, str]:
    if ctx.files_read_count < 2:
        return False, f"Read at least 2 files before planning (read {ctx.files_read_count} so far)"
    return True, ""

def _gate_plan_to_execute(ctx: WorkflowContext) -> tuple[bool, str]:
    if not ctx.plan_exists:
        return False, "Create a plan in .agentkit/current_plan.md first"
    if not ctx.plan_approved:
        return False, "Plan must be approved — run: agentkit workflow approve"
    return True, ""

def _gate_execute_to_review(ctx: WorkflowContext) -> tuple[bool, str]:
    if ctx.edits_count < 1:
        return False, "Make at least one code change before reviewing"
    return True, ""

def _gate_review_to_ship(ctx: WorkflowContext) -> tuple[bool, str]:
    if not ctx.all_quality_gates_passed:
        return False, "All quality gates must pass before shipping"
    return True, ""


STATE_GATES: dict[str, callable] = {
    "RESEARCH→PLAN":   _gate_research_to_plan,
    "PLAN→EXECUTE":    _gate_plan_to_execute,
    "EXECUTE→REVIEW":  _gate_execute_to_review,
    "REVIEW→SHIP":     _gate_review_to_ship,
}


# ---------------------------------------------------------------------------
# WorkflowEnforcer
# ---------------------------------------------------------------------------

class WorkflowEnforcer:
    """
    Manages workflow state for a single project.
    State is persisted to <project_root>/.agentkit/workflow.json
    """

    def __init__(self, project_root: str | None = None):
        self.project_root = Path(project_root or os.getcwd())
        self.state_dir = self.project_root / ".agentkit"
        self.state_file = self.state_dir / "workflow.json"
        self.plan_file  = self.state_dir / "current_plan.md"

    def _load(self) -> WorkflowContext:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                ctx = WorkflowContext(**{k: v for k, v in data.items()
                                         if k in WorkflowContext.__dataclass_fields__})
                return ctx
            except Exception:
                pass
        return WorkflowContext()

    def _save(self, ctx: WorkflowContext) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(asdict(ctx), indent=2))

    # ------------------------------------------------------------------
    # State queries
    # ------------------------------------------------------------------

    def get_state(self) -> WorkflowContext:
        ctx = self._load()
        # Sync plan_exists from filesystem
        ctx.plan_exists = self.plan_file.exists() and self.plan_file.stat().st_size > 0
        return ctx

    def current_state(self) -> str:
        return self.get_state().state

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def transition(self, to_state: str, force: bool = False) -> tuple[bool, str]:
        """
        Attempt a state transition. Returns (success, message).
        Set force=True to bypass gate checks (logged as an override).
        """
        ctx = self.get_state()
        from_state = ctx.state

        if to_state not in VALID_TRANSITIONS.get(from_state, []):
            return False, f"Invalid transition: {from_state} → {to_state}"

        gate_key = f"{from_state}→{to_state}"
        gate_fn  = STATE_GATES.get(gate_key)

        if gate_fn and not force:
            ok, msg = gate_fn(ctx)
            if not ok:
                return False, msg

        ctx.history.append({
            "from": from_state,
            "to":   to_state,
            "ts":   int(time.time()),
            "forced": force,
        })
        ctx.state = to_state
        ctx.state_entered_at = int(time.time())
        self._save(ctx)
        return True, f"{from_state} → {to_state}"

    def reset(self) -> None:
        """Reset to IDLE (new task)."""
        ctx = WorkflowContext()
        self._save(ctx)
        if self.plan_file.exists():
            self.plan_file.unlink()

    # ------------------------------------------------------------------
    # Event handlers (called by hooks)
    # ------------------------------------------------------------------

    def on_file_read(self, path: str) -> None:
        ctx = self._load()
        ctx.files_read_count += 1
        # Auto-advance IDLE → RESEARCH on first read
        if ctx.state == "IDLE":
            ctx.state = "RESEARCH"
            ctx.state_entered_at = int(time.time())
        self._save(ctx)

    def on_file_edit(self, path: str) -> tuple[bool, str]:
        """
        Called before an Edit/Write tool use.
        Returns (allowed, message). If not allowed, hook should block.
        """
        ctx = self.get_state()

        if ctx.state in ("EXECUTE", "SHIP"):
            ctx.edits_count += 1
            self._save(ctx)
            return True, ""

        if ctx.state == "PLAN":
            # Editing the plan file itself is allowed
            if str(path) == str(self.plan_file):
                return True, ""
            # Writing code without an approved plan → block
            ok, msg = _gate_plan_to_execute(ctx)
            if not ok:
                return False, msg
            # Auto-advance to EXECUTE
            self.transition("EXECUTE")
            ctx = self._load()   # reload after transition to capture new state
            ctx.edits_count += 1
            self._save(ctx)
            return True, ""

        if ctx.state in ("IDLE", "RESEARCH"):
            return False, (
                f"[AgentKit] PLAN REQUIRED\n"
                f"Current state: {ctx.state}. You must:\n"
                f"  1. Read relevant files (≥2 done: {ctx.files_read_count})\n"
                f"  2. Write a plan to .agentkit/current_plan.md\n"
                f"  3. Approve it with: agentkit workflow approve\n"
                f"  4. Then start coding"
            )

        return True, ""

    def on_quality_gates_passed(self) -> None:
        ctx = self._load()
        ctx.all_quality_gates_passed = True
        self._save(ctx)

    def approve_plan(self) -> tuple[bool, str]:
        ctx = self._load()
        ctx.plan_exists = self.plan_file.exists() and self.plan_file.stat().st_size > 0
        if not ctx.plan_exists:
            return False, "No plan found at .agentkit/current_plan.md"
        ctx.plan_approved = True
        # Auto-advance to PLAN state so the next edit can proceed to EXECUTE
        if ctx.state in ("IDLE", "RESEARCH"):
            ctx.history.append({"from": ctx.state, "to": "PLAN", "ts": int(time.time()), "forced": False})
            ctx.state = "PLAN"
            ctx.state_entered_at = int(time.time())
        self._save(ctx)
        return True, "Plan approved. You can now start coding."

    # ------------------------------------------------------------------
    # Status display
    # ------------------------------------------------------------------

    def status_text(self) -> str:
        ctx = self.get_state()
        lines = [
            f"Workflow state : {ctx.state}",
            f"Task           : {ctx.current_task or '(none)'}",
            f"Files read     : {ctx.files_read_count}",
            f"Edits made     : {ctx.edits_count}",
            f"Plan exists    : {'yes' if ctx.plan_exists else 'no'}",
            f"Plan approved  : {'yes' if ctx.plan_approved else 'no'}",
            f"Gates passed   : {'yes' if ctx.all_quality_gates_passed else 'no'}",
        ]
        next_steps = VALID_TRANSITIONS.get(ctx.state, [])
        if next_steps:
            lines.append(f"Next states    : {', '.join(next_steps)}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AgentKit workflow enforcer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status",  help="Show current workflow state")
    sub.add_parser("approve", help="Approve the current plan")
    sub.add_parser("reset",   help="Reset workflow to IDLE")

    p_trans = sub.add_parser("transition", help="Attempt a state transition")
    p_trans.add_argument("to_state", choices=STATES)
    p_trans.add_argument("--force", action="store_true")

    p_read = sub.add_parser("on-read", help="Record a file read event")
    p_read.add_argument("path")

    p_edit = sub.add_parser("on-edit", help="Check if edit is allowed")
    p_edit.add_argument("path")

    args = parser.parse_args()
    enforcer = WorkflowEnforcer()

    if args.cmd == "status":
        print(enforcer.status_text())

    elif args.cmd == "approve":
        ok, msg = enforcer.approve_plan()
        print(msg)
        raise SystemExit(0 if ok else 1)

    elif args.cmd == "reset":
        enforcer.reset()
        print("Workflow reset to IDLE.")

    elif args.cmd == "transition":
        ok, msg = enforcer.transition(args.to_state, force=args.force)
        print(msg)
        raise SystemExit(0 if ok else 1)

    elif args.cmd == "on-read":
        enforcer.on_file_read(args.path)

    elif args.cmd == "on-edit":
        ok, msg = enforcer.on_file_edit(args.path)
        if not ok:
            print(msg)
        raise SystemExit(0 if ok else 1)
