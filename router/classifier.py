"""
AgentKit — Layer 1: Task Classifier
3-tier classification: keyword matching → heuristic scoring → Haiku fallback.

Tier 1: Regex keyword matching   — covers ~70% of prompts, < 5ms
Tier 2: Weighted heuristic score — covers ~20% of prompts, < 10ms
Tier 3: Haiku LLM fallback       — covers ~10% of prompts, ~50ms, ~$0.0003
"""

import re
import os
import json
from router.models import ClassificationResult

# ---------------------------------------------------------------------------
# Category keyword lists
# ---------------------------------------------------------------------------

CATEGORIES: dict[str, list[str]] = {
    "debugging": [
        "bug", "error", "exception", "crash", "fix", "broken", "failing",
        "traceback", "undefined", "null", "not working", "doesn't work",
        "why is", "what's wrong", "stack trace", "stacktrace", "segfault",
        "TypeError", "AttributeError", "KeyError", "ValueError", "NameError",
        "ImportError", "RuntimeError", "SyntaxError", "NullPointerException",
    ],
    "writing-tests": [
        "test", "spec", "coverage", "tdd", "jest", "pytest", "vitest",
        "unit test", "integration test", "mock", "stub", "assert", "expect",
        "describe", "it(", "beforeEach", "afterEach", "fixture", "snapshot",
        "e2e", "end-to-end", "cypress", "playwright", "testing library",
    ],
    "designing-ui": [
        "ui", "ux", "design", "component", "layout", "style", "css",
        "figma", "responsive", "animation", "tailwind", "styled-components",
        "flexbox", "grid", "typography", "color", "theme", "dark mode",
        "mobile", "accessibility", "a11y", "aria", "screen reader",
        "button", "form", "modal", "dropdown", "sidebar", "navbar",
    ],
    "deploying": [
        "deploy", "ci", "cd", "docker", "k8s", "kubernetes", "pipeline",
        "build", "release", "helm", "terraform", "ansible", "nginx",
        "github actions", "gitlab ci", "circleci", "jenkins", "vercel",
        "netlify", "aws", "gcp", "azure", "heroku", "railway", "fly.io",
        "container", "image", "registry", "pod", "ingress", "service mesh",
    ],
    "reviewing-pr": [
        "review", "pr ", "pull request", "diff", "code review", "feedback",
        "approve", "merge", "lgtm", "nitpick", "suggestion", "comment",
        "change request", "cr ", "code quality", "readability",
    ],
    "architecting": [
        "architect", "design system", "scalab", "pattern", "structure",
        "microservice", "ddd", "cqrs", "event sourcing", "hexagonal",
        "how should we", "best approach", "trade-off", "pros and cons",
        "monolith", "modular", "domain", "bounded context", "aggregate",
        "solid", "clean architecture", "layered", "mvc", "mvvm",
    ],
    "writing-docs": [
        "document", "readme", "jsdoc", "docstring", "api docs", "swagger",
        "openapi", "wiki", "changelog", "contributing", "comment", "explain",
        "what does this", "how does this work", "describe", "annotate",
    ],
    "db-work": [
        "database", "sql", "query", "migration", "schema", "orm",
        "postgres", "postgresql", "mysql", "sqlite", "mongodb", "redis",
        "prisma", "sequelize", "typeorm", "drizzle", "knex",
        "index", "foreign key", "join", "transaction", "aggregate",
        "select", "insert", "update", "delete", "upsert",
    ],
    "api-work": [
        "api", "endpoint", "rest", "graphql", "route", "http",
        "request", "response", "webhook", "payload", "status code",
        "get ", "post ", "put ", "patch ", "delete ",
        "fetch", "axios", "trpc", "grpc", "openapi", "postman",
        "authentication", "authorization", "cors", "rate limit",
    ],
    "refactoring": [
        "refactor", "clean up", "improve", "restructure", "simplify",
        "dry ", "don't repeat", "extract", "rename", "move",
        "technical debt", "code smell", "duplicate", "reuse",
        "too long", "hard to read", "messy", "spaghetti",
    ],
    "security": [
        "security", "auth", "jwt", "oauth", "xss", "injection",
        "vuln", "cve", "pentest", "audit", "sanitize", "validate",
        "csrf", "sql injection", "password", "hash", "encrypt",
        "secret", "token", "permission", "rbac", "acl", "firewall",
    ],
    "performance": [
        "performance", "slow", "latency", "optimize", "profil",
        "memory leak", "benchmark", "load test", "bottleneck",
        "cache", "memoize", "lazy load", "bundle size", "lighthouse",
        "n+1", "query optimization", "cdn", "compress", "minify",
    ],
    "ai-engineering": [
        "llm", "prompt", "embedding", "rag", "agent", "fine-tun",
        "eval", "claude", "openai", "gpt", "anthropic", "langchain",
        "vector", "semantic search", "context window", "token",
        "system prompt", "few-shot", "chain of thought", "tool use",
        "mcp", "function calling", "structured output",
    ],
}

