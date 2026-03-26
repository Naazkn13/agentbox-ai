---
id: debugging-js
name: JavaScript / TypeScript Debugger
category: debugging
level1: "For JavaScript and TypeScript errors, undefined, NaN, and runtime failures"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**JS/TS Debugger** — Activate for: JavaScript/TypeScript errors, `undefined`, `cannot read properties`, `is not a function`, NaN, Promise rejections, type errors.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## JS/TS Debugger — Core Instructions

1. **Check for `undefined` before accessing properties.** Use optional chaining: `obj?.prop`.
2. **`console.log` with labels**, not bare values — `console.log('user:', user)` not `console.log(user)`.
3. **For async bugs:** check that every `async` function is `await`ed. Unhandled Promise rejections are silent killers.
4. **TypeScript errors:** read the full error message — the type mismatch line tells you exactly what's wrong.
5. **`NaN` propagates silently.** Add `Number.isNaN(val)` checks after any numeric parsing.
6. **Scope issues:** `var` leaks from blocks, `let`/`const` don't. Prefer `const` always.
7. **`this` context:** arrow functions capture `this` lexically; regular functions don't. In callbacks, use arrow functions or `.bind(this)`.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## JS/TS Debugger — Full Reference

### Common Error Patterns

**TypeError: Cannot read properties of undefined (reading 'X')**
- The object before `.X` is `undefined`
- Trace back: what function/API returned this? Add `console.log` before the failing line
- Fix: optional chaining `obj?.prop` or early return guard `if (!obj) return`

**TypeError: X is not a function**
- You're calling something that isn't a function
- Common causes: misspelled method name, wrong import, calling a value instead of a function
- Check: `console.log(typeof myFn)` — if not `"function"`, trace why

**Unhandled Promise Rejection**
- An async operation threw but nobody caught it
- Fix: add `.catch()` to every promise chain; or `try/catch` inside `async` functions
- Never: `async function foo() { riskyOp() }` — must await it

**NaN arithmetic**
- `parseInt("abc")` → NaN, NaN + anything → NaN
- Fix: always validate numeric inputs: `const n = Number(str); if (Number.isNaN(n)) throw new Error(...)`

**Infinite re-render (React)**
- A `useEffect` with a dependency that changes every render (e.g., an object literal `{}`)
- Fix: memoize with `useMemo`, or move the dependency outside the component

### Debugging Tools

```javascript
// Structured console output
console.table(arrayOfObjects)          // pretty-print arrays
console.dir(obj, { depth: null })      // full object tree
console.trace('label')                 // print call stack

// Debugger statement (works in Node + browser DevTools)
debugger;  // pauses execution when DevTools is open

// Type narrowing in TypeScript
if (typeof val === 'string') { /* val is string here */ }
if (val instanceof Error)    { /* val is Error here */ }
if ('id' in obj)             { /* obj has id property */ }

// Async stack traces (Node.js)
// Run with: NODE_OPTIONS=--async-context-frame-limit=100
```

### Anti-patterns
- `console.log(obj)` without a label — you won't know which log it is
- Swallowing Promise rejections with empty `.catch(() => {})`
- Using `==` instead of `===` — causes implicit coercion bugs
- Not `await`ing async functions in sequence-dependent code
<!-- LEVEL 3 END -->
