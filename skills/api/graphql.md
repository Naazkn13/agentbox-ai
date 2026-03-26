---
id: graphql
name: GraphQL Expert
category: api-work
level1: "For GraphQL schemas, resolvers, queries, mutations, and subscriptions"
platforms: [claude-code, cursor, codex]
priority: 2
---

<!-- LEVEL 1 START -->
**GraphQL Expert** — Activate for: GraphQL schema design, resolvers, queries, mutations, subscriptions, DataLoader, N+1 problems.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## GraphQL — Core Instructions

1. **Schema first:** define types before writing resolvers. The schema is the contract.
2. **Use DataLoader for every relation** to batch and cache DB calls — the #1 GraphQL performance fix.
3. **Never return null for list fields** — return an empty array `[]` instead.
4. **Errors:** use `extensions` on GraphQL errors for machine-readable codes. Don't throw raw DB errors.
5. **Input types for mutations:** always use a dedicated `input` type, not individual args.
6. **Pagination:** use cursor-based pagination (Relay spec) for large datasets, not offset.
7. **Authorization in resolvers**, not schema — check permissions before resolving any sensitive field.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## GraphQL — Full Reference

### Schema Patterns
```graphql
type User {
  id: ID!
  email: String!
  posts: [Post!]!          # Never nullable list
}

type Post {
  id: ID!
  title: String!
  author: User!
}

input CreateUserInput {
  email: String!
  password: String!
  name: String
}

type Mutation {
  createUser(input: CreateUserInput!): User!
  updateUser(id: ID!, input: UpdateUserInput!): User!
}

type Query {
  user(id: ID!): User      # nullable — user may not exist
  users(first: Int, after: String): UserConnection!
}
```

### DataLoader (N+1 fix)
```typescript
// Without DataLoader: N+1 queries (1 query per post's author)
// With DataLoader: 1 batched query for all authors

const userLoader = new DataLoader(async (userIds: string[]) => {
  const users = await db.users.findMany({ where: { id: { in: userIds } } });
  return userIds.map(id => users.find(u => u.id === id) ?? null);
});

// In resolver:
author: (post, _, { loaders }) => loaders.user.load(post.authorId)
```

### Error Handling
```typescript
import { GraphQLError } from 'graphql';

throw new GraphQLError('User not found', {
  extensions: { code: 'USER_NOT_FOUND', http: { status: 404 } }
});
```

### Cursor Pagination (Relay spec)
```typescript
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
}
type UserEdge { node: User!; cursor: String! }
type PageInfo { hasNextPage: Boolean!; endCursor: String }
```
<!-- LEVEL 3 END -->
