---
id: prisma-orm
name: Prisma ORM Expert
category: db-work
level1: "For Prisma schema, migrations, relations, and query patterns"
platforms: [claude-code, cursor, codex]
priority: 1
---

<!-- LEVEL 1 START -->
**Prisma Expert** — Activate for: Prisma schema design, `prisma migrate`, relations, `findMany`/`create`/`upsert`, type-safe queries.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Prisma — Core Instructions

1. **Run `prisma generate` after every schema change** — the client won't reflect your changes otherwise.
2. **Use `prisma migrate dev` in development**, `prisma migrate deploy` in production — never use `db push` in production.
3. **Optional relations:** use `?` on the field type (`User?`) and include the foreign key field explicitly.
4. **N+1 fix:** use `include` to eager-load relations in a single query, not nested `findUnique` calls.
5. **Transactions for multi-step writes:** use `prisma.$transaction([...])` or interactive transactions.
6. **Rollback a migration:** `prisma migrate resolve --rolled-back <migration_name>` then fix and re-run.
7. **Never edit migration files** after they've been applied — create a new migration instead.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Prisma — Full Reference

### Schema Patterns
```prisma
model User {
  id        String   @id @default(cuid())
  email     String   @unique
  createdAt DateTime @default(now())
  posts     Post[]
  profile   Profile? // optional one-to-one
}

model Post {
  id       String  @id @default(cuid())
  title    String
  authorId String
  author   User    @relation(fields: [authorId], references: [id])

  @@index([authorId]) // always index foreign keys
}
```

### Query Patterns
```typescript
// Eager load relations (avoids N+1)
const users = await prisma.user.findMany({
  include: { posts: true, profile: true },
  where: { email: { contains: '@acme.com' } },
  orderBy: { createdAt: 'desc' },
  take: 20,
  skip: 0,
});

// Upsert
await prisma.user.upsert({
  where: { email: 'a@b.com' },
  update: { name: 'Alice' },
  create: { email: 'a@b.com', name: 'Alice' },
});

// Transaction
await prisma.$transaction([
  prisma.post.delete({ where: { id: postId } }),
  prisma.user.update({ where: { id: userId }, data: { postCount: { decrement: 1 } } }),
]);
```

### Migration Commands
```bash
npx prisma migrate dev --name add_phone_to_users  # dev migration
npx prisma migrate deploy                          # production deploy
npx prisma migrate resolve --rolled-back <name>    # mark as rolled back
npx prisma db seed                                 # run seed script
npx prisma studio                                  # GUI browser for DB
```

### Common Gotchas
- Forgot `prisma generate` → TypeScript types are stale
- Using `db push` in prod → no migration history, can't rollback
- Not indexing `@relation` foreign keys → slow joins on large tables
- Using `prisma.user.findUnique` inside a loop → N+1 problem, use `findMany` with `in`
<!-- LEVEL 3 END -->
