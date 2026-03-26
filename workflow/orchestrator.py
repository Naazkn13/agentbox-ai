"""
AgentKit — Layer 4: Subagent Orchestrator
Defines subagent configs and builds minimal-context dispatch prompts.
Each subagent gets only what it needs — no full session context bleed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Subagent roster
# ---------------------------------------------------------------------------

MODEL_HAIKU  = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"
MODEL_OPUS   = "claude-opus-4-6"


@dataclass
class SubagentConfig:
    name: str
    model: str
    skills: list[str]
    max_tokens: int
    description: str
    fresh_context: bool = False        # True → no memory injection
    extended_thinking: int = 0         # >0 → enable extended thinking
    system_hint: str = ""


SUBAGENT_CONFIGS: dict[str, SubagentConfig] = {
    "writer": SubagentConfig(
        name="writer",
        model=MODEL_HAIKU,
        skills=["clean-code", "tdd-workflow"],
        max_tokens=4096,
        description="Standard implementation — write clean, tested code",
        system_hint="You are an implementation specialist. Write clean, focused code. Follow existing patterns.",
    ),
    "reviewer": SubagentConfig(
        name="reviewer",
        model=MODEL_SONNET,
        skills=["clean-code", "auth-jwt"],
        max_tokens=8192,
        description="Fresh-context code review — no inherited bias",
        fresh_context=True,
        system_hint=(
            "You are a code reviewer with no prior context about this codebase. "
            "Review critically: logic errors, security issues, missing edge cases, "
            "unclear naming, missing tests. Be specific about line numbers."
        ),
    ),
    "researcher": SubagentConfig(
        name="researcher",
        model=MODEL_HAIKU,
        skills=["llm-prompting"],
        max_tokens=2048,
        description="Find info, read docs, search codebase",
        system_hint="You are a researcher. Be thorough and concise. Return findings in structured bullet points.",
    ),
    "architect": SubagentConfig(
        name="architect",
        model=MODEL_OPUS,
        skills=["clean-code", "rest-api", "sql-query"],
        max_tokens=16384,
        description="Complex design decisions — Opus + extended thinking",
        extended_thinking=16000,
        system_hint=(
            "You are a software architect. Think deeply about trade-offs, scalability, "
            "and maintainability. Return a concrete design with rationale."
        ),
    ),
    "tester": SubagentConfig(
        name="tester",
        model=MODEL_HAIKU,
        skills=["tdd-workflow", "jest-testing"],
        max_tokens=4096,
        description="Write and run tests",
        system_hint="You are a testing specialist. Write comprehensive, readable tests. Prefer edge cases.",
    ),
    "security": SubagentConfig(
        name="security",
        model=MODEL_SONNET,
        skills=["auth-jwt"],
        max_tokens=8192,
        description="Security audit of changes before ship",
        fresh_context=True,
        system_hint=(
            "You are a security auditor. Check for: injection, auth bypass, IDOR, "
            "secrets exposure, missing validation, insecure defaults. "
            "Reference OWASP Top 10. Flag critical → high → medium → low."
        ),
    ),
}


# ---------------------------------------------------------------------------
# Dispatch result
# ---------------------------------------------------------------------------

@dataclass
class SubagentResult:
    agent_type: str
    success: bool
    output: str
    error: str = ""
    tokens_used: int = 0


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class SubagentOrchestrator:
    """
    Build dispatch prompts and (when the Anthropic SDK is available)
    call subagents directly via the API.
    """

    def __init__(self, memory_db_path: str | None = None):
        self.memory_db_path = memory_db_path

    def _build_context(
        self,
        config: SubagentConfig,
        task: str,
        files: list[str] | None = None,
        extra_context: str = "",
    ) -> str:
        """Build the full prompt for a subagent, injecting only what it needs."""
        parts: list[str] = []

        if config.system_hint:
            parts.append(f"## Role\n{config.system_hint}\n")

        # Memory injection (skip for fresh-context agents)
        if not config.fresh_context and self.memory_db_path:
            memory_ctx = self._get_memory_context(task)
            if memory_ctx:
                parts.append(f"## Relevant Context\n{memory_ctx}\n")

        # File contents
        if files:
            for fpath in files:
                content = self._read_file(fpath)
                if content:
                    parts.append(f"## File: {fpath}\n```\n{content[:3000]}\n```\n")

        if extra_context:
            parts.append(f"## Additional Context\n{extra_context}\n")

        parts.append(f"## Task\n{task}")
        return "\n".join(parts)

    def _get_memory_context(self, task: str, max_chars: int = 1000) -> str:
        """Pull relevant memory for the task (best-effort)."""
        if not self.memory_db_path:
            return ""
        try:
            import sys
            sys.path.insert(0, str(os.path.dirname(os.path.dirname(__file__))))
            from memory.injector import build_injection
            return build_injection(
                task_category="",
                current_files=[],
                prompt=task,
                db_path=self.memory_db_path,
                max_chars=max_chars,
            )
        except Exception:
            return ""

    def _read_file(self, path: str) -> str:
        try:
            with open(path) as f:
                return f.read()
        except Exception:
            return ""

    def build_dispatch_prompt(
        self,
        task: str,
        agent_type: str,
        files: list[str] | None = None,
        extra_context: str = "",
    ) -> tuple[SubagentConfig, str]:
        """
        Return (config, full_prompt) for a subagent dispatch.
        The caller passes this to Claude Code's Agent tool or API.
        """
        config = SUBAGENT_CONFIGS.get(agent_type)
        if not config:
            raise ValueError(f"Unknown agent type: {agent_type}. "
                             f"Available: {list(SUBAGENT_CONFIGS.keys())}")

        prompt = self._build_context(config, task, files, extra_context)
        return config, prompt

    def dispatch(
        self,
        task: str,
        agent_type: str,
        files: list[str] | None = None,
        extra_context: str = "",
    ) -> SubagentResult:
        """
        Dispatch a task to a subagent via the Anthropic API.
        Falls back to a stub if the SDK is not available.
        """
        config, prompt = self.build_dispatch_prompt(task, agent_type, files, extra_context)

        try:
            import anthropic
            client = anthropic.Anthropic()

            kwargs: dict = {
                "model":     config.model,
                "max_tokens": config.max_tokens,
                "messages": [{"role": "user", "content": prompt}],
            }
            if config.extended_thinking > 0:
                kwargs["thinking"] = {
                    "type":         "enabled",
                    "budget_tokens": config.extended_thinking,
                }

            msg = client.messages.create(**kwargs)
            text = msg.content[-1].text if msg.content else ""
            tokens = (msg.usage.input_tokens or 0) + (msg.usage.output_tokens or 0)
            return SubagentResult(
                agent_type=agent_type,
                success=True,
                output=text,
                tokens_used=tokens,
            )
        except ImportError:
            return SubagentResult(
                agent_type=agent_type,
                success=False,
                output="",
                error="anthropic SDK not installed — run: pip3 install anthropic",
            )
        except Exception as e:
            return SubagentResult(
                agent_type=agent_type,
                success=False,
                output="",
                error=str(e),
            )


# ---------------------------------------------------------------------------
# Orchestration patterns (convenience helpers)
# ---------------------------------------------------------------------------

def writer_reviewer_pattern(
    task: str,
    files: list[str],
    orchestrator: SubagentOrchestrator,
) -> dict[str, SubagentResult]:
    """Pattern A: Writer → Reviewer → Tester"""
    results: dict[str, SubagentResult] = {}

    results["writer"] = orchestrator.dispatch(
        task=f"Implement the following:\n{task}",
        agent_type="writer",
        files=files,
    )

    if results["writer"].success:
        results["reviewer"] = orchestrator.dispatch(
            task=(
                f"Review this implementation:\n\n{results['writer'].output}\n\n"
                f"Original requirement: {task}"
            ),
            agent_type="reviewer",
        )
        results["tester"] = orchestrator.dispatch(
            task=f"Write tests for:\n{task}\n\nImplementation:\n{results['writer'].output}",
            agent_type="tester",
            files=files,
        )

    return results


def parallel_research_pattern(
    research_topics: list[str],
    orchestrator: SubagentOrchestrator,
) -> list[SubagentResult]:
    """Pattern B: Parallel Research (sequential here — true parallel needs threads)."""
    return [
        orchestrator.dispatch(task=topic, agent_type="researcher")
        for topic in research_topics
    ]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import argparse

    parser = argparse.ArgumentParser(description="AgentKit subagent orchestrator")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list", help="List available subagent types")

    p_dispatch = sub.add_parser("dispatch", help="Dispatch a task to a subagent")
    p_dispatch.add_argument("agent_type")
    p_dispatch.add_argument("--task",    required=True)
    p_dispatch.add_argument("--files",   nargs="*", default=[])
    p_dispatch.add_argument("--dry-run", action="store_true",
                             help="Print the prompt without calling the API")

    p_prompt = sub.add_parser("prompt", help="Print dispatch prompt only")
    p_prompt.add_argument("agent_type")
    p_prompt.add_argument("--task", required=True)

    args = parser.parse_args()
    orch = SubagentOrchestrator()

    if args.cmd == "list":
        for name, cfg in SUBAGENT_CONFIGS.items():
            model_short = cfg.model.split("-")[1]
            print(f"  {name:12s}  {model_short:7s}  {cfg.description}")

    elif args.cmd == "dispatch":
        if args.dry_run:
            _, prompt = orch.build_dispatch_prompt(args.task, args.agent_type, args.files)
            print(prompt)
        else:
            result = orch.dispatch(args.task, args.agent_type, args.files)
            print(json.dumps({
                "success":     result.success,
                "agent_type":  result.agent_type,
                "output":      result.output[:500],
                "error":       result.error,
                "tokens_used": result.tokens_used,
            }, indent=2))

    elif args.cmd == "prompt":
        _, prompt = orch.build_dispatch_prompt(args.task, args.agent_type)
        print(prompt)
