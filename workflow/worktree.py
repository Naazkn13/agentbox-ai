"""
AgentKit — Layer 4: Git Worktree Manager
Create isolated git worktrees for parallel feature development.
Subagents work in their own worktrees — zero conflict with the main branch.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Worktree:
    path: str
    branch: str
    commit: str = ""
    is_main: bool = False

    @staticmethod
    def parse_list_line(line: str) -> Optional["Worktree"]:
        """Parse a line from `git worktree list --porcelain`."""
        # format: "worktree /path/to/wt\nHEAD <sha>\nbranch refs/heads/<name>"
        # We receive the split dict from parse_list() instead.
        return None


def _run(cmd: list[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
        check=check,
    )


def _slug(name: str) -> str:
    """Convert a feature name to a filesystem-safe slug."""
    name = name.lower().strip()
    name = re.sub(r"[^a-z0-9_-]", "-", name)
    name = re.sub(r"-+", "-", name).strip("-")
    return name[:50]


# ---------------------------------------------------------------------------
# WorktreeManager
# ---------------------------------------------------------------------------

class WorktreeManager:
    """
    Manages git worktrees for parallel subagent development.
    Worktrees are created as siblings of the main repo directory.
    """

    def __init__(self, repo_root: str | None = None):
        self.repo_root = Path(repo_root or _find_repo_root())
        self.worktrees_parent = self.repo_root.parent / "agentkit-worktrees"

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        feature_name: str,
        base_branch: str = "main",
        copy_agentkit_config: bool = True,
    ) -> Worktree:
        """
        Create a new worktree for a feature branch.
        Returns the Worktree descriptor.
        """
        slug   = _slug(feature_name)
        branch = f"feature/{slug}"
        wt_path = self.worktrees_parent / slug

        if wt_path.exists():
            raise FileExistsError(f"Worktree already exists: {wt_path}")

        self.worktrees_parent.mkdir(parents=True, exist_ok=True)

        # Create the worktree + branch
        _run(
            ["git", "worktree", "add", str(wt_path), "-b", branch, base_branch],
            cwd=str(self.repo_root),
        )

        # Copy .agentkit config so the subagent inherits gates + state
        if copy_agentkit_config:
            src = self.repo_root / ".agentkit"
            dst = wt_path / ".agentkit"
            if src.exists():
                shutil.copytree(str(src), str(dst), dirs_exist_ok=True)

        return Worktree(path=str(wt_path), branch=branch)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def list_active(self) -> list[Worktree]:
        """Return all current worktrees (including main)."""
        result = _run(
            ["git", "worktree", "list", "--porcelain"],
            cwd=str(self.repo_root),
            check=False,
        )
        if result.returncode != 0:
            return []

        worktrees: list[Worktree] = []
        current: dict[str, str] = {}

        for line in result.stdout.splitlines():
            if line.startswith("worktree "):
                if current:
                    worktrees.append(_parse_wt_block(current))
                current = {"worktree": line[len("worktree "):]}
            elif line.startswith("HEAD "):
                current["HEAD"] = line[5:]
            elif line.startswith("branch "):
                current["branch"] = line[7:].replace("refs/heads/", "")
            elif line == "bare":
                current["bare"] = "true"

        if current:
            worktrees.append(_parse_wt_block(current))

        return worktrees

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------

    def merge(
        self,
        worktree: Worktree,
        strategy: str = "squash",
        target_branch: str = "main",
    ) -> None:
        """
        Merge a worktree's branch into target_branch, then remove the worktree.
        strategy: "squash" | "no-ff" | "ff"
        """
        merge_flags = {
            "squash": ["--squash"],
            "no-ff":  ["--no-ff"],
            "ff":     [],
        }.get(strategy, ["--squash"])

        _run(
            ["git", "merge"] + merge_flags + [worktree.branch],
            cwd=str(self.repo_root),
        )
        self.remove(worktree)

    # ------------------------------------------------------------------
    # Remove
    # ------------------------------------------------------------------

    def remove(self, worktree: Worktree, force: bool = False) -> None:
        """Remove the worktree directory and optionally delete its branch."""
        flags = ["--force"] if force else []
        _run(
            ["git", "worktree", "remove"] + flags + [worktree.path],
            cwd=str(self.repo_root),
            check=False,
        )
        # Delete the feature branch
        _run(
            ["git", "branch", "-d", worktree.branch],
            cwd=str(self.repo_root),
            check=False,
        )

    # ------------------------------------------------------------------
    # Status display
    # ------------------------------------------------------------------

    def status_text(self) -> str:
        wts = self.list_active()
        if not wts:
            return "No worktrees found."
        lines = []
        for wt in wts:
            label = "(main)" if wt.is_main else ""
            lines.append(f"  {wt.branch:40s}  {wt.path}  {label}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_wt_block(block: dict) -> Worktree:
    return Worktree(
        path=block.get("worktree", ""),
        branch=block.get("branch", "(detached)"),
        commit=block.get("HEAD", ""),
        is_main=block.get("branch", "") in ("main", "master"),
    )


def _find_repo_root(start: str | None = None) -> str:
    current = Path(start or os.getcwd())
    for _ in range(15):
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

    parser = argparse.ArgumentParser(description="AgentKit worktree manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_create = sub.add_parser("create", help="Create a worktree for a feature")
    p_create.add_argument("feature_name")
    p_create.add_argument("--base", default="main")

    p_merge = sub.add_parser("merge", help="Merge a feature worktree")
    p_merge.add_argument("branch", help="Feature branch name (e.g. feature/oauth2)")
    p_merge.add_argument("--strategy", choices=["squash", "no-ff", "ff"], default="squash")

    p_remove = sub.add_parser("remove", help="Remove a worktree without merging")
    p_remove.add_argument("branch")
    p_remove.add_argument("--force", action="store_true")

    sub.add_parser("list", help="List active worktrees")

    args = parser.parse_args()
    mgr  = WorktreeManager()

    if args.cmd == "create":
        try:
            wt = mgr.create(args.feature_name, base_branch=args.base)
            print(f"Created worktree: {wt.path}  (branch: {wt.branch})")
        except Exception as e:
            print(f"Error: {e}")
            raise SystemExit(1)

    elif args.cmd == "list":
        print(mgr.status_text())

    elif args.cmd == "merge":
        wts = [w for w in mgr.list_active() if w.branch == args.branch]
        if not wts:
            print(f"No worktree found for branch: {args.branch}")
            raise SystemExit(1)
        mgr.merge(wts[0], strategy=args.strategy)
        print(f"Merged {args.branch} → main (strategy: {args.strategy}). Worktree removed.")

    elif args.cmd == "remove":
        wts = [w for w in mgr.list_active() if w.branch == args.branch]
        if not wts:
            print(f"No worktree found for branch: {args.branch}")
            raise SystemExit(1)
        mgr.remove(wts[0], force=args.force)
        print(f"Removed worktree for {args.branch}.")
