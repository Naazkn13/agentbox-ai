---
id: rest-api
name: REST API Design
category: api-work
level1: "For designing and implementing REST APIs — routes, status codes, error handling"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**REST API Expert** — Activate for: REST endpoints, HTTP methods, status codes, request/response design, API error handling, versioning.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## REST API — Core Instructions

1. **Use correct HTTP methods:** GET (read), POST (create), PUT (full replace), PATCH (partial update), DELETE (remove).
2. **Return correct status codes:** 200 (ok), 201 (created), 204 (no content), 400 (bad request), 401 (unauthenticated), 403 (forbidden), 404 (not found), 409 (conflict), 422 (validation error), 500 (server error).
3. **Consistent error format:** always return `{ "error": "message", "code": "MACHINE_READABLE_CODE" }`.
4. **Validate at the boundary:** validate and sanitize all input before it touches business logic.
5. **Never expose internal errors** to clients — log the full error server-side, return a generic message.
6. **Resource URLs are nouns, not verbs:** `/users/123` not `/getUser?id=123`.
7. **Pagination on all list endpoints:** default `limit=20`, max `limit=100`. Return `{ data: [], total, page, limit }`.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## REST API — Full Reference

### URL Structure
```
GET    /api/v1/users           → list users (paginated)
POST   /api/v1/users           → create user
GET    /api/v1/users/:id       → get user by ID
PUT    /api/v1/users/:id       → replace user
PATCH  /api/v1/users/:id       → partial update
DELETE /api/v1/users/:id       → delete user
GET    /api/v1/users/:id/posts → get user's posts (nested resource)
```

### Status Code Reference
```
2xx Success
  200 OK             — GET, PUT, PATCH success
  201 Created        — POST success (include Location header)
  204 No Content     — DELETE success, or PATCH with no response body

4xx Client Error
  400 Bad Request    — malformed request syntax
  401 Unauthorized   — not authenticated (missing/invalid token)
  403 Forbidden      — authenticated but lacks permission
  404 Not Found      — resource doesn't exist
  409 Conflict       — duplicate entry, optimistic lock failure
  422 Unprocessable  — validation errors (return field-level errors)
  429 Too Many Reqs  — rate limited

5xx Server Error
  500 Internal Error — unexpected server error (never expose details)
  503 Unavailable    — service temporarily down
```

### Standard Error Response
```json
{
  "error": "Email address is already in use",
  "code": "EMAIL_DUPLICATE",
  "field": "email"
}
```

### Pagination Response
```json
{
  "data": [...],
  "pagination": {
    "total": 150,
    "page": 2,
    "limit": 20,
    "pages": 8
  }
}
```

### Security Checklist
- Rate limiting on all public endpoints
- Authentication required on all non-public endpoints
- Input validation before any DB query
- Never log request bodies that may contain passwords/tokens
- CORS: whitelist specific origins, never `*` in production
<!-- LEVEL 3 END -->
