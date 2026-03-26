---
id: auth-jwt
name: Auth & JWT Expert
category: security
level1: "For JWT tokens, authentication flows, refresh tokens, and session security"
platforms: [claude-code, cursor, codex, gemini-cli]
priority: 1
---

<!-- LEVEL 1 START -->
**Auth & JWT Expert** — Activate for: JWT tokens, authentication, refresh tokens, OAuth, session management, password hashing, bcrypt.
<!-- LEVEL 1 END -->

<!-- LEVEL 2 START -->
## Auth & JWT — Core Instructions

1. **Short-lived access tokens** (15 minutes), long-lived refresh tokens (7–30 days) in httpOnly cookies.
2. **Never store JWTs in localStorage** — vulnerable to XSS. Use httpOnly, Secure, SameSite=Strict cookies.
3. **Validate on EVERY request** — never trust a token without verifying signature + expiry.
4. **Rotate refresh tokens on use** (single-use) — invalidate the old one immediately on exchange.
5. **Hash passwords with bcrypt** (cost factor ≥ 12). Never MD5, SHA1, or plain SHA256 for passwords.
6. **JWT secret must be long + random** — min 256-bit entropy. Use env var, never hardcode.
7. **Include only necessary claims** in JWT payload — no sensitive data (email is fine, password hash is not).
<!-- LEVEL 2 END -->

<!-- LEVEL 3 START -->
## Auth & JWT — Full Reference

### Token Architecture
```
Access Token:  JWT, 15min TTL, stateless, in Authorization header
Refresh Token: opaque random string, 7d TTL, stored in Redis, httpOnly cookie
```

### JWT Implementation (Node.js)
```typescript
import jwt from 'jsonwebtoken';
import { randomBytes } from 'crypto';

const ACCESS_SECRET = process.env.JWT_ACCESS_SECRET!;   // 256-bit random
const REFRESH_SECRET = process.env.JWT_REFRESH_SECRET!;

// Sign access token
function signAccessToken(userId: string): string {
  return jwt.sign({ sub: userId }, ACCESS_SECRET, {
    expiresIn: '15m',
    algorithm: 'HS256',
  });
}

// Generate opaque refresh token
function generateRefreshToken(): string {
  return randomBytes(48).toString('hex'); // 96 hex chars
}

// Verify (throws on invalid/expired)
function verifyAccessToken(token: string): { sub: string } {
  return jwt.verify(token, ACCESS_SECRET) as { sub: string };
}
```

### Refresh Token Flow
```
1. POST /auth/login         → returns access_token + sets refresh_token cookie
2. GET  /protected          → sends access_token in Authorization: Bearer header
3. 401 Unauthorized         → access_token expired
4. POST /auth/refresh        → sends refresh_token cookie → returns new access_token
                              → old refresh_token invalidated in Redis
                              → new refresh_token set in cookie
5. POST /auth/logout         → invalidate refresh_token in Redis, clear cookie
```

### Password Hashing
```typescript
import bcrypt from 'bcrypt';

const COST_FACTOR = 12; // ~300ms on modern hardware — tune as hardware improves

const hash = await bcrypt.hash(password, COST_FACTOR);
const isValid = await bcrypt.compare(inputPassword, hash); // timing-safe
```

### Security Checklist
- [ ] Access tokens: 15min or less
- [ ] Refresh tokens: httpOnly, Secure, SameSite=Strict cookie
- [ ] JWT secret: 256-bit entropy minimum, stored in env var
- [ ] Refresh token rotation on every use
- [ ] bcrypt cost factor ≥ 12
- [ ] Rate limiting on login/refresh endpoints (10 req/15min per IP)
- [ ] Logout invalidates refresh token in server-side store
<!-- LEVEL 3 END -->