# Weights: some keywords are stronger signals than others
STRONG_KEYWORDS: dict[str, float] = {
    "traceback": 2.0, "pytest": 2.0, "jest ": 2.0, "docker": 2.0,
    "kubernetes": 2.0, "graphql": 2.0, "prisma": 2.0, "jwt": 2.0,
    "llm": 2.0, "embedding": 2.0, "refactor": 1.8, "migration": 1.8,
    "pull request": 1.8, "architect": 1.8, "deploy": 1.5,
}

CONFIDENCE_FLOOR = 0.6  # below this → Haiku fallback


# ---------------------------------------------------------------------------
# Tier 1: Keyword matching
# ---------------------------------------------------------------------------

def _keyword_score(text: str) -> dict[str, float]:
    """Score each category based on keyword presence in text."""
    text_lower = text.lower()
    scores: dict[str, float] = {}

    for category, keywords in CATEGORIES.items():
        score = 0.0
        matched = []
        for kw in keywords:
            if kw.lower() in text_lower:
                weight = STRONG_KEYWORDS.get(kw.lower(), 1.0)
                score += weight
                matched.append(kw)
        if score > 0:
            scores[category] = score

    return scores


# ---------------------------------------------------------------------------
# Tier 2: Context heuristics (file extensions, branch names)
# ---------------------------------------------------------------------------

FILE_EXT_HINTS: dict[str, list[str]] = {
    ".test.ts": ["writing-tests"], ".test.js": ["writing-tests"],
    ".spec.ts": ["writing-tests"], ".spec.js": ["writing-tests"],
    ".test.py": ["writing-tests"],
    ".css": ["designing-ui"], ".scss": ["designing-ui"],
    ".tsx": ["designing-ui"], ".jsx": ["designing-ui"],
    "Dockerfile": ["deploying"], "docker-compose": ["deploying"],
    ".github/workflows": ["deploying"],
    "migration": ["db-work"], "schema.prisma": ["db-work"],
    "route": ["api-work"], "controller": ["api-work"],
    "README": ["writing-docs"],
}

BRANCH_HINTS: dict[str, list[str]] = {
    "fix/": ["debugging"], "bug/": ["debugging"],
    "test/": ["writing-tests"], "feat/": ["api-work"],
    "refactor/": ["refactoring"], "perf/": ["performance"],
    "docs/": ["writing-docs"], "deploy/": ["deploying"],
    "security/": ["security"], "auth/": ["security"],
    "db/": ["db-work"], "ui/": ["designing-ui"],
}


def _context_hints(files: list[str], branch: str) -> dict[str, float]:
    """Extra score signals from file names and git branch."""
    hints: dict[str, float] = {}

    for f in files:
        for pattern, categories in FILE_EXT_HINTS.items():
            if pattern in f:
                for cat in categories:
                    hints[cat] = hints.get(cat, 0.0) + 1.5

    for prefix, categories in BRANCH_HINTS.items():
        if branch.startswith(prefix):
            for cat in categories:
                hints[cat] = hints.get(cat, 0.0) + 1.0

    return hints


