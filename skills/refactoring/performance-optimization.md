---
id: performance-optimization
name: Performance Optimization Expert
category: refactoring
level1: "For profiling, N+1 queries, caching, algorithmic complexity, lazy loading, database indexing, bundle size, and memory leaks"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Performance Optimization Expert** — Activate for: slow queries, N+1 problems, caching strategies, big-O complexity improvements, lazy loading, database indexing, frontend bundle size reduction, and memory leak diagnosis.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Performance Optimization — Core Instructions

1. **Profile before optimizing** — measure with real data using profilers (py-spy, Node --prof, Chrome DevTools) before changing any code; never guess bottlenecks.
2. **Eliminate N+1 queries first** — use eager loading (`include`/`joinedload`), `DataLoader` batching in GraphQL, or a single JOIN query instead of looping DB calls.
3. **Cache at the right layer** — cache expensive queries in Redis with appropriate TTL; use HTTP Cache-Control headers for public data; memoize pure functions in-process.
4. **Reduce algorithmic complexity** — replace O(n²) nested loops with hash-map lookups O(1); sort once then binary-search instead of repeated linear scans.
5. **Add database indexes on filtered/sorted columns** — use `EXPLAIN ANALYZE` to confirm index usage; composite indexes must match query column order.
6. **Lazy-load and code-split on the frontend** — dynamic `import()` for routes; defer non-critical scripts; use `loading="lazy"` on images.
7. **Find memory leaks** — look for growing caches without eviction, event listeners never removed, closures holding large objects; use heap snapshots in DevTools.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Performance Optimization — Full Reference

### N+1 Query Detection and Fix (Prisma)
```typescript
// PROBLEM — N+1: 1 query for posts + N queries for authors
const posts = await prisma.post.findMany();
for (const post of posts) {
  const author = await prisma.user.findUnique({ where: { id: post.authorId } });
  console.log(author.name);
}

// FIX — single query with include
const posts = await prisma.post.findMany({
  include: { author: true },   // JOIN in one round-trip
});
```

### DataLoader Batching (GraphQL / Node)
```typescript
import DataLoader from 'dataloader';

const userLoader = new DataLoader<string, User>(async (ids) => {
  const users = await prisma.user.findMany({
    where: { id: { in: ids as string[] } },
  });
  // Return in same order as ids
  const map = new Map(users.map(u => [u.id, u]));
  return ids.map(id => map.get(id) ?? new Error(`User ${id} not found`));
});

// In resolver — automatically batched
const author = await userLoader.load(post.authorId);
```

### Redis Caching Pattern
```typescript
import { createClient } from 'redis';
const redis = createClient();

async function getCachedUser(userId: string): Promise<User> {
  const cacheKey = `user:${userId}`;
  const cached = await redis.get(cacheKey);
  if (cached) return JSON.parse(cached);

  const user = await db.users.findById(userId);
  await redis.setEx(cacheKey, 300, JSON.stringify(user)); // TTL 5min
  return user;
}

// Invalidate on update
async function updateUser(userId: string, data: Partial<User>) {
  await db.users.update(userId, data);
  await redis.del(`user:${userId}`);  // bust cache
}
```

### O(n²) to O(n) Refactor
```python
# SLOW — O(n²) nested loop
def find_duplicates_slow(items: list[str]) -> list[str]:
    duplicates = []
    for i, item in enumerate(items):
        for j, other in enumerate(items):
            if i != j and item == other and item not in duplicates:
                duplicates.append(item)
    return duplicates

# FAST — O(n) with Counter
from collections import Counter

def find_duplicates_fast(items: list[str]) -> list[str]:
    counts = Counter(items)
    return [item for item, count in counts.items() if count > 1]
```

### Database Index Strategy
```sql
-- Check query plan before adding index
EXPLAIN ANALYZE
SELECT * FROM orders WHERE user_id = 42 AND status = 'pending'
ORDER BY created_at DESC;

-- Composite index — column order matters: equality first, then range/sort
CREATE INDEX CONCURRENTLY idx_orders_user_status_created
  ON orders (user_id, status, created_at DESC);

-- Partial index for common filtered subset
CREATE INDEX CONCURRENTLY idx_orders_pending
  ON orders (user_id, created_at DESC)
  WHERE status = 'pending';
```

### Frontend Bundle Size
```javascript
// vite.config.ts — manual code splitting
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          charts: ['recharts'],
          utils: ['date-fns', 'lodash-es'],
        },
      },
    },
  },
});

// Dynamic import for route-level splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Settings  = lazy(() => import('./pages/Settings'));
```

### Memory Leak — Event Listener Cleanup
```typescript
// LEAK — listener added on every render, never removed
useEffect(() => {
  window.addEventListener('resize', handleResize);
});  // missing dependency array AND missing cleanup

// FIXED
useEffect(() => {
  window.addEventListener('resize', handleResize);
  return () => window.removeEventListener('resize', handleResize);
}, []);  // runs once, cleanup on unmount
```

### Anti-patterns to Avoid
- Optimizing without profiling — fix the actual bottleneck, not what seems slow
- Caching mutable data without invalidation (stale reads)
- Adding indexes to every column — write amplification, excessive disk use
- Using `SELECT *` when only 2 columns are needed
- Loading entire datasets into memory to filter in application code
- `bundle.js` over 500 KB unparsed — always analyze with `vite-bundle-visualizer` or `webpack-bundle-analyzer`
- Ignoring database connection pool exhaustion (symptom: requests queue up under load)
<!-- LEVEL 3 END -->
