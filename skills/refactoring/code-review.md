---
id: code-review
name: Code Review Expert
category: refactoring
level1: "For reviewing PRs — what to check, how to give constructive feedback, red flags to catch"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 2
---

<!-- LEVEL 1 START -->
**Code Review Expert** — Activate for: pull request reviews, PR feedback, code review checklists, reviewing diffs, security review, readability issues, spotting bugs in patches.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Code Review Expert — Core Instructions

1. **Check correctness first** — does the logic actually do what it claims? Trace edge cases: empty input, null/None, off-by-one, concurrent access.
2. **Scan for security red flags** — hardcoded secrets, SQL injection via string concatenation, missing auth checks, unvalidated user input, insecure deserialization.
3. **Evaluate performance at scale** — N+1 queries, unbounded loops over large datasets, missing indexes on filtered columns, unnecessary allocations in hot paths.
4. **Assess test coverage** — new behavior must have tests. Ask: is the happy path tested? Error paths? Edge cases? Are tests actually asserting the right thing?
5. **Give actionable feedback, not nitpicks** — every comment should say what to change and why. If it's a suggestion not a blocker, mark it `nit:` or `optional:`.
6. **Know when to block vs comment** — block (request changes) on security issues, correctness bugs, missing tests for critical paths, and PRs over 600 lines with no justification. Comment/suggest on style, naming, and minor improvements.
7. **Keep PR size in check** — PRs over 400 lines become hard to review thoroughly. Flag large PRs and ask the author to split by concern (feature + tests, or refactor + feature separately).
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Code Review Expert — Full Reference

### Review Checklist

**Correctness**
- Does the logic match the spec/ticket?
- Are all branches handled (if/else, switch exhaustiveness)?
- Off-by-one errors in loops and slice indices
- Integer overflow, division by zero, floating-point precision issues
- Concurrent access: shared state mutated without locks or atomic operations

**Security**
- Hardcoded credentials, API keys, or tokens (even in tests — they end up in git history)
- SQL built by string concatenation — must use parameterized queries
- Missing authentication or authorization checks on new endpoints
- Unvalidated or unsanitized user input passed to shell commands, file paths, or HTML output
- Deserialization of untrusted data (pickle, YAML, Java ObjectInputStream)
- Overly permissive CORS, missing CSRF protection on state-changing endpoints

**Performance**
- N+1 queries: a query inside a loop over a result set
- Missing `.select_related()` / `.prefetch_related()` in Django ORM
- Fetching full rows when only one column is needed
- Unbounded queries with no LIMIT on user-controlled inputs
- Creating large objects repeatedly in a tight loop

**Readability & Naming**
- Function and variable names describe what, not how
- Functions do one thing — if you can't describe it without "and", split it
- Magic numbers explained with named constants
- Comments explain why, not what the code already says

**Tests**
- Every new public function has at least one test
- Tests cover the error path, not just success
- Assertions are specific (`assertEqual(result, 42)` not `assertTrue(result)`)
- No tests that only test the mock — the real behavior must be exercised

### Feedback Tone Guide

```
# Blocker (request changes)
❌ Blocker: This SQL is built by string concatenation — SQL injection risk.
   Use parameterized queries: cursor.execute("SELECT * FROM users WHERE id = %s", [user_id])

# Suggestion (approve with comment)
nit: Variable name `d` → `document` would make this easier to scan.

# Question (not blocking, wants context)
optional: Could we use `dict.get()` here to avoid the KeyError on missing keys?
         Happy to merge as-is if there's a reason to keep the explicit access.
```

### Security Red Flags — Code Examples

```python
# BAD: hardcoded secret
API_KEY = "sk-prod-abc123xyz"  # visible in git history forever

# BAD: SQL injection
query = f"SELECT * FROM users WHERE name = '{user_input}'"

# GOOD: parameterized
cursor.execute("SELECT * FROM users WHERE name = %s", [user_input])

# BAD: missing auth check
@app.route("/admin/delete-user", methods=["POST"])
def delete_user():
    db.delete(request.json["user_id"])  # no check that caller is an admin

# GOOD
@app.route("/admin/delete-user", methods=["POST"])
@require_role("admin")
def delete_user():
    db.delete(request.json["user_id"])
```

### N+1 Query Pattern

```python
# BAD: N+1 — one query per post to fetch its author
posts = Post.objects.all()
for post in posts:
    print(post.author.name)  # hits DB on every iteration

# GOOD: 2 queries total
posts = Post.objects.select_related("author").all()
for post in posts:
    print(post.author.name)
```

### PR Size Best Practices

| Lines changed | Guidance |
|---|---|
| < 200 | Ideal — easy to review in one sitting |
| 200–400 | Acceptable — request clear description and test coverage |
| 400–600 | Ask to split if possible |
| > 600 | Strong recommendation to split; correctness review is unreliable at this size |

Split strategies: (1) refactor in one PR, behavior change in another; (2) data model PR, then API PR, then UI PR; (3) feature behind a flag merged incrementally.

### What to Block On vs. What to Suggest

| Category | Block | Suggest/Comment |
|---|---|---|
| Security | Injection, missing auth, hardcoded secrets | Overly verbose sanitization |
| Correctness | Logic bug, unhandled exception path | Minor edge case with low impact |
| Tests | Zero tests for new critical path | Could add one more edge case |
| PR size | > 600 lines, no justification | 400–600 lines with good description |
| Style | — | Naming, comment clarity, formatting |

### Anti-patterns to Avoid
- Leaving comments like "this is wrong" with no explanation of what correct looks like
- Blocking on personal style preferences (tabs vs spaces) if a linter already enforces it
- Approving large PRs without actually reading them — a rubber-stamp approval is worse than none
- Piling on 40 nits in one review — batch minor style comments into one summary note
- Reviewing without running the code or reading the tests
<!-- LEVEL 3 END -->