# ---------------------------------------------------------------------------
# Tier 3: Haiku LLM fallback
# ---------------------------------------------------------------------------

HAIKU_CLASSIFY_PROMPT = """Classify this developer prompt into ONE primary category and optionally one secondary category.

Categories: debugging, writing-tests, designing-ui, deploying, reviewing-pr, architecting, writing-docs, db-work, api-work, refactoring, security, performance, ai-engineering

Prompt: {prompt}

Respond with JSON only, no explanation:
{{"primary": "<category>", "secondary": "<category or empty string>", "confidence": <0.0-1.0>}}"""


def _haiku_fallback(prompt: str) -> tuple[str, str, float]:
    """Call Haiku for ambiguous prompts. Returns (primary, secondary, confidence)."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[{"role": "user", "content": HAIKU_CLASSIFY_PROMPT.format(prompt=prompt[:500])}],
        )
        result = json.loads(response.content[0].text.strip())
        return result.get("primary", "api-work"), result.get("secondary", ""), float(result.get("confidence", 0.7))
    except Exception:
        return "api-work", "", 0.5  # safe default if API call fails


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def classify(
    prompt: str,
    files: list[str] | None = None,
    branch: str = "",
) -> ClassificationResult:
    """
    Classify a developer prompt into task categories.

    Args:
        prompt:  The user's natural language prompt.
        files:   List of currently modified/open file paths (optional).
        branch:  Current git branch name (optional).

    Returns:
        ClassificationResult with primary/secondary category + confidence.
    """
    files = files or []

    # --- Tier 1: keyword scoring ---
    scores = _keyword_score(prompt)

    # --- Tier 2: context hints ---
    hints = _context_hints(files, branch)
    for cat, bonus in hints.items():
        scores[cat] = scores.get(cat, 0.0) + bonus

    if not scores:
        # No signals at all → go straight to Haiku
        primary, secondary, confidence = _haiku_fallback(prompt)
        return ClassificationResult(
            primary_category=primary,
            secondary_category=secondary,
            confidence=confidence,
            matched_keywords=[],
            fallback_used=True,
        )

    # Sort categories by score descending
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_cat, top_score = ranked[0]
    second_cat = ranked[1][0] if len(ranked) > 1 else ""

    # Normalise confidence to 0–1 using softmax-style scaling
    total = sum(s for _, s in ranked)
    confidence = top_score / total if total > 0 else 0.0

    # Collect matched keywords for transparency
    matched = [kw for kw in CATEGORIES.get(top_cat, []) if kw.lower() in prompt.lower()]

    # --- Tier 3: Haiku fallback if confidence too low ---
    if confidence < CONFIDENCE_FLOOR:
        primary, secondary, haiku_conf = _haiku_fallback(prompt)
        return ClassificationResult(
            primary_category=primary,
            secondary_category=secondary,
            confidence=haiku_conf,
            matched_keywords=matched,
            fallback_used=True,
        )

    return ClassificationResult(
        primary_category=top_cat,
        secondary_category=second_cat if second_cat != top_cat else "",
        confidence=min(confidence, 1.0),
        matched_keywords=matched,
        fallback_used=False,
    )


# ---------------------------------------------------------------------------
# CLI entry point (used by shell hooks)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="AgentKit task classifier")
    parser.add_argument("--prompt", required=True, help="User prompt text")
    parser.add_argument("--files", default="", help="Comma-separated modified file paths")
    parser.add_argument("--branch", default="", help="Current git branch name")
    args = parser.parse_args()

    files = [f.strip() for f in args.files.split(",") if f.strip()]
    result = classify(args.prompt, files=files, branch=args.branch)

    print(json.dumps({
        "primary_category": result.primary_category,
        "secondary_category": result.secondary_category,
        "confidence": result.confidence,
        "matched_keywords": result.matched_keywords,
        "fallback_used": result.fallback_used,
    }))
