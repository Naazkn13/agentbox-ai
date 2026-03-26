---
id: jest-testing
name: Jest / Vitest Testing
category: writing-tests
level1: "For Jest and Vitest test files — mocking, spies, async tests, snapshots"
platforms: [claude-code, cursor, codex]
priority: 1
---

<!-- LEVEL 1 START -->
**Jest/Vitest Expert** — Activate for: Jest or Vitest test files, `describe`/`it`/`expect`, mocking modules, spies, async tests, snapshot testing.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Jest/Vitest — Core Instructions

1. **Mock modules at the top of the file** with `jest.mock('./module')` before imports are resolved.
2. **Use `beforeEach` to reset mocks:** `beforeEach(() => jest.clearAllMocks())` — prevents test pollution.
3. **Async tests:** always `await` or return the promise. A test that doesn't await will always pass even if it throws.
4. **`expect.assertions(N)`** in async tests to ensure your assertions actually ran.
5. **Spy on methods** with `jest.spyOn(obj, 'method')` — restores original after test if you call `.mockRestore()`.
6. **Snapshot tests:** good for UI output; bad for business logic. Don't snapshot objects with random/time-based fields.
7. **`--watch` mode during development:** run `jest --watch` or `vitest --watch` for instant feedback.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Jest/Vitest — Full Reference

### Mocking Patterns

```typescript
// Mock an entire module
jest.mock('../services/emailService', () => ({
  sendEmail: jest.fn().mockResolvedValue({ success: true }),
}));

// Mock only one method (spyOn)
const sendSpy = jest.spyOn(emailService, 'sendEmail').mockResolvedValue({ success: true });
afterEach(() => sendSpy.mockRestore());

// Mock a return value per test
mockFn.mockReturnValueOnce('first call').mockReturnValueOnce('second call');

// Mock implementation
mockFn.mockImplementation((arg) => arg * 2);
```

### Async Test Patterns

```typescript
// Always await
it('fetches user', async () => {
  const user = await getUser(1);
  expect(user.id).toBe(1);
});

// Ensure assertions ran (async guard)
it('calls callback on error', async () => {
  expect.assertions(1);
  await expect(riskyOp()).rejects.toThrow('expected error');
});

// Fake timers for setTimeout / setInterval
jest.useFakeTimers();
setTimeout(() => callback(), 1000);
jest.runAllTimers();
expect(callback).toHaveBeenCalled();
jest.useRealTimers();
```

### Common Matchers

```typescript
expect(val).toBe(exact)           // strict equality (===)
expect(val).toEqual(obj)          // deep equality
expect(val).toMatchObject(subset) // partial object match
expect(fn).toHaveBeenCalledWith(arg1, arg2)
expect(fn).toHaveBeenCalledTimes(2)
expect(promise).resolves.toBe(val)
expect(promise).rejects.toThrow('message')
expect(arr).toContain(item)
expect(str).toMatch(/regex/)
```

### Vitest-specific (same API, faster)
```typescript
import { vi } from 'vitest'
vi.mock('../module')     // same as jest.mock
vi.spyOn(obj, 'method')  // same as jest.spyOn
vi.useFakeTimers()
```
<!-- LEVEL 3 END -->
