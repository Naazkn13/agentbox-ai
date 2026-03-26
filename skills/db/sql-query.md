---
id: sql-query
name: SQL Query Expert
category: db-work
level1: "For SQL queries, indexes, joins, migrations, and query optimization"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**SQL Expert** — Activate for: SQL queries, JOIN, indexes, query optimization, migrations, schema design, N+1 detection, postgres/mysql/sqlite.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## SQL — Core Instructions

1. **Always add indexes** on foreign keys and columns used in WHERE/JOIN/ORDER BY clauses.
2. **Use EXPLAIN/EXPLAIN ANALYZE** before and after optimization to confirm improvement.
3. **SELECT only needed columns** — avoid `SELECT *` in production code.
4. **Parameterized queries always** — never string-interpolate user input into SQL.
5. **Transactions for multi-step writes** — if any step fails, the whole operation rolls back.
6. **N+1 detection:** if you're querying inside a loop, rewrite as a single JOIN or batch query.
7. **Migrations:** always write a `down` migration. Never drop a column without a transition period.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## SQL — Full Reference

### Index Strategy
```sql
-- Index foreign keys
CREATE INDEX idx_posts_user_id ON posts(user_id);

-- Composite index: order matters (most selective first)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);

-- Partial index for common filter
CREATE INDEX idx_active_users ON users(email) WHERE deleted_at IS NULL;

-- Check index usage
EXPLAIN ANALYZE SELECT * FROM posts WHERE user_id = 1;
```

### JOIN Patterns
```sql
-- INNER JOIN: only matching rows
SELECT u.name, p.title FROM users u
INNER JOIN posts p ON p.user_id = u.id;

-- LEFT JOIN: all users, even those with no posts
SELECT u.name, COUNT(p.id) as post_count FROM users u
LEFT JOIN posts p ON p.user_id = u.id
GROUP BY u.id;

-- Avoid N+1: batch fetch instead of loop queries
SELECT * FROM posts WHERE user_id IN (1, 2, 3, 4, 5);
```

### Safe Migrations
```sql
-- Step 1: Add nullable column (safe, no lock)
ALTER TABLE users ADD COLUMN phone VARCHAR(20);

-- Step 2: Backfill data in batches (not all at once)
UPDATE users SET phone = '000' WHERE phone IS NULL LIMIT 1000;

-- Step 3: Add NOT NULL constraint only after backfill is complete
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;

-- Never in one step: ALTER TABLE users ADD COLUMN phone VARCHAR(20) NOT NULL
-- This locks the table for the entire migration
```

### Query Optimization Checklist
- `EXPLAIN ANALYZE` shows actual vs estimated rows — big differences = stale statistics
- `Seq Scan` on a large table = missing index
- `Hash Join` vs `Nested Loop` — Hash Join better for large sets
- `rows=1` in EXPLAIN with `LIMIT 1` = inefficient (no early exit)
- Run `ANALYZE table_name` to update statistics after large data changes
<!-- LEVEL 3 END -->
