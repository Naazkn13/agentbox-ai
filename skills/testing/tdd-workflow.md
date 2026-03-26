---
id: tdd-workflow
name: TDD Workflow
category: writing-tests
level1: "For test-driven development — write tests before implementation"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**TDD Workflow** — Activate for: test-driven development, red-green-refactor, writing tests before code, coverage improvement.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## TDD Workflow — Core Instructions

1. **Red first:** write a failing test that describes the behaviour you want. Run it — confirm it fails for the right reason.
2. **Green minimal:** write the *simplest possible* code that makes the test pass. No extras.
3. **Refactor:** now clean up the implementation. Tests stay green throughout.
4. **One behaviour per test.** A test with multiple unrelated assertions is a hidden integration test.
5. **Name tests as sentences:** `it('returns 401 when token is expired')` not `it('works')`.
6. **Test behaviour, not implementation.** Don't test private methods or internal state — test outputs and side effects.
7. **Arrange-Act-Assert (AAA):** structure every test clearly with setup, the action, and the assertion.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## TDD Workflow — Full Reference

### The Cycle
```
Write failing test → confirm it fails → write minimal code → confirm it passes → refactor → repeat
```

### Test Anatomy (AAA Pattern)
```python
def test_user_login_returns_token_on_valid_credentials():
    # Arrange
    user = create_user(email="a@b.com", password="secret")

    # Act
    result = login(email="a@b.com", password="secret")

    # Assert
    assert result["token"] is not None
    assert result["user"]["email"] == "a@b.com"
```

### What Makes a Good Test
- **Fast:** should run in milliseconds. Slow tests don't get run.
- **Isolated:** no shared state between tests. Each test sets up its own data.
- **Deterministic:** same result every time. No random data, no time-dependent logic without mocking.
- **Readable:** a failing test should tell you exactly what broke and why.

### What NOT to Test
- Implementation details (private methods, internal state)
- Third-party library behaviour (that's their job to test)
- Trivial getters/setters with zero logic

### Coverage Strategy
- Aim for 100% on business logic, ~80% overall
- Prioritise: edge cases > happy path > error paths
- Untested code is code you can't safely refactor

### Mocking Guidelines
- Mock at the boundary (HTTP calls, DB, filesystem) — not in the middle of business logic
- Prefer real objects over mocks where the real object is fast and deterministic
- If mocking is painful, the design is wrong — consider refactoring for testability
<!-- LEVEL 3 END -->
