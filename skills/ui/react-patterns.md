---
id: react-patterns
name: React Patterns Expert
category: designing-ui
level1: "For React components, hooks, state management, and performance patterns"
platforms: [claude-code, cursor, codex]
priority: 1
---

<!-- LEVEL 1 START -->
**React Patterns Expert** — Activate for: React components, hooks (`useState`, `useEffect`, `useMemo`), props, context, performance, re-render issues.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## React Patterns — Core Instructions

1. **Lift state only as high as needed** — state that only one component needs should stay in that component.
2. **`useEffect` cleanup:** always return a cleanup function if you set up subscriptions, timers, or event listeners.
3. **Avoid inline object/array literals as props** — they create new references every render, causing child re-renders.
4. **`useMemo` for expensive calculations, `useCallback` for stable function references** passed to child components.
5. **Keys must be stable and unique** — never use array index as key if the list can reorder or filter.
6. **Don't derive state from props in `useState`** — use `useMemo` or compute directly in render.
7. **One source of truth:** if two components need the same data, lift it up or use context/state manager.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## React Patterns — Full Reference

### Hook Patterns
```tsx
// Correct useEffect with cleanup
useEffect(() => {
  const sub = eventEmitter.subscribe('event', handler);
  return () => sub.unsubscribe(); // cleanup on unmount
}, [handler]);

// Stable callback reference
const handleClick = useCallback((id: string) => {
  doSomething(id);
}, []); // empty deps = stable reference

// Expensive computation
const sortedItems = useMemo(
  () => items.slice().sort(compareFn),
  [items] // recomputes only when items changes
);
```

### Avoiding Re-renders
```tsx
// BAD: new object every render → child re-renders
<Child style={{ color: 'red' }} />

// GOOD: stable reference
const style = useMemo(() => ({ color: 'red' }), []);
<Child style={style} />

// Memo to skip re-render if props unchanged
const Child = React.memo(({ name }: { name: string }) => <div>{name}</div>);
```

### Context Pattern
```tsx
// 1. Create typed context
const UserContext = createContext<User | null>(null);

// 2. Custom hook with null guard
function useUser() {
  const user = useContext(UserContext);
  if (!user) throw new Error('useUser must be inside UserProvider');
  return user;
}

// 3. Provider at appropriate level (not always root)
<UserContext.Provider value={user}>
  <ProtectedRoutes />
</UserContext.Provider>
```

### Common Anti-patterns
- `useEffect` with no dependency array → runs every render (use `[]` if truly one-time)
- State that could be derived from props → use `useMemo` instead
- Fetching data in `useEffect` without abort controller → memory leaks on unmount
- Prop drilling >3 levels → use context or co-locate state lower
<!-- LEVEL 3 END -->
