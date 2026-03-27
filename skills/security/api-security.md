---
id: api-security
name: API Security Expert
category: security
level1: "For rate limiting, input validation, CORS, API key management, OAuth 2.0 scopes, and SSRF prevention"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**API Security Expert** — Activate for: rate limiting, input validation, output encoding, SQL injection prevention, CORS configuration, API key management, OAuth 2.0 scopes, SSRF prevention.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## API Security — Core Instructions

1. **Validate all input at the boundary** — use a schema validation library (Zod, Joi, Pydantic) and reject requests that fail validation before any business logic runs.
2. **Rate-limit every public endpoint** — apply per-IP and per-user limits; use sliding-window counters in Redis; return 429 with `Retry-After` header.
3. **Configure CORS explicitly** — never use wildcard `*` in production; enumerate allowed origins, methods, and headers; reflect `Origin` only after whitelist check.
4. **Rotate and scope API keys** — generate keys with `crypto.randomBytes`, store only the hash; issue separate keys per consumer with minimal permission scopes.
5. **Enforce OAuth 2.0 scopes** — check required scope on every protected route; reject tokens missing the required scope with 403, not 401.
6. **Encode output to prevent injection** — HTML-encode in HTML responses, JSON-encode for JSON (automatic with `res.json()`), avoid building response strings manually.
7. **Block SSRF via strict URL validation** — whitelist allowed upstream hosts; reject private/loopback IPs; disable redirects on outbound HTTP clients.
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## API Security — Full Reference

### Input Validation with Zod (TypeScript)
```typescript
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email().max(254),
  password: z.string().min(8).max(128),
  role: z.enum(['user', 'admin']).default('user'),
});

app.post('/api/users', (req, res) => {
  const result = CreateUserSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json({ errors: result.error.flatten() });
  }
  const { email, password, role } = result.data;  // type-safe, validated
  // ... proceed
});
```

### Rate Limiting with Redis (Express)
```typescript
import { RateLimiterRedis } from 'rate-limiter-flexible';
import Redis from 'ioredis';

const redis = new Redis();
const limiter = new RateLimiterRedis({
  storeClient: redis,
  keyPrefix: 'rl_api',
  points: 100,         // requests
  duration: 60,        // per 60 seconds per key
});

const rateLimitMiddleware = async (req, res, next) => {
  try {
    await limiter.consume(req.ip);
    next();
  } catch (rej) {
    res.set('Retry-After', Math.ceil(rej.msBeforeNext / 1000));
    res.status(429).json({ error: 'Too many requests' });
  }
};
```

### CORS Configuration
```typescript
import cors from 'cors';

const ALLOWED_ORIGINS = new Set([
  'https://app.example.com',
  'https://admin.example.com',
]);

app.use(cors({
  origin: (origin, callback) => {
    if (!origin || ALLOWED_ORIGINS.has(origin)) {
      callback(null, true);
    } else {
      callback(new Error('Not allowed by CORS'));
    }
  },
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  allowedHeaders: ['Content-Type', 'Authorization'],
  credentials: true,
  maxAge: 86400,  // preflight cache 24h
}));
```

### API Key Generation and Verification
```typescript
import crypto from 'crypto';
import bcrypt from 'bcrypt';

// Generate — return plaintext once, store hash
function generateApiKey(): { key: string; hash: string } {
  const key = `ak_live_${crypto.randomBytes(32).toString('hex')}`;
  const hash = bcrypt.hashSync(key, 10);
  return { key, hash };
}

// Verify — constant-time comparison via bcrypt
async function verifyApiKey(provided: string, storedHash: string): Promise<boolean> {
  return bcrypt.compare(provided, storedHash);
}
```

### OAuth 2.0 Scope Enforcement
```typescript
function requireScope(scope: string) {
  return (req: Request, res: Response, next: NextFunction) => {
    const tokenScopes: string[] = req.auth?.scopes ?? [];
    if (!tokenScopes.includes(scope)) {
      return res.status(403).json({
        error: 'insufficient_scope',
        required: scope,
      });
    }
    next();
  };
}

// Usage
app.delete('/api/users/:id',
  requireAuth,
  requireScope('users:delete'),
  deleteUserHandler,
);
```

### Input Validation with Pydantic (FastAPI)
```python
from pydantic import BaseModel, EmailStr, constr, validator
from fastapi import FastAPI

app = FastAPI()

class CreateUserRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=128)
    name: constr(strip_whitespace=True, max_length=100)

    @validator('password')
    def password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        return v

@app.post('/users')
async def create_user(body: CreateUserRequest):
    # body is fully validated before handler runs
    ...
```

### Anti-patterns to Avoid
- Using `Access-Control-Allow-Origin: *` with `Access-Control-Allow-Credentials: true`
- Returning detailed error messages (stack traces, SQL errors) to API consumers
- Storing API keys in plaintext in the database
- Applying rate limiting only at the application layer (bypass via proxy) — also enforce at gateway
- Trusting `Content-Type` header without validating the actual body structure
- Skipping input validation on "internal" endpoints that could be reached by lateral movement
- Using GET requests for state-changing operations (CSRF and caching risk)
<!-- LEVEL 3 END -->
