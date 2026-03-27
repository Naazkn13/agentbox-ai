#!/usr/bin/env python3
"""Create 15 good-first-issue GitHub issues for AgentKit v0.5.0 skill contributions."""
import json, os, urllib.request, urllib.error

REPO  = "Ajaysable123/AgentKit"
TOKEN = os.environ["GITHUB_TOKEN"]
API   = f"https://api.github.com/repos/{REPO}/issues"

TEMPLATE = (
    "Add the SKILL.md file following the "
    "[SKILL.md format spec](https://github.com/Ajaysable123/AgentKit/blob/main/platform/spec.md). "
    "The file needs:\n"
    "- Frontmatter (id, name, category, level1, platforms, keywords)\n"
    "- `<!-- LEVEL 1 START/END -->` — one-line activation trigger (~45 tokens)\n"
    "- `<!-- LEVEL 2 START/END -->` — 7 core rules (~480 tokens)\n"
    "- `<!-- LEVEL 3 START/END -->` — full reference with real code examples (~2000 tokens)\n\n"
    "See [python-debugger.md](https://github.com/Ajaysable123/AgentKit/blob/main/skills/debugging/python-debugger.md) "
    "as a reference implementation.\n\n"
    "**Test:** `python3 -c \"from platform.adapter import load_skills; "
    "s=load_skills('skills'); print(len(s), 'skills')\"` should show 50+ skills.\n\n"
    "Also add the skill entry to `skills/registry.yaml` with correct `bundles` tags."
)

ISSUES = [
    ("skill: Add `rust-debugger` skill",
     "Borrow checker errors, lifetime annotations, cargo test debugging, LLDB/GDB with Rust, "
     "common panic messages (index out of bounds, unwrap on None), rustfmt/clippy integration.\n\n" + TEMPLATE),

    ("skill: Add `svelte-patterns` skill",
     "Svelte 4/5 component syntax, reactive declarations (`$:`), stores (readable/writable/derived), "
     "SvelteKit routing (+page.svelte / +layout.svelte / +server.ts), form actions, transitions/animations.\n\n" + TEMPLATE),

    ("skill: Add `typescript-advanced` skill",
     "Generics, conditional types, mapped types, template literal types, utility types "
     "(Partial/Required/Pick/Omit/ReturnType), discriminated unions, type guards, declaration files (.d.ts).\n\n" + TEMPLATE),

    ("skill: Add `python-async` skill",
     "asyncio event loop, async def/await, asyncio.gather/create_task, aiohttp, asyncpg, "
     "common pitfalls (blocking the event loop, missing await), asyncio debug mode, anyio.\n\n" + TEMPLATE),

    ("skill: Add `caching-strategies` skill",
     "Cache-aside vs write-through vs write-behind, CDN caching (Cache-Control headers, Cloudflare), "
     "browser caching, cache invalidation patterns, stale-while-revalidate, cache stampede prevention.\n\n" + TEMPLATE),

    ("skill: Add `message-queues` skill",
     "Kafka (topics/partitions/consumer groups), RabbitMQ (exchanges/queues/bindings), SQS, "
     "dead letter queues, idempotent consumers, at-least-once vs exactly-once delivery, backpressure.\n\n" + TEMPLATE),

    ("skill: Add `web-scraping` skill",
     "BeautifulSoup, Scrapy, Playwright for dynamic pages, robots.txt compliance, rate limiting, "
     "rotating proxies, XPath vs CSS selectors, handling pagination, storing scraped data.\n\n" + TEMPLATE),

    ("skill: Add `regex-patterns` skill",
     "Character classes, quantifiers, groups/lookahead/lookbehind, common patterns (email/URL/IP/phone), "
     "PCRE vs Python re vs JS regex, catastrophic backtracking, testing regex with regex101.\n\n" + TEMPLATE),

    ("skill: Add `git-workflow` skill",
     "Branching strategies (trunk-based, gitflow), Conventional Commits, interactive rebase, "
     "cherry-pick, bisect for bug hunting, pre-commit/pre-push hooks, merge vs rebase trade-offs.\n\n" + TEMPLATE),

    ("skill: Add `aws-serverless` skill",
     "Lambda function anatomy, API Gateway integration, SAM/CDK deployment, environment variables, "
     "cold starts, IAM roles for Lambda, DynamoDB from Lambda, SQS triggers, CloudWatch logs.\n\n" + TEMPLATE),

    ("skill: Add `stripe-payments` skill",
     "Checkout Sessions vs Payment Intents, webhook handling (HMAC signature verification), "
     "subscription management, refunds, idempotency keys, test mode cards, Stripe CLI for local webhook testing.\n\n" + TEMPLATE),

    ("skill: Add `websockets` skill",
     "WebSocket vs SSE vs long-polling, Socket.io rooms/namespaces, connection lifecycle, "
     "heartbeat/ping-pong, reconnection logic, scaling WebSockets (sticky sessions / Redis adapter), auth over WS.\n\n" + TEMPLATE),

    ("skill: Add `date-time-handling` skill",
     "UTC everywhere (never store local time), ISO 8601 format, timezone conversion pitfalls, "
     "daylight saving edge cases, dayjs/date-fns, Python datetime/pendulum, SQL timestamp types.\n\n" + TEMPLATE),

    ("skill: Add `error-handling-patterns` skill",
     "Custom exception hierarchies, React error boundaries, Result/Either types, "
     "structured error logging, user-facing vs internal errors, retry with exponential backoff, circuit breaker.\n\n" + TEMPLATE),

    ("skill: Add `data-modeling` skill",
     "Relational normalization (1NF-3NF), when to denormalize, ER diagrams, naming conventions, "
     "soft delete patterns, audit trails (created_at/updated_at/deleted_at), polymorphic associations, JSON columns.\n\n" + TEMPLATE),
]

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "Content-Type": "application/json",
}

for title, body in ISSUES:
    payload = json.dumps({"title": title, "body": body, "labels": ["good first issue", "skill"]}).encode()
    req = urllib.request.Request(API, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print(f"  ✓ #{data['number']}  {data['html_url']}")
    except urllib.error.HTTPError as e:
        print(f"  ✗ {title[:50]}  →  {e.code} {e.read().decode()[:100]}")
