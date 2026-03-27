#!/usr/bin/env bash
# Creates 15 "good first issue" GitHub issues for AgentKit v0.5.0 skill contributions
# Usage: GITHUB_TOKEN=<token> bash cli/create-issues.sh

REPO="Ajaysable123/AgentKit"
TOKEN="${GITHUB_TOKEN}"
API="https://api.github.com/repos/${REPO}/issues"

create_issue() {
  local title="$1"
  local body="$2"
  curl -s -X POST \
    -H "Authorization: token ${TOKEN}" \
    -H "Accept: application/vnd.github+json" \
    "${API}" \
    -d "{\"title\": ${title}, \"body\": ${body}, \"labels\": [\"good first issue\", \"skill\"]}" \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('html_url','error: '+str(d)))"
}

TEMPLATE='Add the SKILL.md file following the [SKILL.md format spec](https://github.com/Ajaysable123/AgentKit/blob/main/platform/spec.md). The file needs:\n- Frontmatter (id, name, category, level1, platforms, keywords)\n- `<!-- LEVEL 1 START/END -->` — one-line activation trigger (~45 tokens)\n- `<!-- LEVEL 2 START/END -->` — 7 core rules (~480 tokens)\n- `<!-- LEVEL 3 START/END -->` — full reference with code examples (~2000 tokens)\n\nSee [python-debugger.md](https://github.com/Ajaysable123/AgentKit/blob/main/skills/debugging/python-debugger.md) as a reference implementation.\n\n**Test your skill:** `python3 -c \"from platform.adapter import load_skills; skills = load_skills('"'"'skills'"'"'); print(len(skills), '"'"'skills loaded'"'"')\"` should show 50+ skills.\n\nAdd the skill to `skills/registry.yaml` with correct bundle tags.'

echo "Creating 15 good first issues..."

create_issue '"skill: Add \`rust-debugger\` skill"' \
  "\"Add a Rust debugger skill covering: borrow checker errors, lifetime annotations, cargo test debugging, LLDB/GDB with Rust, common panic messages, rustfmt/clippy integration.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`svelte-patterns\` skill"' \
  "\"Add a Svelte patterns skill covering: Svelte 4/5 component syntax, reactive declarations (\\\`\$:\\\`), stores (readable/writable/derived), SvelteKit routing, +page.svelte, +layout.svelte, form actions, transitions.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`typescript-advanced\` skill"' \
  "\"Add an advanced TypeScript skill covering: generics, conditional types, mapped types, template literal types, utility types (Partial/Required/Pick/Omit/ReturnType), discriminated unions, type guards, declaration files.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`python-async\` skill"' \
  "\"Add a Python async/await skill covering: asyncio event loop, async def/await, asyncio.gather/create_task, aiohttp, asyncpg, common pitfalls (blocking the event loop, missing await), debugging with asyncio debug mode.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`caching-strategies\` skill"' \
  "\"Add a caching strategies skill covering: cache-aside vs write-through vs write-behind, CDN caching (Cache-Control headers, Cloudflare), browser caching, cache invalidation patterns, stale-while-revalidate, cache stampede prevention.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`message-queues\` skill"' \
  "\"Add a message queues skill covering: Kafka (topics/partitions/consumer groups), RabbitMQ (exchanges/queues/bindings), SQS, dead letter queues, idempotent consumers, at-least-once vs exactly-once delivery, backpressure.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`web-scraping\` skill"' \
  "\"Add a web scraping skill covering: BeautifulSoup, Scrapy, Playwright for dynamic pages, robots.txt compliance, rate limiting, rotating proxies, XPath vs CSS selectors, handling pagination, storing scraped data.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`regex-patterns\` skill"' \
  "\"Add a regex patterns skill covering: character classes, quantifiers, groups/lookahead/lookbehind, common patterns (email/URL/IP/phone), PCRE vs Python re vs JS regex differences, performance pitfalls (catastrophic backtracking), testing regex.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`git-workflow\` skill"' \
  "\"Add a git workflow skill covering: branching strategies (trunk-based, gitflow), commit message conventions (Conventional Commits), interactive rebase, cherry-pick, bisect for bug hunting, hooks (pre-commit/pre-push), merge vs rebase.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`aws-serverless\` skill"' \
  "\"Add an AWS serverless skill covering: Lambda function anatomy, API Gateway integration, SAM/CDK deployment, environment variables, cold starts, IAM roles for Lambda, DynamoDB from Lambda, SQS triggers, CloudWatch logs.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`stripe-payments\` skill"' \
  "\"Add a Stripe payments skill covering: Checkout Sessions vs Payment Intents, webhook handling (signature verification), subscription management, refunds, idempotency keys, test mode cards, Stripe CLI for local webhook testing.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`websockets\` skill"' \
  "\"Add a WebSocket skill covering: WebSocket vs SSE vs long-polling, Socket.io rooms/namespaces, connection lifecycle, heartbeat/ping-pong, reconnection logic, scaling WebSockets (sticky sessions / Redis adapter), auth over WS.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`date-time-handling\` skill"' \
  "\"Add a date/time handling skill covering: UTC everywhere (never store local time), ISO 8601 format, timezone conversion pitfalls, daylight saving, date libraries (dayjs/date-fns vs Moment.js), Python datetime/pendulum, SQL timestamp types.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`error-handling-patterns\` skill"' \
  "\"Add an error handling patterns skill covering: custom exception hierarchies, error boundaries (React), Result/Either types, never swallow errors, structured error logging, user-facing vs internal errors, retry with exponential backoff, circuit breaker.\\n\\n${TEMPLATE}\""

create_issue '"skill: Add \`data-modeling\` skill"' \
  "\"Add a data modeling skill covering: relational normalization (1NF-3NF), when to denormalize, entity-relationship diagrams, naming conventions, soft delete patterns, audit trails (created_at/updated_at/deleted_at), polymorphic associations, JSON columns.\\n\\n${TEMPLATE}\""

echo ""
echo "Done! Check https://github.com/${REPO}/issues"
